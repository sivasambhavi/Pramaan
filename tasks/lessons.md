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

---
