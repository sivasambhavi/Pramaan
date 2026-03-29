"""
verdict.py — PRAMAAN Intelligence Verdict Router

GET /verdict/context  — Assembles full graph state as structured context for LLM
"""

import logging
from fastapi import APIRouter
from app.neo4j_client import get_session

log    = logging.getLogger("pramaan.verdict")
router = APIRouter(prefix="/verdict", tags=["verdict"])


@router.get("/context")
def get_verdict_context() -> dict:
    """
    Pull live graph state for the Intelligence Verdict:
    - All high/critical events with domains, dates, severity
    - Cross-domain CONNECTED_TO edges with reasons
    - Active crisis indicators (latest values)
    - Scheme utilization gaps
    - Key actors and their linked events
    """
    with get_session() as s:

        # 1. All events (high + critical)
        events_rows = s.run("""
            MATCH (e:Event)
            WHERE e.severity IN ['high','critical']
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(d:Domain)
            OPTIONAL MATCH (e)-[:OCCURRED_IN]->(r:Region)
            RETURN e.event_id    AS id,
                   e.name        AS name,
                   e.severity    AS severity,
                   e.date        AS date,
                   e.description AS description,
                   d.name        AS domain,
                   r.name        AS region
            ORDER BY e.severity DESC, e.date DESC
        """).data()

        # 2. Cross-domain connections
        connections_rows = s.run("""
            MATCH (a:Event)-[r:CONNECTED_TO]->(b:Event)
            RETURN a.name AS from_event,
                   b.name AS to_event,
                   r.reason AS reason,
                   r.strength AS strength
        """).data()

        # 3. Active crisis indicators (most recent per indicator)
        indicators_rows = s.run("""
            MATCH (i:Indicator)
            RETURN i.name  AS name,
                   i.value AS value,
                   i.unit  AS unit,
                   i.trend AS trend
            ORDER BY i.name
        """).data()

        # 4. Scheme utilization
        schemes_rows = s.run("""
            MATCH (s:Scheme)
            OPTIONAL MATCH (e:Event)-[:TRIGGERED]->(s)
            RETURN s.name          AS name,
                   s.budget_crore  AS budget,
                   s.status        AS status,
                   s.domain        AS domain,
                   collect(e.name) AS triggered_by
        """).data()

        # 5. Key actors and their event links
        actors_rows = s.run("""
            MATCH (a:Actor)-[:RESPONDS_TO|MANAGES|OVERSEES]->(e:Event)
            RETURN a.name        AS actor,
                   a.role        AS role,
                   collect(e.name) AS events
            LIMIT 15
        """).data()

        # 6. Impact nodes (high/critical severity)
        impacts_rows = s.run("""
            MATCH (i:Impact)<-[:CAUSED]-(e:Event)
            WHERE i.severity IN ['high','critical']
            RETURN e.name      AS event,
                   i.name      AS impact,
                   i.domain    AS domain,
                   i.severity  AS severity
            ORDER BY i.severity DESC
            LIMIT 20
        """).data()

    return {
        "events":      events_rows,
        "connections": connections_rows,
        "indicators":  indicators_rows,
        "schemes":     schemes_rows,
        "actors":      actors_rows,
        "impacts":     impacts_rows,
    }
