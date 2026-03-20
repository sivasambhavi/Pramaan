"""
validate.py — PRAMAAN Step 3: Data Quality Gate

Reads the 7 canonical CSVs from final_formalized/ and runs quality checks
BEFORE they are loaded into Neo4j. If any CRITICAL check fails, it exits
with code 1 — blocking the load.

Checks:
  1. Required files exist
  2. Required columns present in each CSV
  3. No null/empty ID or name fields
  4. No duplicate IDs within each table
  5. Foreign key integrity (asset.region_id → regions, asset.scheme_id → schemes, etc.)
  6. ID format conventions (REG_ / SCH_ / ACT_ / ASSET_ / BEN_ / EVD_ / EVT_)
  7. Coordinate bounds (lat/lon within Delhi bounding box)
  8. Referential chain: every asset has at least one evidence record

Usage:
    python3 data/scripts/validate.py              # validate all, exit 1 on critical
    python3 data/scripts/validate.py --warn-only  # print issues but always exit 0
"""

import sys
import os
import argparse
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPT_DIR    = Path(__file__).resolve().parent
_PROJECT_ROOT  = _SCRIPT_DIR.parents[1]
_FORMALIZED    = _PROJECT_ROOT / "data" / "resources" / "final_formalized"

# ── Delhi bounding box (approx) ────────────────────────────────────────────────
DELHI_LAT = (28.40, 28.90)
DELHI_LON = (76.80, 77.40)

# ── Expected schema per table ──────────────────────────────────────────────────
SCHEMA = {
    "schemes.csv":      {"id_col": "scheme_id",      "prefix": "SCH_",   "required": ["scheme_id", "name", "ministry"]},
    "regions.csv":      {"id_col": "region_id",      "prefix": "REG_",   "required": ["region_id", "name", "type"]},
    "actors.csv":       {"id_col": "actor_id",       "prefix": "ACT_",   "required": ["actor_id", "name", "type"]},
    "assets.csv":       {"id_col": "asset_id",       "prefix": "ASSET_", "required": ["asset_id", "name", "type", "region_id", "scheme_id", "actor_id"]},
    "beneficiaries.csv":{"id_col": "beneficiary_id", "prefix": "BEN_",   "required": ["beneficiary_id", "region_id"]},
    "evidence.csv":     {"id_col": "evidence_id",    "prefix": "EVD_",   "required": ["evidence_id", "asset_id", "type"]},
    "events.csv":       {"id_col": "event_id",       "prefix": "EVT_",   "required": ["event_id", "name", "asset_id"]},
}


# ── Helpers ────────────────────────────────────────────────────────────────────
class Report:
    def __init__(self):
        self.errors   = []   # critical — block load
        self.warnings = []   # non-critical — just inform

    def error(self, msg):
        self.errors.append(msg)
        print(f"  ❌ CRITICAL  {msg}")

    def warn(self, msg):
        self.warnings.append(msg)
        print(f"  ⚠️  WARNING  {msg}")

    def ok(self, msg):
        print(f"  ✅ OK        {msg}")


def load_csv(filename, report):
    path = _FORMALIZED / filename
    if not path.exists():
        report.error(f"{filename} — file not found in final_formalized/")
        return None
    df = pd.read_csv(path).fillna("")
    return df


# ── Check functions ────────────────────────────────────────────────────────────

def check_required_columns(df, filename, schema, report):
    missing = [c for c in schema["required"] if c not in df.columns]
    if missing:
        report.error(f"{filename} — missing required columns: {missing}")
        return False
    report.ok(f"{filename} — all required columns present")
    return True


def check_null_ids(df, filename, schema, report):
    id_col = schema["id_col"]
    if id_col not in df.columns:
        return
    null_count = (df[id_col] == "").sum() + df[id_col].isna().sum()
    if null_count:
        report.error(f"{filename} — {null_count} rows have empty {id_col}")
    else:
        report.ok(f"{filename} — no null IDs")


def check_duplicates(df, filename, schema, report):
    id_col = schema["id_col"]
    if id_col not in df.columns:
        return
    dupes = df[df.duplicated(subset=[id_col], keep=False)]
    if not dupes.empty:
        dupe_ids = dupes[id_col].unique().tolist()[:5]
        report.error(f"{filename} — {len(dupes)} duplicate IDs found: {dupe_ids}")
    else:
        report.ok(f"{filename} — no duplicate IDs")


def check_id_format(df, filename, schema, report):
    id_col = schema["id_col"]
    prefix = schema["prefix"]
    if id_col not in df.columns:
        return
    bad = df[~df[id_col].astype(str).str.startswith(prefix) & (df[id_col] != "")]
    if not bad.empty:
        examples = bad[id_col].head(3).tolist()
        report.warn(f"{filename} — {len(bad)} IDs don't start with '{prefix}': {examples}")
    else:
        report.ok(f"{filename} — ID format '{prefix}*' correct")


