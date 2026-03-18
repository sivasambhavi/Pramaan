from datetime import datetime, timezone
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
            stamp = {
                "source_type":  "ai_extract",
                "ingested_at":  datetime.now(timezone.utc).isoformat(),
                "ingested_by":  "pramaan_live_ingestion",
            }
            for entity in payload.entities:
                try:
                    props = {**entity.properties, **stamp}
                    # Don't overwrite confidence if LLM already set it
                    if "confidence" not in props:
                        props["confidence"] = 0.7
                    query = build_merge_entity_query(entity.label)
                    session.run(query, id=entity.id, properties=props)
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

    delivery_chain = None
    try:
        primary_asset_id = next((e.id for e in payload.entities if e.label == "Asset"), None)
        if primary_asset_id:
            from app.queries import ASSET_CHAIN
            with get_session() as session:
                res = session.run(ASSET_CHAIN, asset_id=primary_asset_id)
                rec = res.single()
                if rec and rec["a"]:
                    ward_name = dict(rec["ward"]).get("name") if rec["ward"] else None
                    street_name = dict(rec["street"]).get("name") if rec["street"] else None
                    delivery_chain = {
                        "asset_id": primary_asset_id,
                        "asset_name": dict(rec["a"]).get("name", "Unknown"),
                        "scheme": dict(rec["s"]) if rec["s"] else None,
                        "actor": dict(rec["act"]) if rec["act"] else None,
                        "region": {"ward": ward_name, "street": street_name},
                        "people_served": rec["people_served"],
                        "beneficiary_desc": rec["beneficiary_desc"],
                        "evidence": [dict(e) for e in rec["evidence_list"] if e is not None],
                        "matched_existing": entities_created == 0  # Approximation
                    }
    except Exception as e:
        print(f"Error fetching delivery chain: {e}")

    return IngestResponse(
        entities_created=entities_created,
        relations_created=relations_created,
        delivery_chain=delivery_chain
    )
