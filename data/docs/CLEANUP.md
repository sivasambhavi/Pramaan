# PRAMAAN — Stale File Cleanup Plan

> **Why this doc exists:** After the pipeline enhancement (Steps 1–3), several old scripts
> and data files became redundant. They must be deleted to avoid confusion about which
> scripts to run and which data is authoritative.
>
> **When to clean:** Before the next team sprint / demo prep.  
> **Who cleans:** Sreenu (data pipeline owner).

---

## Summary

| Category | Count | Action |
|---|---|---|
| Stale fetch scripts | 8 | Delete — replaced by `fetch_govdata.py` |
| One-time inspection scripts | 2 | Delete — were never part of pipeline |
| Stale transform scripts | 2 | Delete — replaced by `transform_to_7_table_schema.py` |
| Wrong-data JSON files | 3 | Delete — fetched incorrect datasets |
| Temp/test output files | 2 | Delete — scratch outputs, not canonical |
| **Total** | **17** | |

---

## Section 1 — Stale Fetch Scripts (`data/scripts/`)

All 7 individual fetch scripts below are **fully replaced** by `fetch_govdata.py` +
`govdata_registry.json`. They are identical in structure, have hardcoded API keys,
and save output to the **wrong location** (`data/scripts/` instead of `data/resources/`).

| File | Why Stale | Replaced By |
|---|---|---|
| `extract_amrut.py` | Single-dataset fetcher, saves to `data/scripts/`, hardcoded key | `fetch_govdata.py` |
| `amrut_funds.py` | Single-dataset fetcher, saves to `data/scripts/`, hardcoded key | `fetch_govdata.py` |
| `statewise_allocation.py` | Wrong UUID (fetches Ayush Mission, not AMRUT allocation) | `fetch_govdata.py` + corrected UUID in registry |
| `sbm_toilets.py` | Wrong UUID (fetches Pincode Directory, not SBM data) | `fetch_govdata.py` + corrected UUID in registry |
| `credit_guarantee_scheme.py` | Returns empty response — dataset not useful for project | `fetch_govdata.py` (dataset marked inactive in registry) |
| `extract_pmay.py` | Scrapes data.gov.in HTML to find UUID (fragile) — UUID now in registry | `fetch_govdata.py` |
| `api_test.py` | Duplicate of `extract_amrut.py`, saves to `data/scripts/output.json` | `fetch_govdata.py` |
| `amrut_water_logging.py` | Same pattern as all above — saves to `data/scripts/`, hardcoded key | Add UUID `caadd339-...` to `govdata_registry.json` instead |

**Clean-up commands:**
```bash
cd data/scripts
rm extract_amrut.py amrut_funds.py statewise_allocation.py sbm_toilets.py \
   credit_guarantee_scheme.py extract_pmay.py api_test.py amrut_water_logging.py
```

> **Before deleting `amrut_water_logging.py`:** Add its UUID (`caadd339-a9a7-47bc-adbe-671bf57ad3fe`)
> to `govdata_registry.json` as an inactive entry so it isn't lost.

---

## Section 2 — One-Time Inspection Scripts (`data/scripts/`)

These were written during initial exploration to understand raw file schemas.
They are not part of any pipeline, cannot run on Linux (hardcoded Windows paths),
and their output has already been captured in `data/docs/DATA_EXTRACTION_PLAN.md`.

| File | Purpose | Why Stale |
|---|---|---|
| `inspect_excel.py` | Printed column names of Excel files to console | One-time exploration; hardcoded `e:\Pramaan\` path; never called by pipeline |
| `analyze_data_schemas.py` | Printed schema of all raw files to `schema_analysis.json` | One-time exploration; hardcoded `e:\Pramaan\` path; output already committed to `data/resources/schema_analysis.json` |

**Clean-up commands:**
```bash
cd data/scripts
rm inspect_excel.py analyze_data_schemas.py
```

---

## Section 3 — Stale Transform Scripts (`data/scripts/`)

Both scripts below produce **incompatible ID schemas** (`WARD_45`, `id` column instead
of `region_id`) and write to the **wrong output folder** (`data/resources/data/final/`
instead of `final_formalized/`). They have also been superseded by the rewritten
`transform_to_7_table_schema.py`.

| File | Why Stale | Replaced By |
|---|---|---|
| ~~`generate_final_datasets.py`~~ | ✅ **Deleted** — Old schema (`WARD_45` IDs, `id` column), wrote to `/data/final/` (wrong folder); conflicted with canonical transform script | `transform_to_7_table_schema.py` |
| `deep_data_extraction.py` | Hardcoded Windows paths (`e:\Pramaan\`), old schema (`WARD_45`, `id` column), writes to `/data/final/`, produces proxy image evidence from Wikimedia | `transform_to_7_table_schema.py` |

> **Note on `generate_seed_data.py`:** This script generates fully mocked data with
> lowercase IDs (`asset_001`, `region_w45`) to `data/` (root level). It is **not
> referenced by any other script** and the data it writes is never loaded into Neo4j.
> It can be deleted, but if you want to keep a minimal mocked-data fallback for offline
> demos, rename it to `generate_mock_demo_data.py` to make its purpose clear.

**Clean-up commands:**
```bash
cd data/scripts
rm generate_final_datasets.py deep_data_extraction.py

