from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.models import IngestPayload, IngestResponse
from app.queries import build_merge_entity_query, build_merge_relation_query, SOURCE_CONFIDENCE, DETECT_CONFLICTS

router = APIRouter()


@router.delete("/demo-nodes", summary="Delete all AI-ingested demo nodes")
def delete_demo_nodes():
    with get_session() as session:
        result = session.run("""
            MATCH (n)
            WHERE n.ingested_by = 'pramaan_live_ingestion'
            DETACH DELETE n
            RETURN count(n) AS deleted
        """)
        record = result.single()
    deleted = record["deleted"] if record else 0
    return {"deleted": deleted, "message": f"Removed {deleted} demo-ingested node(s)"}


@router.post("/entities", summary="Ingest entities and relations", response_model=IngestResponse)
def ingest_entities(payload: IngestPayload):
    entities_created = 0
    relations_created = 0
    skipped_relations = 0

    try:
        with get_session() as session:
            valid_source_types = {"unstructured_llm", "unstructured_rss"}
            if payload.source_type not in valid_source_types:
                raise HTTPException(status_code=422, detail=f"Invalid source_type '{payload.source_type}'. Must be one of: {valid_source_types}")

            stamp = {
                "source_type":  payload.source_type,
                "ingested_at":  datetime.now(timezone.utc).isoformat(),
                "ingested_by":  "pramaan_live_ingestion",
            }
            for entity in payload.entities:
                try:
                    # LLM confidence from entity.properties takes precedence — never overwrite it
                    props = {**stamp, **entity.properties}
                    if "confidence" not in props:
                        raise ValueError(f"Entity {entity.id!r} has no confidence score — LLM must set it")
                    query = build_merge_entity_query(entity.label)
                    session.run(query, id=entity.id, properties=props)
                    entities_created += 1
                except (ValueError, Exception) as e:
                    print(f"Skipping entity {entity.id!r}: {e}")

            # Ingest relations with confidence scoring
            base_confidence = SOURCE_CONFIDENCE.get(payload.source_type, 0.6)
            now = stamp["ingested_at"]
            for relation in payload.relations:
                try:
                    query = build_merge_relation_query(
                        relation.type,
                        from_label=relation.from_label,
                        to_label=relation.to_label,
                    )
                    session.run(
                        query,
                        from_id=relation.from_id,
                        to_id=relation.to_id,
                        properties=getattr(relation, 'properties', {}),
                        source_type=payload.source_type,
                        now=now,
                        base_confidence=base_confidence,
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


@router.get("/conflicts", summary="Detect relationship conflicts (multi-actor BUILT_BY or multi-scheme FUNDS)")
def get_conflicts():
    """
    Returns assets where the same relationship type is asserted by more than one party.
    E.g. two actors claiming BUILT_BY the same asset, or two schemes FUNDS the same asset.
    Useful for auditing contradictory AI-ingested data against seed data.
    """
    with get_session() as session:
        result = session.run(DETECT_CONFLICTS)
        conflicts = [
            {
                "asset_id":            rec["asset_id"],
                "asset_name":          rec["asset_name"],
                "conflict_type":       rec["conflict_type"],
                "conflicting_parties": [dict(p) for p in rec["conflicting_parties"]],
            }
            for rec in result
        ]
    return {"total": len(conflicts), "conflicts": conflicts}