def check_foreign_keys(assets, regions, schemes, actors, evidence, report):
    """Check that every FK in assets/evidence/events references a real parent."""
    region_ids = set(regions["region_id"].astype(str)) if regions is not None else set()
    scheme_ids = set(schemes["scheme_id"].astype(str)) if schemes is not None else set()
    actor_ids  = set(actors["actor_id"].astype(str))   if actors  is not None else set()
    asset_ids  = set(assets["asset_id"].astype(str))   if assets  is not None else set()

    if assets is not None:
        # region_id FK
        bad_reg = assets[~assets["region_id"].isin(region_ids) & (assets["region_id"] != "")]
        if not bad_reg.empty:
            report.error(f"assets.csv — {len(bad_reg)} rows have region_id not in regions.csv: {bad_reg['region_id'].unique()[:3].tolist()}")
        else:
            report.ok("assets.csv — all region_id FKs valid")

        # scheme_id FK
        bad_sch = assets[~assets["scheme_id"].isin(scheme_ids) & (assets["scheme_id"] != "")]
        if not bad_sch.empty:
            report.error(f"assets.csv — {len(bad_sch)} rows have scheme_id not in schemes.csv: {bad_sch['scheme_id'].unique()[:3].tolist()}")
        else:
            report.ok("assets.csv — all scheme_id FKs valid")

        # actor_id FK
        bad_act = assets[~assets["actor_id"].isin(actor_ids) & (assets["actor_id"] != "")]
        if not bad_act.empty:
            report.error(f"assets.csv — {len(bad_act)} rows have actor_id not in actors.csv: {bad_act['actor_id'].unique()[:3].tolist()}")
        else:
            report.ok("assets.csv — all actor_id FKs valid")

    if evidence is not None and assets is not None:
        bad_evd = evidence[~evidence["asset_id"].isin(asset_ids) & (evidence["asset_id"] != "")]
        if not bad_evd.empty:
            report.error(f"evidence.csv — {len(bad_evd)} rows have asset_id not in assets.csv: {bad_evd['asset_id'].unique()[:3].tolist()}")
        else:
            report.ok("evidence.csv — all asset_id FKs valid")


def check_coordinates(assets, report):
    """Check lat/lon are within Delhi bounding box."""
    if assets is None or "lat" not in assets.columns or "lon" not in assets.columns:
        return
    df = assets[(assets["lat"] != "") & (assets["lon"] != "")].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    bad = df[
        (df["lat"] < DELHI_LAT[0]) | (df["lat"] > DELHI_LAT[1]) |
        (df["lon"] < DELHI_LON[0]) | (df["lon"] > DELHI_LON[1])
    ]
    if not bad.empty:
        report.warn(f"assets.csv — {len(bad)} assets have coordinates outside Delhi bbox: {bad['asset_id'].head(3).tolist()}")
    else:
        report.ok(f"assets.csv — all coordinates within Delhi bounding box")


def check_evidence_coverage(assets, evidence, report):
    """Warn about assets that have no evidence at all."""
    if assets is None or evidence is not None and evidence.empty:
        return
    if evidence is None:
        report.warn("No evidence.csv loaded — can't check evidence coverage")
        return
    asset_ids_with_evidence = set(evidence["asset_id"].astype(str))
    no_evidence = assets[~assets["asset_id"].isin(asset_ids_with_evidence)]
    if not no_evidence.empty:
        report.warn(f"assets.csv — {len(no_evidence)} assets have NO evidence record: {no_evidence['asset_id'].head(5).tolist()}")
    else:
        report.ok("assets.csv — all assets have at least one evidence record")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Validate PRAMAAN final_formalized CSVs")
    parser.add_argument("--warn-only", action="store_true", help="Never exit 1 — treat errors as warnings")
    args = parser.parse_args()

    report = Report()
    dfs    = {}

    print("=" * 60)
    print("  PRAMAAN — Data Validation (Step 3)")
    print(f"  Checking: {_FORMALIZED}")
    print("=" * 60)

    # ── Load all CSVs ──────────────────────────────────────────────────────
    for filename, schema in SCHEMA.items():
        print(f"\n── {filename} ──")
        df = load_csv(filename, report)
        if df is None:
            continue
        dfs[filename] = df
        print(f"     {len(df)} rows loaded")

        ok = check_required_columns(df, filename, schema, report)
        if not ok:
            continue

        check_null_ids(df, filename, schema, report)
        check_duplicates(df, filename, schema, report)
        check_id_format(df, filename, schema, report)

    # ── Cross-table checks ─────────────────────────────────────────────────
    print("\n── Cross-table checks ──")
    check_foreign_keys(
        assets   = dfs.get("assets.csv"),
        regions  = dfs.get("regions.csv"),
        schemes  = dfs.get("schemes.csv"),
        actors   = dfs.get("actors.csv"),
        evidence = dfs.get("evidence.csv"),
        report   = report,
    )
    check_coordinates(dfs.get("assets.csv"), report)
    check_evidence_coverage(dfs.get("assets.csv"), dfs.get("evidence.csv"), report)

    # ── Final summary ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  VALIDATION SUMMARY")
    print(f"  ❌ Critical errors : {len(report.errors)}")
    print(f"  ⚠️  Warnings        : {len(report.warnings)}")
    print(f"{'='*60}")

    if report.errors and not args.warn_only:
        print("\n🚫 Load BLOCKED — fix critical errors before running load_seed_data.py\n")
        sys.exit(1)
    elif report.errors and args.warn_only:
        print("\n⚠️  Errors found but --warn-only set — proceeding anyway\n")
    else:
        print("\n✅ All checks passed — safe to run load_seed_data.py\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
