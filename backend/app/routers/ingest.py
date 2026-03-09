from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.models import IngestPayload, IngestResponse
from app.queries import build_merge_entity_query, build_merge_relation_query

router = APIRouter()


@router.post("/entities", summary="Ingest entities and relations", response_model=IngestResponse)
def ingest_entities(payload: IngestPayload):
    entities_created = 0
    relations_created = 0
    skipped_relations = 0

    try:
        with get_session() as session:
            # Always ingest entities first
            for entity in payload.entities:
                try:
                    query = build_merge_entity_query(entity.label)
                    session.run(query, id=entity.id, properties=entity.properties)
                    entities_created += 1
                except (ValueError, Exception) as e:
                    print(f"Skipping entity {entity.id!r}: {e}")

            # Ingest relations, skipping any with unknown/invalid types
            for relation in payload.relations:
                try:
                    query = build_merge_relation_query(
                        relation.type,
                        from_label=relation.from_label,
                        to_label=relation.to_label
                    )
                    session.run(
                        query,
                        from_id=relation.from_id,
                        to_id=relation.to_id,
                        properties=getattr(relation, 'properties', {}),
                    )
                    relations_created += 1
                except ValueError as e:
                    print(f"Skipping relation {relation.type!r} ({relation.from_id}->{relation.to_id}): {e}")
                    skipped_relations += 1
                except Exception as e:
                    print(f"Relation error {relation.type!r}: {e}")
                    skipped_relations += 1

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return IngestResponse(
        entities_created=entities_created,
        relations_created=relations_created,
    )
