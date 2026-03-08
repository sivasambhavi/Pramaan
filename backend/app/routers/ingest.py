from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.models import IngestPayload, IngestResponse
from app.queries import build_merge_entity_query, build_merge_relation_query

router = APIRouter()


@router.post("/entities", summary="Ingest entities and relations", response_model=IngestResponse)
def ingest_entities(payload: IngestPayload):
    entities_created = 0
    relations_created = 0

    try:
        with get_session() as session:
            for entity in payload.entities:
                query = build_merge_entity_query(entity.label)
                session.run(query, id=entity.id, properties=entity.properties)
                entities_created += 1

            for relation in payload.relations:
                query = build_merge_relation_query(relation.type)
                session.run(
                    query,
                    from_id=relation.from_id,
                    to_id=relation.to_id,
                    properties=relation.properties,
                )
                relations_created += 1

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return IngestResponse(
        entities_created=entities_created,
        relations_created=relations_created,
    )
