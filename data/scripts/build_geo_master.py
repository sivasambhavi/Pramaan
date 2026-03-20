"""
build_geo_master.py — PRAMAAN Geo Master Builder
Reads LGD XLS files for 3 states and builds:
  data/resources/final_formalized/regions.csv — Neo4j-ready regions

Hierarchy: State → ULB (city) → Ward
Data source: lgdirectory.gov.in XLS downloads placed in data/resources/lgd/
  Required files: {state}_ulbs.xls, {state}_wards.xls

Usage:
  python3 data/scripts/build_geo_master.py
  python3 data/scripts/build_geo_master.py --geocode     # enrich lat/lon via Nominatim
  python3 data/scripts/build_geo_master.py --dry-run     # preview counts only
"""

import argparse
import time
import pandas as pd
from lxml import etree
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
LGD_DIR     = _ROOT / "data" / "resources" / "lgd"
OUT_REGIONS = _ROOT / "data" / "resources" / "final_formalized" / "regions.csv"

NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}

# ── State seeds ───────────────────────────────────────────────────────────────
STATES = [
    {"geo_id": "GEO_IN_DL", "lgd_code": "7",  "name": "Delhi",          "state_abbr": "DL", "file_prefix": "delhi",          "lat": 28.7041, "lon": 77.1025},
    {"geo_id": "GEO_IN_AP", "lgd_code": "28", "name": "Andhra Pradesh", "state_abbr": "AP", "file_prefix": "andhra_pradesh", "lat": 15.9129, "lon": 79.7400},
    {"geo_id": "GEO_IN_KA", "lgd_code": "29", "name": "Karnataka",      "state_abbr": "KA", "file_prefix": "karnataka",      "lat": 15.3173, "lon": 75.7139},
]

STATE_CODE_MAP = {s["lgd_code"]: s for s in STATES}

# ── XLS parser (SpreadsheetML) ────────────────────────────────────────────────
def parse_xls(path: Path) -> pd.DataFrame:
    """Parse LGD SpreadsheetML .xls file into a DataFrame. Skips 5 header rows."""
    tree = etree.parse(str(path))
    root = tree.getroot()
    rows = root.findall(".//ss:Row", NS)

    # Row 0-1: title/subtitle, Row 2: empty, Row 3: col headers, Row 4: (In English/Local)
    # Row 5+ : actual data
    if len(rows) < 6:
        return pd.DataFrame()

    raw_headers = [c.text or f"col_{i}" for i, c in enumerate(rows[3].findall("ss:Cell/ss:Data", NS))]
    # Deduplicate column names (LGD files have duplicate "Local Body Name" etc.)
    seen = {}
    headers = []
    for h in raw_headers:
        if h in seen:
            seen[h] += 1
            headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            headers.append(h)

    data = []
    for row in rows[5:]:
        cells = row.findall("ss:Cell/ss:Data", NS)
        vals = [c.text for c in cells]
        # Pad to header length
        while len(vals) < len(headers):
            vals.append(None)
        data.append(vals[:len(headers)])

    df = pd.DataFrame(data, columns=headers)
    # Drop fully empty rows
    df = df.dropna(how="all").reset_index(drop=True)
    return df


# ── Geocode via Nominatim ─────────────────────────────────────────────────────
def geocode(name: str, state: str) -> tuple:
    """Query Nominatim for lat/lon. Returns (lat, lon) or (None, None)."""
    try:
        import requests
        query = f"{name}, {state}, India"
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "PRAMAAN-GeoBuilder/1.0"},
            timeout=10,
        )
        results = r.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"    Geocode failed for '{name}': {e}")
    return None, None


# ── Loaders ───────────────────────────────────────────────────────────────────
def load_ulbs(state_abbr: str, file_prefix: str, state_geo_id: str, state_name: str, do_geocode: bool) -> pd.DataFrame:
    path = LGD_DIR / f"{file_prefix}_ulbs.xls"
    if not path.exists():
        print(f"  ⚠  Missing: {path.name}")
        return pd.DataFrame()

    raw = parse_xls(path)
    if raw.empty:
        return pd.DataFrame()

    rows = []
    for _, r in raw.iterrows():
        ulb_code = str(r.get("Localbody Code") or "").strip()
        ulb_name = str(r.get("Local Body Name") or "").strip()  # first occurrence = English
        if not ulb_code or not ulb_name or ulb_name == "nan":
            continue

        geo_id = f"{state_geo_id}_{ulb_code}"

        lat, lon = None, None
        if do_geocode:
            lat, lon = geocode(ulb_name, state_name)
            time.sleep(1.1)  # Nominatim rate limit: 1 req/sec

        rows.append({
            "geo_id":         geo_id,
            "level":          "city",
            "name":           ulb_name,
            "lgd_code":       ulb_code,
            "parent_geo_id":  state_geo_id,
            "lat":            lat,
            "lon":            lon,
        })

    df = pd.DataFrame(rows)
    print(f"  ✓ {state_abbr} ULBs: {len(df)} rows")
    return df


