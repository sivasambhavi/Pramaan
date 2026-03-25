"""
ingest.py — PRAMAAN Live Ingestion Router

POST /ingest/entities — write AI-extracted entities + relations into Neo4j.

Validation pipeline:
  Gate 1 — label allowlist check
  Gate 2 — confidence threshold (≥ 0.6 default)
  Gate 3 — entity resolver (static map + fuzzy Neo4j match)
  Gate 4 — relation endpoint existence check

Returns IngestResponse with per-entity ValidationSummary.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from app.models import (
    IngestPayload, IngestResponse,
    ValidationEntry, ValidationSummary,
)
from app.services.entity_resolver import resolve_entity_id

log    = logging.getLogger("pramaan.ingest")
router = APIRouter(prefix="/ingest", tags=["ingest"])

# ── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_LABELS: set[str] = {
    "Event", "Region", "Actor", "Scheme", "Policy",
    "Impact", "Evidence", "Asset", "Domain",
}

ALLOWED_REL_TYPES: set[str] = {
    "OCCURRED_IN", "BELONGS_TO", "ALSO_IN", "MANAGED_BY",
    "FUNDED_BY", "CAUSED", "TRIGGERED", "CONNECTED_TO",
    "PART_OF", "PROVEN_BY", "FUNDS", "LOCATED_IN", "HAS_EVIDENCE",
}

# Map label → primary key field name
_LABEL_ID_FIELD: dict[str, str] = {
    "Domain":   "domain_id",
    "Region":   "region_id",
    "Actor":    "actor_id",
    "Scheme":   "scheme_id",
    "Policy":   "policy_id",
    "Event":    "event_id",
    "Impact":   "impact_id",
    "Evidence": "evidence_id",
    "Asset":    "asset_id",
}

CONFIDENCE_THRESHOLD = 0.6   # entities below this are rejected
INGESTED_BY_TAG      = "pramaan_live_ingestion"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _merge_node(session, label: str, id_field: str, node_id: str, props: dict[str, Any],
                source_type: str) -> bool:
    """MERGE a single node into Neo4j. Returns True if created/updated."""
    audit = {
        "source":      "live_ingestion",
        "source_type": source_type,
        "ingested_at": _now_iso(),
        "ingested_by": INGESTED_BY_TAG,
    }
    all_props = {**props, **audit, id_field: node_id}
    # Build SET clause dynamically — skip None values
    set_pairs  = ", ".join(f"n.{k} = ${k}" for k, v in all_props.items() if v is not None)
    cypher     = f"MERGE (n:{label} {{{id_field}: ${id_field}}}) SET {set_pairs} RETURN n"
    params     = {k: v for k, v in all_props.items() if v is not None}
    try:
        result = session.run(cypher, params)
        return result.single() is not None
    except Exception as e:
        log.warning("[ingest] MERGE node failed (%s %s): %s", label, node_id, e)
        return False


def _merge_relation(session, from_label: str, from_id_field: str, from_id: str,
                    to_label: str,   to_id_field:   str, to_id:   str,
                    rel_type: str,   props: dict[str, Any]) -> bool:
    """MERGE a single relation into Neo4j. Returns True if created."""
    reason = props.get("reason", "")
    try:
        result = session.run(f"""
            MATCH (a:{from_label} {{{from_id_field}: $from_id}})
            MATCH (b:{to_label}   {{{to_id_field}:  $to_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r.reason = $reason, r.ingested_at = $ts
            RETURN r
        """, {
            "from_id": from_id,
            "to_id":   to_id,
            "reason":  reason,
            "ts":      _now_iso(),
        })
        return result.single() is not None
    except Exception as e:
        log.warning("[ingest] MERGE relation failed (%s -[%s]-> %s): %s",
                    from_id, rel_type, to_id, e)
        return False


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/entities", response_model=IngestResponse)
def ingest_entities(payload: IngestPayload) -> IngestResponse:
    """
    Write AI-extracted entities + relations into Neo4j.
    Validates confidence, label allowlist, and resolves canonical IDs.
    """
    from app.neo4j_client import get_session

    validation_log: list[ValidationEntry] = []
    entities_created  = 0
    relations_created = 0
    skipped_low_conf  = 0
    skipped_hall      = 0
    skipped_dup       = 0
    skipped_rel       = 0

    with get_session() as session:
        # ── Phase 1: Entities ────────────────────────────────────────────────
        for ent in payload.entities:
            props      = ent.properties or {}
            confidence = float(props.get("confidence", 1.0))
            name       = str(props.get("name", ent.id))
            label      = ent.label

            # Gate 1 — label allowlist
            if label not in ALLOWED_LABELS:
                validation_log.append(ValidationEntry(
                    id=ent.id, label=label, name=name, confidence=confidence,
                    decision="REJECTED_HALLUCINATION",
                    reason=f"Label '{label}' not in allowed set",
                ))
                skipped_hall += 1
                continue

            # Gate 2 — confidence
            if confidence < CONFIDENCE_THRESHOLD:
                validation_log.append(ValidationEntry(
                    id=ent.id, label=label, name=name, confidence=confidence,
                    decision="REJECTED_LOW_CONFIDENCE",
                    reason=f"Confidence {confidence:.2f} < threshold {CONFIDENCE_THRESHOLD}",
                ))
                skipped_low_conf += 1
                continue

            # Gate 3 — entity resolver
            canonical_id = resolve_entity_id(
                raw_id=ent.id, name=name, label=label, session=session
            )
            id_field = _LABEL_ID_FIELD.get(label, f"{label.lower()}_id")

            ok = _merge_node(
                session, label, id_field, canonical_id, props, payload.source_type
            )

            if ok:
                entities_created += 1
                decision = "ACCEPTED"
            else:
                decision = "ERROR"

            validation_log.append(ValidationEntry(
                id=ent.id, label=label, name=name, confidence=confidence,
                decision=decision,
                resolved_id=canonical_id if ok else None,
            ))

        # ── Phase 2: Relations ───────────────────────────────────────────────
        for rel in payload.relations:
            from_label = rel.from_label
            to_label   = rel.to_label
            rel_type   = rel.type

            # Gate 1 — label + type allowlist
            if from_label not in ALLOWED_LABELS or to_label not in ALLOWED_LABELS:
                skipped_rel += 1
                continue
            if rel_type not in ALLOWED_REL_TYPES:
                skipped_rel += 1
                continue

            from_id_field = _LABEL_ID_FIELD.get(from_label, f"{from_label.lower()}_id")
            to_id_field   = _LABEL_ID_FIELD.get(to_label,   f"{to_label.lower()}_id")

            # Resolve IDs
            from_id = resolve_entity_id(raw_id=rel.from_id, label=from_label, session=session)
            to_id   = resolve_entity_id(raw_id=rel.to_id,   label=to_label,   session=session)

            ok = _merge_relation(
                session, from_label, from_id_field, from_id,
                to_label,   to_id_field,   to_id,
                rel_type,   rel.properties or {},
            )
            if ok:
                relations_created += 1
            else:
                skipped_rel += 1

    accepted  = sum(1 for v in validation_log if v.decision == "ACCEPTED")
    rejected  = len(validation_log) - accepted
    total_sub = len(payload.entities)

    log.info(
        "[ingest] entities=%d created=%d | relations=%d created=%d | "
        "low_conf=%d halluc=%d dup=%d rel_skip=%d",
        total_sub, entities_created,
        len(payload.relations), relations_created,
        skipped_low_conf, skipped_hall, skipped_dup, skipped_rel,
    )

    return IngestResponse(
        entities_created=entities_created,
        relations_created=relations_created,
        skipped_low_confidence=skipped_low_conf,
        skipped_duplicates=skipped_dup,
        skipped_hallucinations=skipped_hall,
        skipped_unrelated_relations=skipped_rel,
        validation_summary=ValidationSummary(
            total_submitted=total_sub,
            accepted=accepted,
            rejected=rejected,
            log=validation_log,
        ),
    )


@router.get("/live/recent-nodes", tags=["live"])
def recent_nodes(limit: int = 5) -> dict:
    """
    Return the most recently ingested nodes (those with an ingested_at timestamp).
    Used by the frontend live ticker to show real-time activity.
    Neo4j 5.x compatible — uses IS NOT NULL instead of deprecated EXISTS().
    """
    try:
        from app.neo4j_client import get_session
        with get_session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE n.ingested_at IS NOT NULL
                RETURN n.name        AS name,
                       n.ingested_at AS ts,
                       labels(n)[0]  AS label,
                       n.source      AS source
                ORDER BY n.ingested_at DESC
                LIMIT $limit
                """,
                {"limit": limit},
            )
            nodes = [
                {
                    "name":   rec["name"] or "",
                    "ts":     rec["ts"]   or "",
                    "label":  rec["label"] or "",
                    "source": rec["source"] or "",
                }
                for rec in result
            ]
        return {"nodes": nodes}
    except Exception as e:
        log.warning("[live/recent-nodes] Neo4j query failed: %s", e)
        return {"nodes": []}
