# 🗺️ GEO MASTER TABLE — Implementation Plan
## Master Geographic Hierarchy for PRAMAAN

> **Purpose:** A single authoritative table that maps every geographic entity
> (Country → State → District → Sub-district → ULB → Zone → Ward → Street)
> used by all PRAMAAN pipelines, Neo4j nodes, and the Geo Resolution Agent.

---

## 1. Why This Is Needed (Problem Statement)

### Current `regions.csv` is critically broken:

| Issue | Current State | Required |
|---|---|---|
| Missing hierarchy levels | Only `city, zone, ward, street` | `country → state → district → ulb → zone → ward` |
| All 217 wards → same parent | All → `REG_SHAHDARA_SOUTH` (wrong) | Each ward → its correct zone/district |
| No State / Country nodes | Not present | `India → Delhi → East Delhi District → ...` |
| No official LGD codes | Not present | Each node must carry `lgd_code` for cross-system linking |
| No population / area | Not present | Required for delivery score calculations |

### Why the Agent is Needed:

Government data (news, PIB, CSVs, API responses) refers to locations in **dozens of
inconsistent formats**:

```
"Shahdara"          → Which ward? Zone? District?
"North Delhi"       → District or zone?
"Ward 45"           → 45 of which ULB?
"East Delhi MC"     → same as "EDMC"?
"Ward No. - 45"     → same as "Ward 45"?
```

A **Geo Resolution Agent** takes any fuzzy geographic string and returns the
canonical `geo_id` + confidence score, enabling all pipelines to link data
to the correct graph node.

---

## 2. Solution Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                            │
│  LGD Portal          data.gov.in         Census 2011       │
│  (lgdirectory.gov.in)  (geo datasets)   (boundaries)       │
└──────────────┬─────────────┬────────────────┬─────────────┘
               │             │                │
               ▼             ▼                ▼
┌────────────────────────────────────────────────────────────┐
│              build_geo_master.py  (Phase 2)                │
│  Downloads → Parses → Deduplicates → Assigns geo_ids       │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│         data/resources/geo_master.csv  (Master Table)      │
│  ~500 rows for Delhi  |  ~500K rows for all India          │
│  geo_id, level, name, lgd_code, parent_geo_id, lat, lon    │
└──────┬──────────────────────────────────────┬──────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────────┐              ┌───────────────────────────┐
│ transform_to_    │              │  geo_resolution_agent.py  │
│ 7_table_schema.py│              │  (Phase 3)                │
│                  │              │                           │
│ regions.csv now  │              │  Input:  "Shahdara Delhi" │
│ derives from     │              │  Output: GEO_IN_DL_EE_SHD │
│ geo_master.csv   │              │          confidence: 0.94 │
└──────────────────┘              └───────────────────────────┘
       │
       ▼
┌──────────────────┐
│  Neo4j           │
│  Region nodes    │
│  with lgd_code   │
└──────────────────┘
```

---

## 3. Master Table Schema (`geo_master.csv`)

```
Column          | Type    | Example                        | Notes
────────────────|─────────|────────────────────────────────|──────────────────────────────
geo_id          | string  | GEO_IN_DL_EE_MCD_W045          | Internal ID — never changes
level           | enum    | ward                           | country/state/district/
                |         |                                | subdistrict/ulb/zone/ward/street
name            | string  | Ward No. 45 — Shahdara         | Official name
local_name      | string  | Shahdara Ward 45               | Common/alternate names (CSV)
lgd_code        | string  | 803045                         | Official LGD code (key for linking)
census_code     | string  | 07NE0045                       | Census 2011 entity code
parent_geo_id   | string  | GEO_IN_DL_EE_MCD               | Parent entity's geo_id
state_code      | string  | DL                             | ISO state abbreviation
district_code   | string  | DL_EAST                        | Internal district code
ulb_code        | string  | MCD_SHAHDARA                   | Urban Local Body code
pincode         | string  | 110032                         | Comma-separated if multiple
lat             | float   | 28.6748                        | Centroid latitude
lon             | float   | 77.2921                        | Centroid longitude
population      | int     | 18432                          | Census 2011 population
area_sqkm       | float   | 1.2                            | Area in sq km
is_active       | bool    | True                           | False if merged/renamed
notes           | string  | Merged with Ward 47 in 2022    | For renamed/split wards
```

### geo_id Convention

```
GEO_{country}_{state}_{district}_{ulb}_{ward}

