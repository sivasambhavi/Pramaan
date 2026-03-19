# Pramaan – Lessons Learned

Patterns and corrections captured during development.
Updated after every mistake or user correction.

---

## Format

**Pattern:** what went wrong or what to watch out for
**Fix:** the correct approach
**Date:** when captured

---

## Lessons

### 1. Cypher does not support parameterised labels or relationship types
**Pattern:** Used `$label` and `$type` as Cypher parameters in `MERGE (n:$label)` and `MERGE (a)-[r:$type]->(b)` — this is invalid Cypher syntax.
**Fix:** Use Python string interpolation to build the query string before passing it to the driver, e.g. `f"MERGE (n:{label} {{id: $id}})"`. Always sanitise/whitelist label and type values before interpolating.
**Date:** Mar 8

### 2. Pydantic-settings env key mismatch
**Pattern:** `config.py` declared `app_env` but `env.example` exported `PRAMAAN_ENV` — pydantic-settings maps field names to env vars by uppercasing the field name, so `app_env` maps to `APP_ENV`, not `PRAMAAN_ENV`.
**Fix:** Either rename the field to `pramaan_env` in `config.py`, or add `env='PRAMAAN_ENV'` as a field-level alias.
**Date:** Mar 8

### 3. Git identity must be set before committing
**Pattern:** First commit attempt failed because git user name/email was not configured on this WSL machine.
**Fix:** Run `git config user.name` and `git config user.email` locally in the repo before committing. Do not set `--global` unless the user asks.
**Date:** Mar 8

### 4. Asset ID split-brain between data/ and final_formalized/
**Pattern:** `data/assets.csv` uses IDs like `ASSET_W45_GALI7_DRAIN`. `final_formalized/assets.csv` uses `ASSET_DRAIN_GALI7`. `load_seed_data.py` reads `final_formalized/`, so Neo4j only knows the second format. `constants.py` references both — causing evidence photos to fail silently.
**Fix:** Treat `final_formalized/` as the canonical source. Align all UI constants, Cypher queries, and seed scripts to use `final_formalized/` IDs. Never edit `data/assets.csv` expecting graph changes.
**Date:** Mar 19

### 5. Docker Neo4j password mismatch with config.py default
**Pattern:** `docker-compose.yml` sets `NEO4J_AUTH=neo4j/pramaa2026`. `backend/app/config.py` has `neo4j_password: str = "password"` as default. Without a `.env` file, the app silently uses the wrong password and all Neo4j queries fail with auth errors.
**Fix:** Always create a `.env` file at project root before running. Add a startup health check that verifies Neo4j connectivity and logs a clear error if auth fails.
**Date:** Mar 19

### 6. Windows paths break all ETL scripts on Linux
**Pattern:** `data/scripts/generate_final_datasets.py` and `transform_to_7_table_schema.py` have hardcoded `e:\\INDIA_INNOVATES\\Pramaan\\` paths. Running them on Linux raises `FileNotFoundError` immediately.
**Fix:** Always use `Path(__file__).resolve().parents[N]` for cross-platform paths. Never hardcode drive letters.
**Date:** Mar 19

### 7. Duplicate groq_api_key field in config.py causes Pydantic warning
**Pattern:** `groq_api_key` was defined twice in `backend/app/config.py`. Pydantic-settings silently uses the first definition but logs a validation warning on startup that confuses debugging.
**Fix:** Search for duplicate field names in config before adding new ones. Use `grep` to verify.
**Date:** Mar 19

### 8. `sbm_toilets.json` is a pincode directory, not SBM data
**Pattern:** Assumed `sbm_toilets.json` contained SBM toilet counts. It actually contains pincode-to-city mapping data from a different data.gov.in catalog.
**Fix:** Always inspect JSON structure (`head`, `jq .`) before assuming contents match the filename. Verify `resource_id` in data.gov.in API response matches the intended catalog.
**Date:** Mar 19

### 9. Frontend CSS injected in `app.py` bleeds into all pages — must not duplicate
**Pattern:** Global CSS is injected via `st.markdown()` in `frontend/app.py`. If individual page files also inject the same CSS block, it runs twice, causing double-styled elements and performance degradation.
**Fix:** Inject global CSS only once in `app.py`. Page files should only add page-specific styles using scoped class names.
**Date:** Mar 19

### 10. Emoji in page filenames causes cross-platform issues
**Pattern:** Emoji-named page files cause filesystem errors on some Linux distributions (especially in Docker or WSL) due to emoji encoding in filenames.
**Fix:** Use plain ASCII filenames (e.g. `01_Ward_Map.py`). Streamlit uses the display name from `st.set_page_config(page_title=...)`, not the filename, for the sidebar label.
**Date:** Mar 19

### 11. `hidden_Live_Ingestion.py` left behind after promotion
**Pattern:** When promoting a hidden page to `frontend/pages/`, the original hidden file was not deleted. Both files now coexist, causing confusion about which is authoritative.
**Fix:** When promoting a file from a hidden location to `pages/`, immediately delete the original. Use git to confirm only one copy exists.
**Date:** Mar 19

### 12. Keeping duplicate PRD files (PRD.md + prd1.md)
**Pattern:** `prd1.md` was an exact copy of `PRD.md` (zero diff). Having two identical 2113-line files wastes space and confuses contributors about which is canonical.
**Fix:** Always run `diff file1 file2` before keeping multiple copies of large docs. Delete duplicates immediately. Use git blame/log to determine which file is the intended canonical one.
**Date:** Mar 19

### 13. Outdated AI context files give wrong advice
**Pattern:** `.claude/onepager_MVP.md` and `.claude/architecture.md` referenced old 6-screen structure and emoji page names months after the codebase changed. Claude was giving advice based on stale context.
**Fix:** Update `.claude/` files whenever significant structural changes happen (page renames, new routers, folder changes). Treat them as living documents, not one-time setup files.
**Date:** Mar 19

---
