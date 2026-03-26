"""
agentic.py — PRAMAAN Agentic Ingestion Router

POST /ingest/agentic
  Runs a multi-step agent loop:
    Step 1: Fetch news articles for topic
    Step 2: Score relevance (drop unrelated)
    Step 3: Extract entities + relations via Ollama → Groq fallback
    Step 4: Check graph — existing nodes vs new
    Step 5: Ingest + VerificationAgent (Bayesian confidence, conflict detection)
  Returns full step trace + summary.
"""

import re
import logging
import time
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.news_service import news_service
from app.services.ai_service import ai_service
from app.services.entity_resolver import resolve_entity_id
from app.services.verification_agent import VerificationAgent
from app.queries import validate_extracted

log    = logging.getLogger("pramaan.agentic")
router = APIRouter(prefix="/ingest", tags=["agentic"])

_LABEL_ID_FIELD = {
    "Domain": "domain_id", "Region": "region_id", "Actor": "actor_id",
    "Scheme": "scheme_id", "Policy": "policy_id", "Event": "event_id",
    "Impact": "impact_id", "Evidence": "evidence_id", "Asset": "asset_id",
}
_ALLOWED_LABELS = {
    "Event", "Region", "Actor", "Scheme", "Policy",
    "Impact", "Evidence", "Asset", "Domain",
}
CONFIDENCE_THRESHOLD = 0.6

# Domain property value → Neo4j domain_id
_DOMAIN_ID_MAP = {
    "DOM_GEOPOLITICS": "DOM_GEOPOLITICS",
    "DOM_ECONOMICS":   "DOM_ECONOMICS",
    "DOM_DEFENSE":     "DOM_DEFENSE",
    "DOM_TECHNOLOGY":  "DOM_TECHNOLOGY",
    "DOM_CLIMATE":     "DOM_CLIMATE",
    "DOM_SOCIETY":     "DOM_SOCIETY",
    "DOM_GOVERNANCE":  "DOM_GOVERNANCE",
    # Also handle plain names in case LLM returns them
    "Geopolitics": "DOM_GEOPOLITICS",
    "Economics":   "DOM_ECONOMICS",
    "Defense":     "DOM_DEFENSE",
    "Technology":  "DOM_TECHNOLOGY",
    "Climate":     "DOM_CLIMATE",
    "Society":     "DOM_SOCIETY",
    "Governance":  "DOM_GOVERNANCE",
}

# Keyword → region_id for auto OCCURRED_IN inference
_KEYWORD_REGION: list[tuple[list[str], str]] = [
    (["iran", "tehran", "irgc", "hormuz", "persian gulf"], "REG_IRAN"),
    (["israel", "tel aviv", "idf", "gaza"],                "REG_ISRAEL"),
    (["pakistan", "islamabad", "isi", "lahore"],           "REG_PAKISTAN"),
    (["kashmir", "j&k", "jammu", "pok", "pojk", "loc"],   "REG_JK"),
    (["wayanad", "kerala"],                                 "REG_KERALA"),
    (["odisha", "cyclone dana", "puri"],                   "REG_ODISHA"),
    (["manipur"],                                           "REG_MANIPUR"),
    (["delhi", "yamuna", "shahdara"],                      "REG_DELHI"),
    (["joshimath", "uttarakhand", "chamoli"],              "REG_UTTARAKHAND"),
    (["uk", "britain", "london", "ceta"],                  "REG_UK"),
    (["china", "beijing"],                                 "REG_CHINA") if False else ([], ""),  # placeholder
    (["red sea", "bab el mandeb"],                         "REG_RED_SEA"),
    (["west asia", "middle east"],                         "REG_WEST_ASIA"),
    (["russia", "ukraine"],                                "REG_RUSSIA"),
]
# Remove empty placeholder
_KEYWORD_REGION = [(kws, rid) for kws, rid in _KEYWORD_REGION if kws]


def _infer_region(name: str, description: str = "") -> str:
    """Infer best-fit region_id from event name/description keywords. Falls back to REG_INDIA."""
    text = (name + " " + description).lower()
    for keywords, region_id in _KEYWORD_REGION:
        if any(kw in text for kw in keywords):
            return region_id
    return "REG_INDIA"


