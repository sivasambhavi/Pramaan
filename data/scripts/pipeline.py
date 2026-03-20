"""
PRAMAAN — Unified Data Pipeline
Runs all steps in order: fetch → transform → validate → load → cleanup

Usage:
    ./venv/bin/python3 data/scripts/pipeline.py              # full run
    ./venv/bin/python3 data/scripts/pipeline.py --skip-fetch # transform onwards
    ./venv/bin/python3 data/scripts/pipeline.py --dry-run    # fetch only, no Neo4j write
"""

import sys
import argparse
import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PYTHON       = sys.executable


def run(label: str, cmd: list[str], env: dict = None) -> bool:
    import os
    full_env = {**os.environ, **(env or {})}
    print(f"\n{'='*60}")
    print(f"  STEP: {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, env=full_env)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {label} — pipeline aborted.")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="PRAMAAN unified data pipeline")
    parser.add_argument("--skip-fetch",  action="store_true", help="Skip fetch steps (use existing structured/ files)")
    parser.add_argument("--dry-run",     action="store_true", help="Fetch only — do not write to Neo4j")
    args = parser.parse_args()

    scripts    = _PROJECT_ROOT / "data" / "scripts"
    backend    = _PROJECT_ROOT / "backend"
    pythonpath = {"PYTHONPATH": str(backend)}

    steps = []

    # ── Step 1: Fetch all data sources ───────────────────────────────────────
    if not args.skip_fetch:
        steps.append(("1a. Fetch govdata (data.gov.in)",
                       [_PYTHON, str(scripts / "fetch_govdata.py")]))
        steps.append(("1b. Fetch external (census, opencity.in)",
                       [_PYTHON, str(scripts / "fetch_external.py")]))
        steps.append(("1b-semi. Parse semi-structured (KML + xlsx + md)",
                       [_PYTHON, str(scripts / "fetch_semi_structured.py")]))
        steps.append(("1c. Extract unstructured (PDFs + docs → AI)",
                       [_PYTHON, str(scripts / "fetch_unstructured.py")]))

    if args.dry_run:
        print("\n[dry-run] Fetch only — stopping before transform/load.")
        for label, cmd in steps:
            if not run(label, cmd):
                sys.exit(1)
        sys.exit(0)

    # ── Step 2: Transform all sources → 7-table schema ───────────────────────
    steps.append(("2. Transform → final_formalized/",
                   [_PYTHON, str(scripts / "transform_to_7_table_schema.py")]))

    # ── Step 3: Validate staging CSVs ────────────────────────────────────────
    steps.append(("3. Validate staging CSVs",
                   [_PYTHON, str(scripts / "validate.py")]))

    # ── Step 4: Load into Neo4j (validates every row, cleans up CSVs) ────────
    steps.append(("4. Load into Neo4j",
                   [_PYTHON, str(_PROJECT_ROOT / "backend" / "scripts" / "load_seed_data.py")],
                   pythonpath))

    for item in steps:
        label, cmd = item[0], item[1]
        env = item[2] if len(item) > 2 else None
        if not run(label, cmd, env):
            sys.exit(1)

    print(f"\n{'='*60}")
    print("  PIPELINE COMPLETE ✅")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
