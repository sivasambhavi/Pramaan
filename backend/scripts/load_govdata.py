"""
load_govdata.py — PRAMAAN ETL Step 4: Load

MERGEs govdata-derived Impact and Evidence nodes into Neo4j.
Reads: data/resources/ontology/govdata_nodes.json

Does NOT wipe existing nodes — safe to run incrementally.
Re-running is idempotent (MERGE, not CREATE).

Usage:
    PYTHONPATH=backend venv/bin/python3 backend/scripts/load_govdata.py
"""

import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.neo4j_client import get_driver

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

_GOVDATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data" / "resources" / "ontology" / "govdata_nodes.json"
)

# Valid edge config — mirrors load_ontology.py EDGE_CONFIG
EDGE_CONFIG = {
    "OCCURRED_IN":  ("Event",   "event_id",   "Region",   "region_id"),
    "BELONGS_TO":   ("Event",   "event_id",   "Domain",   "domain_id"),
    "ALSO_IN":      ("Event",   "event_id",   "Domain",   "domain_id"),
    "MANAGED_BY":   ("Event",   "event_id",   "Actor",    "actor_id"),
    "FUNDED_BY":    ("Event",   "event_id",   "Scheme",   "scheme_id"),
    "CAUSED":       ("Event",   "event_id",   "Impact",   "impact_id"),
    "TRIGGERED":    ("Event",   "event_id",   "Policy",   "policy_id"),
    "PROVEN_BY":    ("Event",   "event_id",   "Evidence", "evidence_id"),
    "CONNECTED_TO": ("Event",   "event_id",   "Event",    "event_id"),
    "PART_OF":      ("Actor",   "actor_id",   "Actor",    "actor_id"),
}


def load_impacts(session, impacts: list):
    ok = 0
    for imp in impacts:
        session.run("""
            MERGE (n:Impact {impact_id: $impact_id})
            SET n.type        = $type,
                n.value       = $value,
                n.unit        = $unit,
                n.description = $description,
                n.source      = 'data.gov.in'
        """, {
            "impact_id":   imp["impact_id"],
            "type":        imp["type"],
            "value":       imp["value"],
            "unit":        imp.get("unit", ""),
            "description": imp.get("description", ""),
        })
        ok += 1
    logger.info("  Loaded %d Impact nodes.", ok)


def load_evidence(session, evidence: list):
    ok = 0
    for evd in evidence:
        session.run("""
            MERGE (n:Evidence {evidence_id: $evidence_id})
            SET n.type   = $type,
                n.title  = $title,
                n.source = $source,
                n.url    = $url,
                n.date   = $date
        """, {
            "evidence_id": evd["evidence_id"],
            "type":        evd.get("type", "dataset"),
            "title":       evd.get("title", ""),
            "source":      evd.get("source", "data.gov.in"),
            "url":         evd.get("url", ""),
            "date":        evd.get("date", ""),
        })
        ok += 1
    logger.info("  Loaded %d Evidence nodes.", ok)


def load_edges(session, edges: list):
    ok = skipped = 0
    for edge in edges:
        etype = edge["type"]
        cfg   = EDGE_CONFIG.get(etype)
        if not cfg:
            logger.warning("  Unknown edge type: %s — skipped.", etype)
            skipped += 1
            continue

        from_label, from_id_field, to_label, to_id_field = cfg
        result = session.run(f"""
            MATCH (a:{from_label} {{{from_id_field}: $from_id}})
            MATCH (b:{to_label}   {{{to_id_field}:  $to_id}})
            MERGE (a)-[r:{etype}]->(b)
            SET r.reason = $reason, r.source = 'data.gov.in'
            RETURN r
        """, {
            "from_id": edge["from"],
            "to_id":   edge["to"],
            "reason":  edge.get("reason", ""),
        })

        if result.single():
            ok += 1
        else:
            logger.warning("  Edge %s -[%s]-> %s: node(s) not found.",
                           edge["from"], etype, edge["to"])
            skipped += 1

    logger.info("  Edges: %d created/merged, %d skipped.", ok, skipped)


def main():
    if not _GOVDATA_FILE.exists():
        logger.error("govdata_nodes.json not found: %s", _GOVDATA_FILE)
        logger.error("Run: python3 data/scripts/transform.py")
        sys.exit(1)

    data = json.loads(_GOVDATA_FILE.read_text())
    impacts  = data.get("impacts",  [])
    evidence = data.get("evidence", [])
    edges    = data.get("edges",    [])

    logger.info("govdata_nodes.json loaded")
    logger.info("  Impacts:  %d", len(impacts))
    logger.info("  Evidence: %d", len(evidence))
    logger.info("  Edges:    %d", len(edges))

    driver = get_driver()
    with driver.session() as session:
        logger.info("\n── Loading Impact nodes ───────────────────────────")
        load_impacts(session, impacts)

        logger.info("\n── Loading Evidence nodes ─────────────────────────")
        load_evidence(session, evidence)

        logger.info("\n── Loading edges ──────────────────────────────────")
        load_edges(session, edges)

    logger.info("\nSUCCESS: govdata nodes loaded into Neo4j.")
    logger.info("Total new nodes: %d | New edges: %d",
                len(impacts) + len(evidence), len(edges))


if __name__ == "__main__":
    main()
