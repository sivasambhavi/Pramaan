# PRAMAAN — Stale File Cleanup Plan

> **Why this doc exists:** After the pipeline enhancement (Steps 1–3), several old scripts
> and data files became redundant. They must be deleted to avoid confusion about which
> scripts to run and which data is authoritative.
>
> **When to clean:** Before the next team sprint / demo prep.
> **Who cleans:** Sreenu (data pipeline owner).
> **Last reviewed:** Mar 19, 2026

---

## Summary

| Category | Count | Action |
|---|---|---|
| Stale fetch scripts | 8 | Delete — replaced by `fetch_govdata.py` + `fetch_external.py` |
| One-time inspection scripts | 2 | Delete — were never part of pipeline |
| Stale transform scripts | 1 | Delete — replaced by `transform_to_7_table_schema.py` (`generate_final_datasets.py` already deleted) |
| Wrong-data JSON files | 3 | Delete — fetched incorrect datasets |
| Temp/test output files | 3 | Delete — scratch outputs, not canonical |
| Stale PDF/CSV resources | 8 | Delete — reference docs, not pipeline inputs |
| **Total** | **25** | |

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

> ✅ **UUID from `amrut_water_logging.py` (`caadd339-a9a7-47bc-adbe-671bf57ad3fe`) already added
> to `govdata_registry.json` as inactive entry `amrut_waterlogging_eliminated` — Mar 19.**

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
rm deep_data_extraction.py generate_seed_data.py
# generate_final_datasets.py already deleted ✅
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

## Section 6 — Stale PDF/CSV Resources (`data/resources/`)

These files are reference documents or old pipeline inputs that are no longer needed.
The pipeline now fetches everything via `fetch_govdata.py` + `fetch_external.py`.

**Delete:**

| File | Why Remove |
|---|---|
| `4,48,955 Houses Constructed Under PMAY (URBAN)...pdf` | Reference PDF — data now in `pmay_housing_data.json` |
| `New_colony_ward_zone_mapping (1).pdf` | Duplicate of ward zone mapping PDF |
| `New_colony_ward_zone_mapping.pdf` | Zone mapping — now handled via `CONTAINS` hierarchy in Neo4j |
| `RS_Session_255_AS_240.csv` | Parliamentary session data — not used in pipeline |
| `agricultureandruraldevelopment.pdf` | Out of scope — Pramaan focuses on urban governance |
| `amrut.mohua.gov.in_approvedProjects_state.pdf` | Data now in `amrut_storm_water_drainage.json` |
| `climate-delhi.pdf` | Reference only — not loaded into pipeline |
| `delhipovertyline.pdf` | Not used in pipeline |
| `electricity.csv` | Not referenced by transform script |
| `f1a46aa8-123b-41f9-b267-31da999081ba.csv` | Unknown origin — not referenced anywhere |
| `general_account_income_and_expenditure_budget_2024-2025...pdf` | Budget PDF — not loaded into pipeline |
| `housingandurbandevelopment.pdf` | Reference PDF — superseded by API data |
| `watersupplyandsewarage.pdf` | Reference PDF — not in pipeline |
| `c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv` | Old ward CSV — superseded by `delhi_ward_population_2011.json` |
| `c16ccda1-eb93-40d9-8f78-b2f0327fcaca.csv` | Duplicate of above |

**Clean-up commands:**
```bash
cd data/resources
rm "4,48,955 Houses Constructed Under PMAY (URBAN) with Rs 6,654.35 crore Central Assistance.pdf"
rm "New_colony_ward_zone_mapping (1).pdf" "New_colony_ward_zone_mapping.pdf"
rm RS_Session_255_AS_240.csv
rm agricultureandruraldevelopment.pdf
rm amrut.mohua.gov.in_approvedProjects_state.pdf
rm climate-delhi.pdf delhipovertyline.pdf
rm electricity.csv
rm f1a46aa8-123b-41f9-b267-31da999081ba.csv
rm "general_account_income_and_expenditure_budget_2024-2025_and_revised_budget_estimates_2024-2025_a.pdf"
rm housingandurbandevelopment.pdf watersupplyandsewarage.pdf
rm "c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv" "c16ccda1-eb93-40d9-8f78-b2f0327fcaca.csv"
```

**Keep:**
| File | Reason |
|---|---|
| `amrut_funds.json`, `amrut_statewise_allocation.json`, `amrut_storm_water_drainage.json` | Fetched by `fetch_govdata.py` ✅ |
| `ayushman_bharat_cards.json`, `pmay_housing_data.json`, `pm_svanidhi_beneficiaries.json` | Fetched by `fetch_govdata.py` ✅ |
| `sbm_toilets_2122.json`, `sbm_toilets_comprehensive.json` | Fetched by `fetch_govdata.py` ✅ |
| `delhi_ward_population_2011.json` | Fetched by `fetch_external.py` ✅ |
| `delhi_tenders_data.md` | Used by transform script (actor extraction) ✅ |
| `watercensusmap.kml` | Used by transform script (water body assets) ✅ |
| `sh_north_zone_duty_roaster_of_mali_2512011212291229.xlsx` | Mali roster reference ✅ |
| `beat_list_shn_2511141026251125.xlsx` | Beat list reference ✅ |
| `b4219512-7105-4227-9c95-9bdf64020799.kml` | Alternate KML — verify before deleting |

