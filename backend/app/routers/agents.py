from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.neo4j_client import get_session
from app.services.verification_agent import VerificationAgent

router = APIRouter(prefix="/agents", tags=["agents"])


class VerifyPayload(BaseModel):
    cost: Optional[float] = None
    status: Optional[str] = None
    confidence: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    source: Optional[str] = "agent_verify_api"


def _asset_snapshot(asset_id: str, session) -> dict | None:
    rec = session.run(
        """
        MATCH (a:Asset {asset_id: $asset_id})
        RETURN properties(a) AS props
        LIMIT 1
        """,
        asset_id=asset_id,
    ).single()
    return dict(rec["props"]) if rec else None


@router.post("/verify/{asset_id}", summary="Run verification on one asset")
def verify_asset(asset_id: str, payload: VerifyPayload | None = None):
    with get_session() as session:
        snap = _asset_snapshot(asset_id, session)
        if snap is None:
            raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

        incoming = {
            "cost": (payload.cost if payload and payload.cost is not None else snap.get("cost")),
            "status": (payload.status if payload and payload.status is not None else snap.get("status")),
            "confidence": (payload.confidence if payload and payload.confidence is not None else 0.7),
            "source": (payload.source if payload and payload.source else "agent_verify_api"),
        }

        vr = VerificationAgent.verify(
            label="Asset",
            node_id=asset_id,
            incoming=incoming,
            session=session,
        )

    return {
        "asset_id": asset_id,
        "action": vr.action,
        "old_conf": vr.old_conf,
        "new_conf": vr.new_conf,
        "trust_tier": vr.trust_tier,
        "conflicts": vr.conflicts,
    }


@router.post("/verify-all", summary="Run verification sweep for all assets")
def verify_all_assets(default_confidence: float = 0.7):
    if default_confidence < 0 or default_confidence > 1:
        raise HTTPException(status_code=400, detail="default_confidence must be in [0, 1]")

    summary = {
        "total_assets": 0,
        "corroborated": 0,
        "created": 0,
        "conflicts": 0,
        "failed": 0,
        "items": [],
    }

    with get_session() as session:
        rows = session.run(
            """
            MATCH (a:Asset)
            RETURN a.asset_id AS asset_id, a.cost AS cost, a.status AS status
            """
        )
        for r in rows:
            summary["total_assets"] += 1
            asset_id = r["asset_id"]
            incoming = {
                "cost": r.get("cost"),
                "status": r.get("status"),
                "confidence": default_confidence,
                "source": "agent_verify_sweep",
            }
            try:
                vr = VerificationAgent.verify("Asset", asset_id, incoming, session)
                if vr.action == "CORROBORATED":
                    summary["corroborated"] += 1
                elif vr.action == "CREATED":
                    summary["created"] += 1
                elif vr.action == "CONFLICT_FLAGGED":
                    summary["conflicts"] += 1
                summary["items"].append(
                    {
                        "asset_id": asset_id,
                        "action": vr.action,
                        "new_conf": vr.new_conf,
                        "trust_tier": vr.trust_tier,
                    }
                )
            except Exception as e:
                summary["failed"] += 1
                summary["items"].append(
                    {
                        "asset_id": asset_id,
                        "action": "ERROR",
                        "error": str(e),
                    }
                )

    return summary
