"""
Questions router — hardcoded Cypher endpoints + custom NL query endpoint.
All queries are adapted to the PRAMAAN schema:
  Asset, Region, Actor, Scheme, Evidence nodes.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.neo4j_client import get_session

router = APIRouter(prefix="/questions", tags=["questions"])


def _run(cypher: str, params: dict = {}) -> list:
    """Execute a read query and return list of dicts."""
    with get_session() as session:
        result = session.run(cypher, **params)
        return [dict(r) for r in result]


# ─── Q1: Assets funded by AMRUT ─────────────────────────────────────────────
@router.get("/q_amrut")
def q_amrut(ward_id: str = "REG_W45"):
    cypher = """
    MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE (r.region_id = $ward_id OR r.parent_region_id = $ward_id)
      AND toLower(s.name) CONTAINS 'amrut'
    RETURN a.name AS Asset, a.type AS Type, a.status AS Status,
           a.cost AS `Cost (₹)`, s.name AS Scheme
    ORDER BY a.name
    """
    rows = _run(cypher, {"ward_id": ward_id})
    return {"data": rows}


# ─── Q2: Assets with no evidence ────────────────────────────────────────────
@router.get("/q_no_evidence")
def q_no_evidence(ward_id: str = "REG_W45"):
    cypher = """
    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE (r.region_id = $ward_id OR r.parent_region_id = $ward_id)
    AND NOT EXISTS { MATCH (e:Evidence)-[:PROVES]->(a) }
    AND NOT EXISTS { MATCH (n:NewsArticle)<-[:MENTIONED_IN]-(a) }
    RETURN a.name AS `Asset`,
           a.type AS `Type`,
           a.status AS `Status`
    ORDER BY a.name
    """
    rows = _run(cypher, {"ward_id": ward_id})
    return {"data": rows}


# ─── Q3: Scheme funding totals ───────────────────────────────────────────────
@router.get("/q_scheme_funding")
def q_scheme_funding(ward_id: str = "REG_W45"):
    cypher = """
    MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE r.region_id = $ward_id OR r.parent_region_id = $ward_id
    RETURN s.name AS Scheme,
           count(DISTINCT a) AS `Asset Count`,
           sum(CASE WHEN a.cost IS NOT NULL THEN a.cost ELSE 0 END) AS `Total Allocated (₹)`,
           collect(DISTINCT a.type) AS `Asset Types`
    ORDER BY `Total Allocated (₹)` DESC
    """
    rows = _run(cypher, {"ward_id": ward_id})
    return {"data": rows}


# ─── Q4: Top agencies ────────────────────────────────────────────────────────
@router.get("/q_top_agency")
def q_top_agency(ward_id: str = "REG_W45"):
    cypher = """
    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE r.region_id = $ward_id OR r.parent_region_id = $ward_id
    MATCH (a)-[:BUILT_BY]->(act:Actor)
    RETURN act.name AS Agency, act.type AS Type,
           count(DISTINCT a) AS `Projects Implemented`,
           collect(DISTINCT a.type) AS `Asset Types`
    ORDER BY `Projects Implemented` DESC
    """
    rows = _run(cypher, {"ward_id": ward_id})
    return {"data": rows}


# ─── Q5: Completed drain projects ────────────────────────────────────────────
@router.get("/q_drains")
def q_drains(ward_id: str = "REG_W45"):
    cypher = """
    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE (r.region_id = $ward_id OR r.parent_region_id = $ward_id)
      AND a.type = 'drain' AND a.status = 'completed'
    OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
    RETURN a.name AS Asset,
           a.cost AS `Cost (₹)`,
           a.status AS Status,
           count(e) AS `Evidence Articles`
    ORDER BY a.name
    """
    rows = _run(cypher, {"ward_id": ward_id})
    return {"data": rows}


# ─── Custom LLM→Cypher query ─────────────────────────────────────────────────
class CustomQuery(BaseModel):
    cypher: str
    params: dict = {}

@router.post("/custom")
def custom_query(payload: CustomQuery):
    """Run an arbitrary Cypher query passed from the LLM-generated frontend call."""
    try:
        rows = _run(payload.cypher, payload.params)
        return {"data": rows}
    except Exception as e:
        return {"data": [], "error": str(e)}