---

## Section 7 — After Cleanup: Canonical Script List

Once cleanup is done, `data/scripts/` should contain only:

```
data/scripts/
├── fetch_govdata.py               ← STEP 1a: Fetch raw JSONs from data.gov.in API
├── fetch_external.py              ← STEP 1b: Fetch external sources (opencity.in, etc.)
├── transform_to_7_table_schema.py ← STEP 2:  Normalize all sources → 7-table schema
├── validate.py                    ← STEP 3:  Quality gate before Neo4j load
└── (auto_pipeline.py)             ← STEP 0:  Orchestrator [to be built]
```

And `data/config/` should contain:
```
data/config/
├── govdata_registry.json    ← data.gov.in dataset registry (UUID + metadata)
└── external_registry.json   ← external source registry (opencity.in, GitHub, etc.)
```

---

## Section 8 — Root-Level Stale CSVs (`data/*.csv`)

These are the original manually curated CSVs from the initial scaffold (Mar 10).
These root-level CSVs are v1 schema (old column names like `actorid` not `actor_id`),
not loaded by any script. `data/residents.csv` also contains real phone numbers — privacy risk.

**Note:** `final_formalized/*.csv` are now auto-deleted by `load_seed_data.py` after
a successful Neo4j load. Neo4j is the source of truth — staging CSVs are transient.

| File | Why Remove |
|---|---|
| `data/actors.csv` | v1 schema — superseded, not loaded |
| `data/assets.csv` | v1 schema — superseded, not loaded |
| `data/beneficiaries.csv` | v1 schema — superseded, not loaded |
| `data/events.csv` | v1 schema — superseded, not loaded |
| `data/evidence.csv` | v1 schema — superseded, not loaded |
| `data/regions.csv` | v1 schema — superseded, not loaded |
| `data/residents.csv` | Not in 7-table schema, never loaded, contains real phone numbers (privacy risk) |
| `data/schemes.csv` | v1 schema — superseded, not loaded |
| `data/resources/data/` | Orphan duplicate of `final_formalized/` from March 8 — stale copy |

**Clean-up commands:**
```bash
cd data
rm actors.csv assets.csv beneficiaries.csv events.csv evidence.csv regions.csv residents.csv schemes.csv
rm -rf resources/data/
```

---

## Section 8b — Superseded Govdata JSON

| File | Reason |
|---|---|
| `data/resources/structured/govdata/sbm_toilets_2122.json` | Superseded by `sbm_toilets_comprehensive.json` which has the same totals plus full year-by-year breakdown (2017→2022). Registry entry marked `active: false`. |

```bash
rm data/resources/structured/govdata/sbm_toilets_2122.json
```

---

## Section 9 — Cache Folder (`data/cache/`)

| File | Action | Reason |
|---|---|---|
| `data/cache/amrut_delhi_cached.json` | ✅ **KEEP** | Offline demo cache — AI extraction result for Live Ingestion demo PIB text. Needed for demo reliability without Groq API. |
| `data/cache/last_autosearch.json` | Delete | Runtime state file — auto-regenerated on every use. Currently empty. |

---

## Section 10 — Python Cache (`data/__pycache__/`)

| Path | Action |
|---|---|
| `data/__pycache__/` | Delete — Python bytecode from running scripts in `data/` root. Auto-regenerated. |

---

## Section 11 — Frontend Stale Files (`frontend/`)

| File | Why Remove |
|---|---|
| `frontend/pages/.gitkeep` | Placeholder — pages folder now has 4 real pages, no longer needed |
| `frontend/hidden_Live_Ingestion.py` | Old hidden version — `pages/03_Live_Ingestion.py` is the active one |
| `frontend/06_❓_Questions.py.bak` | Backup file — Questions page merged into Proof Chain (`02_Proof_Chain.py`) |

**Clean-up commands:**
```bash
rm frontend/pages/.gitkeep
rm frontend/hidden_Live_Ingestion.py
rm "frontend/06_❓_Questions.py.bak"
```

**Python cache (all frontend pycache):**
```bash
find frontend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; echo "done"
```

---

## Section 12 — Backend Dead Scripts

These were one-time utilities or superseded by the current pipeline. None are imported or called anywhere.

