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
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.neo4j_client import get_session
from app.models import IngestPayload, IngestResponse, ValidationEntry, ValidationSummary
from app.queries import build_merge_entity_query, build_merge_relation_query, SOURCE_CONFIDENCE, DETECT_CONFLICTS
from app.services.verification_agent import VerificationAgent
from app.services.entity_resolver import resolve_entity_id, invalidate_cache
import exifread

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


def _audit_stamp(
    confidence: float | None = None,
    source_type: str = "ai_extract",
    source_text: str | None = None,
    ai_model: str | None = None,
    ai_prompt_version: str | None = None,
) -> dict:
    """Return properties stamped on every ingested node for full data lineage."""
    return {
        "source":       "live_ingestion",
        "source_type":  source_type,
        "source_text":  source_text or "",
        "ai_model":     ai_model or "",
        "ai_prompt_version": ai_prompt_version or "",
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
                    stamp = _audit_stamp(
                        conf,
                        source_type=payload_source_type,
                        source_text=getattr(payload, "source_text", None),
                        ai_model=getattr(payload, "ai_model", None),
                        ai_prompt_version=getattr(payload, "ai_prompt_version", None),
                    )
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


def _exif_to_decimal(tags: dict, ref_key: str, val_key: str) -> float | None:
    """Convert EXIF GPS rationals to signed decimal degrees."""
    ref = tags.get(ref_key)
    val = tags.get(val_key)
    if not ref or not val:
        return None
    try:
        d = float(val.values[0].num) / float(val.values[0].den)
        m = float(val.values[1].num) / float(val.values[1].den)
        s = float(val.values[2].num) / float(val.values[2].den)
        out = d + (m / 60.0) + (s / 3600.0)
        if str(ref).upper() in {"S", "W"}:
            out = -out
        return out
    except Exception:
        return None


@router.post("/photo-evidence", summary="Upload photo, parse EXIF GPS, and link to nearest asset")
async def ingest_photo_evidence(
    photo: UploadFile = File(...),
    ward_id: str | None = Form(default=None),
    radius_meters: float = Form(default=200.0),
):
    import io

    content = await photo.read()
    try:
        tags = exifread.process_file(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse EXIF data: {e}")

    lat = _exif_to_decimal(tags, "GPS GPSLatitudeRef", "GPS GPSLatitude")
    lon = _exif_to_decimal(tags, "GPS GPSLongitudeRef", "GPS GPSLongitude")
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="No GPS EXIF data found in uploaded photo.")

    uploads_dir = Path(__file__).resolve().parents[3] / "frontend" / "static" / "evidence" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(photo.filename or "").suffix or ".jpg"
    filename = f"upload_{uuid.uuid4().hex}{suffix}"
    fpath = uploads_dir / filename
    fpath.write_bytes(content)
    rel_url = f"frontend/static/evidence/uploads/{filename}"

    with get_session() as session:
        query = """
            MATCH (a:Asset)
            WHERE a.lat IS NOT NULL AND a.lon IS NOT NULL
              AND ($ward_id IS NULL OR a.region_id = $ward_id OR EXISTS {
                  MATCH (r:Region {region_id: a.region_id}) WHERE r.parent_region_id = $ward_id
              })
            WITH a, point({latitude: toFloat(a.lat), longitude: toFloat(a.lon)}) AS p,
                 point({latitude: $lat, longitude: $lon}) AS q
            RETURN a.asset_id AS asset_id, a.name AS asset_name, distance(p, q) AS meters
            ORDER BY meters ASC
            LIMIT 1
        """
        rec = session.run(query, lat=lat, lon=lon, ward_id=ward_id).single()
        if not rec:
            raise HTTPException(status_code=404, detail="No nearby asset with coordinates found.")

        asset_id = rec["asset_id"]
        meters = float(rec["meters"])
        if meters > radius_meters:
            raise HTTPException(status_code=422, detail=f"Nearest asset is {meters:.1f}m away (> {radius_meters}m radius).")

        evidence_id = f"EV_UP_{uuid.uuid4().hex[:10].upper()}"
        session.run(
            """
            MATCH (a:Asset {asset_id: $asset_id})
            MERGE (e:Evidence {evidence_id: $evidence_id})
            SET e.type='image',
                e.url=$url,
                e.before_or_after='after',
                e.capture_date=date().toString(),
                e.source='photo_exif_upload',
                e.source_type='photo_exif',
                e.confidence=0.95,
                e.ingested_at=$now,
                e.ingested_by='photo_exif_uploader',
                e.lat=$lat,
                e.lon=$lon
            MERGE (e)-[:PROVES]->(a)
            SET a.proof_status='fully_verified',
                a.verified=true
            """,
            asset_id=asset_id,
            evidence_id=evidence_id,
            url=rel_url,
            now=datetime.now(timezone.utc).isoformat(),
            lat=lat,
            lon=lon,
        )

    return {
        "success": True,
        "asset_id": asset_id,
        "asset_name": rec["asset_name"],
        "distance_meters": round(meters, 2),
        "evidence_id": evidence_id,
        "stored_path": rel_url,
        "lat": lat,
        "lon": lon,
        "message": "Photo evidence linked and asset marked fully_verified.",
    }