Examples:
  GEO_IN                          → India (country)
  GEO_IN_DL                       → Delhi (state/UT)
  GEO_IN_DL_EE                    → East Delhi (district)
  GEO_IN_DL_EE_MCD                → MCD Shahdara South (ULB)
  GEO_IN_DL_EE_MCD_Z_SHD_S       → Shahdara South Zone
  GEO_IN_DL_EE_MCD_W045          → Ward 45 (ward)
  GEO_IN_DL_EE_MCD_W045_GALI7    → Gali No. 7 (street)
```

---

## 4. Data Sources

### Source 1 — LGD (Local Government Directory) ⭐ Primary

- **URL:** https://lgdirectory.gov.in/
- **Data:** All States, Districts, Sub-districts, ULBs, Wards, GPs, Villages
- **Format:** Downloadable CSV (no API key needed, publicly available)
- **Coverage:** 100% of India
- **Update frequency:** Quarterly

**Download steps:**
```
1. Go to: https://lgdirectory.gov.in/
2. Click "Download" in top menu
3. Select entity type: State / District / Urban Local Body / Ward
4. Download CSV
```

**LGD Ward CSV columns (urban):**
```
State Code | State Name | District Code | District Name |
Sub Dist Code | Sub Dist Name | ULB Code | ULB Name |
Ward Code | Ward Name | Census Code | Population
```

### Source 2 — data.gov.in Geo Datasets

| Dataset | UUID | Entity |
|---|---|---|
| Delhi Ward Boundaries | `c16ccda1-eb93-40d9-8f78-b2f0327fcaca` | Ward → population |
| LGD State Master | To be found | State codes |
| LGD District Master | To be found | District codes |
| Census 2011 Urban Frames | To be found | ULB boundaries |

**Add these to `govdata_registry.json`** with `maps_to_entity: "geo_master"`.

### Source 3 — Bhuvan (ISRO) — For Geo-coordinates

- **URL:** https://bhuvan.nrsc.gov.in/
- **Data:** Administrative boundary shapefiles with centroids
- **Use:** Populate `lat`, `lon` for each geo entity

---

## 5. Phase 1 — Fix Delhi Regions NOW (Immediate Priority)

**Script:** `data/scripts/fix_delhi_regions.py`

**What it does:**
- Adds missing hierarchy nodes: `India → Delhi → East Delhi → MCD → Shahdara South → Ward`
- Corrects `parent_region_id` for each ward based on its actual zone
- Adds `lgd_code` column to `regions.csv`
- Writes updated `regions.csv` to `final_formalized/`

### Delhi Hierarchy (Correct Structure)

```
India (GEO_IN)
  └── Delhi / NCT of Delhi (GEO_IN_DL) [state]
        ├── North Delhi District (GEO_IN_DL_ND) [district]
        │     └── North Delhi Municipal Corp (GEO_IN_DL_ND_NDMC) [ulb]
        │           ├── Civil Lines Zone (GEO_IN_DL_ND_NDMC_Z_CL) [zone]
        │           ├── Rohini Zone (GEO_IN_DL_ND_NDMC_Z_RH) [zone]
        │           └── ...12 zones → wards
        ├── East Delhi District (GEO_IN_DL_EE) [district]
        │     └── East Delhi Municipal Corp (GEO_IN_DL_EE_EDMC) [ulb]
        │           └── Shahdara South Zone (GEO_IN_DL_EE_EDMC_Z_SS) [zone]  ← Our demo zone
        │                 ├── Ward 45 (GEO_IN_DL_EE_EDMC_W045) [ward]
        │                 └── ... (Wards 40–69 approx.)
        ├── South Delhi District (GEO_IN_DL_SD) [district]
        └── New Delhi District (GEO_IN_DL_NDIST) [district]
```

### Script Skeleton: `fix_delhi_regions.py`

```python
"""
fix_delhi_regions.py — PRAMAAN Phase 1 Geo Fix
Builds the correct Delhi geo hierarchy and writes an updated regions.csv.
Run ONCE to fix the flat/broken regions.csv.
Output: data/resources/data/final_formalized/regions.csv
"""
import pandas as pd
from pathlib import Path

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]
OUTPUT_DIR    = _PROJECT_ROOT / "data" / "resources" / "data" / "final_formalized"