| File | Reason |
|---|---|
| `ai/llm_extractor.py` | Replaced by `backend/app/services/ai_service.score_evidence()` |
| `backend/run_cypher.py` | One-off actor rename with hardcoded Windows path — already applied |
| `backend/scripts/cleanup_mistagged_assets.py` | One-time water body fix — already fixed in transform pipeline |
| `backend/scripts/debug_scraper.py` | Debug-only RSS script — covered by live `/scrape/news` endpoint |
| `backend/scripts/deep_data_extraction.py` | Writes to old path, superseded by pipeline |
| `backend/scripts/seed_multi_scheme.py` | Old multi-scheme seeder — superseded by `load_seed_data.py` |
| `backend/scripts/setup_constraints.py` | One-time Neo4j constraint setup — already applied |
| `backend/test_db.py` | Old Neo4j connection test |
| `backend/utils/stats.py` | Used `PART_OF` (stale) — 0 active callers |
| `backend/app/utils/stats_helper.py` | Used `PART_OF` (stale) — 0 active callers |
| `scripts/load_seed_data.py` | Root-level duplicate using `PART_OF` and old schema — real one is `backend/scripts/load_seed_data.py` |

**Clean-up commands:**
```bash
rm ai/llm_extractor.py
rm backend/run_cypher.py
rm backend/scripts/cleanup_mistagged_assets.py
rm backend/scripts/debug_scraper.py
rm backend/scripts/deep_data_extraction.py
rm backend/scripts/seed_multi_scheme.py
rm backend/scripts/setup_constraints.py
rm backend/test_db.py
rm backend/utils/stats.py
rm backend/app/utils/stats_helper.py
rm scripts/load_seed_data.py
```

---

## Section 13 — Root-Level Diagnostic Scripts

These were one-off debug scripts using the old `PART_OF` relationship and `WARD45_SHAHDARA` IDs (both now replaced). No longer valid.

| File | Reason |
|---|---|
| `check_neo4j_local.py` | Uses `PART_OF`, old `WARD45_SHAHDARA` ID — stale |
| `diag_hierarchy.py` | Same — old hierarchy debug using `PART_OF` |
| `test_query.py` | Old `PART_OF` debug query |

**Clean-up commands:**
```bash
rm check_neo4j_local.py diag_hierarchy.py test_query.py
```

---

## Section 14 — Windows Metadata Artifacts

Zone.Identifier files are Windows NTFS metadata — meaningless on Linux, should not be in git.

| File |
|---|
| `prd1.md:Zone.Identifier` |
| `Pramaan_logo 1 (1).png:Zone.Identifier` |
| `Tryminds_logo.jpeg:Zone.Identifier` |

**Clean-up commands:**
```bash
find . -name "*:Zone.Identifier" -delete
```

---

## Cleanup Checklist

```
[x] Add amrut_water_logging UUID to govdata_registry.json — DONE Mar 19 ✅
[x] Fix PART_OF → CONTAINS in queries.py, wards.py — DONE Mar 20 ✅
[x] Fix ward_population.py hardcoded values → Neo4j lookup — DONE Mar 20 ✅
[x] Unified ai_service.py (merged llm_extractor + ai_service) — DONE Mar 20 ✅
[x] Delete 8 stale fetch scripts (Section 1): extract_amrut.py, amrut_funds.py, statewise_allocation.py, sbm_toilets.py, credit_guarantee_scheme.py, extract_pmay.py, api_test.py, amrut_water_logging.py — DONE Mar 20 ✅
[x] Delete 2 inspection scripts (Section 2): inspect_excel.py, analyze_data_schemas.py — DONE Mar 20 ✅
[x] Delete deep_data_extraction.py, generate_seed_data.py (Section 3) — DONE Mar 20 ✅
[x] Delete 3 wrong-data JSON files (Section 4) — DONE Mar 19 ✅
[x] Delete 3 temp output files (Section 5) — DONE Mar 19 ✅
[x] Delete stale PDF/CSVs + old ward CSVs (Section 6) — DONE Mar 19 ✅
[x] Delete 8 root-level stale CSVs + orphan resources/data/ dir (Section 8) — DONE Mar 20 ✅
[x] Delete data/cache/last_autosearch.json (Section 9) — DONE Mar 20 ✅
[x] Delete data/__pycache__/ (Section 10) — DONE Mar 20 ✅
[x] Delete frontend stale files: .gitkeep, hidden_Live_Ingestion.py, 06_❓_Questions.py.bak (Section 11) — DONE Mar 20 ✅
[x] Delete all frontend __pycache__/ folders (Section 11) — DONE Mar 20 ✅
[x] Delete backend dead scripts (Section 12) — DONE Mar 20 ✅
[x] Delete root-level diagnostic scripts (Section 13) — DONE Mar 20 ✅
[x] Delete Windows Zone.Identifier files (Section 14) — DONE Mar 20 ✅
[x] Run: python3 data/scripts/validate.py  — confirm 0 critical errors after cleanup — DONE Mar 20 ✅
[x] git add -A && git commit -m "chore: cleanup stale scripts and dead files" — DONE Mar 20 ✅
```
