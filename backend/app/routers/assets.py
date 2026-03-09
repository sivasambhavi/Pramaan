from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.queries import ASSET_CHAIN, LIST_ALL_ASSETS

router = APIRouter()

@router.get("/list", summary="List all assets in the knowledge graph")
def list_all_assets(ward_region_id: str = "REG_W45"):
    with get_session() as session:
        result = session.run(LIST_ALL_ASSETS, ward_region_id=ward_region_id)
        assets = [{"asset_id": r["asset_id"], "name": r["name"], "type": r["type"], "status": r["status"]} for r in result]
    return {"assets": assets}


@router.get("/{asset_id}/chain", summary="Get proof chain for an asset")
def asset_chain(asset_id: str):
    with get_session() as session:
        result = session.run(ASSET_CHAIN, asset_id=asset_id)
        record = result.single()

    if not record or record["a"] is None:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    return {
        "asset_id": asset_id,
        "asset": dict(record["a"]),
        "scheme": dict(record["s"]) if record["s"] else None,
        "built_by": dict(record["act"]) if record["act"] else None,
        "region": dict(record["street"]) if record["street"] else None,
        "ward": dict(record["ward"]) if record["ward"] else None,
        "evidence": [dict(e) for e in record["evidence_list"] if e is not None],
        "people_served": record["people_served"],
        "beneficiary_desc": record["beneficiary_desc"],
    }
