# PRAMAAN – Data Extraction & ETL Plan
> Last updated: March 19, 2026

## 1. Overview

PRAMAAN's seed data is mapped to a 7-table ontology:
**Regions → Schemes → Actors → Assets → Beneficiaries → Evidence → Events**

The canonical seed data lives in:
```
data/resources/data/final_formalized/
```
This is the **only** folder loaded into Neo4j by `backend/scripts/load_seed_data.py`.

> ⚠️ `data/*.csv` (root-level) are legacy files — **not loaded into Neo4j**. Do not edit them expecting graph changes.

---

## 2. Source Files & What Was Extracted

### A. Regions
| Source File | Location | What Was Extracted |
|---|---|---|
| `c16ccda1...csv` | `data/resources/` | 272 Delhi DMC wards — population, ward number, zone |
| `f1a46aa8...csv` | `data/resources/` | Sub-district names, amenity counts per ward |
| `New_colony_ward_zone_mapping.pdf` | `data/resources/` | Colony → Ward → Zone mapping |

**Output:** `final_formalized/regions.csv`
**Status:** ✅ Done — covers Ward 45 (Shahdara South) + 2 ghost wards (Ward 12, Ward 28)

---

### B. Actors
| Source File | Location | What Was Extracted |
|---|---|---|
| `sh_north_zone_duty_roaster...xlsx` | `data/resources/` | Shahdara North Zone Malis, Inspectors — name, employee ID, zone, beat |
| `beat_list_shn...xlsx` | `data/resources/` | Beat assignments for sanitation workers |
| `delhi_tenders_data.md` | `data/resources/` | Org names, no. of tenders, total value (₹ Lakhs) — **untapped, not yet seeded** |

**Output:** `final_formalized/actors.csv`, `final_formalized/actors_enriched.csv`
**Status:** ✅ Done — 6 actors (MCD Works, Sanitation, Electrical, Councillor, 2 contractors)
**Gap:** `delhi_tenders_data.md` tender orgs have NOT been seeded into Neo4j yet

---

### C. Assets
| Source File | Location | What Was Extracted |
|---|---|---|
| `watercensusmap.kml` | `data/resources/` | 897 geo-tagged water bodies with coordinates + photo URLs |
| Manual curation | — | 5 hero assets in Ward 45 (drain, road, toilet, housing, streetlight) |
| `f1a46aa8...csv` | `data/resources/` | Amenity totals (schools, roads km) — used as macro-asset placeholders |

**Output:** `final_formalized/assets.csv`
**Status:** ✅ Done — 57 total (5 hero + 51 water bodies from KML + 1 park)

---

### D. Schemes
| Source File | Location | What Was Extracted |
|---|---|---|
| `statewise_allocation.json` | `data/resources/` | AMRUT + SBM annual fund releases 2019–2024 |
| `amrut_storm_water_drainage.json` | `data/resources/` | AMRUT drainage project counts + costs |
| `pmay_housing_data.json` | `data/resources/` | State-wise PMAY housing completion data |
| Manual | — | SFC Grant 2024, Local Streetlight scheme |

**Output:** `final_formalized/schemes.csv`, `final_formalized/scheme_allocations.csv`
**Status:** ✅ Done — 8 schemes (SFC Grant, AMRUT, PMAY, SBM, PMKISAN, JJBY, AB, PMGSY)
**Gap:** PMKISAN, JJBY, AB have 0 assets/beneficiaries — chains are incomplete

---

### E. Beneficiaries
| Source File | Location | What Was Extracted |
|---|---|---|
| Manual curation | — | 5 beneficiary groups (~750 people total) tied to Ward 45 assets |
| `data/residents.csv` | `data/` | Resident phone numbers — **NOT loaded into graph** (privacy risk) |

**Output:** `final_formalized/beneficiaries.csv`
**Status:** ✅ Done — 5 groups for hero assets
**Gap:** SFC Grant, AMRUT, PMGSY, Streetlight schemes have 0 beneficiary rows

---

### F. Evidence
| Source File | Location | What Was Extracted |
|---|---|---|
| `watercensusmap.kml` | `data/resources/` | 893 photo URLs from water body nodes |
| `frontend/static/evidence/` | `frontend/` | 14 before/after geo-tagged photos for Ward 45 hero assets |

**Output:** `final_formalized/evidence.csv`
**Status:** ✅ Done — 15 pieces (before/after images + water body evidence)

---

### G. Events
| Source File | Location | What Was Extracted |
|---|---|---|
| Manual curation | — | 5 completion/inauguration events for hero assets |
| PIB RSS feed | live | `https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3` — ingested via Live Ingestion page |

**Output:** `final_formalized/events.csv`
**Status:** ✅ Done — 5 events
**Gap:** ClimateHazard, TechEvent, SocialEvent domains empty (needed for PRD global vision)

---

## 3. ETL Scripts

| Script | Location | Purpose | Status |
|---|---|---|---|
| `generate_final_datasets.py` | `data/scripts/` | Generate all 7 CSVs from raw sources | ⚠️ Has Windows paths — fix before running |
| `transform_to_7_table_schema.py` | `data/scripts/` | Transform raw data → 7-table schema | ⚠️ Has Windows paths — fix before running |
| `extract_amrut.py` | `data/scripts/` | Fetch AMRUT data from data.gov.in API | ✅ Works — needs `DATA_GOV_API_KEY` in `.env` |
| `extract_pmay.py` | `data/scripts/` | Fetch PMAY data from data.gov.in API | ✅ Works — needs `DATA_GOV_API_KEY` in `.env` |
| `generate_seed_data.py` | `data/scripts/` | Generate seed CSV from real + mocked data | ✅ Done |
| `load_seed_data.py` | `backend/scripts/` | Load `final_formalized/` CSVs → Neo4j | ✅ Works |

### Fix Windows Paths (Before Running ETL Scripts)

In `data/scripts/generate_final_datasets.py` and `data/scripts/transform_to_7_table_schema.py`, replace all hardcoded Windows paths:

```python
# ❌ Old (Windows)
BASE_DIR = r"e:\INDIA_INNOVATES\Pramaan\data\resources"

# ✅ New (cross-platform)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2] / "data" / "resources"
```

---

## 4. Planned Automation Pipeline

> See `docs/todo.md` → "Data Pipeline — Automated Scraping" section for full task list.

Target: single command fetches, transforms, and loads all data.

```
backend/scripts/auto_pipeline.py  (to be created)
    ├── Source A: data.gov.in API → data/resources/*.json
    ├── Source B: Ward Population CSV → regions.csv (272 wards)
    ├── Source C: delhi_tenders_data.md → actors.csv (tender orgs)
    ├── Source D: watercensusmap.kml → assets.csv (water bodies)
    ├── Source E: Google News RSS → evidence.csv (per-asset news)
    └── Source F: PIB RSS → events.csv
         ↓
    load_seed_data.py → Neo4j (MERGE, never wipe)
```

Scheduler: APScheduler (daily at 2am) + watchdog (file change trigger).

---

## 5. Data Quality Notes

| Issue | File | Impact |
|---|---|---|
| `sbm_toilets.json` is a pincode directory | `data/resources/` | Wrong data — no SBM endpoint served |
| `data/residents.csv` has real phone numbers | `data/` | Privacy risk — replace with mock numbers before public demo |
| Asset IDs split between `data/assets.csv` and `final_formalized/assets.csv` | Both | UI `constants.py` must use `final_formalized/` IDs only |
| 3 asset IDs in `constants.py` ASSET_EVIDENCE_PHOTOS don't exist in `final_formalized/assets.csv` | `frontend/utils/constants.py` | Evidence photos won't display |
