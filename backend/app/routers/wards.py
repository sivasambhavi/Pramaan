from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.queries import LIST_WARDS, WARD_ASSETS, WARD_GAPS, WARD_ASSET_DETAIL, GET_WARDS_WITH_ASSETS

router = APIRouter()


@router.get("/with-assets", summary="List wards that have at least 1 asset")
def wards_with_assets():
    with get_session() as session:
        result = session.run(GET_WARDS_WITH_ASSETS)
        return [{"region_id": r["region_id"], "name": r["name"], "asset_count": r["asset_count"]} for r in result]

@router.get("/comparison", summary="Compare assets across wards")
def ward_comparison():
    from app.queries import DISTRICT_COMPARISON
    with get_session() as session:
        result = session.run(DISTRICT_COMPARISON)
        return [{"ward_name": r["ward_name"], "assets": r["assets"]} for r in result]


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


@router.get("/{ward_id}/score", summary="Get honest delivery score (A+B criteria) for a ward")
def ward_score(ward_id: str):
    with get_session() as session:
        result = session.run(WARD_ASSET_DETAIL, ward_id=ward_id)
        rows = [dict(r) for r in result]

    if not rows:
        return {
            "ward_id": ward_id,
            "total_assets": 0,
            "proven_assets": 0,
            "delivery_score": 0.0,
            "asset_breakdown": [],
            "scheme_breakdown": {},
            "counts": {"fully_verified": 0, "partially_verified": 0, "news_only": 0, "data_only": 0, "unverified": 0}
        }

    counts = {"fully_verified": 0, "partially_verified": 0, "news_only": 0, "data_only": 0, "unverified": 0}
    scheme_breakdown: dict = {}
    breakdown = []

    for r in rows:
        status = r.get("proof_status")
        if not status:
            status = "unverified"
        if status == "verified":
            status = "fully_verified"
            
        counts[status] = counts.get(status, 0) + 1

        # Scheme breakdown
        sname = r.get("scheme_name") or "Unknown"
        scheme_breakdown[sname] = scheme_breakdown.get(sname, 0) + 1

        breakdown.append({
            "asset_id": r.get("asset_id"),
            "name": r.get("name"),
            "type": r.get("type"),
            "status": r.get("status"),
            "cost": r.get("cost"),
            "scheme_name": r.get("scheme_name"),
            "actor_name": r.get("actor_name"),
            "proof_status": status,
            "lat": r.get("lat"),
            "lon": r.get("lon"),
        })

    total = len(breakdown)
    
    # Mathematical score weighting
    weighted = sum(
        1.0 if b.get('proof_status') in ['fully_verified', 'verified']
        else 0.5 if b.get('proof_status') == 'partially_verified'
        else 0.0
        for b in breakdown
    )
    
    proven = sum(1 for b in breakdown if b.get('proof_status') in ['fully_verified', 'verified', 'partially_verified', 'news_only'])
    score = round(100 * (weighted / total), 1) if total > 0 else 0.0

    return {
        "ward_id": ward_id,
        "total_assets": total,
        "proven_assets": proven,
        "delivery_score": score,
        "counts": counts,
        "scheme_breakdown": scheme_breakdown,
        "asset_breakdown": breakdown,
    }
