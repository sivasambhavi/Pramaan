from fastapi import APIRouter

router = APIRouter()


@router.get("/{asset_id}/chain", summary="Get proof chain for an asset")
async def asset_chain(asset_id: str):
    """Return a stubbed proof/evidence chain for a given asset."""
    return {
        "asset_id": asset_id,
        "chain": [
            {"step": 1, "type": "creation", "source": "Seed CSV"},
            {"step": 2, "type": "update", "source": "Field survey"},
        ],
    }

