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
_INGESTIBLE_RELEVANCE = {"Direct Match", "Zone Context", "National Context"}
CONFIDENCE_THRESHOLD  = 0.6


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
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


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

    # ── Step 2: Score relevance ───────────────────────────────────────────────
    add("Filter", f"Scoring {len(articles)} articles for governance relevance via {llm_used.upper()}")
    relevant, dropped = [], 0
    for art in articles[:req.max_articles]:
        snippet = f"{art.get('title','')} {art.get('snippet','')}"
        scored  = ai_service.score_evidence(text=snippet, asset_name=req.topic, ward_name="India")
        rel     = scored.get("relevance", "")
        if rel in _INGESTIBLE_RELEVANCE:
            art["relevance"]  = rel
            art["confidence"] = scored.get("confidence", 0.5)
            relevant.append(art)
        else:
            dropped += 1

    if not relevant:
        add("Filter", f"All {dropped} articles unrelated — nothing to extract", "warn")
        return AgenticResponse(steps=steps, entities_created=0, relations_created=0,
                               entities_skipped=0, duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    whitelisted_count = sum(1 for a in relevant if a.get("whitelisted", False))
    add("Filter",
        f"Kept {len(relevant)} relevant · dropped {dropped} unrelated · "
        f"{whitelisted_count}/{len(relevant)} from whitelisted gov sources",
        "ok" if whitelisted_count > 0 else "warn")

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

                canonical_id = resolve_entity_id(
                    raw_id=ent.get("id", ""), name=name, label=label, session=session
                )
                id_field = _LABEL_ID_FIELD.get(label, f"{label.lower()}_id")

                # Check if exists
                existing = session.run(
                    f"MATCH (n:{label} {{{id_field}: $id}}) RETURN n LIMIT 1",
                    id=canonical_id
                ).single()

                audit_props = {
                    **props,
                    id_field:     canonical_id,
                    "source":     "agentic_ingestion",
                    "ingested_at": _now(),
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

                    # VerificationAgent
                    vr = VerificationAgent.verify(label, canonical_id, props, session)
                    if vr.action == "CONFLICT_FLAGGED":
                        conflict_count += 1
                else:
                    entities_skipped += 1

            # Relations
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
                    """, fid=fid, tid=tid, ts=_now()).single()
                    if r:
                        relations_created += 1
                except Exception:
                    pass

    except Exception as e:
        add("Graph Check", f"Neo4j error: {e}", "warn")
        return AgenticResponse(steps=steps, entities_created=entities_created,
                               relations_created=relations_created,
                               entities_skipped=entities_skipped,
                               duration_s=round(time.time()-t0, 2),
                               llm_used=llm_used, topic=req.topic)

    add("Graph Check",
        f"{new_count} new nodes created · {existing_count} existing corroborated"
        + (f" · {conflict_count} conflicts flagged" if conflict_count else ""),
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
