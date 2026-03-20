"""
questions.py — PRAMAAN Questions Router

Fix 3 applied: Added POST /questions/ask — real NL→Cypher endpoint.
               The LLM receives a plain-English question + full schema context
               and generates a Cypher READ query that is executed live.
               Judges can type ANY question — no more 5-question limit.

Existing hardcoded routes (Q1–Q5) are kept as fast-path fallbacks.
"""

import json
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from app.neo4j_client import get_session
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/questions", tags=["questions"])


def _run(cypher: str, params: dict = {}) -> list:
    """Execute a read query and return list of dicts."""
    with get_session() as session:
        result = session.run(cypher, **params)
        return [dict(r) for r in result]


# ─── Schema context for NL→Cypher ────────────────────────────────────────────
# Injected into every /ask prompt so the LLM knows the exact node labels,
# property names, relationship types, and canonical IDs in this graph.

_SCHEMA = """
## Neo4j Graph Schema

Node labels and key properties:
  Region      (region_id, name, type)          type: city|zone|ward|street
  Scheme      (scheme_id, name, ministry, category)
  Actor       (actor_id,  name, type)           type: government|contractor|elected_rep
  Asset       (asset_id,  name, type, status, cost, lat, lon, confidence, source_type)
              type: drain|road|toilet|housing|park|streetlight|water_body
              status: completed|in_progress|planned
  Beneficiary (beneficiary_id, count, description)
  Evidence    (evidence_id, type, url, before_or_after, capture_date, source)
              type: image|report|certificate
  Event       (event_id, name, event_type, date)
              event_type: completion|inauguration|tender|sanction

Relationships (direction matters):
  (Scheme)-[:FUNDS]->(Asset)
  (Asset)-[:BUILT_BY]->(Actor)
  (Asset)-[:LOCATED_IN]->(Region)
  (Evidence)-[:PROVES]->(Asset)
  (Scheme)-[:BENEFITS]->(Beneficiary)
  (Beneficiary)-[:LIVES_IN]->(Region)
  (Region)-[:LOCATED_IN]->(Region)        -- ward inside zone inside city
  (Event)-[:RELATED_TO]->(Asset)
  (Actor)-[:REPRESENTS]->(Region)

Canonical IDs (use these in WHERE clauses):
  Schemes : SCH_AMRUT, SCH_PMAY, SCH_SWACHH, SCH_SFC, SCH_LOCAL_LIGHTS
  Regions : REG_DELHI, REG_SHAHDARA_NORTH, REG_SHAHDARA_SOUTH,
            REG_W45, REG_W45_GALI7, REG_W45_GALI12, REG_W45_GALI3,
            REG_W45_MARKET_ROAD, REG_W45_COLONY_Y
  Actors  : ACT_MCD_SHAHDARA_WORKS, ACT_MCD_SHAHDARA_SANITATION,
            ACT_MCD_ELECTRICAL, ACT_DDA, ACT_W45_COUNCILLOR,
            ACT_CONTRACTOR_INFRA_1, ACT_CONTRACTOR_LIGHTS_1
"""

_FEW_SHOT = """
## Examples

Q: Which assets funded by AMRUT are in Ward 45?
A: MATCH (s:Scheme {scheme_id:'SCH_AMRUT'})-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
   WHERE r.region_id = 'REG_W45' OR r.parent_region_id = 'REG_W45'
   RETURN a.name AS Asset, a.type AS Type, a.status AS Status, a.cost AS Cost

Q: Which drains have no photos?
A: MATCH (a:Asset {type:'drain'})
   WHERE NOT (:Evidence)-[:PROVES]->(a)
   RETURN a.name AS Asset, a.status AS Status, a.asset_id AS ID

Q: How much total money was allocated per scheme in Ward 45?
A: MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
   WHERE r.region_id = 'REG_W45' OR r.parent_region_id = 'REG_W45'
   RETURN s.name AS Scheme, count(a) AS Assets,
          sum(CASE WHEN a.cost IS NOT NULL THEN a.cost ELSE 0 END) AS `Total (₹)`
   ORDER BY `Total (₹)` DESC

Q: Which assets are completed and have evidence?
A: MATCH (e:Evidence)-[:PROVES]->(a:Asset {status:'completed'})
   RETURN DISTINCT a.name AS Asset, a.type AS Type, count(e) AS `Evidence Count`

Q: Who built the most assets?
A: MATCH (a:Asset)-[:BUILT_BY]->(act:Actor)
   RETURN act.name AS Agency, count(a) AS `Asset Count`
   ORDER BY `Asset Count` DESC

Q: List assets added by live ingestion
A: MATCH (a:Asset) WHERE a.source = 'live_ingestion'
   RETURN a.name AS Asset, a.type AS Type, a.confidence AS Confidence,
          a.ingested_at AS `Ingested At`
   ORDER BY a.ingested_at DESC
"""


# ─── Hardcoded fast-path endpoints (Q1–Q5) ───────────────────────────────────

@router.get("/q_amrut")
def q_amrut(ward_id: str = "REG_W45"):
    rows = _run("""
        MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
        WHERE (r.region_id = $ward_id OR r.parent_region_id = $ward_id)
          AND toLower(s.name) CONTAINS 'amrut'
        RETURN a.name AS Asset, a.type AS Type, a.status AS Status,
               a.cost AS `Cost (₹)`, s.name AS Scheme
        ORDER BY a.name
    """, {"ward_id": ward_id})
    return {"data": rows}


