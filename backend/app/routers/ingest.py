from fastapi import APIRouter

router = APIRouter()


@router.post("/entities", summary="Ingest entities/evidence")
async def ingest_entities(payload: dict):
    """Stub endpoint to accept ingested entities/evidence.

    In the future, validate with Pydantic models and write to Neo4j.
    """
    return {
        "received": True,
        "count": len(payload) if isinstance(payload, dict) else None,
    }

