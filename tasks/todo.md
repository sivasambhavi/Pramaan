# Pramaan – Task Tracker

## Sprint: March 7–10, 2026 (India Innovates MVP)

---

## Sambhavi – Ontology & Data

- [ ] Choose final Delhi ward (Ward 45 Shahdara or confirm alternative)
- [ ] Fill `data/regions.csv` with ward + region data
- [ ] Fill `data/schemes.csv` (2–3 schemes: SFC Grant, PMAY, Swachh Bharat)
- [ ] Fill `data/actors.csv` (agencies, departments)
- [ ] Fill `data/assets.csv` (3–5 assets: roads, drains, streetlights)
- [ ] Fill `data/beneficiaries.csv`
- [ ] Fill `data/evidence.csv` (10–15 pieces)
- [ ] Fill `data/events.csv` (optional)
- [ ] Define Delivery Score formula and gap criteria (document in `.claude/` or `tasks/`)
- [ ] Provide 1 PIB/news text with annotated expected entities for AI extraction

---

## Aparna – Graph & Backend

- [ ] Set up Neo4j locally and verify connectivity
- [ ] Implement constraints and indexes in Neo4j for entity IDs
- [ ] Implement `load_seed_data.py` — parse all CSVs and load nodes/relationships
- [ ] Write Cypher queries in `queries.py`:
  - [ ] Ward overview + Delivery Score
  - [ ] Ward assets list
  - [ ] Asset proof chain (scheme → asset → evidence → beneficiaries)
  - [ ] Ward gaps (missing assets/evidence)
- [ ] Wire `GET /wards` to Neo4j
- [ ] Wire `GET /wards/{ward_id}/assets` (new endpoint)
- [ ] Wire `GET /wards/{ward_id}/gaps` to Neo4j
- [ ] Wire `GET /assets/{asset_id}/chain` to Neo4j
- [ ] Wire `POST /ingest/entities` to use `IngestPayload` model and write to Neo4j
- [ ] Fix `config.py` key mismatch (`app_env` → `PRAMAAN_ENV`)
- [ ] Test all endpoints via `/docs` (Swagger UI)

---

## Sreenu – AI & Frontend

- [ ] Implement `ai_extraction.py` — LLM call to extract governance entities from text
- [ ] Cache LLM response for the main demo PIB text (offline reliability)
- [ ] Implement `nl_query.py` — route 3 fixed questions to backend calls
- [ ] Build `01_🏙_Ward_Map.py` — ward overview + Delivery Score + asset list
- [ ] Build `02_🧷_Proof_Chain.py` — asset selector + full chain visualization
- [ ] Build `03_❓_Questions.py` — 3 fixed NL questions → backend → display results
- [ ] Build `04_⚡_Live_Ingestion.py` — paste text → extract → show JSON → ingest → refresh
- [ ] Polish UI for 3–4 min demo flow
- [ ] Remove `frontend/pages/.gitkeep`

---

## Shared / Submission

- [ ] README with setup instructions (Neo4j, backend, frontend)
- [ ] Unstop form filled completely
- [ ] 7–10 slide PPT (problem, solution, architecture, demo flow, team)
- [ ] 3–5 min demo video (recommended)
- [ ] Final end-to-end demo run before submission

---

## Completed

<!-- Move items here with date when done -->
- [x] Project scaffold created (all dirs, stub files, requirements) — Mar 8
