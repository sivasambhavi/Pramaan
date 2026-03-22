from typing import Optional
from fastapi import APIRouter, Query
from app.neo4j_client import get_session

router = APIRouter()

GET_REGION = """
MATCH (r:Region {region_id: $region_id})
OPTIONAL MATCH (parent:Region)-[:CONTAINS]->(r)
RETURN r.region_id  AS region_id,
       r.name       AS name,
       r.type       AS type,
       r.lat        AS lat,
       r.lon        AS lon,
       parent.region_id AS parent_id,
       parent.name      AS parent_name,
       parent.type      AS parent_type
"""

@router.get("/", summary="List regions — filter by type and/or parent_id")
def list_regions(
    type:      Optional[str] = Query(None, description="Filter by region type: state|city|zone|ward|street"),
    parent_id: Optional[str] = Query(None, description="Filter by parent region_id"),
):
    params = {}

    if parent_id:
        # Match children of a specific parent
        type_filter = "WHERE r.type = $type" if type else ""
        params["parent_id"] = parent_id
        if type:
            params["type"] = type
        cypher = f"""
            MATCH (parent:Region {{region_id: $parent_id}})-[:CONTAINS]->(r:Region)
            {type_filter}
            RETURN r.region_id  AS region_id,
                   r.name       AS name,
                   r.type       AS type,
                   r.lat        AS lat,
                   r.lon        AS lon,
                   parent.region_id AS parent_id,
                   parent.name      AS parent_name,
                   parent.type      AS parent_type
            ORDER BY r.name
        """
    elif type:
        params["type"] = type
        cypher = """
            MATCH (r:Region {type: $type})
            OPTIONAL MATCH (parent:Region)-[:CONTAINS]->(r)
            RETURN r.region_id  AS region_id,
                   r.name       AS name,
                   r.type       AS type,
                   r.lat        AS lat,
                   r.lon        AS lon,
                   parent.region_id AS parent_id,
                   parent.name      AS parent_name,
                   parent.type      AS parent_type
            ORDER BY r.name
        """
    else:
        cypher = """
            MATCH (r:Region)
            OPTIONAL MATCH (parent:Region)-[:CONTAINS]->(r)
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

    with get_session() as session:
        result = session.run(cypher, **params)
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