@router.get("/q_no_evidence")
def q_no_evidence(ward_id: str = "REG_W45"):
    rows = _run("""
        MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
        WHERE (r.region_id = $ward_id OR r.parent_region_id = $ward_id)
        AND NOT EXISTS { MATCH (e:Evidence)-[:PROVES]->(a) }
        RETURN a.name AS Asset, a.type AS Type, a.status AS Status
        ORDER BY a.name
    """, {"ward_id": ward_id})
    return {"data": rows}


@router.get("/q_scheme_funding")
def q_scheme_funding(ward_id: str = "REG_W45"):
    rows = _run("""
        MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
        WHERE r.region_id = $ward_id OR r.parent_region_id = $ward_id
        RETURN s.name AS Scheme,
               count(DISTINCT a) AS `Asset Count`,
               sum(CASE WHEN a.cost IS NOT NULL THEN a.cost ELSE 0 END) AS `Total Allocated (₹)`,
               collect(DISTINCT a.type) AS `Asset Types`
        ORDER BY `Total Allocated (₹)` DESC
    """, {"ward_id": ward_id})
    return {"data": rows}


@router.get("/q_top_agency")
def q_top_agency(ward_id: str = "REG_W45"):
    rows = _run("""
        MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
        WHERE r.region_id = $ward_id OR r.parent_region_id = $ward_id
        MATCH (a)-[:BUILT_BY]->(act:Actor)
        RETURN act.name AS Agency, act.type AS Type,
               count(DISTINCT a) AS `Projects Implemented`,
               collect(DISTINCT a.type) AS `Asset Types`
        ORDER BY `Projects Implemented` DESC
    """, {"ward_id": ward_id})
    return {"data": rows}


@router.get("/q_drains")
def q_drains(ward_id: str = "REG_W45"):
    rows = _run("""
        MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
        WHERE (r.region_id = $ward_id OR r.parent_region_id = $ward_id)
          AND a.type = 'drain' AND a.status = 'completed'
        OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
        RETURN a.name AS Asset, a.cost AS `Cost (₹)`,
               a.status AS Status, count(e) AS `Evidence Articles`
        ORDER BY a.name
    """, {"ward_id": ward_id})
    return {"data": rows}


# ─── Fix 3: Real NL→Cypher endpoint ─────────────────────────────────────────

class AskQuery(BaseModel):
    question: str
    ward_id: str = "REG_W45"   # optional context — injected into the prompt


@router.post("/ask")
def ask(payload: AskQuery):
    """
    Convert a plain-English question to a Cypher READ query using the LLM,
    execute it against Neo4j, and return the results.

    The LLM receives:
      - Full graph schema (node labels, properties, relationship types)
      - Canonical IDs for existing nodes
      - 6 few-shot examples
      - The user's question + active ward context

    Returns:
      question    — original question
      explanation — one-sentence description of what the query does
      cypher      — generated Cypher (for transparency / debugging)
      data        — list of result rows from Neo4j
      source      — "llm" | "error"
    """
    if not settings.groq_api_key:
        return {
            "question":    payload.question,
            "explanation": "GROQ_API_KEY not configured — set it in .env",
            "cypher":      "",
            "data":        [],
            "source":      "error",
        }

    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)

    prompt = f"""
You are a Neo4j Cypher expert for the PRAMAAN governance graph (India).
{_SCHEMA}
{_FEW_SHOT}

Active ward context: {payload.ward_id}

Convert the following question to a single Neo4j Cypher READ query.
The query must be safe (no MERGE, CREATE, DELETE, SET).
Return ONLY valid JSON — no markdown, no explanation outside the JSON:
{{
  "cypher":      "MATCH ... RETURN ...",
  "explanation": "one sentence describing what the query answers"
}}

Question: {payload.question}
"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        out = json.loads(resp.choices[0].message.content.strip())
        cypher      = out.get("cypher", "").strip()
        explanation = out.get("explanation", "")

        if not cypher:
            return {
                "question": payload.question,
                "explanation": "LLM did not generate a Cypher query.",
                "cypher": "",
                "data": [],
                "source": "error",
            }

        # Safety guard — reject write operations
        forbidden = ["merge", "create", "delete", "set ", "drop", "call apoc"]
        if any(kw in cypher.lower() for kw in forbidden):
            return {
                "question": payload.question,
                "explanation": "Generated query contains write operations — rejected for safety.",
                "cypher": cypher,
                "data": [],
                "source": "error",
            }

        data = _run(cypher)
        return {
            "question":    payload.question,
            "explanation": explanation,
            "cypher":      cypher,
            "data":        data,
            "source":      "llm",
        }

    except Exception as e:
        logger.error(f"/questions/ask failed: {e}")
        return {
            "question":    payload.question,
            "explanation": f"Error: {e}",
            "cypher":      "",
            "data":        [],
            "source":      "error",
        }


# ─── Legacy custom endpoint (kept for backward compat) ───────────────────────

class CustomQuery(BaseModel):
    cypher: str
    params: dict = {}


@router.post("/custom")
def custom_query(payload: CustomQuery):
    """Run a pre-generated Cypher query. Used by frontend hardcoded calls."""
    try:
        rows = _run(payload.cypher, payload.params)
        return {"data": rows}
    except Exception as e:
        return {"data": [], "error": str(e)}