def load_wards(state_abbr: str, file_prefix: str, state_geo_id: str, ulb_geo_map: dict) -> pd.DataFrame:
    """ulb_geo_map: {lgd_ulb_code -> geo_id}"""
    path = LGD_DIR / f"{file_prefix}_wards.xls"
    if not path.exists():
        print(f"  ⚠  Missing: {path.name}")
        return pd.DataFrame()

    raw = parse_xls(path)
    if raw.empty:
        return pd.DataFrame()

    rows = []
    for _, r in raw.iterrows():
        ulb_code  = str(r.get("Local Body Code") or "").strip()
        ward_code = str(r.get("Ward Code") or "").strip()
        ward_name = str(r.get("Ward Name") or "").strip()

        if not ward_code or not ward_name or ward_name == "nan":
            continue

        parent_geo_id = ulb_geo_map.get(ulb_code, state_geo_id)
        geo_id = f"{parent_geo_id}_W{ward_code}"

        rows.append({
            "geo_id":         geo_id,
            "level":          "ward",
            "name":           ward_name,
            "lgd_code":       ward_code,
            "parent_geo_id":  parent_geo_id,
            "lat":            None,
            "lon":            None,
        })

    df = pd.DataFrame(rows)
    print(f"  ✓ {state_abbr} Wards: {len(df)} rows")
    return df


# ── Main build ────────────────────────────────────────────────────────────────
def build(do_geocode: bool = False, dry_run: bool = False):
    print("\n" + "=" * 60)
    print("  PRAMAAN — build_geo_master.py")
    print(f"  States: Delhi, Andhra Pradesh, Karnataka")
    print(f"  Geocode: {do_geocode} | Dry run: {dry_run}")
    print("=" * 60 + "\n")

    all_rows = []

    # Country root
    all_rows.append({
        "geo_id": "GEO_IN", "level": "country", "name": "India",
        "lgd_code": "1", "parent_geo_id": None, "lat": 20.5937, "lon": 78.9629,
    })

    for state in STATES:
        print(f"\n── {state['name']} (LGD: {state['lgd_code']}) ──")
        state_abbr   = state["state_abbr"]
        file_prefix  = state["file_prefix"]
        state_geo    = state["geo_id"]

        # State node
        all_rows.append({
            "geo_id":        state_geo,
            "level":         "state",
            "name":          state["name"],
            "lgd_code":      state["lgd_code"],
            "parent_geo_id": "GEO_IN",
            "lat":           state["lat"],
            "lon":           state["lon"],
        })

        # ULBs
        ulb_df = load_ulbs(state_abbr, file_prefix, state_geo, state["name"], do_geocode)
        if not ulb_df.empty:
            all_rows.extend(ulb_df.to_dict("records"))
            ulb_geo_map = dict(zip(ulb_df["lgd_code"], ulb_df["geo_id"]))
        else:
            ulb_geo_map = {}

        # Wards
        ward_df = load_wards(state_abbr, file_prefix, state_geo, ulb_geo_map)
        if not ward_df.empty:
            all_rows.extend(ward_df.to_dict("records"))

    master = pd.DataFrame(all_rows)
    master = master[["geo_id", "level", "name", "lgd_code", "parent_geo_id", "lat", "lon"]]

    print(f"\n{'─'*40}")
    print(f"  Total rows: {len(master)}")
    print(f"\n  Level breakdown:")
    print(master["level"].value_counts().to_string())

    if dry_run:
        print("\n  [DRY RUN] — No files written.")
        return

    # ── Write regions.csv (Neo4j format) ─────────────────────────────────────
    # Map geo columns to regions schema
    regions = master[master["level"].isin(["state", "city", "ward"])].copy()
    regions = regions.rename(columns={
        "geo_id":        "region_id",
        "parent_geo_id": "parent_region_id",
    })
    regions["population"] = None

    # Keep only columns load_seed_data.py expects
    regions = regions[["region_id", "name", "type" if "type" in regions.columns else "level",
                        "parent_region_id", "population", "lat", "lon"]]

    # Rename level → type
    if "level" in regions.columns and "type" not in regions.columns:
        regions = regions.rename(columns={"level": "type"})

    OUT_REGIONS.parent.mkdir(parents=True, exist_ok=True)
    regions.to_csv(OUT_REGIONS, index=False)
    print(f"  ✓ regions.csv    → {OUT_REGIONS}")
    print(f"     ({len(regions)} rows: states + ULBs + wards)")
    print("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build PRAMAAN geo master table from LGD data")
    parser.add_argument("--geocode",  action="store_true", help="Enrich ULBs with lat/lon via Nominatim")
    parser.add_argument("--dry-run",  action="store_true", help="Preview counts without writing files")
    args = parser.parse_args()
    build(do_geocode=args.geocode, dry_run=args.dry_run)