def _is_duplicate_event(name: str, session) -> tuple[bool, str]:
    """
    Check if an Event with a similar name already exists in Neo4j.
    Returns (is_duplicate, existing_event_id).
    Matches if >= 3 significant words overlap (words > 3 chars).
    """
    stopwords = {"the", "and", "for", "with", "from", "that", "this", "india", "2025", "2026", "2024"}
    new_words = {w for w in re.findall(r'\b\w{4,}\b', name.lower()) if w not in stopwords}
    if not new_words:
        return False, ""
    existing = session.run(
        "MATCH (n:Event) RETURN n.event_id AS id, n.name AS name"
    ).data()
    for row in existing:
        existing_name = (row.get("name") or "").lower()
        existing_words = {w for w in re.findall(r'\b\w{4,}\b', existing_name) if w not in stopwords}
        overlap = new_words & existing_words
        if len(overlap) >= 3:
            return True, row.get("id", "")
        # Also catch exact substring match (e.g. "Iran War" vs "Iran-US-Israel War")
        if name.lower() in existing_name or existing_name in name.lower():
            return True, row.get("id", "")
    return False, ""


class AgenticRequest(BaseModel):
    topic:       str
    max_articles: int = 6
    source_type:  str = "unstructured_rss"


class AgentStep(BaseModel):
    step:    int
    label:   str
    detail:  str
    status:  str   # "ok" | "warn" | "skip"
    ts:      str


class AgenticResponse(BaseModel):
    steps:             list[AgentStep]
    entities_created:  int
    relations_created: int
    entities_skipped:  int
    duration_s:        float
    llm_used:          str
    topic:             str