# ─── 1. Seed the static hierarchy (Country → State → District → Zone) ─────────
HIERARCHY = [
    # geo_id                        level       name                              lgd_code  parent_geo_id              lat       lon
    ("GEO_IN",                      "country",  "India",                          "1",      None,                      20.5937,  78.9629),
    ("GEO_IN_DL",                   "state",    "Delhi",                          "7",      "GEO_IN",                  28.7041,  77.1025),
    ("GEO_IN_DL_EE",                "district", "East Delhi",                     "707",    "GEO_IN_DL",               28.6692,  77.2980),
    ("GEO_IN_DL_EE_EDMC",           "ulb",      "East Delhi Municipal Corp",      "803",    "GEO_IN_DL_EE",            28.6692,  77.2980),
    ("GEO_IN_DL_EE_EDMC_Z_SN",      "zone",     "Shahdara North Zone",            "803N",   "GEO_IN_DL_EE_EDMC",       28.6900,  77.2950),
    ("GEO_IN_DL_EE_EDMC_Z_SS",      "zone",     "Shahdara South Zone",            "803S",   "GEO_IN_DL_EE_EDMC",       28.6700,  77.2900),
    # Add more districts/zones as LGD data is downloaded
]

# ─── 2. Load existing wards from census CSV ────────────────────────────────────
# Ward → Zone mapping (based on MCD ward list — Wards 40–69 are Shahdara South)
# Source: MCD Delhi Ward List (LGD portal)
WARD_ZONE_MAP = {
    range(1,  21):  "GEO_IN_DL_EE_EDMC_Z_SN",   # Shahdara North: Wards 1–20  (approx)
    range(21, 70):  "GEO_IN_DL_EE_EDMC_Z_SS",   # Shahdara South: Wards 21–69 (approx — Ward 45 is here)
    # TODO: Fill in remaining zones from LGD download
}

def get_zone_for_ward(ward_num: int) -> str:
    for ward_range, zone_id in WARD_ZONE_MAP.items():
        if ward_num in ward_range:
            return zone_id
    return "GEO_IN_DL_EE_EDMC"   # fallback: attach to ULB

def build_regions():
    rows = []

    # Add hierarchy nodes
    for geo_id, level, name, lgd_code, parent, lat, lon in HIERARCHY:
        rows.append({
            "region_id":        geo_id,         # keep region_id = geo_id for now
            "name":             name,
            "type":             level,
            "parent_region_id": parent,
            "lgd_code":         lgd_code,
            "lat":              lat,
            "lon":              lon,
        })

    # Load ward data from census CSV
    census_path = _PROJECT_ROOT / "data" / "resources" / "c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv"
    df = pd.read_csv(census_path).drop_duplicates(subset=["Ward"])

    for _, row in df.iterrows():
        ward_str  = str(row["Ward"])
        match     = __import__("re").search(r"\d+", ward_str)
        ward_num  = int(match.group()) if match else 0
        geo_id    = f"GEO_IN_DL_EE_EDMC_W{ward_num:03d}"
        parent_id = get_zone_for_ward(ward_num)

        rows.append({
            "region_id":        geo_id,
            "name":             ward_str,
            "type":             "ward",
            "parent_region_id": parent_id,
            "lgd_code":         f"803{ward_num:03d}",   # approximate — replace with real LGD codes
            "lat":              float(row.get("Latitude", 28.6748)),
            "lon":              float(row.get("Longitude", 77.2921)),
        })

    df_out = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "regions.csv"
    df_out.to_csv(out_path, index=False)
    print(f"✅ regions.csv updated — {len(df_out)} rows → {out_path}")
    print(f"   Hierarchy nodes : {len(HIERARCHY)}")
    print(f"   Ward nodes      : {len(df_out) - len(HIERARCHY)}")

if __name__ == "__main__":
    build_regions()
