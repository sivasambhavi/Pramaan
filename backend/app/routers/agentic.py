"""
agentic.py — PRAMAAN Agentic Ingestion Router

POST /ingest/agentic
  Runs a multi-step agent loop:
    Step 1: Fetch news articles for topic
    Step 2: Score relevance (drop unrelated)
    Step 3: Detect if topic is an ongoing crisis → route to crisis pipeline
    Step 4: Extract entities + relations via Ollama → Groq fallback
    Step 5: Check graph — existing nodes vs new
    Step 6: Ingest + VerificationAgent (Bayesian confidence, conflict detection)
    Step 7: Infer cross-domain CONNECTED_TO edges for new events
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

    # ── Step 3: Crisis detection — semantic route to crisis pipeline if ongoing event ──
    # Construct snippet early for the classifier
    combined_for_crisis = "\n\n".join(
        f"Headline: {a['title']}\nSummary: {a.get('snippet','')}" for a in relevant
    )

    is_crisis = ai_service.is_crisis(combined_for_crisis, topic=req.topic)
    matched_crisis_event_id = None

    if is_crisis:
        from app.neo4j_client import get_session as _get_session
        with _get_session() as sess:
            matched_crisis_event_id = resolve_entity_id(
                raw_id=f"evt_{req.topic.replace(' ', '_').lower().strip()}",
                name=req.topic,
                label="Event",
                session=sess
            )

    if matched_crisis_event_id:
        add("Crisis Route",
            f"Topic evaluated as ongoing crisis ({matched_crisis_event_id}) — extracting sub-events via crisis pipeline",
            "ok")
        try:
            crisis_extracted = ai_service.extract_crisis_update(
                text=combined_for_crisis,
                parent_event_id=matched_crisis_event_id,
                parent_event_name=matched_crisis_event_id,
            )
            se_count  = len(crisis_extracted.get("subevents",  []))
            ind_count = len(crisis_extracted.get("indicators", []))
            dec_count = len(crisis_extracted.get("decisions",  []))

            ts_now = _now_iso()
            with _get_session() as sess:
                # Get last SubEvent for PRECEDES chain
                last_row = sess.run("""
                    MATCH (e:Event {event_id: $eid})-[:CONTAINS]->(se:SubEvent)
                    RETURN se ORDER BY se.day_number DESC LIMIT 1
                """, eid=matched_crisis_event_id).single()
                prev_se_id = dict(last_row["se"])["subevent_id"] if last_row else None

                for se in crisis_extracted.get("subevents", []):
                    sid = se.get("subevent_id","")
                    if not sid:
                        continue
                    sess.run("""
                        MERGE (n:SubEvent {subevent_id: $sid})
                        SET n.name = $name, n.date = $date, n.category = $cat,
                            n.description = $desc, n.severity = $sev,
                            n.india_impact = $impact,
                            n.source = 'live_ingested', n.ingested_at = $ts
                        WITH n
                        MATCH (e:Event {event_id: $eid})
                        MERGE (e)-[r:CONTAINS]->(n) SET r.ingested_at = $ts
                    """, sid=sid, name=se.get("name",""), date=se.get("date",""),
                         cat=se.get("category",""), desc=se.get("description",""),
                         sev=se.get("severity","medium"), impact=se.get("india_impact",""),
                         eid=matched_crisis_event_id, ts=ts_now)
                    if prev_se_id and prev_se_id != sid:
                        sess.run("""
                            MATCH (a:SubEvent {subevent_id: $a})
                            MATCH (b:SubEvent {subevent_id: $b})
                            MERGE (a)-[r:PRECEDES]->(b) SET r.ingested_at = $ts
                        """, a=prev_se_id, b=sid, ts=ts_now)
                    prev_se_id = sid
                    relations_created += 1

                for ind in crisis_extracted.get("indicators", []):
                    iid = ind.get("indicator_id","")
                    if not iid:
                        continue
                    sess.run("""
                        MERGE (n:Indicator {indicator_id: $iid})
                        SET n.name=$name, n.value=$val, n.unit=$unit,
                            n.trend=$trend, n.as_of=$as_of,
                            n.source='live_ingested', n.ingested_at=$ts
                        WITH n
                        MATCH (e:Event {event_id: $eid})
                        MERGE (e)-[r:SIGNALS]->(n) SET r.ingested_at=$ts
                    """, iid=iid, name=ind.get("name",""), val=float(ind.get("value",0)),
                         unit=ind.get("unit",""), trend=ind.get("trend",""),
                         as_of=ind.get("as_of",""), eid=matched_crisis_event_id, ts=ts_now)
                    entities_created += 1

                for dec in crisis_extracted.get("decisions", []):
                    did = dec.get("decision_id","")
                    if not did:
                        continue
                    sess.run("""
                        MERGE (n:Decision {decision_id: $did})
                        SET n.name=$name, n.date=$date, n.status=$status,
                            n.description=$desc,
                            n.source='live_ingested', n.ingested_at=$ts
                        WITH n
                        MATCH (e:Event {event_id: $eid})
                        MERGE (n)-[r:RESPONDS_TO]->(e) SET r.ingested_at=$ts
                    """, did=did, name=dec.get("name",""), date=dec.get("date",""),
                         status=dec.get("status",""), desc=dec.get("description",""),
                         eid=matched_crisis_event_id, ts=ts_now)
                    entities_created += 1

            add("Crisis Route",
                f"Stored {se_count} sub-events · {ind_count} indicators · {dec_count} decisions → {matched_crisis_event_id}",
                "ok")
        except Exception as ex:
            add("Crisis Route", f"Crisis extraction failed: {ex}", "warn")

        duration = round(time.time() - t0, 2)
        add("Done",
            f"Crisis update complete in {duration}s — LLM: {llm_used.upper()}", "ok")
        return AgenticResponse(
            steps=steps, entities_created=entities_created,
            relations_created=relations_created, entities_skipped=entities_skipped,
            duration_s=duration, llm_used=llm_used, topic=req.topic,
        )

    # ── Step 4: Extract entities (non-crisis path) ────────────────────────────
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

                # Resolve canonical ID, handling Event duplicates by remapping instead of skipping
                canonical_id = ""
                if label == "Event":
                    is_dup, dup_id = _is_duplicate_event(name, session)
                    if is_dup and dup_id:
                        log.info("[agent] Duplicate event matched! Merging %r into existing %s", name, dup_id)
                        canonical_id = dup_id
                        
                if not canonical_id:
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
                    "source":      "live_ingested",
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
                    # Track all Events (new + existing) for edge wiring
                    # Existing events may be missing edges if ingested before the fix
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

    # ── Step 6: Relations ─────────────────────────────────────────────────────
    add("Relations", f"{relations_created} relationships written to graph", "ok")

    # ── Step 7: Cross-domain CONNECTED_TO inference for new events ────────────
    if ingested_events and new_count > 0:
        add("Connect", f"Inferring cross-domain links for {new_count} new event(s) via {llm_used.upper()}")
        try:
            from app.neo4j_client import get_session as _get_session2
            with _get_session2() as sess2:
                # Fetch all existing events for comparison context
                all_events = sess2.run("""
                    MATCH (e:Event)
                    RETURN e.event_id AS id, e.name AS name,
                           e.domain AS domain, e.description AS description
                """).data()

            for new_evt_id, new_evt_props in ingested_events:
                if not any(e["id"] == new_evt_id for e in all_events):
                    continue  # shouldn't happen but guard

                new_name = new_evt_props.get("name", new_evt_id)
                new_desc = new_evt_props.get("description", "")
                new_domain = new_evt_props.get("domain", "")

                # Build existing events context (exclude the new event itself)
                candidates = [
                    e for e in all_events if e["id"] != new_evt_id
                ]
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
  Name:        {new_name}
  Domain:      {new_domain}
  Description: {new_desc}

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
                conn_result = {}
                if ai_service.ollama_available:
                    try:
                        import json as _json
                        raw = ai_service._call_ollama(connection_prompt)
                        conn_result = _json.loads(raw.strip())
                    except Exception:
                        pass
                if not conn_result and ai_service.client:
                    try:
                        import json as _json
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
                        import json as _json
                        raw = ai_service._call_gemini(connection_prompt)
                        conn_result = _json.loads(raw.strip())
                    except Exception:
                        pass

                connections = conn_result.get("connections", [])
                conn_created = 0
                with _get_session2() as sess3:
                    for conn in connections[:4]:
                        to_id = conn.get("to_event_id","")
                        reason = conn.get("reason","")
                        if not to_id or not reason:
                            continue
                        try:
                            r = sess3.run("""
                                MATCH (a:Event {event_id: $aid})
                                MATCH (b:Event {event_id: $bid})
                                MERGE (a)-[r:CONNECTED_TO]->(b)
                                SET r.reason = $reason, r.ingested_at = $ts
                                RETURN r
                            """, aid=new_evt_id, bid=to_id, reason=reason,
                                 ts=_now_iso()).single()
                            if r:
                                conn_created += 1
                                relations_created += 1
                        except Exception:
                            pass

                if conn_created:
                    add("Connect",
                        f"{new_evt_id} → {conn_created} cross-domain link(s) created", "ok")

        except Exception as ex:
            add("Connect", f"Connection inference failed: {ex}", "warn")

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