# Optional (read note above before deciding):
rm generate_seed_data.py
```

---

## Section 4 — Wrong-Data JSON Files (`data/resources/`)

These JSON files contain **incorrect datasets** — the fetch scripts used wrong UUIDs.
They are not used by the transform script and keeping them risks future confusion.

| File | Contains | Expected | Action |
|---|---|---|---|
| `statewise_allocation.json` | **National Ayush Mission** fund allocation | AMRUT statewise allocation | Delete — wrong data. Re-fetch with correct UUID once found |
| `sbm_toilets.json` | **All India Pincode Directory** | SBM urban toilet construction | Delete — wrong data. Re-fetch with correct UUID once found |
| `credit_guarantee_scheme.json` | Empty response (`field: []`, no records) | Credit guarantee data | Delete — failed fetch |

**Clean-up commands:**
```bash
cd data/resources
rm statewise_allocation.json sbm_toilets.json credit_guarantee_scheme.json
```

---

## Section 5 — Temp/Test Output Files (`data/resources/`)

These files are scratch outputs from one-time runs of exploration scripts.
They are not canonical data and should not be in the repository.

| File | Created By | Why Remove |
|---|---|---|
| `output.json` | `api_test.py` (duplicate fetch run) | Scratch output, same data as `amrut_storm_water_drainage.json` |
| `schema_analysis.json` | `analyze_data_schemas.py` (one-time schema inspection) | One-time analysis artifact; content captured in `DATA_EXTRACTION_PLAN.md` |

**Clean-up commands:**
```bash
cd data/resources
rm output.json schema_analysis.json
```

---

## Section 6 — After Cleanup: Canonical Script List

Once cleanup is done, `data/scripts/` should contain only these files:

```
data/scripts/
├── govdata_registry.json        ← UUID registry for all data.gov.in datasets
├── fetch_govdata.py             ← STEP 1: Fetch raw JSONs from data.gov.in API
├── transform_to_7_table_schema.py ← STEP 2: Normalize to 7-table canonical schema
├── validate.py                  ← STEP 3: Quality gate before Neo4j load
└── (auto_pipeline.py)           ← STEP 0: Orchestrator [to be built]
```

And `data/resources/` should contain only:

```
data/resources/
├── amrut_storm_water_drainage.json  ← fetched by fetch_govdata.py ✅
├── pmay_housing_data.json           ← fetched by fetch_govdata.py ✅
├── amrut_funds.json                 ← fetched by fetch_govdata.py (pending verify)
├── c16ccda1-...csv                  ← ward population (static, keep)
├── delhi_tenders_data.md            ← tender data (static, keep)
├── watercensusmap.kml               ← water bodies (static, keep)
├── sh_north_zone_...xlsx            ← mali roster (static, keep)
└── data/final_formalized/           ← OUTPUT of transform step (7 canonical CSVs)
```

---

## Cleanup Checklist

```
[ ] Add amrut_water_logging UUID to govdata_registry.json before deleting script
[ ] Delete 8 stale fetch scripts (Section 1)
[ ] Delete 2 inspection scripts (Section 2)
[ ] Delete 2 stale transform scripts (Section 3)
[ ] Decide on generate_seed_data.py — delete or rename (Section 3 note)
[ ] Delete 3 wrong-data JSON files (Section 4)
[ ] Delete 2 temp output files (Section 5)
[ ] Run: python3 data/scripts/validate.py  — confirm 0 critical errors after cleanup
[ ] git add -A && git commit -m "chore: cleanup stale scripts and wrong-data files"
```
