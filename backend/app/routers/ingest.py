"""
ingest.py — PRAMAAN Live Ingestion Router

Fix 1 applied: resolve_canonical_id() maps LLM-generated IDs to canonical
               graph IDs before any write, preventing orphan nodes.
Fix 5 applied: Every ingested node gets confidence, source, ingested_at,
               and ingested_by stamps so the graph retains full data lineage.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.models import IngestPayload, IngestResponse
from app.queries import build_merge_entity_query, build_merge_relation_query

router = APIRouter()


# ─── Fix 1: Canonical ID resolver ────────────────────────────────────────────
# Maps keyword patterns (lower-case) → the canonical graph ID that already
# exists in Neo4j. The LLM often generates ids like "scheme_amrut" or
# "reg_w45_shahdara" — this table normalises them before any write.

_CANONICAL_MAP: dict[str, str] = {
    # ── Schemes ──────────────────────────────────────────────
    "sch_amrut":        "SCH_AMRUT",
    "amrut":            "SCH_AMRUT",
    "scheme_amrut":     "SCH_AMRUT",
    "sch_pmay":         "SCH_PMAY",
    "pmay":             "SCH_PMAY",
    "scheme_pmay":      "SCH_PMAY",
    "pradhan mantri awas": "SCH_PMAY",
    "sch_swachh":       "SCH_SWACHH",
    "swachh":           "SCH_SWACHH",
    "swachhbharat":     "SCH_SWACHH",
    "sch_sfc":          "SCH_SFC",
    "sfc":              "SCH_SFC",
    "sch_local_lights": "SCH_LOCAL_LIGHTS",
    "streetlight":      "SCH_LOCAL_LIGHTS",
    # ── Regions ──────────────────────────────────────────────
    "reg_delhi":                "REG_DELHI",
    "reg_w45":                  "REG_W45",
    "ward_45":                  "REG_W45",
    "ward45":                   "REG_W45",
    "ward 45":                  "REG_W45",
    "shahdara ward 45":         "REG_W45",
    "reg_shahdara_north":       "REG_SHAHDARA_NORTH",
    "shahdara north":           "REG_SHAHDARA_NORTH",
    "reg_shahdara_south":       "REG_SHAHDARA_SOUTH",
    "shahdara south":           "REG_SHAHDARA_SOUTH",
    "reg_w45_gali7":            "REG_W45_GALI7",
    "gali 7":                   "REG_W45_GALI7",
    "gali7":                    "REG_W45_GALI7",
    "reg_w45_gali12":           "REG_W45_GALI12",
    "gali 12":                  "REG_W45_GALI12",
    "gali12":                   "REG_W45_GALI12",
    "reg_w45_gali3":            "REG_W45_GALI3",
    "gali 3":                   "REG_W45_GALI3",
    "reg_w45_market_road":      "REG_W45_MARKET_ROAD",
    "shahdara market":          "REG_W45_MARKET_ROAD",
    "reg_w45_colony_y":         "REG_W45_COLONY_Y",
    "colony y":                 "REG_W45_COLONY_Y",
    # ── Actors ───────────────────────────────────────────────
    "act_mcd_shahdara_works":       "ACT_MCD_SHAHDARA_WORKS",
    "mcd shahdara works":           "ACT_MCD_SHAHDARA_WORKS",
    "mcd_shahdara":                 "ACT_MCD_SHAHDARA_WORKS",
    "act_mcd_shahdara_sanitation":  "ACT_MCD_SHAHDARA_SANITATION",
    "mcd sanitation":               "ACT_MCD_SHAHDARA_SANITATION",
    "act_mcd_electrical":           "ACT_MCD_ELECTRICAL",
    "mcd electrical":               "ACT_MCD_ELECTRICAL",
    "act_dda":                      "ACT_DDA",
    "dda":                          "ACT_DDA",
    "delhi development authority":  "ACT_DDA",
    "act_w45_councillor":           "ACT_W45_COUNCILLOR",
    "councillor":                   "ACT_W45_COUNCILLOR",
    "act_contractor_infra_1":       "ACT_CONTRACTOR_INFRA_1",
    "abc infra":                    "ACT_CONTRACTOR_INFRA_1",
    "act_contractor_lights_1":      "ACT_CONTRACTOR_LIGHTS_1",
    "brightlights":                 "ACT_CONTRACTOR_LIGHTS_1",
}


def resolve_canonical_id(entity_id: str, entity_name: str = "") -> str:
    """
    Map an LLM-generated entity ID (or name) to its canonical graph ID.

    Strategy:
      1. Exact match on lower-case entity_id
      2. Substring match of any keyword inside entity_id
      3. Substring match of any keyword inside entity_name
      4. Return original entity_id unchanged (it's a genuinely new node)
    """
    id_lower   = entity_id.lower().strip().replace("-", "_").replace(" ", "_")
    name_lower = entity_name.lower().strip()

    # 1. Exact match
    if id_lower in _CANONICAL_MAP:
        return _CANONICAL_MAP[id_lower]

    # 2. Keyword substring in id
    for keyword, canonical in _CANONICAL_MAP.items():
        if keyword.replace(" ", "_") in id_lower or keyword in id_lower:
            return canonical

    # 3. Keyword substring in name
    for keyword, canonical in _CANONICAL_MAP.items():
        if keyword in name_lower:
            return canonical

    # 4. Genuinely new node — keep as-is
    return entity_id


# ─── Fix 5: Build audit stamp ─────────────────────────────────────────────────

def _audit_stamp(confidence: float | None = None) -> dict:
    """
    Return properties stamped on every ingested node for full data lineage.
    Fix 5: Every node now carries source, confidence, ingested_at, ingested_by.
    """
    return {
        "source":       "live_ingestion",
        "source_type":  "ai_extract",
        "confidence":   round(float(confidence), 3) if confidence is not None else 0.7,
        "ingested_at":  datetime.now(timezone.utc).isoformat(),
        "ingested_by":  "pramaan_live_ingestion",
    }


# ─── POST /ingest/entities ────────────────────────────────────────────────────

@router.post("/entities", summary="Ingest entities and relations", response_model=IngestResponse)
def ingest_entities(payload: IngestPayload):
    entities_created  = 0
    relations_created = 0
    skipped_relations = 0

    # Build a mapping of original LLM id → resolved canonical id so that
    # relations referencing the original ids are also rewritten.
    id_remap: dict[str, str] = {}

    try:
        with get_session() as session:

            # ── Step 1: resolve + write entities ─────────────────────────────
            for entity in payload.entities:
                try:
                    name       = entity.properties.get("name", "")
                    raw_conf   = entity.properties.get("confidence")
                    resolved   = resolve_canonical_id(entity.id, name)
                    id_remap[entity.id] = resolved

                    # Merge: user-provided props + audit stamp
                    # (audit stamp does NOT overwrite existing confidence if higher)
                    stamp = _audit_stamp(raw_conf)
                    props = {**entity.properties, **stamp}

                    # If LLM confidence is present, keep the higher value
                    if raw_conf is not None:
                        props["confidence"] = round(max(float(raw_conf), stamp["confidence"]), 3)

                    query = build_merge_entity_query(entity.label)
                    session.run(query, id=resolved, properties=props)
                    entities_created += 1

                    if resolved != entity.id:
                        print(f"  [ID Resolver] {entity.id!r} → {resolved!r}")
                    else:
                        print(f"  [New node]    {entity.id!r} ({entity.label})")

                except (ValueError, Exception) as e:
                    print(f"Skipping entity {entity.id!r}: {e}")

            # ── Step 2: rewrite relation ids + write relations ────────────────
            for relation in payload.relations:
                try:
                    # Rewrite from_id / to_id using the resolved map
                    from_id = id_remap.get(relation.from_id, relation.from_id)
                    to_id   = id_remap.get(relation.to_id,   relation.to_id)

                    # Also resolve any ids that weren't in this batch
                    # (i.e. the LLM referenced an existing entity without
                    #  including it in the entities list)
                    from_id = resolve_canonical_id(from_id)
                    to_id   = resolve_canonical_id(to_id)

                    query = build_merge_relation_query(
                        relation.type,
                        from_label=relation.from_label,
                        to_label=relation.to_label,
                    )
                    rel_props = {
                        **getattr(relation, "properties", {}),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "source": "live_ingestion",
                    }
                    session.run(query, from_id=from_id, to_id=to_id, properties=rel_props)
                    relations_created += 1

                except ValueError as e:
                    print(f"Skipping relation {relation.type!r} ({relation.from_id}→{relation.to_id}): {e}")
                    skipped_relations += 1
                except Exception as e:
                    print(f"Relation error {relation.type!r}: {e}")
                    skipped_relations += 1

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ── Step 3: return delivery chain for the primary asset ──────────────────
    delivery_chain = None
    try:
        primary_raw = next((e.id for e in payload.entities if e.label == "Asset"), None)
        if primary_raw:
            primary_asset_id = id_remap.get(primary_raw, primary_raw)
            from app.queries import ASSET_CHAIN
            with get_session() as session:
                res = session.run(ASSET_CHAIN, asset_id=primary_asset_id)
                rec = res.single()
                if rec and rec["a"]:
                    ward_name   = dict(rec["ward"]).get("name")   if rec["ward"]   else None
                    street_name = dict(rec["street"]).get("name") if rec["street"] else None
                    delivery_chain = {
                        "asset_id":        primary_asset_id,
                        "asset_name":      dict(rec["a"]).get("name", "Unknown"),
                        "scheme":          dict(rec["s"])   if rec["s"]   else None,
                        "actor":           dict(rec["act"]) if rec["act"] else None,
                        "region":          {"ward": ward_name, "street": street_name},
                        "people_served":   rec["people_served"],
                        "beneficiary_desc":rec["beneficiary_desc"],
                        "evidence":        [dict(e) for e in rec["evidence_list"] if e],
                        "matched_existing": primary_raw != primary_asset_id,
                    }
    except Exception as e:
        print(f"Error fetching delivery chain: {e}")

    return IngestResponse(
        entities_created=entities_created,
        relations_created=relations_created,
        delivery_chain=delivery_chain,
    )


# ─── DELETE /ingest/demo-nodes ────────────────────────────────────────────────
# Removes all nodes created by live ingestion (source = "live_ingestion").
# Keeps seed data (source = "official_csv") intact.
# Called by the Live Ingestion page "Reset Demo" button.

@router.delete("/demo-nodes", summary="Remove all AI-ingested demo nodes")
def delete_demo_nodes():
    """
    Delete all nodes where source = 'live_ingestion'.
    Seed data (source_type = 'official_csv') is preserved.
    """
    deleted_nodes = 0
    deleted_rels  = 0
    try:
        with get_session() as session:
            # Count before delete for the response
            res = session.run(
                "MATCH (n) WHERE n.source = 'live_ingestion' RETURN count(n) AS c"
            )
            deleted_nodes = res.single()["c"]

            # Detach-delete removes the node and all its relationships
            session.run(
                "MATCH (n) WHERE n.source = 'live_ingestion' DETACH DELETE n"
            )
        return {
            "success": True,
            "deleted_nodes": deleted_nodes,
            "message": f"Removed {deleted_nodes} live-ingested node(s). Seed data untouched.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
