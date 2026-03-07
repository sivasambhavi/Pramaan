from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List all wards")
async def list_wards():
    \"\"\"Return a stubbed list of wards.

    Replace this with a real Neo4j query using helpers from `queries.py`.
    \"\"\"
    return [
        {"id": "ward-1", "name": "Sample Ward 1"},
        {"id": "ward-2", "name": "Sample Ward 2"},
    ]


@router.get("/{ward_id}/gaps", summary="Get gaps for a ward")
async def ward_gaps(ward_id: str):
    \"\"\"Return stubbed 'gaps' for a given ward."""
    return {
        "ward_id": ward_id,
        "gaps": [
            {"type": "infra", "description": "Missing PHC"},
            {"type": "staffing", "description": "ANM vacancy"},
        ],
    }

