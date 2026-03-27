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
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.neo4j_client import get_session
from app.queries import (
    build_merge_entity_query, build_merge_relation_query,
    SOURCE_CONFIDENCE, validate_extracted,
    BLAST_SCORE_CYPHER,
)
from app.services.news_service import news_service
from app.services.ai_service import ai_service
from app.services.entity_resolver import resolve_entity_id
from app.services.verification_agent import VerificationAgent

log = logging.getLogger("pramaan.scheduler")

# Project root (scheduler.py lives at backend/app/services/)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
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

def _update_blast_scores() -> int:
    """
    Step 8: Re-compute blast_score for every Event node and persist it to Neo4j.
    Returns count of events updated.
    """
    since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        with get_session() as session:
            rows = session.run(BLAST_SCORE_CYPHER, {"since_24h": since_24h}).data()
        log.info("[scheduler] Step8 blast_scores — %d events updated", len(rows))
        return len(rows)
    except Exception as e:
        log.warning("[scheduler] Step8 blast_scores error: %s", e)
        return 0


def _infer_cross_domain_connections(new_event_ids: list[str]) -> int:
    """
    Step 7: For each newly ingested event, ask the LLM to infer CONNECTED_TO edges
    to existing events. Mirrors the same logic in agentic.py.
    Returns count of connections created.
    """
    import json as _json

    if not new_event_ids:
        return 0

    try:
        with get_session() as sess:
            all_events = sess.run("""
                MATCH (e:Event)
                RETURN e.event_id AS id, e.name AS name,
                       e.domain AS domain, e.description AS description
            """).data()
    except Exception as e:
        log.warning("[scheduler] Step7 — could not fetch events: %s", e)
        return 0

    all_event_map = {e["id"]: e for e in all_events}
    conn_total = 0
    ts = datetime.now(timezone.utc).isoformat()

    for new_evt_id in new_event_ids:
        new_evt = all_event_map.get(new_evt_id)
        if not new_evt:
            continue

        candidates = [e for e in all_events if e["id"] != new_evt_id]
        if not candidates:
            continue

        events_list = "\n".join(
            f"  {e['id']} [{e['domain']}]: {e['name']} — {(e['description'] or '')[:120]}"
            for e in candidates[:30]
        )

        connection_prompt = f"""
You are a strategic intelligence analyst for India's National Security Council.

A new event was ingested into the knowledge graph:
  ID:          {new_evt_id}
  Name:        {new_evt.get('name', '')}
  Domain:      {new_evt.get('domain', '')}
  Description: {new_evt.get('description', '')}

Existing events in the graph:
{events_list}

Task: Which of the existing events have a meaningful CAUSAL, STRATEGIC, or CONSEQUENTIAL
connection to the new event? Only include connections where the link is specific and
defensible — not just thematic similarity.

Return ONLY valid JSON:
{{
  "connections": [
    {{
      "to_event_id": "<existing event_id>",
      "reason": "<1-2 sentence specific reason why these events are connected>"
    }}
  ]
}}

Rules:
- Maximum 4 connections per new event.
- Do NOT connect events just because they happened in the same year or same domain.
- Each connection must have a specific causal, escalatory, or consequential link.
- If no strong connections exist, return an empty list.
"""
        conn_result: dict = {}

        if ai_service.ollama_available:
            try:
                raw = ai_service._call_ollama(connection_prompt)
                conn_result = _json.loads(raw.strip())
            except Exception:
                pass

        if not conn_result and ai_service.client:
            try:
                chat = ai_service.client.chat.completions.create(
                    messages=[{"role": "user", "content": connection_prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                conn_result = _json.loads(chat.choices[0].message.content)
            except Exception:
                pass

        if not conn_result and ai_service.gemini:
            try:
                raw = ai_service._call_gemini(connection_prompt)
                conn_result = _json.loads(raw.strip())
            except Exception:
                pass

        connections = conn_result.get("connections", [])
        if not connections:
            continue

        try:
            with get_session() as sess:
                for conn in connections[:4]:
                    to_id  = conn.get("to_event_id", "")
                    reason = conn.get("reason", "")
                    if not to_id or not reason:
                        continue
                    try:
                        r = sess.run("""
                            MATCH (a:Event {event_id: $aid})
                            MATCH (b:Event {event_id: $bid})
                            MERGE (a)-[rel:CONNECTED_TO]->(b)
                            SET rel.reason = $reason, rel.ingested_at = $ts
                            RETURN rel
                        """, aid=new_evt_id, bid=to_id, reason=reason, ts=ts).single()
                        if r:
                            conn_total += 1
                            log.info("[scheduler] Step7 CONNECTED_TO: %s → %s", new_evt_id, to_id)
                    except Exception as e:
                        log.warning("[scheduler] Step7 CONNECTED_TO write error: %s", e)
        except Exception as e:
            log.warning("[scheduler] Step7 session error: %s", e)

    return conn_total


def _ingest_extracted(extracted: dict, source_type: str) -> tuple[int, int, list[str]]:
    """
    Write ai_service extraction output to Neo4j with full validation pipeline:
      1. Schema validation (validate_extracted)
      2. Entity ID resolution (static map + fuzzy Neo4j match)
      3. Confidence threshold gate (drop < 0.5)
      4. MERGE entity into graph
      5. VerificationAgent (Bayesian update + conflict detection)
      6. Relation ID resolution + MERGE

    Returns (entities_written, relations_written, new_event_ids).
    """
    raw_entities = extracted.get("entities", [])
    raw_relations = extracted.get("relations", [])

    # ── Layer 1: Schema validation ────────────────────────────────────────────
    entities, relations, schema_dropped = validate_extracted(raw_entities, raw_relations)
    if schema_dropped:
        log.warning("[scheduler] %d entity/relation(s) failed schema validation", schema_dropped)

    stamp = {
        "source_type": source_type,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "ingested_by": "scheduler",
    }
    ent_count = rel_count = 0
    new_event_ids: list[str] = []
    base_confidence = SOURCE_CONFIDENCE.get(source_type, 0.6)
    now = stamp["ingested_at"]

    with get_session() as session:
        for ent in entities:
            try:
                label = ent.get("label", "")
                props = {**stamp, **ent.get("properties", {})}

                # ── Layer 2: Confidence threshold ─────────────────────────────
                conf = float(props.get("confidence", base_confidence))
                if conf < 0.5:
                    log.info("[scheduler] entity skipped — low confidence %.2f: %r", conf, ent.get("id"))
                    continue

                # ── Layer 3: Entity ID resolution ─────────────────────────────
                name = str(props.get("name", ent.get("id", "")))
                canonical_id = resolve_entity_id(
                    raw_id=ent.get("id", ""), name=name, label=label, session=session
                )

                # Track new Event IDs for Step 7 CONNECTED_TO inference
                if label == "Event":
                    existing = session.run(
                        "MATCH (e:Event {event_id: $id}) RETURN e.event_id LIMIT 1",
                        id=canonical_id,
                    ).single()
                    if not existing:
                        new_event_ids.append(canonical_id)

                query = build_merge_entity_query(label)
                session.run(query, id=canonical_id, properties=props)
                ent_count += 1

                # ── Layer 4: VerificationAgent ────────────────────────────────
                vr = VerificationAgent.verify(label, canonical_id, props, session)
                if vr.action == "CONFLICT_FLAGGED":
                    log.warning("[scheduler] CONFLICT on %s(%s): %s", label, canonical_id, vr.conflicts)

            except Exception as e:
                log.warning("[scheduler] Entity ingest error: %s", e)

        for rel in relations:
            try:
                fl    = rel.get("from_label", "")
                tl    = rel.get("to_label",   "")
                rtype = rel.get("type",        "")

                # ── Layer 5: Relation endpoint ID resolution ──────────────────
                fid = resolve_entity_id(raw_id=rel.get("from_id", ""), label=fl, session=session)
                tid = resolve_entity_id(raw_id=rel.get("to_id",   ""), label=tl, session=session)

                query = build_merge_relation_query(rtype, from_label=fl, to_label=tl)
                session.run(
                    query,
                    from_id=fid,
                    to_id=tid,
                    properties={},
                    source_type=source_type,
                    now=now,
                    base_confidence=base_confidence,
                )
                rel_count += 1
            except Exception as e:
                log.warning("[scheduler] Relation ingest error: %s", e)

    return ent_count, rel_count, new_event_ids


def job_news_refresh():
    """Scrape governance news (RSS feeds + search queries) and auto-ingest extracted entities."""
    queries  = _build_news_queries()
    rss_list = _get_active_rss_urls()
    log.info("[scheduler] news_refresh — %d queries, %d RSS feeds", len(queries), len(rss_list))
    total_ent = total_rel = total_art = 0
    all_new_event_ids: list[str] = []

    # ── Search-based news (Google News / generic) ──────────────────────────────
    for query in queries:
        try:
            articles = news_service.fetch_google_news(query)
            if not articles:
                continue
            total_art += len(articles)

            # Filter to India-relevant articles across all 7 domains
            relevant = []
            for a in articles:
                snippet = f"{a.get('title', '')} {a.get('summary', '')}"
                scored  = ai_service.classify_content(text=snippet, topic=query)
                if scored.get("relevant", False) and scored.get("confidence", 0) >= 0.4:
                    relevant.append(a)
            if not relevant:
                log.info("[scheduler] query=%r — all articles filtered out", query)
                continue

            combined  = "\n\n".join(
                f"Headline: {a['title']}\nSummary: {a.get('summary', '')}" for a in relevant
            )
            extracted = ai_service.extract_ontology(combined, source_type="unstructured_rss")
            e, r, new_evts = _ingest_extracted(extracted, source_type="unstructured_rss")
            total_ent += e
            total_rel += r
            all_new_event_ids.extend(new_evts)
            log.info("[scheduler] query=%r → %d/%d relevant → %d entities", query, len(relevant), len(articles), e)
        except Exception as exc:
            log.error("[scheduler] news_refresh query=%r error: %s", query, exc)

    # ── Direct RSS feed fetch ─────────────────────────────────────────────────
    for feed in rss_list:
        try:
            articles = news_service.fetch_rss(feed["url"])
            if not articles:
                continue
            total_art += len(articles)

            # Filter to India-relevant articles across all 7 domains
            relevant = []
            for a in articles:
                snippet = f"{a.get('title', '')} {a.get('summary', '')}"
                scored  = ai_service.classify_content(text=snippet, topic=feed.get("name", ""))
                if scored.get("relevant", False) and scored.get("confidence", 0) >= 0.4:
                    relevant.append(a)
            if not relevant:
                log.info("[scheduler] RSS %r — all articles filtered out", feed.get("name"))
                continue

            combined  = "\n\n".join(
                f"Headline: {a['title']}\nSummary: {a.get('summary', '')}" for a in relevant
            )
            extracted = ai_service.extract_ontology(combined, source_type="unstructured_rss")
            e, r, new_evts = _ingest_extracted(extracted, source_type="unstructured_rss")
            total_ent += e
            total_rel += r
            all_new_event_ids.extend(new_evts)
            log.info("[scheduler] RSS %r → %d/%d relevant → %d entities", feed["name"], len(relevant), len(articles), e)
        except Exception as exc:
            log.error("[scheduler] RSS feed=%r error: %s", feed.get("name"), exc)

    # ── Step 7: Cross-domain CONNECTED_TO inference for new events ────────────
    if all_new_event_ids:
        unique_new = list(dict.fromkeys(all_new_event_ids))  # deduplicate, preserve order
        log.info("[scheduler] Step7 — inferring cross-domain links for %d new event(s)", len(unique_new))
        try:
            conn_count = _infer_cross_domain_connections(unique_new)
            total_rel += conn_count
            log.info("[scheduler] Step7 — %d CONNECTED_TO edge(s) created", conn_count)
        except Exception as exc:
            log.error("[scheduler] Step7 error: %s", exc)

    # ── Step 8: Recompute blast_score on all Event nodes ─────────────────────
    try:
        updated = _update_blast_scores()
        log.info("[scheduler] Step8 — blast_score updated on %d events", updated)
    except Exception as exc:
        log.error("[scheduler] Step8 error: %s", exc)

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
        trigger=IntervalTrigger(hours=1),
        id="news_refresh",
        name="News scrape + auto-ingest",
        replace_existing=True,
        misfire_grace_time=300,
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
    log.info("[scheduler] started — news_refresh every 1h, govdata_refresh every 24h")


def stop_scheduler():
    """Gracefully shut down. Call from FastAPI lifespan shutdown."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[scheduler] stopped")


def set_news_refresh_interval(minutes: int) -> None:
    """Reschedule news_refresh at a new interval (in minutes)."""
    _scheduler.reschedule_job(
        "news_refresh",
        trigger=IntervalTrigger(minutes=minutes),
    )
    log.info("[scheduler] news_refresh rescheduled to every %d minutes", minutes)


def get_scheduler_status() -> dict:
    """Return current job schedules and next run times."""
    jobs = {}
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs[job.id] = {
            "name":     job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger":  str(job.trigger),
        }
    return {"running": _scheduler.running, "jobs": jobs}