```

**Run order:**
```bash
python3 data/scripts/fix_delhi_regions.py
python3 data/scripts/validate.py          # confirm no broken FKs
python3 backend/scripts/load_seed_data.py # reload Neo4j
```

---

## 6. Phase 2 — `build_geo_master.py` (Full India, All States)

**Script:** `data/scripts/build_geo_master.py`

**What it does:**
1. Reads LGD CSV downloads (State, District, ULB, Ward level files)
2. Reads Census 2011 population data from data.gov.in
3. Reads ward centroid coordinates from Bhuvan shapefiles (or uses geo-coded CSV)
4. Merges all sources into a single `geo_master.csv`
5. Generates canonical `geo_id` for every entity

### Input Files Expected

```
data/resources/lgd/
  ├── lgd_states.csv          ← Download from lgdirectory.gov.in
  ├── lgd_districts.csv       ← Download from lgdirectory.gov.in
  ├── lgd_ulbs.csv            ← Download from lgdirectory.gov.in (Urban LBs)
  ├── lgd_wards.csv           ← Download from lgdirectory.gov.in (Urban Wards)
  ├── lgd_gp.csv              ← Download from lgdirectory.gov.in (Gram Panchayats)
  └── lgd_villages.csv        ← Download from lgdirectory.gov.in (Villages)

data/resources/census/
  ├── census_2011_towns.csv   ← Census 2011 Urban Frame Survey
  └── census_2011_pop.csv     ← Census 2011 population by ward
```

### Script Skeleton: `build_geo_master.py`

```python
"""
build_geo_master.py — PRAMAAN Phase 2: Build Master Geo Table
Reads LGD CSV downloads and Census data to produce geo_master.csv.

Run AFTER downloading LGD files to data/resources/lgd/
Output: data/resources/geo_master.csv

Usage:
  python3 data/scripts/build_geo_master.py              # All states
  python3 data/scripts/build_geo_master.py --state DL  # Delhi only
  python3 data/scripts/build_geo_master.py --dry-run   # Show stats only
"""
import pandas as pd
import argparse
from pathlib import Path

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]
LGD_DIR       = _PROJECT_ROOT / "data" / "resources" / "lgd"
CENSUS_DIR    = _PROJECT_ROOT / "data" / "resources" / "census"
OUTPUT_PATH   = _PROJECT_ROOT / "data" / "resources" / "geo_master.csv"

# ─── Canonical geo_id generator ───────────────────────────────────────────────
def make_geo_id(level: str, state_code: str = "", district_code: str = "",
                ulb_code: str = "", ward_code: str = "") -> str:
    parts = ["GEO", "IN"]
    if state_code:    parts.append(state_code.upper())
    if district_code: parts.append(district_code.upper())
    if ulb_code:      parts.append(ulb_code.upper())
    if ward_code:     parts.append(f"W{ward_code.zfill(4)}")
    return "_".join(parts)

# ─── Loaders ──────────────────────────────────────────────────────────────────
def load_lgd_states() -> pd.DataFrame:
    path = LGD_DIR / "lgd_states.csv"
    if not path.exists():
        print(f"  ⚠️  Missing: {path} — download from lgdirectory.gov.in")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # LGD columns: State Code | State Name (In English) | Census Code | ...
    df["geo_id"]     = df["State Code"].apply(lambda c: make_geo_id("state", state_code=str(c)))
    df["level"]      = "state"
    df["parent_geo_id"] = "GEO_IN"
    return df[["geo_id", "level", "State Name (In English)", "State Code", "Census Code", "parent_geo_id"]] \
             .rename(columns={"State Name (In English)": "name", "State Code": "lgd_code", "Census Code": "census_code"})

