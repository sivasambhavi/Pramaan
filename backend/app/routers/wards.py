from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.queries import LIST_WARDS, WARD_ASSETS, WARD_GAPS, WARD_DELIVERY_SCORE

router = APIRouter()


@router.get("/", summary="List all wards")
def list_wards():
    with get_session() as session:
        result = session.run(LIST_WARDS)
        return [dict(r) for r in result]


@router.get("/{ward_id}/assets", summary="List assets in a ward")
def ward_assets(ward_id: str):
    with get_session() as session:
        result = session.run(WARD_ASSETS, ward_id=ward_id)
        assets = [dict(r) for r in result]
    if not assets:
        raise HTTPException(status_code=404, detail=f"Ward '{ward_id}' not found or has no assets")
    return {"ward_id": ward_id, "assets": assets}


@router.get("/{ward_id}/gaps", summary="Get delivery gaps for a ward")
def ward_gaps(ward_id: str):
    with get_session() as session:
        result = session.run(WARD_GAPS, ward_id=ward_id)
        gaps = [dict(r) for r in result]
    return {"ward_id": ward_id, "gaps": gaps}


@router.get("/{ward_id}/score", summary="Get delivery score for a ward")
def ward_score(ward_id: str):
    with get_session() as session:
        result = session.run(WARD_DELIVERY_SCORE, ward_id=ward_id)
        record = result.single()
    if not record:
        raise HTTPException(status_code=404, detail=f"Ward '{ward_id}' not found")
    return {"ward_id": ward_id, **dict(record)}
