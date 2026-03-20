"""
ingest.py — PRAMAAN Live Ingestion Router

Fix 1 applied: resolve_canonical_id() maps LLM-generated IDs to canonical
               graph IDs before any write, preventing orphan nodes.
Fix 5 applied: Every ingested node gets confidence, source, ingested_at,
               and ingested_by stamps so the graph retains full data lineage.

Validation layer (6 gates):
  Gate 1 — Confidence threshold  : skip entities with confidence < MIN_CONFIDENCE
  Gate 2 — Hallucination guard   : sanity-check cost + status values against known bounds
  Gate 3 — Duplicate entity check: skip if a node with the same name+label already exists
  Gate 4 — Relevance threshold   : drop relations whose source article is "Unrelated"
  Gate 5 — ID resolver           : map LLM IDs → canonical graph IDs (Fix 1)
  Gate 6 — Audit stamp           : write lineage metadata on every node (Fix 5)
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.neo4j_client import get_session
from app.models import IngestPayload, IngestResponse, ValidationEntry, ValidationSummary
from app.queries import build_merge_entity_query, build_merge_relation_query, SOURCE_CONFIDENCE, DETECT_CONFLICTS
from app.services.verification_agent import VerificationAgent
from app.services.entity_resolver import resolve_entity_id, invalidate_cache

logger = logging.getLogger(__name__)

# ─── Validation thresholds ────────────────────────────────────────────────────
MIN_CONFIDENCE   = 0.55          # entities below this are quarantined, not written
MAX_ASSET_COST   = 5_00_00_00_000  # ₹500 crore — anything above is likely hallucinated
MIN_ASSET_COST   = 100           # ₹100 — anything below is likely a parsing error
VALID_STATUSES   = {"completed", "in_progress", "planned", ""}
VALID_RELEVANCES = {"Direct Match", "Zone Context", "National Context"}  # "Unrelated" is excluded

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
    # ── Ward 12 actors ───────────────────────────────────────
    "act_w12_councillor":           "ACT_W12_COUNCILLOR",
    "act_w12_works_dept":           "ACT_W12_WORKS_DEPT",
    # ── Ward 28 actors ───────────────────────────────────────
    "act_w28_councillor":           "ACT_W28_COUNCILLOR",
    "act_w28_sanitation_dept":      "ACT_W28_SANITATION_DEPT",
    # ── Extended regions ─────────────────────────────────────
    "reg_w12":   "REG_W12",
    "ward_12":   "REG_W12",
    "ward 12":   "REG_W12",
    "reg_w28":   "REG_W28",
    "ward_28":   "REG_W28",
    "ward 28":   "REG_W28",
    # ── New schemes ───────────────────────────────────────────
    "sch_jjby":      "SCH_JJBY",
    "jal jeevan":    "SCH_JJBY",
    "sch_ayushman":  "SCH_AYUSHMAN",
    "ayushman":      "SCH_AYUSHMAN",
    "pmjay":         "SCH_AYUSHMAN",
    "sch_ddugjy":    "SCH_DDUGJY",
    "ddugjy":        "SCH_DDUGJY",
}


def resolve_canonical_id(entity_id: str, entity_name: str = "") -> str:
    """
    Map an LLM-generated entity ID (or name) to its canonical graph ID.
    """
    id_lower   = entity_id.lower().strip().replace("-", "_").replace(" ", "_")
    name_lower = entity_name.lower().strip()

    if id_lower in _CANONICAL_MAP:
        return _CANONICAL_MAP[id_lower]

    for keyword, canonical in _CANONICAL_MAP.items():
        if keyword.replace(" ", "_") in id_lower or keyword in id_lower:
            return canonical

    for keyword, canonical in _CANONICAL_MAP.items():
        if keyword in name_lower:
            return canonical

    return entity_id


def _audit_stamp(confidence: float | None = None, source_type: str = "ai_extract") -> dict:
    """Return properties stamped on every ingested node for full data lineage."""
    return {
        "source":       "live_ingestion",
        "source_type":  source_type,
        "confidence":   round(float(confidence), 3) if confidence is not None else 0.7,
        "ingested_at":  datetime.now(timezone.utc).isoformat(),
        "ingested_by":  "pramaan_live_ingestion",
    }


def _check_hallucination(entity_id: str, label: str, props: dict) -> str | None:
    """
    Gate 2 — Sanity-check numeric + categorical values for plausibility.
    Returns an error string if the entity looks hallucinated, else None.
    """
    if label == "Asset":
        cost = props.get("cost")
        if cost is not None:
            try:
                c = float(cost)
                if c < MIN_ASSET_COST:
                    return f"cost ₹{c} is implausibly low (< ₹{MIN_ASSET_COST})"
                if c > MAX_ASSET_COST:
                    return f"cost ₹{c:,.0f} exceeds ₹500 crore ceiling — likely hallucinated"
            except (ValueError, TypeError):
                return f"cost value '{cost}' is not a valid number"

        status = str(props.get("status", "")).lower().strip()
        if status and status not in VALID_STATUSES:
            return f"status '{status}' not in allowed set {VALID_STATUSES}"

    return None  # passes


def _entity_exists(session, label: str, name: str) -> bool:
    """
    Gate 3 — Check if a node with the same label+name already exists in Neo4j.
    Uses case-insensitive match to catch near-duplicates.
    """
    if not name:
        return False
    result = session.run(
        f"MATCH (n:{label}) WHERE toLower(trim(n.name)) = toLower(trim($name)) RETURN count(n) AS c",
        name=name,
    )
    rec = result.single()
    return bool(rec and rec["c"] > 0)


# ─── POST /ingest/entities ────────────────────────────────────────────────────

@router.post("/entities", summary="Ingest entities and relations", response_model=IngestResponse)
def ingest_entities(payload: IngestPayload):
    entities_created         = 0
    relations_created        = 0
    skipped_low_confidence   = 0
    skipped_hallucinations   = 0
    skipped_duplicates       = 0
    skipped_unrelated        = 0
    validation_log: list[ValidationEntry] = []   # per-entity typed audit trail

    id_remap: dict[str, str] = {}
    payload_source_type = getattr(payload, "source_type", "unstructured_llm")

    try:
        with get_session() as session:

            # ── Step 1: validate + write entities ────────────────────────────
            for entity in payload.entities:
                name     = entity.properties.get("name", "")
                raw_conf = entity.properties.get("confidence")
                conf     = float(raw_conf) if raw_conf is not None else 0.0
                # Gate 1 — Confidence threshold
                if conf < MIN_CONFIDENCE:
                    validation_log.append(ValidationEntry(
                        id=entity.id, label=entity.label, name=name, confidence=conf,
                        decision="REJECTED_LOW_CONFIDENCE",
                        reason=f"confidence {conf:.2f} < threshold {MIN_CONFIDENCE}",
                    ))
                    skipped_low_confidence += 1
                    logger.info("[ingest] SKIP low-conf %r (%.2f)", entity.id, conf)
                    id_remap[entity.id] = entity.id
                    continue

                # Gate 2 — Hallucination guard
                halluc_reason = _check_hallucination(entity.id, entity.label, entity.properties)
                if halluc_reason:
                    validation_log.append(ValidationEntry(
                        id=entity.id, label=entity.label, name=name, confidence=conf,
                        decision="REJECTED_HALLUCINATION",
                        reason=halluc_reason,
                    ))
                    skipped_hallucinations += 1
                    logger.warning("[ingest] HALLUCINATION %r: %s", entity.id, halluc_reason)
                    id_remap[entity.id] = entity.id
                    continue

                # Gate 5 — ID resolver (Phase 1 static + Phase 2 dynamic fuzzy)
                resolved = resolve_entity_id(entity.id, name, entity.label, session)
                id_remap[entity.id] = resolved

                # Gate 3 — Duplicate check (only for NEW ids, not canonical ones)
                if resolved == entity.id and _entity_exists(session, entity.label, name):
                    validation_log.append(ValidationEntry(
                        id=entity.id, label=entity.label, name=name, confidence=conf,
                        decision="SKIPPED_DUPLICATE",
                        reason=f"Node {entity.label}(name='{name}') already exists in graph",
                        resolved_id=resolved,
                    ))
                    skipped_duplicates += 1
                    logger.info("[ingest] DUPLICATE %r ('%s')", entity.id, name)
                    continue

                # ── Write to Neo4j ──────────────────────────────────────────
                try:
                    stamp = _audit_stamp(conf, source_type=payload_source_type)
                    props = {**entity.properties, **stamp}
                    props["confidence"] = round(max(conf, stamp["confidence"]), 3)

                    query = build_merge_entity_query(entity.label)
                    session.run(query, id=resolved, properties=props)

                    # Gate 7 — Verification Agent: Bayesian update + conflict detection
                    vr = VerificationAgent.verify(
                        label=entity.label,
                        node_id=resolved,
                        incoming=entity.properties,
                        session=session,
                    )
                    if vr.action == "CONFLICT_FLAGGED":
                        logger.warning(
                            "[ingest] CONFLICT %s(%s): %s",
                            entity.label, resolved, vr.conflicts
                        )

                    entities_created += 1
                    validation_log.append(ValidationEntry(
                        id=entity.id, label=entity.label, name=name, confidence=vr.new_conf,
                        decision=f"ACCEPTED ({vr.action})",
                        resolved_id=resolved,
                    ))

                except Exception as e:
                    validation_log.append(ValidationEntry(
                        id=entity.id, label=entity.label, name=name, confidence=conf,
                        decision="ERROR",
                        reason=str(e),
                    ))
                    logger.error("[ingest] write error %r: %s", entity.id, e)

            # ── Step 2: rewrite relation ids + write relations ────────────────
            base_confidence = SOURCE_CONFIDENCE.get(payload_source_type, 0.6)
            now = datetime.now(timezone.utc).isoformat()

            for relation in payload.relations:
                try:
                    from_id = id_remap.get(relation.from_id, relation.from_id)
                    to_id   = id_remap.get(relation.to_id,   relation.to_id)
                    from_id = resolve_entity_id(from_id, label=relation.from_label, session=session)
                    to_id   = resolve_entity_id(to_id,   label=relation.to_label,   session=session)

                    # Gate 4 — Relevance threshold: skip relations whose
                    # source article was flagged "Unrelated" by score_evidence
                    rel_relevance = relation.properties.get("relevance", "")
                    if rel_relevance and rel_relevance not in VALID_RELEVANCES:
                        skipped_unrelated += 1
                        logger.info("[ingest] SKIP unrelated relation %s→%s (%s)", from_id, to_id, rel_relevance)
                        continue

                    query = build_merge_relation_query(
                        relation.type,
                        from_label=relation.from_label,
                        to_label=relation.to_label,
                    )
                    session.run(
                        query,
                        from_id=from_id,
                        to_id=to_id,
                        properties=getattr(relation, "properties", {}),
                        source_type=payload_source_type,
                        now=now,
                        base_confidence=base_confidence,
                    )
                    relations_created += 1

                except Exception as e:
                    logger.error("[ingest] relation error %r: %s", relation.type, e)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Invalidate entity resolver cache so new nodes are visible to next request
    if entities_created > 0:
        invalidate_cache()

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
        skipped_low_confidence=skipped_low_confidence,
        skipped_duplicates=skipped_duplicates,
        skipped_hallucinations=skipped_hallucinations,
        skipped_unrelated_relations=skipped_unrelated,
        validation_summary=ValidationSummary(
            total_submitted=len(payload.entities),
            accepted=entities_created,
            rejected=skipped_low_confidence + skipped_hallucinations + skipped_duplicates,
            log=validation_log,
        ),
    )


@router.get("/conflicts", summary="Detect relationship conflicts (multi-actor BUILT_BY or multi-scheme FUNDS)")
def get_conflicts():
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


@router.delete("/demo-nodes", summary="Remove all AI-ingested demo nodes")
def delete_demo_nodes():
    deleted_nodes = 0
    try:
        with get_session() as session:
            res = session.run("MATCH (n) WHERE n.source = 'live_ingestion' OR n.ingested_by = 'pramaan_live_ingestion' RETURN count(n) AS c")
            record = res.single()
            deleted_nodes = record["c"] if record else 0

            session.run("MATCH (n) WHERE n.source = 'live_ingestion' OR n.ingested_by = 'pramaan_live_ingestion' DETACH DELETE n")
        return {
            "success": True,
            "deleted_nodes": deleted_nodes,
            "message": f"Removed {deleted_nodes} live-ingested node(s).",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