def load_lgd_districts(state_filter: str = None) -> pd.DataFrame:
    path = LGD_DIR / "lgd_districts.csv"
    if not path.exists():
        print(f"  ⚠️  Missing: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    if state_filter:
        df = df[df["State Code"].astype(str) == state_filter]
    df["geo_id"]        = df.apply(lambda r: make_geo_id("district", state_code=str(r["State Code"]),
                                                          district_code=str(r["District Code"])), axis=1)
    df["level"]         = "district"
    df["parent_geo_id"] = df["State Code"].apply(lambda c: make_geo_id("state", state_code=str(c)))
    return df[["geo_id", "level", "District Name (In English)", "District Code", "Census Code", "parent_geo_id"]] \
             .rename(columns={"District Name (In English)": "name", "District Code": "lgd_code", "Census Code": "census_code"})

def load_lgd_ulbs(state_filter: str = None) -> pd.DataFrame:
    path = LGD_DIR / "lgd_ulbs.csv"
    if not path.exists():
        print(f"  ⚠️  Missing: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    if state_filter:
        df = df[df["State Code"].astype(str) == state_filter]
    df["geo_id"]        = df.apply(lambda r: make_geo_id("ulb", state_code=str(r["State Code"]),
                                                          district_code=str(r["District Code"]),
                                                          ulb_code=str(r["ULB Code"])), axis=1)
    df["level"]         = "ulb"
    df["parent_geo_id"] = df.apply(lambda r: make_geo_id("district", state_code=str(r["State Code"]),
                                                          district_code=str(r["District Code"])), axis=1)
    return df[["geo_id", "level", "ULB Name (In English)", "ULB Code", "Census Code", "parent_geo_id"]] \
             .rename(columns={"ULB Name (In English)": "name", "ULB Code": "lgd_code", "Census Code": "census_code"})

def load_lgd_wards(state_filter: str = None) -> pd.DataFrame:
    path = LGD_DIR / "lgd_wards.csv"
    if not path.exists():
        print(f"  ⚠️  Missing: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    if state_filter:
        df = df[df["State Code"].astype(str) == state_filter]
    df["geo_id"]        = df.apply(lambda r: make_geo_id("ward", state_code=str(r["State Code"]),
                                                          district_code=str(r["District Code"]),
                                                          ulb_code=str(r["ULB Code"]),
                                                          ward_code=str(r["Ward Code"])), axis=1)
    df["level"]         = "ward"
    df["parent_geo_id"] = df.apply(lambda r: make_geo_id("ulb", state_code=str(r["State Code"]),
                                                          district_code=str(r["District Code"]),
                                                          ulb_code=str(r["ULB Code"])), axis=1)
    return df[["geo_id", "level", "Ward Name (In English)", "Ward Code", "parent_geo_id"]] \
             .rename(columns={"Ward Name (In English)": "name", "Ward Code": "lgd_code"})

# ─── Main ─────────────────────────────────────────────────────────────────────
def build(state_filter: str = None, dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"  PRAMAAN — build_geo_master.py")
    print(f"  Filter: {state_filter or 'All India'} | Dry run: {dry_run}")
    print(f"{'='*60}\n")

    # Country root
    root = pd.DataFrame([{
        "geo_id": "GEO_IN", "level": "country", "name": "India",
        "lgd_code": "1", "census_code": "1", "parent_geo_id": None,
        "lat": 20.5937, "lon": 78.9629, "population": 1210854977,
        "area_sqkm": 3287263.0, "is_active": True
    }])

    dfs = [root]
    for loader in [load_lgd_states, load_lgd_districts, load_lgd_ulbs, load_lgd_wards]:
        try:
            df = loader(state_filter) if loader != load_lgd_states else loader()
            if not df.empty:
                dfs.append(df)
                print(f"  ✅ Loaded {loader.__name__}: {len(df)} rows")
        except Exception as e:
            print(f"  ❌ Error in {loader.__name__}: {e}")

    master = pd.concat(dfs, ignore_index=True)

    # Ensure required columns exist
    for col in ["lat", "lon", "population", "area_sqkm", "is_active", "local_name", "pincode", "notes"]:
        if col not in master.columns:
            master[col] = None
    master["is_active"] = master["is_active"].fillna(True)

    print(f"\n  Total rows: {len(master)}")
    print(f"  Level breakdown:\n{master['level'].value_counts().to_string()}")

    if dry_run:
        print("\n  [DRY RUN] — No file written.")
        return

    master.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Written → {OUTPUT_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state",    type=str, help="State LGD code to filter (e.g. '7' for Delhi)")
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()
    build(state_filter=args.state, dry_run=args.dry_run)
```

---

## 7. Phase 3 — `geo_resolution_agent.py` (The Intelligent Layer)

**Script:** `data/scripts/geo_resolution_agent.py`

**Purpose:** Takes any fuzzy geographic string from unstructured text and maps it
to the canonical `geo_id` in `geo_master.csv`.

### Input / Output Contract

```python
# Input
resolve("Shahdara, Delhi")

# Output
{
  "input":       "Shahdara, Delhi",
  "geo_id":      "GEO_IN_DL_EE_EDMC_Z_SS",
  "name":        "Shahdara South Zone",
  "level":       "zone",
  "confidence":  0.94,
  "method":      "fuzzy_match",      # exact / fuzzy_match / llm_assist / manual
  "alternatives": [
    {"geo_id": "GEO_IN_DL_EE_EDMC_Z_SN", "name": "Shahdara North Zone", "score": 0.81}
  ]
}
```

### Resolution Strategy (3 Layers)

```
Layer 1: Exact match
  → Normalize input (lowercase, strip punctuation)
  → Check exact match against geo_master.name + local_name
  → Return if match found (confidence: 1.0)

Layer 2: Fuzzy match (RapidFuzz)
  → Token-sort ratio match against all names in geo_master
  → Return top match if score > 0.80 (confidence = score/100)
  → Filter by level if context clues present ("ward", "district", "zone")

Layer 3: LLM assist (Groq — only when layers 1+2 fail)
  → Prompt: "Which geo_id from this list best matches '{input}'?"
  → Provide top-5 fuzzy candidates as context
  → LLM selects the best match with reasoning
  → confidence: 0.70 (LLM-assisted, needs human review)
```

### Script Skeleton: `geo_resolution_agent.py`

```python
"""
geo_resolution_agent.py — PRAMAAN Geo Resolution Agent

Resolves any fuzzy geographic string to a canonical geo_id from geo_master.csv.
Uses 3-layer strategy: Exact → Fuzzy (RapidFuzz) → LLM (Groq).

Usage:
  from data.scripts.geo_resolution_agent import GeoResolutionAgent
  agent = GeoResolutionAgent()
  result = agent.resolve("Shahdara, Delhi")
  print(result["geo_id"], result["confidence"])

  # Batch resolve
  results = agent.resolve_batch(["Ward 45 Delhi", "North Delhi", "Rohini sector 3"])
"""
import pandas as pd
import json
import os
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_SCRIPT_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT   = _SCRIPT_DIR.parents[1]
GEO_MASTER_PATH = _PROJECT_ROOT / "data" / "resources" / "geo_master.csv"

# ─── Normalization ─────────────────────────────────────────────────────────────
def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[,.\-\/()]+", " ", text)         # remove punctuation
    text = re.sub(r"\b(no|number|ward|zone|dist|district|sector|block)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ─── Level hint extractor ──────────────────────────────────────────────────────
def _extract_level_hint(text: str) -> Optional[str]:
    t = text.lower()
    if "ward"     in t: return "ward"
    if "zone"     in t: return "zone"
    if "district" in t or "dist" in t: return "district"
    if "state"    in t: return "state"
    if "village"  in t: return "village"
    return None

# ─── Main Agent Class ──────────────────────────────────────────────────────────
class GeoResolutionAgent:

    def __init__(self, geo_master_path: Path = GEO_MASTER_PATH):
        if not geo_master_path.exists():
            raise FileNotFoundError(
                f"geo_master.csv not found at {geo_master_path}. "
                f"Run build_geo_master.py first."
            )
        self.master = pd.read_csv(geo_master_path).fillna("")
        self._build_index()
        print(f"✅ GeoResolutionAgent loaded — {len(self.master)} geo entities")

    def _build_index(self):
        """Build a normalized name → row lookup for fast exact matching."""
        self._index = {}
        for _, row in self.master.iterrows():
            key = _normalize(row["name"])
            self._index[key] = row
            # Also index local_name aliases
            for alias in str(row.get("local_name", "")).split(","):
                alias_key = _normalize(alias)
                if alias_key:
                    self._index[alias_key] = row

    def _exact_match(self, normalized: str, level_hint: str) -> Optional[dict]:
        row = self._index.get(normalized)
        if row is not None:
            if level_hint and row["level"] != level_hint:
                return None   # level mismatch — don't force wrong level
            return {
                "geo_id":       row["geo_id"],
                "name":         row["name"],
                "level":        row["level"],
                "confidence":   1.0,
                "method":       "exact",
                "alternatives": []
            }
        return None

    def _fuzzy_match(self, normalized: str, level_hint: str) -> Optional[dict]:
        try:
            from rapidfuzz import process, fuzz
        except ImportError:
            print("  ⚠️  rapidfuzz not installed — pip install rapidfuzz")
            return None

        candidates = self.master
        if level_hint:
            candidates = candidates[candidates["level"] == level_hint]
            if candidates.empty:
                candidates = self.master   # fallback to all if filtered too aggressively

        names = candidates["name"].tolist()
        results = process.extract(normalized, names, scorer=fuzz.token_sort_ratio, limit=5)

        if not results or results[0][1] < 60:
            return None

        top_name, top_score, top_idx = results[0]
        top_row = candidates.iloc[top_idx]

        alternatives = []
        for alt_name, alt_score, alt_idx in results[1:]:
            alt_row = candidates.iloc[alt_idx]
            alternatives.append({
                "geo_id": alt_row["geo_id"],
                "name":   alt_name,
                "score":  round(alt_score / 100, 2)
            })

        return {
            "geo_id":       top_row["geo_id"],
            "name":         top_row["name"],
            "level":        top_row["level"],
            "confidence":   round(top_score / 100, 2),
            "method":       "fuzzy_match",
            "alternatives": alternatives
        }

    def _llm_assist(self, original_input: str, candidates: list) -> Optional[dict]:
        """Use Groq LLM to pick best match from fuzzy candidates when score is low."""
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            return None

        try:
            from groq import Groq
            client = Groq(api_key=groq_key)

            candidate_str = "\n".join(
                [f"  {i+1}. geo_id={c['geo_id']} | name={c['name']} | level={c['level']}"
                 for i, c in enumerate(candidates)]
            )
            prompt = f"""You are a geographic resolver for Indian government data.
Given the input location: "{original_input}"
Select the best matching entry from this list:
{candidate_str}

Reply with ONLY a JSON object like:
{{"choice": 1, "reason": "...", "confidence": 0.85}}
"""
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            result_json = json.loads(resp.choices[0].message.content)
            choice_idx  = result_json.get("choice", 1) - 1
            chosen      = candidates[min(choice_idx, len(candidates)-1)]
            return {
                "geo_id":       chosen["geo_id"],
                "name":         chosen["name"],
                "level":        chosen["level"],
                "confidence":   float(result_json.get("confidence", 0.70)),
                "method":       "llm_assist",
                "alternatives": [c for c in candidates if c["geo_id"] != chosen["geo_id"]]
            }
        except Exception as e:
            print(f"  ⚠️  LLM assist failed: {e}")
            return None

    def resolve(self, location_str: str) -> dict:
        """Resolve a geographic string to a canonical geo_id."""
        normalized   = _normalize(location_str)
        level_hint   = _extract_level_hint(location_str)

        # Layer 1: Exact
        result = self._exact_match(normalized, level_hint)
        if result:
            return {"input": location_str, **result}

        # Layer 2: Fuzzy
        result = self._fuzzy_match(normalized, level_hint)
        if result and result["confidence"] >= 0.80:
            return {"input": location_str, **result}

        # Layer 3: LLM assist (only when fuzzy confidence is low)
        fuzzy_candidates = result["alternatives"] if result else []
        if result:
            fuzzy_candidates = [{"geo_id": result["geo_id"], "name": result["name"],
                                  "level": result["level"]}] + result["alternatives"]
        if fuzzy_candidates:
            llm_result = self._llm_assist(location_str, fuzzy_candidates)
            if llm_result:
                return {"input": location_str, **llm_result}

        # Unresolved
        return {
            "input":        location_str,
            "geo_id":       None,
            "name":         None,
            "level":        None,
            "confidence":   0.0,
            "method":       "unresolved",
            "alternatives": fuzzy_candidates
        }

    def resolve_batch(self, locations: list) -> list:
        return [self.resolve(loc) for loc in locations]


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Resolve geographic strings to geo_id")
    parser.add_argument("location", nargs="+", help="Geographic string(s) to resolve")
    args = parser.parse_args()

    agent = GeoResolutionAgent()
    for loc in args.location:
        result = agent.resolve(loc)
        print(f"\n  Input      : {result['input']}")
        print(f"  geo_id     : {result['geo_id']}")
        print(f"  Name       : {result['name']}")
        print(f"  Level      : {result['level']}")
        print(f"  Confidence : {result['confidence']}")
        print(f"  Method     : {result['method']}")
```

---

## 8. Integration Map

### How `geo_master.csv` connects to everything

```
transform_to_7_table_schema.py
  → READS geo_master.csv
  → Uses geo_id as region_id in regions.csv
  → Validates all region_id FKs against geo_master

fetch_govdata.py
  → After fetching a JSON, calls GeoResolutionAgent
  → Resolves "Delhi" / "Shahdara" in API records → geo_id

backend/app/routers/scrape.py (Live Ingestion)
  → After LLM extracts location field from news article
  → Calls GeoResolutionAgent.resolve(location)
  → Stores canonical geo_id in Neo4j node

backend/scripts/load_seed_data.py
  → Loads geo_master.csv as Region nodes into Neo4j
  → Stores lgd_code as node property (for external linking)

frontend/pages/01_Ward_Map.py
  → Queries Neo4j Region nodes
  → All wards now have correct lat/lon from geo_master
  → Map is accurate instead of Delhi-centroid fallback
```

### Neo4j Node Update

```cypher
// Add lgd_code property to existing Region nodes
MATCH (r:Region)
SET r.lgd_code = r.lgd_code   // loaded from geo_master.csv
RETURN count(r) AS updated_regions
```

---

## 9. `govdata_registry.json` Updates Needed

Add these datasets for geo data (add to `data/scripts/govdata_registry.json`):

```json
{
  "name": "lgd_delhi_wards",
  "uuid": "FIND_UUID_ON_DATA_GOV_IN",
  "title": "LGD Delhi Ward Boundaries with Centroids",
  "source_url": "https://data.gov.in/search?title=LGD+ward+Delhi",
  "output_file": "lgd_delhi_wards.json",
  "maps_to_entity": "geo_master (ward level)",
  "active": false,
  "notes": "Alternative to LGD portal CSV download. Find UUID on data.gov.in."
},
{
  "name": "census_2011_delhi_population",
  "uuid": "FIND_UUID_ON_DATA_GOV_IN",
  "title": "Census 2011 Delhi Ward-level Population",
  "source_url": "https://data.gov.in/search?title=census+2011+delhi+ward",
  "output_file": "census_2011_delhi_pop.json",
  "maps_to_entity": "geo_master (population field)",
  "active": false,
  "notes": "For populating geo_master.population field."
}
```

---

## 10. Execution Order (Full Pipeline)

```bash
# ── PHASE 1: Fix Delhi immediately ─────────────────────────────
python3 data/scripts/fix_delhi_regions.py          # Fix regions.csv
python3 data/scripts/validate.py                   # Confirm no broken FKs
python3 backend/scripts/load_seed_data.py          # Reload Neo4j

# ── PHASE 2: Download LGD data (manual step) ───────────────────
# Go to lgdirectory.gov.in → Download → save CSVs to data/resources/lgd/

# ── PHASE 2: Build geo_master ──────────────────────────────────
python3 data/scripts/build_geo_master.py --state 7  # Delhi only first
python3 data/scripts/validate.py                    # Validate again
python3 backend/scripts/load_seed_data.py           # Reload

python3 data/scripts/build_geo_master.py            # Full India
# Note: Full India geo_master.csv will be ~500K rows
# Store in data/resources/ but DO NOT load all into Neo4j
# Neo4j should only contain regions referenced by actual assets

# ── PHASE 3: Test Geo Resolution Agent ─────────────────────────
pip install rapidfuzz                               # Required dependency
python3 data/scripts/geo_resolution_agent.py "Shahdara Delhi"
python3 data/scripts/geo_resolution_agent.py "Ward 45" "North Delhi" "Rohini"
```

---

## 11. Files Created by This Plan

```
data/
├── resources/
│   ├── geo_master.csv              ← NEW: Master geo-hierarchy table
│   └── lgd/                        ← NEW: LGD raw CSV downloads
│       ├── lgd_states.csv
│       ├── lgd_districts.csv
│       ├── lgd_ulbs.csv
│       └── lgd_wards.csv
└── scripts/
    ├── fix_delhi_regions.py         ← NEW (Phase 1): Fix Delhi regions.csv
    ├── build_geo_master.py          ← NEW (Phase 2): Build master table
    └── geo_resolution_agent.py      ← NEW (Phase 3): Fuzzy + LLM resolver
```

---

## 12. Dependencies to Add to `requirements.txt`

```
rapidfuzz>=3.0.0     # Fuzzy string matching (fast, pure Python)
```

---

## 13. Priority Summary

| Phase | Script | Time Estimate | Priority |
|---|---|---|---|
| Phase 1 | `fix_delhi_regions.py` | 2 hours | 🔴 Critical — Fix now |
| Phase 2 (Delhi) | `build_geo_master.py --state 7` | 4 hours | 🟡 Important |
| Phase 3 | `geo_resolution_agent.py` | 6 hours | 🟡 Important |
| Phase 2 (All India) | `build_geo_master.py` (full) | 1 day | 🟢 Vision |

> **Start with Phase 1.** The current broken `regions.csv` means all Neo4j
> Region→Ward→Asset traversal paths are wrong. Fix this before any other work.
