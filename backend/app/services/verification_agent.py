"""
verification_agent.py — PRAMAAN Verification Agent

Responsibilities
----------------
1. **Bayesian confidence aggregation** — when a new claim about an existing
   node arrives, update the stored confidence using the Bayesian combination
   formula:  new_conf = 1 − (1 − old_conf) × (1 − incoming_conf)

2. **Conflict detection** — compare incoming entity properties against what
   is stored in Neo4j (cost ±20%, status mismatch) and flag contradictions.

3. **CONTRADICTS edge** — write a `:CONTRADICTS` relationship to the graph
   so analysts can inspect disputed claims in the proof chain.

4. **Trust-tier promotion** — automatically promote a node's `trust_tier`
   when confidence crosses a threshold.

Usage (called from ingest.py after every entity write):
    result = await VerificationAgent.verify(entity_label, entity_id, incoming, session)
    # result.action: "CREATED" | "CORROBORATED" | "CONFLICT_FLAGGED"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

log = logging.getLogger("pramaan.verification")


# ── Trust-tier thresholds ────────────────────────────────────────────────────

_TIER_MAP: list[tuple[float, str]] = [
    (0.90, "high"),
    (0.70, "medium"),
    (0.50, "low"),
    (0.00, "unverified"),
]


def _confidence_to_tier(conf: float) -> str:
    for threshold, tier in _TIER_MAP:
        if conf >= threshold:
            return tier
    return "unverified"


# ── Bayesian aggregation ─────────────────────────────────────────────────────

def _bayesian_update(old: float, new: float) -> float:
    """
    Combine two independent confidence scores using the Bayesian formula:
        combined = 1 − (1 − old) × (1 − new)
    This is equivalent to:  P(A ∪ B) = 1 − P(¬A)×P(¬B)
    Result is clamped to [0.0, 1.0].
    """
    combined = 1.0 - (1.0 - old) * (1.0 - new)
    return round(min(max(combined, 0.0), 1.0), 4)


# ── Conflict detection helpers ───────────────────────────────────────────────

def _cost_conflict(stored: Any, incoming: Any, threshold: float = 0.20) -> bool:
    """Return True if costs differ by more than *threshold* (default 20%)."""
    try:
        s, i = float(stored), float(incoming)
        if s == 0:
            return i != 0
        return abs(s - i) / s > threshold
    except (TypeError, ValueError):
        return False


def _status_conflict(stored: Any, incoming: Any) -> bool:
    """Return True if status strings are both set but differ."""
    if stored and incoming:
        return str(stored).strip().lower() != str(incoming).strip().lower()
    return False


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    action:       Literal["CREATED", "CORROBORATED", "CONFLICT_FLAGGED"]
    old_conf:     float | None
    new_conf:     float
    trust_tier:   str
    conflicts:    list[str]   # human-readable conflict descriptions


# ── Agent ────────────────────────────────────────────────────────────────────

class VerificationAgent:
    """
    Stateless agent — every method receives an open Neo4j session.
    All writes happen within the caller's transaction.
    """

    # ------------------------------------------------------------------ public

    @classmethod
    def verify(
        cls,
        label:    str,
        node_id:  str,
        incoming: dict,
        session,                 # neo4j.Session
    ) -> VerificationResult:
        """
        Main entry point.

        Parameters
        ----------
        label    : Neo4j label, e.g. "Asset", "Scheme", "Actor"
        node_id  : the node's primary key value (e.g. asset_id value)
        incoming : raw dict from the LLM / ingest payload (may have conf / cost / status)
        session  : open Neo4j driver session
        """
        id_field  = cls._id_field(label)
        stored    = cls._fetch_existing(label, id_field, node_id, session)
        in_conf   = float(incoming.get("confidence", 0.70))

        if stored is None:
            # Brand-new node — no aggregation needed, just set tier
            new_conf  = in_conf
            tier      = _confidence_to_tier(new_conf)
            cls._update_conf_and_tier(label, id_field, node_id, new_conf, tier, session)
            return VerificationResult(
                action="CREATED", old_conf=None, new_conf=new_conf,
                trust_tier=tier, conflicts=[]
            )

        old_conf = float(stored.get("confidence", 0.70))
        new_conf = _bayesian_update(old_conf, in_conf)
        tier     = _confidence_to_tier(new_conf)

        # ── Detect conflicts ─────────────────────────────────────────────
        conflicts: list[str] = []

        if _cost_conflict(stored.get("cost"), incoming.get("cost")):
            conflicts.append(
                f"cost: stored={stored.get('cost')} vs incoming={incoming.get('cost')}"
            )

        if _status_conflict(stored.get("status"), incoming.get("status")):
            conflicts.append(
                f"status: stored={stored.get('status')} vs incoming={incoming.get('status')}"
            )

        if conflicts:
            log.warning(
                "[VerificationAgent] CONFLICT on %s(%s): %s",
                label, node_id, conflicts
            )
            cls._write_contradicts_edge(
                label, id_field, node_id, incoming, conflicts, session
            )
            # Still update confidence (corroboration of identity, not values)
            cls._update_conf_and_tier(label, id_field, node_id, new_conf, tier, session)
            return VerificationResult(
                action="CONFLICT_FLAGGED", old_conf=old_conf, new_conf=new_conf,
                trust_tier=tier, conflicts=conflicts
            )

        # ── No conflict — pure corroboration ────────────────────────────
        cls._update_conf_and_tier(label, id_field, node_id, new_conf, tier, session)
        return VerificationResult(
            action="CORROBORATED", old_conf=old_conf, new_conf=new_conf,
            trust_tier=tier, conflicts=[]
        )

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _id_field(label: str) -> str:
        mapping = {
            "Asset":       "asset_id",
            "Scheme":      "scheme_id",
            "Actor":       "actor_id",
            "Region":      "region_id",
            "Beneficiary": "beneficiary_id",
            "Evidence":    "evidence_id",
            "Event":       "event_id",
        }
        return mapping.get(label, f"{label.lower()}_id")

    @staticmethod
    def _fetch_existing(label: str, id_field: str, node_id: str, session) -> dict | None:
        try:
            q = f"MATCH (n:{label} {{{id_field}: $id}}) RETURN properties(n) AS props LIMIT 1"
            rec = session.run(q, id=node_id).single()
            return dict(rec["props"]) if rec else None
        except Exception as e:
            log.warning("[VerificationAgent] Could not fetch %s(%s): %s", label, node_id, e)
            return None

    @staticmethod
    def _update_conf_and_tier(
        label: str, id_field: str, node_id: str,
        conf: float, tier: str, session
    ):
        try:
            q = (
                f"MATCH (n:{label} {{{id_field}: $id}}) "
                "SET n.confidence = $conf, n.trust_tier = $tier"
            )
            session.run(q, id=node_id, conf=conf, tier=tier)
        except Exception as e:
            log.warning("[VerificationAgent] Could not update conf/tier for %s(%s): %s", label, node_id, e)

    @staticmethod
    def _write_contradicts_edge(
        label: str, id_field: str, node_id: str,
        incoming: dict, conflicts: list[str], session
    ):
        """
        Write a :CONTRADICTS relationship from a synthetic ConflictClaim node
        to the disputed entity.  This keeps the conflict visible in the graph
        without mutating the canonical node's properties.
        """
        try:
            claim_id   = f"CLAIM_{label.upper()}_{node_id}_{int(datetime.now(timezone.utc).timestamp())}"
            source_url = incoming.get("source") or incoming.get("source_url") or "unknown"
            conflict_str = "; ".join(conflicts)

            q = f"""
                MERGE (claim:ConflictClaim {{claim_id: $claim_id}})
                SET claim.source     = $source,
                    claim.conflicts  = $conflicts,
                    claim.created_at = $ts

                WITH claim
                MATCH (node:{label} {{{id_field}: $node_id}})
                MERGE (claim)-[:CONTRADICTS {{reason: $conflicts, detected_at: $ts}}]->(node)
            """
            session.run(
                q,
                claim_id=claim_id,
                source=source_url,
                conflicts=conflict_str,
                node_id=node_id,
                ts=datetime.now(timezone.utc).isoformat(),
            )
            log.info("[VerificationAgent] CONTRADICTS edge written: %s → %s(%s)", claim_id, label, node_id)
        except Exception as e:
            log.error("[VerificationAgent] Failed to write CONTRADICTS edge: %s", e)
