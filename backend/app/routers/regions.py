from fastapi import APIRouter
from app.neo4j_client import get_session

router = APIRouter()

LIST_REGIONS = """
MATCH (r:Region)
OPTIONAL MATCH (r)-[:PART_OF]->(parent:Region)
RETURN r.region_id  AS region_id,
       r.name       AS name,
       r.type       AS type,
       parent.region_id AS parent_id,
       parent.name      AS parent_name,
       parent.type      AS parent_type
ORDER BY r.type, r.name
"""

@router.get("/", summary="List all regions with parent info")
def list_regions():
    with get_session() as session:
        result = session.run(LIST_REGIONS)
        return [dict(r) for r in result]