def _now() -> str:
    """Short HH:MM:SS for agent trace display."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def _now_iso() -> str:
    """Full ISO timestamp for ingested_at property (needed by _rel_time in frontend)."""
    return datetime.now(timezone.utc).isoformat()


@router.post("/agentic", response_model=AgenticResponse)
def run_agentic_ingestion(req: AgenticRequest) -> AgenticResponse:
    t0    = time.time()
    steps: list[AgentStep] = []
    step_n = 0

    def add(label: str, detail: str, status: str = "ok"):
        nonlocal step_n
        step_n += 1
        steps.append(AgentStep(step=step_n, label=label, detail=detail,
                               status=status, ts=_now()))
        log.info("[agent] Step %d [%s] %s", step_n, label, detail)

    entities_created  = 0
    relations_created = 0
    entities_skipped  = 0
    llm_used          = "ollama" if ai_service.ollama_available else ("groq" if ai_service.client else "gemini")

    # ── Step 1: Fetch news ────────────────────────────────────────────────────
    add("Fetch", f"Searching news for: {req.topic!r}")
    try:
        articles = news_service.fetch_google_news(req.topic)
    except Exception as e:
        add("Fetch", f"News fetch failed: {e}", "warn")
        articles = []

    if not articles:
        add("Fetch", "No articles found — nothing to ingest", "warn")
        return AgenticResponse(steps=steps, entities_created=0, relations_created=0,
                               entities_skipped=0, duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    add("Fetch", f"Found {len(articles)} articles from Google News", "ok")

    # ── Step 2: Classify relevance (domain-aware, all 7 domains) ────────────────
    add("Filter", f"Classifying {len(articles)} articles across 7 domains via {llm_used.upper()}")
    relevant, dropped = [], 0
    domain_counts: dict[str, int] = {}

    for art in articles[:req.max_articles]:
        snippet = f"{art.get('title', '')} {art.get('snippet', '')}"
        scored  = ai_service.classify_content(text=snippet, topic=req.topic)
        if scored.get("relevant", False) and scored.get("confidence", 0) >= 0.4:
            art["relevance"]  = scored.get("domain", "DOM_GOVERNANCE")
            art["confidence"] = scored.get("confidence", 0.5)
            relevant.append(art)
            domain_counts[art["relevance"]] = domain_counts.get(art["relevance"], 0) + 1
        else:
            dropped += 1

    if not relevant:
        add("Filter", f"All {dropped} articles unrelated to India — nothing to extract", "warn")
        return AgenticResponse(steps=steps, entities_created=0, relations_created=0,
                               entities_skipped=0, duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    domain_summary = " · ".join(f"{v}×{k.replace('DOM_', '')}" for k, v in domain_counts.items())
    add("Filter",
        f"Kept {len(relevant)} relevant · dropped {dropped} unrelated · domains: {domain_summary}",
        "ok")

    # ── Step 3: Extract entities ──────────────────────────────────────────────
    add("Extract", f"Extracting governance entities via {llm_used.upper()} · {len(relevant)} articles")
    combined = "\n\n".join(
        f"Headline: {a['title']}\nSummary: {a.get('snippet','')}" for a in relevant
    )
    try:
        extracted = ai_service.extract_ontology(combined, source_type=req.source_type)
    except Exception as e:
        add("Extract", f"Extraction failed: {e}", "warn")
        return AgenticResponse(steps=steps, entities_created=0, relations_created=0,
                               entities_skipped=0, duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    raw_entities  = extracted.get("entities",  [])
    raw_relations = extracted.get("relations", [])
    entities, relations, schema_dropped = validate_extracted(raw_entities, raw_relations)

    if not entities:
        add("Extract", "No entities extracted from articles", "warn")
        return AgenticResponse(steps=steps, entities_created=0, relations_created=0,
                               entities_skipped=0, duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    label_counts = {}
    for e in entities:
        label_counts[e.get("label","?")] = label_counts.get(e.get("label","?"), 0) + 1
    summary = " · ".join(f"{v} {k}" for k, v in label_counts.items())
    schema_note = f" · {schema_dropped} failed schema" if schema_dropped else ""
    add("Extract", f"Extracted {len(entities)} entities: {summary}{schema_note}", "ok")

    # ── Step 4: Check graph + ingest ──────────────────────────────────────────
    add("Graph Check", f"Checking {len(entities)} entities against Neo4j knowledge graph")

    from app.neo4j_client import get_session
    new_count = existing_count = conflict_count = 0

    # Track which event_ids were ingested so we can auto-wire edges after
    ingested_events: list[tuple[str, dict]] = []   # (canonical_id, props)
    duplicates_skipped = 0

    try:
        with get_session() as session:
            for ent in entities:
                label = ent.get("label", "")
                props = ent.get("properties", {})
                conf  = float(props.get("confidence", 1.0))
                name  = str(props.get("name", ent.get("id", "")))

                if label not in _ALLOWED_LABELS:
                    entities_skipped += 1
                    continue
                if conf < CONFIDENCE_THRESHOLD:
                    entities_skipped += 1
                    continue

                # Duplicate check for Events — skip if similar event already exists
                if label == "Event":
                    is_dup, dup_id = _is_duplicate_event(name, session)
                    if is_dup:
                        log.info("[agent] Duplicate event skipped: %r matches existing %s", name, dup_id)
                        duplicates_skipped += 1
                        entities_skipped += 1
                        continue

                canonical_id = resolve_entity_id(
                    raw_id=ent.get("id", ""), name=name, label=label, session=session
                )
                id_field = _LABEL_ID_FIELD.get(label, f"{label.lower()}_id")

                # Check if exists already
                existing = session.run(
                    f"MATCH (n:{label} {{{id_field}: $id}}) RETURN n LIMIT 1",
                    id=canonical_id
                ).single()

                audit_props = {
                    **props,
                    id_field:      canonical_id,
                    "source":      "agentic_ingestion",
                    "ingested_at": _now_iso(),
                }
                set_pairs = ", ".join(f"n.{k} = ${k}" for k, v in audit_props.items() if v is not None)
                cypher    = f"MERGE (n:{label} {{{id_field}: ${id_field}}}) SET {set_pairs} RETURN n"
                params    = {k: v for k, v in audit_props.items() if v is not None}

                result = session.run(cypher, params).single()
                if result:
                    entities_created += 1
                    if existing:
                        existing_count += 1
                    else:
                        new_count += 1
                        if label == "Event":
                            ingested_events.append((canonical_id, props))

                    # VerificationAgent
                    vr = VerificationAgent.verify(label, canonical_id, props, session)
                    if vr.action == "CONFLICT_FLAGGED":
                        conflict_count += 1
                else:
                    entities_skipped += 1

            # ── LLM-extracted relations ───────────────────────────────────────
            for rel in relations:
                fl = rel.get("from_label",""); tl = rel.get("to_label","")
                rt = rel.get("type","")
                if fl not in _ALLOWED_LABELS or tl not in _ALLOWED_LABELS:
                    continue
                fif = _LABEL_ID_FIELD.get(fl, f"{fl.lower()}_id")
                tif = _LABEL_ID_FIELD.get(tl, f"{tl.lower()}_id")
                fid = resolve_entity_id(raw_id=rel.get("from_id",""), label=fl, session=session)
                tid = resolve_entity_id(raw_id=rel.get("to_id",""),   label=tl, session=session)
                try:
                    r = session.run(f"""
                        MATCH (a:{fl} {{{fif}: $fid}})
                        MATCH (b:{tl} {{{tif}: $tid}})
                        MERGE (a)-[r:{rt}]->(b)
                        SET r.ingested_at = $ts
                        RETURN r
                    """, fid=fid, tid=tid, ts=_now_iso()).single()
                    if r:
                        relations_created += 1
                except Exception:
                    pass

            # ── Auto full-ontology edges for newly ingested Events ────────────
            # Collect event_ids that already have BELONGS_TO / OCCURRED_IN from LLM
            llm_rel_set: set[tuple[str, str]] = set()
            for rel in relations:
                if rel.get("from_label") == "Event" and rel.get("type") in ("BELONGS_TO", "OCCURRED_IN"):
                    llm_rel_set.add((rel.get("from_id",""), rel.get("type","")))

            for evt_id, evt_props in ingested_events:
                ts = _now_iso()

                # BELONGS_TO → Domain
                if (evt_id, "BELONGS_TO") not in llm_rel_set:
                    domain_val = evt_props.get("domain", "")
                    domain_id  = _DOMAIN_ID_MAP.get(domain_val, "DOM_GOVERNANCE")
                    try:
                        r = session.run("""
                            MATCH (e:Event {event_id: $eid})
                            MATCH (d:Domain {domain_id: $did})
                            MERGE (e)-[r:BELONGS_TO]->(d)
                            SET r.ingested_at = $ts
                            RETURN r
                        """, eid=evt_id, did=domain_id, ts=ts).single()
                        if r:
                            relations_created += 1
                    except Exception as ex:
                        log.warning("[agent] BELONGS_TO edge failed for %s: %s", evt_id, ex)

                # OCCURRED_IN → Region
                if (evt_id, "OCCURRED_IN") not in llm_rel_set:
                    region_id = _infer_region(
                        evt_props.get("name", ""),
                        evt_props.get("description", ""),
                    )
                    try:
                        r = session.run("""
                            MATCH (e:Event {event_id: $eid})
                            MATCH (rg:Region {region_id: $rid})
                            MERGE (e)-[r:OCCURRED_IN]->(rg)
                            SET r.ingested_at = $ts
                            RETURN r
                        """, eid=evt_id, rid=region_id, ts=ts).single()
                        if r:
                            relations_created += 1
                    except Exception as ex:
                        log.warning("[agent] OCCURRED_IN edge failed for %s: %s", evt_id, ex)

    except Exception as e:
        add("Graph Check", f"Neo4j error: {e}", "warn")
        return AgenticResponse(steps=steps, entities_created=entities_created,
                               relations_created=relations_created,
                               entities_skipped=entities_skipped,
                               duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    dup_note = f" · {duplicates_skipped} duplicates blocked" if duplicates_skipped else ""
    add("Graph Check",
        f"{new_count} new nodes created · {existing_count} existing corroborated"
        + (f" · {conflict_count} conflicts flagged" if conflict_count else "")
        + dup_note,
        "warn" if conflict_count else "ok")

    # ── Step 5: Relations ─────────────────────────────────────────────────────
    add("Relations", f"{relations_created} relationships written to graph", "ok")

    # ── Done ──────────────────────────────────────────────────────────────────
    duration = round(time.time() - t0, 2)
    add("Done",
        f"Agent complete in {duration}s — {entities_created} entities · {relations_created} relations · "
        f"{entities_skipped} skipped · LLM: {llm_used.upper()}", "ok")

    return AgenticResponse(
        steps=steps,
        entities_created=entities_created,
        relations_created=relations_created,
        entities_skipped=entities_skipped,
        duration_s=duration,
        llm_used=llm_used,
        topic=req.topic,
    )
