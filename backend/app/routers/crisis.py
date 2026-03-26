"""
crisis.py — PRAMAAN Crisis Intelligence Router

GET  /crisis/{event_id}           — Full crisis state: subevents, indicators, decisions
GET  /crisis/{event_id}/timeline  — SubEvent timeline ordered by day_number
POST /crisis/{event_id}/scenarios — AI-generated scenario analysis
POST /crisis/{event_id}/ingest    — Ingest a new news article as a crisis sub-event
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.neo4j_client import get_session
from app.services.ai_service import ai_service

log    = logging.getLogger("pramaan.crisis")
router = APIRouter(prefix="/crisis", tags=["crisis"])

_ONGOING_EVENTS = {
    "EVT_IRAN_WAR_2026",
    "EVT_IRAN_CEASEFIRE_TALKS_2026",
    "EVT_HORMUZ_BLOCKADE_2026",
    "EVT_INDIA_PAK_DIPLO_CRISIS_2025",
    "EVT_INDUS_WATERS_CRISIS_2025",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── GET /crisis/{event_id} ────────────────────────────────────────────────────
@router.get("/{event_id}")
def get_crisis_state(event_id: str) -> dict:
    """Full crisis snapshot: parent event, subevents, indicators, decisions."""
    with get_session() as s:
        # Parent event
        row = s.run(
            "MATCH (e:Event {event_id: $eid}) RETURN e",
            eid=event_id
        ).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        parent = dict(row["e"])

        # SubEvents (ordered by day_number)
        subevents = s.run("""
            MATCH (e:Event {event_id: $eid})-[:CONTAINS]->(se:SubEvent)
            RETURN se ORDER BY coalesce(se.day_number, 0) ASC
        """, eid=event_id).data()
        subevents = [dict(r["se"]) for r in subevents]

        # Indicators
        indicators = s.run("""
            MATCH (e:Event {event_id: $eid})-[:SIGNALS]->(ind:Indicator)
            RETURN ind ORDER BY ind.domain
        """, eid=event_id).data()
        indicators = [dict(r["ind"]) for r in indicators]

        # Decisions
        decisions = s.run("""
            MATCH (dec:Decision)-[:RESPONDS_TO]->(e:Event {event_id: $eid})
            OPTIONAL MATCH (a:Actor)-[:MADE]->(dec)
            RETURN dec, a.name AS actor_name ORDER BY dec.date DESC
        """, eid=event_id).data()
        decisions = [
            {**dict(r["dec"]), "actor_name": r["actor_name"]}
            for r in decisions
        ]

        # Connected events
        connected = s.run("""
            MATCH (e:Event {event_id: $eid})-[r:CONNECTED_TO]-(other:Event)
            RETURN other.event_id AS id, other.name AS name,
                   other.domain AS domain, r.reason AS reason
        """, eid=event_id).data()

        # Impact nodes from graph
        impacts = s.run("""
            MATCH (e:Event {event_id: $eid})-[:CAUSED]->(i:Impact)
            WHERE i.name IS NOT NULL
            RETURN i.impact_id AS id, i.name AS name,
                   i.domain AS domain, i.severity AS severity
        """, eid=event_id).data()

        return {
            "event":      parent,
            "subevents":  subevents,
            "indicators": indicators,
            "decisions":  decisions,
            "connected":  connected,
            "impacts":    impacts,
            "is_ongoing": event_id in _ONGOING_EVENTS,
        }


# ── GET /crisis/{event_id}/cascade ───────────────────────────────────────────
@router.get("/{event_id}/cascade")
def get_crisis_cascade(event_id: str) -> dict:
    """
    Traverse the ontology graph from a crisis event outward:
    Crisis → Connected Events → Domains → Schemes Activated → Actors Responding → Evidence
    Returns structured cascade layers for Sankey / chain visualization.
    """
    with get_session() as s:
        row = s.run("MATCH (e:Event {event_id: $eid}) RETURN e", eid=event_id).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        parent = dict(row["e"])

        # Layer 1: Direct impacts from this event
        impacts = s.run("""
            MATCH (e:Event {event_id: $eid})-[:CAUSED]->(i:Impact)
            WHERE i.name IS NOT NULL
            RETURN i.impact_id AS id, i.name AS name,
                   i.domain AS domain, i.severity AS severity
        """, eid=event_id).data()

        # Layer 2: Connected events (1-hop)
        connected_events = s.run("""
            MATCH (e:Event {event_id: $eid})-[r:CONNECTED_TO]-(other:Event)
            RETURN DISTINCT other.event_id AS id, other.name AS name,
                   other.domain AS domain, r.reason AS reason
        """, eid=event_id).data()

        # Layer 3: Schemes triggered by this event or connected events
        schemes = s.run("""
            MATCH (e:Event {event_id: $eid})-[:TRIGGERED]->(sc:Scheme)
            RETURN sc.scheme_id AS id, sc.name AS name,
                   sc.domain AS domain, sc.status AS status,
                   'direct' AS trigger_type
            UNION
            MATCH (e:Event {event_id: $eid})-[:CONNECTED_TO]-(other:Event)-[:TRIGGERED]->(sc:Scheme)
            WHERE sc.name IS NOT NULL
            RETURN sc.scheme_id AS id, sc.name AS name,
                   sc.domain AS domain, sc.status AS status,
                   other.name AS trigger_type
        """, eid=event_id).data()

        # Layer 4: Actors responding — via Decisions
        actors = s.run("""
            MATCH (a:Actor)-[:MADE]->(dec:Decision)-[:RESPONDS_TO]->(e:Event {event_id: $eid})
            RETURN DISTINCT a.actor_id AS id, a.name AS name,
                   a.domain AS domain,
                   collect(dec.name)[0..2] AS decisions,
                   count(dec) AS decision_count
        """, eid=event_id).data()

        # Layer 5: Evidence linked to this event
        evidence = s.run("""
            MATCH (e:Event {event_id: $eid})-[:PROVEN_BY]->(ev:Evidence)
            WHERE ev.name IS NOT NULL
            RETURN ev.evidence_id AS id, ev.name AS name,
                   ev.source AS source, ev.date AS date
            LIMIT 6
        """, eid=event_id).data()

        # Sankey links — (source_label, target_label, value, color)
        sankey_nodes, sankey_links = _build_sankey(
            event_id, parent.get("name",""), impacts,
            connected_events, schemes, actors
        )

        return {
            "event":            parent,
            "impacts":          impacts,
            "connected_events": connected_events,
            "schemes":          schemes,
            "actors":           actors,
            "evidence":         evidence,
            "sankey_nodes":     sankey_nodes,
            "sankey_links":     sankey_links,
        }


def _build_sankey(event_id, event_name, impacts, connected_events, schemes, actors):
    """Build Sankey node/link lists for cascade visualization."""
    nodes, links = [], []
    idx = {}

    def _node(label, color="#475569", layer=0):
        if label not in idx:
            idx[label] = len(nodes)
            nodes.append({"label": label, "color": color, "layer": layer})
        return idx[label]

    _DOMAIN_COLOR = {
        "DOM_GEOPOLITICS": "#38bdf8", "DOM_ECONOMICS": "#22c55e",
        "DOM_DEFENSE":     "#f97316", "DOM_TECHNOLOGY": "#a78bfa",
        "DOM_CLIMATE":     "#34d399", "DOM_SOCIETY":    "#fb7185",
        "DOM_GOVERNANCE":  "#facc15",
    }
    _SEV_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}

    # Root crisis node
    root = _node(event_name, "#ef4444", 0)

    # Impacts (layer 1)
    for imp in impacts:
        c = _SEV_COLOR.get(imp.get("severity",""), "#f97316")
        n = _node(imp["name"], c, 1)
        links.append({"source": root, "target": n, "value": 2, "color": c + "66"})

    # Connected events (layer 1)
    for evt in connected_events[:5]:
        c = _DOMAIN_COLOR.get(evt.get("domain",""), "#475569")
        n = _node(evt["name"][:40], c, 1)
        links.append({"source": root, "target": n, "value": 1, "color": c + "55"})

    # Schemes (layer 2 — from root or connected events)
    for sch in schemes:
        if not sch.get("name"):
            continue
        c = _DOMAIN_COLOR.get(sch.get("domain",""), "#facc15")
        n = _node(sch["name"][:40], c, 2)
        src = root if sch.get("trigger_type") == "direct" else root
        links.append({"source": src, "target": n, "value": 2, "color": c + "55"})

    # Actors (layer 3)
    for act in actors:
        if not act.get("name"):
            continue
        n = _node(act["name"][:35], "#38bdf8", 3)
        links.append({"source": root, "target": n, "value": act.get("decision_count", 1),
                       "color": "#38bdf855"})

    return nodes, links


# ── GET /crisis/{event_id}/timeline ──────────────────────────────────────────
@router.get("/{event_id}/timeline")
def get_crisis_timeline(event_id: str) -> dict:
    """Ordered timeline of SubEvents for a crisis."""
    with get_session() as s:
        rows = s.run("""
            MATCH (e:Event {event_id: $eid})-[:CONTAINS]->(se:SubEvent)
            RETURN se ORDER BY coalesce(se.day_number, 0) ASC
        """, eid=event_id).data()
        return {
            "event_id": event_id,
            "timeline": [dict(r["se"]) for r in rows],
        }


# ── POST /crisis/{event_id}/scenarios ────────────────────────────────────────
@router.post("/{event_id}/scenarios")
def generate_crisis_scenarios(event_id: str) -> dict:
    """Generate 3 AI scenario branches for an ongoing crisis."""
    with get_session() as s:
        row = s.run("MATCH (e:Event {event_id: $eid}) RETURN e", eid=event_id).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        parent = dict(row["e"])

        # Latest 5 subevents
        ses = s.run("""
            MATCH (e:Event {event_id: $eid})-[:CONTAINS]->(se:SubEvent)
            RETURN se ORDER BY coalesce(se.day_number, 0) DESC LIMIT 5
        """, eid=event_id).data()
        subevents_summary = "\n".join(
            f"Day {r['se'].get('day_number','?')} [{r['se'].get('category','?')}]: "
            f"{r['se'].get('name','')} — {r['se'].get('india_impact','')}"
            for r in ses
        )

        # All indicators
        inds = s.run("""
            MATCH (e:Event {event_id: $eid})-[:SIGNALS]->(ind:Indicator)
            RETURN ind
        """, eid=event_id).data()
        indicators_summary = "\n".join(
            f"{r['ind'].get('name','')}: {r['ind'].get('value','')} "
            f"{r['ind'].get('unit','')} (trend: {r['ind'].get('trend','')})"
            for r in inds
        )

        # Recent decisions
        decs = s.run("""
            MATCH (dec:Decision)-[:RESPONDS_TO]->(e:Event {event_id: $eid})
            RETURN dec ORDER BY dec.date DESC LIMIT 4
        """, eid=event_id).data()
        decisions_summary = "\n".join(
            f"{r['dec'].get('name','')} [{r['dec'].get('status','')}]: {r['dec'].get('description','')}"
            for r in decs
        )

    result = ai_service.generate_scenarios(
        event_name=parent.get("name", event_id),
        subevents_summary=subevents_summary,
        indicators_summary=indicators_summary,
        decisions_summary=decisions_summary,
    )

    # Persist scenarios to Neo4j
    ts = _now_iso()
    with get_session() as s:
        for scn in result.get("scenarios", []):
            s.run("""
                MERGE (n:Scenario {scenario_id: $sid})
                SET n.name = $name, n.label = $label,
                    n.probability = $prob, n.timeline = $timeline,
                    n.trigger = $trigger, n.india_impact = $impact,
                    n.india_actions = $actions,
                    n.warning_signals = $signals,
                    n.generated_at = $ts
                WITH n
                MATCH (e:Event {event_id: $eid})
                MERGE (n)-[r:BRANCHES_FROM]->(e)
                SET r.generated_at = $ts
            """,
            sid=scn.get("scenario_id", f"SCN_{event_id}_{scn.get('label','?')}"),
            name=scn.get("name", ""),
            label=scn.get("label", ""),
            prob=float(scn.get("probability", 0.33)),
            timeline=scn.get("timeline", ""),
            trigger=scn.get("trigger", ""),
            impact=str(scn.get("india_impact", {})),
            actions=scn.get("india_actions", []),
            signals=scn.get("warning_signals", []),
            eid=event_id,
            ts=ts,
            )

    return result


# ── POST /crisis/{event_id}/ingest ────────────────────────────────────────────
class CrisisIngestRequest(BaseModel):
    text: str


@router.post("/{event_id}/ingest")
def ingest_crisis_update(event_id: str, req: CrisisIngestRequest) -> dict:
    """
    Ingest a news article as structured sub-events/indicators/decisions
    linked to the parent crisis event.
    """
    with get_session() as s:
        row = s.run("MATCH (e:Event {event_id: $eid}) RETURN e", eid=event_id).single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        parent = dict(row["e"])

    extracted = ai_service.extract_crisis_update(
        text=req.text,
        parent_event_id=event_id,
        parent_event_name=parent.get("name", event_id),
    )

    ts = _now_iso()
    created = {"subevents": 0, "indicators": 0, "decisions": 0}

    with get_session() as s:
        # Get current max day_number for PRECEDES chain
        last = s.run("""
            MATCH (e:Event {event_id: $eid})-[:CONTAINS]->(se:SubEvent)
            RETURN se ORDER BY se.day_number DESC LIMIT 1
        """, eid=event_id).single()
        last_se_id = dict(last["se"])["subevent_id"] if last else None

        prev_se_id = last_se_id
        for se in extracted.get("subevents", []):
            sid = se.get("subevent_id", "")
            if not sid:
                continue
            s.run("""
                MERGE (n:SubEvent {subevent_id: $sid})
                SET n.name = $name, n.date = $date,
                    n.category = $cat, n.description = $desc,
                    n.severity = $sev, n.india_impact = $impact,
                    n.source = 'live_ingested', n.ingested_at = $ts
                WITH n
                MATCH (e:Event {event_id: $eid})
                MERGE (e)-[r:CONTAINS]->(n)
                SET r.ingested_at = $ts
            """, sid=sid, name=se.get("name",""), date=se.get("date",""),
                 cat=se.get("category",""), desc=se.get("description",""),
                 sev=se.get("severity","medium"), impact=se.get("india_impact",""),
                 eid=event_id, ts=ts)
            # Chain to previous
            if prev_se_id and prev_se_id != sid:
                s.run("""
                    MATCH (a:SubEvent {subevent_id: $a})
                    MATCH (b:SubEvent {subevent_id: $b})
                    MERGE (a)-[r:PRECEDES]->(b)
                    SET r.ingested_at = $ts
                """, a=prev_se_id, b=sid, ts=ts)
            prev_se_id = sid
            created["subevents"] += 1

        for ind in extracted.get("indicators", []):
            iid = ind.get("indicator_id", "")
            if not iid:
                continue
            s.run("""
                MERGE (n:Indicator {indicator_id: $iid})
                SET n.name = $name, n.value = $val, n.unit = $unit,
                    n.trend = $trend, n.as_of = $as_of,
                    n.source = 'live_ingested', n.ingested_at = $ts
                WITH n
                MATCH (e:Event {event_id: $eid})
                MERGE (e)-[r:SIGNALS]->(n)
                SET r.ingested_at = $ts
            """, iid=iid, name=ind.get("name",""), val=float(ind.get("value",0)),
                 unit=ind.get("unit",""), trend=ind.get("trend",""),
                 as_of=ind.get("as_of",""), eid=event_id, ts=ts)
            created["indicators"] += 1

        for dec in extracted.get("decisions", []):
            did = dec.get("decision_id", "")
            if not did:
                continue
            s.run("""
                MERGE (n:Decision {decision_id: $did})
                SET n.name = $name, n.date = $date, n.status = $status,
                    n.description = $desc,
                    n.source = 'live_ingested', n.ingested_at = $ts
                WITH n
                MATCH (e:Event {event_id: $eid})
                MERGE (n)-[r:RESPONDS_TO]->(e)
                SET r.ingested_at = $ts
            """, did=did, name=dec.get("name",""), date=dec.get("date",""),
                 status=dec.get("status",""), desc=dec.get("description",""),
                 eid=event_id, ts=ts)
            created["decisions"] += 1

    log.info("[crisis] ingested for %s: %s", event_id, created)
    return {"event_id": event_id, "created": created, "extracted": extracted}
