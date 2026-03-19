"""
fetch_govdata.py — PRAMAAN unified data.gov.in API fetcher.

Reads dataset registry from govdata_registry.json, fetches all active
datasets from the data.gov.in API, and saves raw JSON to data/resources/.

Usage:
    python3 data/scripts/fetch_govdata.py              # fetch all active datasets
    python3 data/scripts/fetch_govdata.py --dry-run    # print what would be fetched, no API calls
    python3 data/scripts/fetch_govdata.py --name amrut_storm_water_drainage  # fetch one dataset

Requires:
    DATA_GOV_API_KEY in .env file at project root (or as environment variable)
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]                          # Pramaan/
_RESOURCES_DIR = _PROJECT_ROOT / "data" / "resources"           # where JSONs land
_REGISTRY_FILE = _PROJECT_ROOT / "data" / "config" / "govdata_registry.json"  # UUID registry

# ── Load .env manually (no python-dotenv dependency needed) ───────────────────
def _load_env():
    env_path = _PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

_load_env()

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL   = "https://api.data.gov.in/resource"
API_KEY        = os.getenv("DATA_GOV_API_KEY", "")
FETCH_LIMIT    = 200       # max records per request (data.gov.in max is 100 per page)
REQUEST_TIMEOUT = 30       # seconds
RETRY_COUNT    = 2         # retries on network error
RETRY_DELAY    = 3         # seconds between retries


# ── Core fetch function ────────────────────────────────────────────────────────
def fetch_dataset(dataset: dict, dry_run: bool = False) -> dict:
    """
    Fetch one dataset from data.gov.in and save it to data/resources/.

    Returns a result dict:
      { "name": ..., "status": "ok"|"skipped"|"error", "records": N, "file": path, "message": ... }
    """
    name        = dataset["name"]
    uuid        = dataset["uuid"]
    output_file = dataset["output_file"]
    active      = dataset.get("active", False)
    output_path = _RESOURCES_DIR / output_file

    # ── Skip inactive datasets ─────────────────────────────────────────────
    if not active:
        reason = dataset.get("notes", "marked inactive in registry")
        print(f"  ⏭  SKIP  {name}  —  {reason}")
        return {"name": name, "status": "skipped", "records": 0, "file": None, "message": reason}

    if "REPLACE_WITH" in uuid:
        print(f"  ⚠️  SKIP  {name}  —  UUID not set yet")
        return {"name": name, "status": "skipped", "records": 0, "file": None, "message": "UUID placeholder not replaced"}

    if dry_run:
        url = f"{API_BASE_URL}/{uuid}?api-key=***&format=json&limit={FETCH_LIMIT}"
        print(f"  🔍 DRY   {name}  →  {url}")
        print(f"           would save to: {output_path}")
        return {"name": name, "status": "dry_run", "records": 0, "file": str(output_path), "message": "dry run"}

    # ── Build request ──────────────────────────────────────────────────────
    url    = f"{API_BASE_URL}/{uuid}"
    params = {"api-key": API_KEY, "format": "json", "limit": FETCH_LIMIT}

    print(f"  ⬇  FETCH {name}  …")

    # ── Retry loop ─────────────────────────────────────────────────────────
    last_error = None
    for attempt in range(1, RETRY_COUNT + 2):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt <= RETRY_COUNT:
                print(f"     ↻  attempt {attempt} failed, retrying in {RETRY_DELAY}s …")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ❌ ERROR {name}  —  {last_error}")
                return {"name": name, "status": "error", "records": 0, "file": None, "message": last_error}

    # ── Validate response ──────────────────────────────────────────────────
    if data.get("status") == "error":
        msg = data.get("message", "API returned error status")
        print(f"  ❌ ERROR {name}  —  {msg}")
        return {"name": name, "status": "error", "records": 0, "file": None, "message": msg}

    records = data.get("records", [])
    if not records:
        print(f"  ⚠️  EMPTY {name}  —  API returned 0 records")
        return {"name": name, "status": "error", "records": 0, "file": None, "message": "empty records"}

    # ── Cross-check: verify index_name matches our UUID ───────────────────
    returned_uuid = data.get("index_name", "")
    if returned_uuid and returned_uuid != uuid:
        print(f"  ⚠️  UUID MISMATCH {name}: registry={uuid}, response={returned_uuid}")
        # still save it — but warn

    # ── Add fetch metadata to the JSON ────────────────────────────────────
    data["_pramaan_fetched_at"] = datetime.utcnow().isoformat() + "Z"
    data["_pramaan_dataset_name"] = name

    # ── Save to data/resources/ ────────────────────────────────────────────
    _RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  ✅ OK    {name}  —  {len(records)} records  →  {output_path.name}")
    return {"name": name, "status": "ok", "records": len(records), "file": str(output_path), "message": ""}


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fetch data.gov.in datasets for PRAMAAN")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be fetched without making API calls")
    parser.add_argument("--name", type=str, default=None, help="Fetch only one dataset by name")
    args = parser.parse_args()

    # ── Load registry ──────────────────────────────────────────────────────
    if not _REGISTRY_FILE.exists():
        print(f"ERROR: Registry not found at {_REGISTRY_FILE}")
        sys.exit(1)

    registry = json.loads(_REGISTRY_FILE.read_text())
    datasets  = registry.get("datasets", [])

    # ── Validate API key ───────────────────────────────────────────────────
    if not args.dry_run:
        if not API_KEY:
            print("ERROR: DATA_GOV_API_KEY not set.")
            print("  Add it to your .env file:  DATA_GOV_API_KEY=your_key_here")
            print("  Get a key at: https://data.gov.in/user/register")
            sys.exit(1)
        print(f"API key loaded  ({'*' * 8}{API_KEY[-4:]})\n")

    # ── Filter by --name if provided ───────────────────────────────────────
    if args.name:
        datasets = [d for d in datasets if d["name"] == args.name]
        if not datasets:
            print(f"ERROR: Dataset '{args.name}' not found in registry.")
            print(f"Available names: {[d['name'] for d in registry['datasets']]}")
            sys.exit(1)

    # ── Run fetches ────────────────────────────────────────────────────────
    mode = "DRY RUN" if args.dry_run else "LIVE FETCH"
    print(f"{'='*60}")
    print(f"  PRAMAAN govdata fetcher  [{mode}]")
    print(f"  Registry: {len(datasets)} datasets  |  Target: {_RESOURCES_DIR}")
    print(f"{'='*60}\n")

    results = []
    for dataset in datasets:
        result = fetch_dataset(dataset, dry_run=args.dry_run)
        results.append(result)

    # ── Summary ────────────────────────────────────────────────────────────
    ok      = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors  = [r for r in results if r["status"] == "error"]

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  ✅ Fetched : {len(ok)}  datasets")
    print(f"  ⏭  Skipped : {len(skipped)}  datasets  (inactive/wrong UUID)")
    print(f"  ❌ Failed  : {len(errors)}  datasets")
    if errors:
        for r in errors:
            print(f"     - {r['name']}: {r['message']}")
    print(f"{'='*60}")

    if ok and not args.dry_run:
        print(f"\n✅ Next step: run transform_to_7_table_schema.py to convert JSONs → final_formalized CSVs")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
