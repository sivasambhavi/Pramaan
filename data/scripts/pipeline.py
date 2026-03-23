"""
PRAMAAN — Unified Data Pipeline
Extract → Transform → Validate → Load

Steps:
  1. fetch_govdata.py       — pull structured datasets from data.gov.in
  2. transform.py           — map raw JSONs to ontology Impact/Evidence nodes
  3. validate_ontology.py   — quality gate before Neo4j write
  4. load_govdata.py        — MERGE new nodes into Neo4j (incremental, idempotent)

Usage:
    venv/bin/python3 data/scripts/pipeline.py              # full run
    venv/bin/python3 data/scripts/pipeline.py --skip-fetch # transform onwards
    venv/bin/python3 data/scripts/pipeline.py --dry-run    # fetch + transform only, no Neo4j write
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PYTHON       = sys.executable
_SCRIPTS      = _PROJECT_ROOT / "data" / "scripts"
_BACKEND      = _PROJECT_ROOT / "backend"
_PYTHONPATH   = {**os.environ, "PYTHONPATH": str(_PROJECT_ROOT)}


def run(label: str, cmd: list) -> bool:
    print(f"\n{'='*60}")
    print(f"  STEP: {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, env=_PYTHONPATH)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {label} — pipeline aborted.")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="PRAMAAN ETL pipeline")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Skip fetch step — use existing govdata JSONs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch + transform only — do not load into Neo4j")
    args = parser.parse_args()

    steps = []

    # ── Step 1: Extract ───────────────────────────────────────────────────────
    if not args.skip_fetch:
        steps.append(("1a. Extract structured — fetch_govdata.py (data.gov.in)",
                       [_PYTHON, str(_SCRIPTS / "fetch_govdata.py")]))
        steps.append(("1b. Extract unstructured — fetch_unstructured.py (ISRO/NDMA/PIB)",
                       [_PYTHON, str(_SCRIPTS / "fetch_unstructured.py")]))

    # ── Step 2: Transform ─────────────────────────────────────────────────────
    steps.append(("2. Transform — govdata → ontology nodes",
                   [_PYTHON, str(_SCRIPTS / "transform.py")]))

    if args.dry_run:
        print("\n[dry-run] Stopping after transform — no Neo4j write.")
        for label, cmd in steps:
            if not run(label, cmd):
                sys.exit(1)
        sys.exit(0)

    # ── Step 3: Validate ──────────────────────────────────────────────────────
    steps.append(("3. Validate — ontology nodes quality gate",
                   [_PYTHON, str(_SCRIPTS / "validate_ontology.py")]))

    # ── Step 4: Load ──────────────────────────────────────────────────────────
    steps.append(("4. Load — MERGE nodes into Neo4j",
                   [_PYTHON, str(_BACKEND / "scripts" / "load_govdata.py")]))

    for label, cmd in steps:
        if not run(label, cmd):
            sys.exit(1)

    print(f"\n{'='*60}")
    print("  PIPELINE COMPLETE ✅")
    print(f"  Data from data.gov.in is now in Neo4j.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
