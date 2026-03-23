"""
validate_ontology.py — PRAMAAN ETL Step 3: Validate

Validates data/resources/ontology/govdata_nodes.json before loading into Neo4j.

Checks:
  1. Required fields on every Impact and Evidence node
  2. No duplicate IDs within govdata_nodes.json
  3. No ID collision with seed_graph.json (would cause MERGE conflicts)
  4. All edge from/to IDs exist (in seed_graph OR govdata_nodes)
  5. Value is numeric and positive for Impact nodes
  6. Edge types are valid (must be in EDGE_CONFIG from load_ontology.py)

Usage:
    python3 data/scripts/validate_ontology.py
    python3 data/scripts/validate_ontology.py --warn-only   # never exit 1
"""

import sys
import json
import argparse
from pathlib import Path

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]
_GOVDATA_FILE = _PROJECT_ROOT / "data" / "resources" / "ontology" / "govdata_nodes.json"
_SEED_FILE    = _PROJECT_ROOT / "data" / "resources" / "ontology" / "seed_graph.json"

VALID_EDGE_TYPES = {
    "OCCURRED_IN", "BELONGS_TO", "ALSO_IN", "MANAGED_BY",
    "FUNDED_BY", "CAUSED", "TRIGGERED", "PROVEN_BY",
    "CONNECTED_TO", "PART_OF",
}


class Report:
    def __init__(self):
        self.errors   = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)
        print(f"  ❌ CRITICAL  {msg}")

    def warn(self, msg):
        self.warnings.append(msg)
        print(f"  ⚠️  WARNING   {msg}")

    def ok(self, msg):
        print(f"  ✅ OK        {msg}")


def main():
    parser = argparse.ArgumentParser(description="Validate PRAMAAN govdata ontology nodes")
    parser.add_argument("--warn-only", action="store_true",
                        help="Treat errors as warnings — always exit 0")
    args = parser.parse_args()
    r = Report()

    print("=" * 60)
    print("  PRAMAAN — Validate Ontology Nodes (Step 3)")
    print("=" * 60)

    # ── Load govdata_nodes.json ────────────────────────────────────────────────
    if not _GOVDATA_FILE.exists():
        r.error(f"govdata_nodes.json not found at {_GOVDATA_FILE} — run transform.py first")
        _finish(r, args)
        return

    gd = json.loads(_GOVDATA_FILE.read_text())
    impacts  = gd.get("impacts",  [])
    evidence = gd.get("evidence", [])
    edges    = gd.get("edges",    [])
    print(f"\n  govdata_nodes.json loaded: {len(impacts)} impacts, {len(evidence)} evidence, {len(edges)} edges")

    # ── Load seed_graph.json for collision check ───────────────────────────────
    seed_ids: set[str] = set()
    if _SEED_FILE.exists():
        seed = json.loads(_SEED_FILE.read_text())
        for section in ["domains","regions","actors","schemes","policies","events","impacts","evidence"]:
            id_field = section.rstrip("s") + "_id"
            for node in seed.get(section, []):
                sid = node.get(id_field) or node.get("event_id") or node.get("domain_id")
                if sid:
                    seed_ids.add(sid)
        r.ok(f"seed_graph.json loaded — {len(seed_ids)} existing node IDs")
    else:
        r.warn("seed_graph.json not found — skipping collision check")

    # ── Check 1: Required fields on Impact nodes ───────────────────────────────
    print("\n── Impact nodes ──")
    imp_ids: set[str] = set()
    imp_errors = 0
    for i, imp in enumerate(impacts):
        iid  = imp.get("impact_id", "")
        missing = [f for f in ["impact_id", "type", "value", "unit"] if not imp.get(f)]
        if missing:
            r.error(f"Impact[{i}] {iid!r} — missing required fields: {missing}")
            imp_errors += 1
            continue

        val = imp.get("value")
        if not isinstance(val, (int, float)) or val < 0:
            r.error(f"Impact {iid} — value must be numeric and >= 0, got: {val!r}")
            imp_errors += 1

        if iid in imp_ids:
            r.error(f"Impact {iid} — duplicate ID within govdata_nodes.json")
            imp_errors += 1
        imp_ids.add(iid)

        if iid in seed_ids:
            r.error(f"Impact {iid} — ID collides with existing seed_graph node")
            imp_errors += 1

    if imp_errors == 0:
        r.ok(f"{len(impacts)} Impact nodes — all fields valid, no duplicates, no collisions")

    # ── Check 2: Required fields on Evidence nodes ─────────────────────────────
    print("\n── Evidence nodes ──")
    evd_ids: set[str] = set()
    evd_errors = 0
    for i, evd in enumerate(evidence):
        eid     = evd.get("evidence_id", "")
        missing = [f for f in ["evidence_id", "type", "title", "source"] if not evd.get(f)]
        if missing:
            r.error(f"Evidence[{i}] {eid!r} — missing required fields: {missing}")
            evd_errors += 1
            continue

        if eid in evd_ids:
            r.error(f"Evidence {eid} — duplicate ID within govdata_nodes.json")
            evd_errors += 1
        evd_ids.add(eid)

        if eid in seed_ids:
            r.error(f"Evidence {eid} — ID collides with existing seed_graph node")
            evd_errors += 1

    if evd_errors == 0:
        r.ok(f"{len(evidence)} Evidence nodes — all fields valid, no duplicates, no collisions")

    # ── Check 3: Edge validity ─────────────────────────────────────────────────
    print("\n── Edges ──")
    all_known_ids = seed_ids | imp_ids | evd_ids
    edge_errors = 0
    for i, edge in enumerate(edges):
        etype  = edge.get("type", "")
        from_  = edge.get("from", "")
        to_    = edge.get("to", "")

        if etype not in VALID_EDGE_TYPES:
            r.error(f"Edge[{i}] unknown type {etype!r}")
            edge_errors += 1

        if from_ not in all_known_ids:
            r.warn(f"Edge[{i}] from={from_!r} not found in any known node set")

        if to_ not in all_known_ids:
            r.warn(f"Edge[{i}] to={to_!r} not found in any known node set")

    if edge_errors == 0:
        r.ok(f"{len(edges)} edges — all edge types valid")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  VALIDATION SUMMARY")
    print(f"  ❌ Critical errors : {len(r.errors)}")
    print(f"  ⚠️  Warnings        : {len(r.warnings)}")
    print(f"{'='*60}")

    _finish(r, args)


def _finish(r: Report, args):
    if r.errors and not args.warn_only:
        print("\n🚫 Load BLOCKED — fix errors before running load_govdata.py\n")
        sys.exit(1)
    elif r.errors and args.warn_only:
        print("\n⚠️  Errors found but --warn-only set — proceeding\n")
    else:
        print("\n✅ All checks passed — safe to run backend/scripts/load_govdata.py\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
