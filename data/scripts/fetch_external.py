"""
fetch_external.py — PRAMAAN external dataset fetcher.

Reads dataset registry from external_registry.json, fetches all active
datasets from CKAN APIs (opencity.in) or direct CSV downloads,
and saves raw JSON to data/resources/.

Follows the same pattern as fetch_govdata.py.

Usage:
    python3 data/scripts/fetch_external.py              # fetch all active datasets
    python3 data/scripts/fetch_external.py --dry-run    # print what would be fetched
    python3 data/scripts/fetch_external.py --name delhi_ward_population_2011

Requires:
    No API key needed for opencity.in (open data)
"""

import os
import sys
import json
import time
import csv
import io
import argparse
import requests
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPT_DIR    = Path(__file__).resolve().parent
_PROJECT_ROOT  = _SCRIPT_DIR.parents[1]
_RESOURCES_DIR = _PROJECT_ROOT / "data" / "resources" / "structured" / "external"
_REGISTRY_FILE = _PROJECT_ROOT / "data" / "config" / "external_registry.json"

# ── Config ────────────────────────────────────────────────────────────────────
FETCH_LIMIT     = 500
REQUEST_TIMEOUT = 30
RETRY_COUNT     = 2
RETRY_DELAY     = 3


# ── CKAN fetch (opencity.in datastore_search API) ─────────────────────────────
def _fetch_ckan(dataset: dict) -> list[dict]:
    """
    Fetch records from a CKAN datastore_search endpoint.
    Falls back to direct CSV download if resource_id is placeholder.
    """
    resource_id  = dataset.get("resource_id", "")
    ckan_base    = dataset.get("ckan_base_url", "")
    download_url = dataset.get("download_url", "")

    # ── Try CKAN datastore_search API first ───────────────────────────────
    if resource_id and "REPLACE_WITH" not in resource_id and ckan_base:
        url    = ckan_base
        params = {"resource_id": resource_id, "limit": FETCH_LIMIT}
        resp   = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if data.get("success"):
            records = data.get("result", {}).get("records", [])
            if records:
                return records

    # ── Fallback: direct CSV download ─────────────────────────────────────
    if download_url:
        resp = requests.get(download_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        reader  = csv.DictReader(io.StringIO(resp.text))
        records = [row for row in reader]
        if records:
            return records

    return []


# ── Core fetch function ────────────────────────────────────────────────────────
def fetch_dataset(dataset: dict, dry_run: bool = False) -> dict:
    """
    Fetch one external dataset and save it to data/resources/.

    Returns a result dict:
      { "name": ..., "status": "ok"|"skipped"|"error", "records": N, "file": path, "message": ... }
    """
    name        = dataset["name"]
    fmt         = dataset.get("format", "ckan_csv")
    output_file = dataset["output_file"]
    active      = dataset.get("active", False)
    output_path = _RESOURCES_DIR / output_file

    # ── Skip inactive datasets ─────────────────────────────────────────────
    if not active:
        reason = dataset.get("notes", "marked inactive in registry")
        print(f"  ⏭  SKIP  {name}  —  {reason}")
        return {"name": name, "status": "skipped", "records": 0, "file": None, "message": reason}

    resource_id = dataset.get("resource_id", "")
    if "REPLACE_WITH" in resource_id:
        print(f"  ⚠️  SKIP  {name}  —  resource_id not set yet")
        return {"name": name, "status": "skipped", "records": 0, "file": None, "message": "resource_id placeholder not replaced"}

    if dry_run:
        ckan_url = dataset.get("ckan_base_url", "")
        fallback = dataset.get("download_url", "")
        print(f"  🔍 DRY   {name}  →  {ckan_url or fallback}")
        print(f"           would save to: {output_path}")
        return {"name": name, "status": "dry_run", "records": 0, "file": str(output_path), "message": "dry run"}

    print(f"  ⬇  FETCH {name}  …")

    # ── Retry loop ─────────────────────────────────────────────────────────
    last_error = None
    records    = []
    for attempt in range(1, RETRY_COUNT + 2):
        try:
            if fmt in ("ckan_csv", "ckan_json"):
                records = _fetch_ckan(dataset)
            else:
                # Direct JSON download
                url  = dataset.get("download_url", "")
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                records = resp.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt <= RETRY_COUNT:
                print(f"     ↻  attempt {attempt} failed, retrying in {RETRY_DELAY}s …")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ❌ ERROR {name}  —  {last_error}")
                return {"name": name, "status": "error", "records": 0, "file": None, "message": last_error}

    if not records:
        print(f"  ⚠️  EMPTY {name}  —  0 records returned")
        return {"name": name, "status": "error", "records": 0, "file": None, "message": "empty records"}

    # ── Wrap in envelope matching data.gov.in format ───────────────────────
    output = {
        "records": records,
        "_pramaan_fetched_at":    datetime.utcnow().isoformat() + "Z",
        "_pramaan_dataset_name":  name,
        "_pramaan_source":        dataset.get("source", "external"),
        "_pramaan_record_count":  len(records),
    }

    # ── Save to data/resources/ ────────────────────────────────────────────
    _RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"  ✅ OK    {name}  —  {len(records)} records  →  {output_path.name}")
    return {"name": name, "status": "ok", "records": len(records), "file": str(output_path), "message": ""}


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fetch external datasets for PRAMAAN")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be fetched without making API calls")
    parser.add_argument("--name", type=str, default=None, help="Fetch only one dataset by name")
    args = parser.parse_args()

    if not _REGISTRY_FILE.exists():
        print(f"ERROR: Registry not found at {_REGISTRY_FILE}")
        sys.exit(1)

    registry = json.loads(_REGISTRY_FILE.read_text())
    datasets  = registry.get("datasets", [])

    if args.name:
        datasets = [d for d in datasets if d["name"] == args.name]
        if not datasets:
            print(f"ERROR: Dataset '{args.name}' not found in registry.")
            print(f"Available names: {[d['name'] for d in registry['datasets']]}")
            sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "LIVE FETCH"
    print(f"{'='*60}")
    print(f"  PRAMAAN external fetcher  [{mode}]")
    print(f"  Registry: {len(datasets)} datasets  |  Target: {_RESOURCES_DIR}")
    print(f"{'='*60}\n")

    results = []
    for dataset in datasets:
        result = fetch_dataset(dataset, dry_run=args.dry_run)
        results.append(result)

    ok      = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors  = [r for r in results if r["status"] == "error"]

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  ✅ Fetched : {len(ok)}  datasets")
    print(f"  ⏭  Skipped : {len(skipped)}  datasets  (inactive/wrong resource_id)")
    print(f"  ❌ Failed  : {len(errors)}  datasets")
    if errors:
        for r in errors:
            print(f"     - {r['name']}: {r['message']}")
    print(f"{'='*60}")

    if ok and not args.dry_run:
        print(f"\n✅ Next step: run transform_to_7_table_schema.py to merge into final_formalized CSVs")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
