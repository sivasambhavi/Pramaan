"""
PRAMAAN — Background Scheduler
Runs two recurring jobs:
  1. news_refresh   — every 6 hours: scrape governance news → extract ontology → auto-ingest to Neo4j
  2. govdata_refresh — every 24 hours: re-run full data pipeline (fetch → transform → validate → load)

Wire into FastAPI via lifespan (see main.py).
"""

import subprocess
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.neo4j_client import get_session
from app.queries import build_merge_entity_query, build_merge_relation_query, SOURCE_CONFIDENCE
from app.services.news_service import news_service
from app.services.ai_service import ai_service

log = logging.getLogger("pramaan.scheduler")

# Project root (scheduler.py lives at backend/app/services/)
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_PIPELINE     = _PROJECT_ROOT / "data" / "scripts" / "pipeline.py"
_PYTHON       = sys.executable

# ── Load config from config/pipeline_config.yaml ─────────────────────────────
def _load_config() -> dict:
    cfg_path = _PROJECT_ROOT / "config" / "pipeline_config.yaml"
    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    log.warning("[scheduler] config/pipeline_config.yaml not found — using defaults")
    return {}

_CFG = _load_config()

# ── Build NEWS_QUERIES from active RSS feeds + query templates ────────────────
def _build_news_queries() -> list[str]:
    queries = []
    templates = _CFG.get("news_query_templates", [])
    active_states = [s for s in _CFG.get("states", []) if s.get("active")]

    for state in active_states:
        state_name = state["name"]
        for tmpl in templates:
            q = tmpl.replace("{state}", state_name).replace("{city}", state_name) \
                    .replace("{ward}", "ward").replace("{scheme}", "AMRUT")
            queries.append(q)

    # Fallback if config is empty
    if not queries:
        queries = [
            "MCD Shahdara drain road infrastructure 2025",
            "Delhi AMRUT water body encroachment 2025",
            "Swachh Bharat toilet construction Delhi ward 2025",
            "PMAY housing Delhi progress 2025",
        ]
    return queries

# ── Active RSS feed URLs from config ─────────────────────────────────────────
def _get_active_rss_urls() -> list[dict]:
    return [f for f in _CFG.get("rss_feeds", []) if f.get("active")]


# ── Job 1: News refresh ───────────────────────────────────────────────────────

def _ingest_extracted(extracted: dict, source_type: str) -> tuple[int, int]:
    """Write ai_service extraction output straight to Neo4j. Returns (entities, relations) counts."""
    entities   = extracted.get("entities", [])
    relations  = extracted.get("relations", [])
    stamp = {
        "source_type": source_type,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "ingested_by": "scheduler",
    }
    ent_count = rel_count = 0
    with get_session() as session:
        for ent in entities:
            try:
                props = {**stamp, **ent.get("properties", {})}
                if "confidence" not in props:
                    log.warning("Skipping entity %r — no confidence", ent.get("id"))
                    continue
                query = build_merge_entity_query(ent.get("label", "Entity"))
                session.run(query, id=ent["id"], properties=props)
                ent_count += 1
            except Exception as e:
                log.warning("Entity ingest error: %s", e)

        base_confidence = SOURCE_CONFIDENCE.get(source_type, 0.6)
        now = stamp["ingested_at"]
        for rel in relations:
            try:
                query = build_merge_relation_query(
                    rel["type"],
                    from_label=rel.get("from_label", "Entity"),
                    to_label=rel.get("to_label", "Entity"),
                )
                session.run(
                    query,
                    from_id=rel["from_id"],
                    to_id=rel["to_id"],
                    properties={},
                    source_type=source_type,
                    now=now,
                    base_confidence=base_confidence,
                )
                rel_count += 1
            except Exception as e:
                log.warning("Relation ingest error: %s", e)

    return ent_count, rel_count


def job_news_refresh():
    """Scrape governance news (RSS feeds + search queries) and auto-ingest extracted entities."""
    queries  = _build_news_queries()
    rss_list = _get_active_rss_urls()
    log.info("[scheduler] news_refresh — %d queries, %d RSS feeds", len(queries), len(rss_list))
    total_ent = total_rel = total_art = 0

    # ── Search-based news (Google News / generic) ──────────────────────────────
    for query in queries:
        try:
            articles = news_service.fetch_google_news(query)
            if not articles:
                continue
            total_art += len(articles)
            combined  = "\n\n".join(
                f"Headline: {a['title']}\nSummary: {a['summary']}" for a in articles
            )
            extracted = ai_service.extract_ontology(combined, source_type="unstructured_rss")
            e, r = _ingest_extracted(extracted, source_type="unstructured_rss")
            total_ent += e
            total_rel += r
        except Exception as exc:
            log.error("[scheduler] news_refresh query=%r error: %s", query, exc)

    # ── Direct RSS feed fetch ─────────────────────────────────────────────────
    for feed in rss_list:
        try:
            articles = news_service.fetch_rss(feed["url"])
            if not articles:
                continue
            total_art += len(articles)
            combined  = "\n\n".join(
                f"Headline: {a['title']}\nSummary: {a.get('summary','')}" for a in articles
            )
            extracted = ai_service.extract_ontology(combined, source_type="unstructured_rss")
            e, r = _ingest_extracted(extracted, source_type="unstructured_rss")
            total_ent += e
            total_rel += r
            log.info("[scheduler] RSS %r → %d entities", feed["name"], e)
        except Exception as exc:
            log.error("[scheduler] RSS feed=%r error: %s", feed.get("name"), exc)

    log.info(
        "[scheduler] news_refresh done — %d articles → %d entities, %d relations ingested",
        total_art, total_ent, total_rel,
    )


# ── Job 2: Govdata pipeline refresh ──────────────────────────────────────────

def job_govdata_refresh():
    """Run the full data pipeline: fetch → transform → validate → load into Neo4j."""
    log.info("[scheduler] govdata_refresh starting pipeline...")
    if not _PIPELINE.exists():
        log.error("[scheduler] pipeline.py not found at %s", _PIPELINE)
        return

    try:
        result = subprocess.run(
            [_PYTHON, str(_PIPELINE)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min hard limit
        )
        if result.returncode == 0:
            log.info("[scheduler] govdata_refresh pipeline SUCCESS")
        else:
            log.error(
                "[scheduler] govdata_refresh pipeline FAILED (exit %d):\n%s",
                result.returncode,
                result.stderr[-2000:],
            )
    except subprocess.TimeoutExpired:
        log.error("[scheduler] govdata_refresh timed out after 600s")
    except Exception as e:
        log.error("[scheduler] govdata_refresh error: %s", e)


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

_scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def start_scheduler():
    """Register jobs and start the scheduler. Call from FastAPI lifespan startup."""
    _scheduler.add_job(
        job_news_refresh,
        trigger=IntervalTrigger(hours=6),
        id="news_refresh",
        name="News scrape + auto-ingest",
        replace_existing=True,
        misfire_grace_time=300,  # allow 5 min late start
    )
    _scheduler.add_job(
        job_govdata_refresh,
        trigger=IntervalTrigger(hours=24),
        id="govdata_refresh",
        name="Govdata pipeline refresh",
        replace_existing=True,
        misfire_grace_time=600,
    )
    _scheduler.start()
    log.info("[scheduler] started — news_refresh every 6h, govdata_refresh every 24h")


def stop_scheduler():
    """Gracefully shut down. Call from FastAPI lifespan shutdown."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[scheduler] stopped")
