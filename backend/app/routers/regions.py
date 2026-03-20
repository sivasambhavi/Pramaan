from fastapi import APIRouter
from app.neo4j_client import get_session

router = APIRouter()

LIST_REGIONS = """
MATCH (r:Region)
OPTIONAL MATCH (r)-[:LOCATED_IN]->(parent:Region)
RETURN r.region_id  AS region_id,
       r.name       AS name,
       r.type       AS type,
       r.lat        AS lat,
       r.lon        AS lon,
       parent.region_id AS parent_id,
       parent.name      AS parent_name,
       parent.type      AS parent_type
ORDER BY r.type, r.name
"""

GET_REGION = """
MATCH (r:Region {region_id: $region_id})
OPTIONAL MATCH (r)-[:LOCATED_IN]->(parent:Region)
RETURN r.region_id  AS region_id,
       r.name       AS name,
       r.type       AS type,
       r.lat        AS lat,
       r.lon        AS lon,
       parent.region_id AS parent_id,
       parent.name      AS parent_name,
       parent.type      AS parent_type
"""

@router.get("/", summary="List all regions with parent info and geo-coordinates")
def list_regions():
    with get_session() as session:
        result = session.run(LIST_REGIONS)
        return [dict(r) for r in result]


@router.get("/{region_id}", summary="Get a single region by ID (includes lat/lon)")
def get_region(region_id: str):
    with get_session() as session:
        result = session.run(GET_REGION, region_id=region_id)
        row = result.single()
        if row is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Region '{region_id}' not found")
        return dict(row)
