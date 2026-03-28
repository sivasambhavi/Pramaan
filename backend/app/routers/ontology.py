"""
ontology.py — PRAMAAN Global Ontology Engine API
Routes for the 6-event intelligence graph.

Endpoints:
  GET /ontology/events              — all 6 events summary
  GET /ontology/events/{event_id}   — full subgraph for one event
  GET /ontology/domains             — all 7 domains with event counts
  GET /ontology/domain/{domain_id}  — all events in a domain
  GET /ontology/actor/{actor_id}    — all events an actor is connected to
  GET /ontology/graph               — full graph (nodes + edges) for visualization
  GET /ontology/cross-domain        — only cross-domain CONNECTED_TO edges
  GET /ontology/schemes/by-type     — all schemes grouped by Type 1 / Type 2
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.queries import BLAST_SCORE_CYPHER

router = APIRouter(prefix="/ontology", tags=["ontology"])


# ── /events ───────────────────────────────────────────────────────────────────

@router.get("/events")
def list_events():
    """All 6 events with key metadata."""
    with get_session() as s:
        rows = s.run("""
            MATCH (e:Event)
            WHERE e.confidence IS NOT NULL
            OPTIONAL MATCH (e)-[:OCCURRED_IN]->(r:Region)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(d:Domain)
            OPTIONAL MATCH (e)-[:CAUSED]->(i:Impact)
            RETURN e.event_id    AS event_id,
                   e.name        AS name,
                   e.date        AS date,
                   e.domain      AS domain_id,
                   e.severity    AS severity,
                   e.blast_score AS blast_score,
                   e.description AS description,
                   e.source_url  AS source_url,
                   collect(DISTINCT r.name) AS regions,
                   collect(DISTINCT d.name) AS domains,
                   count(DISTINCT i)        AS impact_count
            ORDER BY e.date DESC
        """).data()
    return {"events": rows, "total": len(rows)}


# ── /events/{event_id} ────────────────────────────────────────────────────────

@router.get("/events/{event_id}")
def get_event(event_id: str):
    """Full subgraph for a single event — all connected nodes and edges."""
    with get_session() as s:
        # Core event
        event = s.run("""
            MATCH (e:Event {event_id: $id})
            RETURN e
        """, {"id": event_id}).single()

        if not event:
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")

        # All connected nodes
        connected = s.run("""
            MATCH (e:Event {event_id: $id})-[r]->(n)
            RETURN type(r) AS rel_type,
                   labels(n)[0] AS node_label,
                   n AS node,
                   r.reason AS reason
        """, {"id": event_id}).data()

        # Impacts with values
        impacts = s.run("""
            MATCH (e:Event {event_id: $id})-[:CAUSED]->(i:Impact)
            RETURN i.impact_id AS id, i.type AS type,
                   coalesce(i.name, i.type, '') AS name,
                   i.value AS value, i.unit AS unit,
                   i.severity AS severity,
                   i.description AS description,
                   coalesce(i.source, '') AS source
            ORDER BY i.value DESC
        """, {"id": event_id}).data()

        # Evidence
        evidence = s.run("""
            MATCH (e:Event {event_id: $id})-[:PROVEN_BY]->(ev:Evidence)
            RETURN ev.evidence_id AS id, ev.type AS type,
                   ev.title AS title, ev.url AS url,
                   ev.source AS source, ev.date AS date
        """, {"id": event_id}).data()

        # Cross-domain connections
        connections = s.run("""
            MATCH (e:Event {event_id: $id})-[r:CONNECTED_TO]-(other:Event)
            RETURN other.event_id AS event_id, other.name AS name,
                   other.domain AS domain, r.reason AS reason
        """, {"id": event_id}).data()

    # Build response
    nodes_by_type = {}
    for row in connected:
        label = row["node_label"]
        node_data = dict(row["node"])
        node_data["_rel"] = row["rel_type"]
        nodes_by_type.setdefault(label, []).append(node_data)

    schemes = nodes_by_type.get("Scheme", [])

    # Enrich schemes with beneficiary counts (separate session)
    if schemes:
        scheme_ids = [sch.get("scheme_id") for sch in schemes if sch.get("scheme_id")]
        with get_session() as s2:
            bene_rows = s2.run("""
                UNWIND $ids AS sid
                MATCH (sc:Scheme {scheme_id: sid})
                OPTIONAL MATCH (sc)-[:BENEFITS]->(b:Beneficiary)
                RETURN sid AS scheme_id,
                       sum(COALESCE(b.count, 0)) AS beneficiary_count,
                       collect(DISTINCT b.description)[0] AS beneficiary_desc
            """, {"ids": scheme_ids}).data()
        bene_map = {r["scheme_id"]: r for r in bene_rows}
        for sch in schemes:
            sid = sch.get("scheme_id")
            if sid and sid in bene_map:
                sch["beneficiary_count"] = bene_map[sid]["beneficiary_count"] or 0
                sch["beneficiary_desc"] = bene_map[sid]["beneficiary_desc"] or ""

    return {
        "event":       dict(event["e"]),
        "regions":     nodes_by_type.get("Region", []),
        "domains":     nodes_by_type.get("Domain", []),
        "actors":      nodes_by_type.get("Actor", []),
        "schemes":     schemes,
        "policies":    nodes_by_type.get("Policy", []),
        "impacts":     impacts,
        "evidence":    evidence,
        "connections": connections,
    }


# ── /domains ──────────────────────────────────────────────────────────────────

@router.get("/domains")
def list_domains():
    """All 7 domains with event counts."""
    with get_session() as s:
        rows = s.run("""
            MATCH (d:Domain)
            OPTIONAL MATCH (e:Event)-[:BELONGS_TO|ALSO_IN]->(d)
            RETURN d.domain_id  AS domain_id,
                   d.name       AS name,
                   d.description AS description,
                   count(DISTINCT e) AS event_count
            ORDER BY event_count DESC
        """).data()
    return {"domains": rows}


# ── /domain/{domain_id} ───────────────────────────────────────────────────────

@router.get("/domain/{domain_id}")
def get_domain(domain_id: str):
    """All events (primary + secondary) in a domain."""
    with get_session() as s:
        domain = s.run("""
            MATCH (d:Domain {domain_id: $id})
            RETURN d
        """, {"id": domain_id}).single()

        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

        events = s.run("""
            MATCH (e:Event)-[:BELONGS_TO|ALSO_IN]->(d:Domain {domain_id: $id})
            OPTIONAL MATCH (e)-[:OCCURRED_IN]->(r:Region)
            OPTIONAL MATCH (e)-[:CAUSED]->(i:Impact)
            RETURN e.event_id   AS event_id,
                   e.name       AS name,
                   e.date       AS date,
                   e.severity   AS severity,
                   collect(DISTINCT r.name) AS regions,
                   count(DISTINCT i)        AS impact_count
            ORDER BY e.date DESC
        """, {"id": domain_id}).data()

    return {
        "domain": dict(domain["d"]),
        "events": events,
        "total":  len(events),
    }


# ── /actor/{actor_id} ─────────────────────────────────────────────────────────

@router.get("/actor/{actor_id}")
def get_actor(actor_id: str):
    """All events an actor is connected to."""
    with get_session() as s:
        actor = s.run("""
            MATCH (a:Actor {actor_id: $id})
            RETURN a
        """, {"id": actor_id}).single()

        if not actor:
            raise HTTPException(status_code=404, detail=f"Actor '{actor_id}' not found")

        events = s.run("""
            MATCH (e:Event)-[:MANAGED_BY]->(a:Actor {actor_id: $id})
            RETURN e.event_id AS event_id, e.name AS name,
                   e.date AS date, e.domain AS domain,
                   e.severity AS severity
            ORDER BY e.date DESC
        """, {"id": actor_id}).data()

        parent = s.run("""
            MATCH (a:Actor {actor_id: $id})-[:PART_OF]->(p:Actor)
            RETURN p.actor_id AS actor_id, p.name AS name
        """, {"id": actor_id}).data()

    return {
        "actor":  dict(actor["a"]),
        "events": events,
        "parent": parent[0] if parent else None,
    }


# ── /graph ────────────────────────────────────────────────────────────────────

@router.get("/graph")
def full_graph():
    """
    Full graph for frontend visualization (streamlit-agraph).
    Returns nodes list and edges list.
    """
    with get_session() as s:
        # All nodes — only ontology nodes (Events must have confidence; others reachable from them)
        all_nodes = s.run("""
            MATCH (n)
            WHERE NOT n:Asset AND NOT n:Beneficiary
              AND (NOT n:Event OR n.confidence IS NOT NULL)
            RETURN labels(n)[0] AS label,
                   properties(n) AS props
        """).data()

        # All edges — only between ontology nodes
        all_edges = s.run("""
            MATCH (a)-[r]->(b)
            WHERE NOT a:Asset AND NOT b:Asset
              AND NOT a:Beneficiary AND NOT b:Beneficiary
              AND (NOT a:Event OR a.confidence IS NOT NULL)
              AND (NOT b:Event OR b.confidence IS NOT NULL)
            RETURN labels(a)[0] + '_' + COALESCE(
                       a.event_id, a.region_id, a.actor_id, a.domain_id,
                       a.scheme_id, a.policy_id, a.impact_id, a.evidence_id
                   ) AS from_id,
                   labels(b)[0] + '_' + COALESCE(
                       b.event_id, b.region_id, b.actor_id, b.domain_id,
                       b.scheme_id, b.policy_id, b.impact_id, b.evidence_id
                   ) AS to_id,
                   type(r) AS rel_type,
                   r.reason AS reason
        """).data()

    # Build node list with unique IDs
    nodes = []
    for row in all_nodes:
        label = row["label"]
        props = row["props"]
        id_field = {
            "Event": "event_id", "Region": "region_id", "Actor": "actor_id",
            "Domain": "domain_id", "Scheme": "scheme_id", "Policy": "policy_id",
            "Impact": "impact_id", "Evidence": "evidence_id",
        }.get(label, "id")
        node_id = f"{label}_{props.get(id_field, '')}"
        nodes.append({
            "id":    node_id,
            "label": props.get("name", node_id),
            "type":  label,
            "props": props,
        })

    edges = [
        {
            "from":   e["from_id"],
            "to":     e["to_id"],
            "type":   e["rel_type"],
            "reason": e.get("reason", ""),
        }
        for e in all_edges if e["from_id"] and e["to_id"]
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }
    }


# ── /compound-risk ────────────────────────────────────────────────────────────

@router.get("/compound-risk")
def compound_risk():
    """
    Cross-domain compound risk context for portfolio-level decision briefs.
    Returns:
      - all events (severity + domain + date)
      - overloaded actors (appear in 2+ critical events)
      - cross-domain connections with causal reasons
      - top quantified impacts across all events
      - temporal clusters (events sharing same year)
    """
    with get_session() as s:

        # All events
        events = s.run("""
            MATCH (e:Event)
            WHERE e.confidence IS NOT NULL
            RETURN e.event_id AS event_id, e.name AS name,
                   e.domain AS domain, e.severity AS severity,
                   e.date AS date, e.description AS description
            ORDER BY e.date DESC
        """).data()

        # Actors appearing in 2+ events — overload signal
        overloaded_actors = s.run("""
            MATCH (e:Event)-[:MANAGED_BY]->(a:Actor)
            WHERE e.confidence IS NOT NULL
            WITH a, collect(DISTINCT e.name) AS event_names,
                    collect(DISTINCT e.severity) AS severities,
                    count(DISTINCT e) AS event_count
            WHERE event_count >= 2
            RETURN a.actor_id AS actor_id, a.name AS name,
                   a.type AS type, event_count,
                   event_names, severities
            ORDER BY event_count DESC
        """).data()

        # Cross-domain connections with reasons
        connections = s.run("""
            MATCH (a:Event)-[r:CONNECTED_TO]->(b:Event)
            RETURN a.event_id AS from_id, a.name AS from_name,
                   a.domain AS from_domain, a.severity AS from_severity,
                   b.event_id AS to_id, b.name AS to_name,
                   b.domain AS to_domain, b.severity AS to_severity,
                   r.reason AS reason
        """).data()

        # Top quantified impacts across all events (resource picture)
        top_impacts = s.run("""
            MATCH (e:Event)-[:CAUSED]->(i:Impact)
            WHERE i.value IS NOT NULL AND i.value > 0
            RETURN e.name AS event_name, e.domain AS domain,
                   i.type AS type, i.value AS value,
                   i.unit AS unit, i.description AS description,
                   coalesce(i.source, '') AS source
            ORDER BY
                CASE i.unit
                    WHEN 'crore_inr'   THEN i.value
                    WHEN 'billion_usd' THEN i.value * 8300
                    WHEN 'persons'     THEN i.value / 1000
                    ELSE i.value
                END DESC
            LIMIT 25
        """).data()

        # Temporal clusters — events sharing same year
        year_clusters = s.run("""
            MATCH (e:Event)
            WHERE e.confidence IS NOT NULL AND e.date IS NOT NULL
            WITH substring(e.date, 0, 4) AS year,
                 collect(e.name) AS event_names,
                 collect(e.severity) AS severities,
                 count(e) AS count
            WHERE count >= 2
            RETURN year, event_names, severities, count
            ORDER BY year DESC
        """).data()

    return {
        "events":            events,
        "overloaded_actors": overloaded_actors,
        "connections":       connections,
        "top_impacts":       top_impacts,
        "year_clusters":     year_clusters,
        "total_events":      len(events),
        "total_connections": len(connections),
    }


# ── /cross-domain ─────────────────────────────────────────────────────────────

@router.get("/cross-domain")
def cross_domain_links():
    """Only the CONNECTED_TO edges between events — the cross-domain insight layer."""
    with get_session() as s:
        rows = s.run("""
            MATCH (a:Event)-[r:CONNECTED_TO]->(b:Event)
            RETURN a.event_id  AS from_id,
                   a.name      AS from_name,
                   a.domain    AS from_domain,
                   b.event_id  AS to_id,
                   b.name      AS to_name,
                   b.domain    AS to_domain,
                   r.reason    AS reason
        """).data()
    return {"connections": rows, "total": len(rows)}


# ── /blast-scores ─────────────────────────────────────────────────────────────

@router.get("/blast-scores")
def get_blast_scores():
    """
    Compute dynamic blast scores for ALL events from graph topology and persist
    blast_score back to each Event node.

    Score (0–10) = graph density weighted by:
      3.0  Impact count (CAUSED edges)
      2.0  Evidence volume (PROVEN_BY edges)
      1.5  Evidence velocity (PROVEN_BY ingested last 24h)
      2.0  Cross-domain spread (CONNECTED_TO edges)
      0.5  Domain breadth (ALSO_IN edges)
      1.0  Source credibility (avg Evidence confidence)

    Thresholds: ≥8.5 critical  ≥6.5 high  ≥4.0 medium  else low
    """
    since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    with get_session() as s:
        rows = s.run(BLAST_SCORE_CYPHER, {"since_24h": since_24h}).data()

    # Build lookup dict for quick frontend access
    by_id = {r["event_id"]: r for r in rows}
    return {"scores": rows, "by_id": by_id, "total": len(rows)}


# ── /schemes/by-type ──────────────────────────────────────────────────────────

@router.get("/schemes/by-type")
def schemes_by_type():
    """All Scheme nodes grouped by scheme_type (Type 1 Emergency / Type 2 Structural)."""
    with get_session() as s:
        rows = s.run("""
            MATCH (sc:Scheme)
            RETURN sc.scheme_id       AS scheme_id,
                   sc.name            AS name,
                   sc.ministry        AS ministry,
                   sc.budget_crore    AS budget_crore,
                   sc.scheme_type     AS scheme_type,
                   sc.scheme_type_label AS scheme_type_label,
                   sc.description     AS description,
                   sc.status          AS status,
                   sc.strategic_value AS strategic_value,
                   sc.risk            AS risk,
                   sc.domain          AS domain
            ORDER BY sc.scheme_type, sc.name
        """).data()

    type1 = [r for r in rows if r.get("scheme_type") == "Type 1"]
    type2 = [r for r in rows if r.get("scheme_type") == "Type 2"]
    return {"type1": type1, "type2": type2, "total": len(rows)}
