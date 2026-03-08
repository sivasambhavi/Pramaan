from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.queries import ASSET_CHAIN

router = APIRouter()


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
        "region": dict(record["r"]) if record["r"] else None,
        "ward": dict(record["w"]) if record["w"] else None,
        "evidence": [dict(e) for e in record["evidence_list"]],
        "beneficiaries": [dict(b) for b in record["beneficiaries"]],
    }
