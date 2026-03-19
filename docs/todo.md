# Pramaan – Task Tracker

## Post-MVP Sprint (Mar 19+, 2026) — India Innovates Submission

---

## Sambhavi – Ontology & Data ✅ Complete

- [x] Ward 45 Shahdara selected as demo ward
- [x] `data/resources/data/final_formalized/regions.csv` — 272 Delhi wards
- [x] `data/resources/data/final_formalized/schemes.csv` — AMRUT, PMAY, SBM, SFC Grant, etc.
- [x] `data/resources/data/final_formalized/actors.csv` — MCD, contractors, personnel
- [x] `data/resources/data/final_formalized/assets.csv` — drains, roads, housing, streetlights
- [x] `data/resources/data/final_formalized/beneficiaries.csv` — partial real + mock for demo
- [x] `data/resources/data/final_formalized/evidence.csv` — geo-tagged photos + news articles
- [x] `data/resources/data/final_formalized/events.csv` — PIB + mocked events
- [x] Delivery Score formula defined: `(assets_with_full_chain / total_assets) × 100`
- [x] PIB/news text provided with annotated expected entities for AI extraction

---

## Aparna – Graph & Backend ✅ Mostly Complete

- [x] Neo4j set up via Docker Compose (`bolt://localhost:7687`)
- [x] Constraints and indexes in Neo4j for entity IDs
- [x] `backend/scripts/load_seed_data.py` — parses all CSVs, loads nodes/relationships
- [x] Cypher queries in `queries.py` — ward overview, asset list, proof chain, gap analysis
- [x] `GET /wards` → Neo4j
- [x] `GET /wards/{ward_id}/assets` → Neo4j
- [x] `GET /wards/{ward_id}/gaps` → Neo4j
- [x] `GET /assets/{asset_id}/chain` → Neo4j
- [x] `POST /ingest/entities` → writes to Neo4j with ID resolution
- [x] All endpoints tested via `/docs`
- [ ] Fix `config.py` key mismatch (`app_env` → `PRAMAAN_ENV`) ← still open (see Blockers)

---

## Sreenu – AI & Frontend

- [x] **AI Mapper** — `ai/llm_extractor.py` — Groq LLM extracts governance entities into 7-table JSON, ID mapping, MD5 cache for offline demo ✅

- [x] **Live Ingestion Screen** — `03_Live_Ingestion.py` — auto-search news, AI extraction, one-click Neo4j ingest ✅
- [x] Build `01_Ward_Map.py` — ward overview + Delivery Score + asset list ✅
- [x] Build `02_Proof_Chain.py` — asset selector + full chain visualization ✅
- [x] Build `04_Micro_Accountability.py` — WhatsApp/SMS alerts via Twilio ✅
- [x] Implement `nl_query.py` — route 3 fixed questions to backend calls ✅
- [ ] Polish UI for 3–4 min demo flow
- [ ] Remove `frontend/pages/.gitkeep`

---

## Shared / Submission

- [x] README with setup instructions (Neo4j, backend, frontend) — Mar 19
- [ ] Unstop form filled completely
- [ ] 7–10 slide PPT (problem, solution, architecture, demo flow, team)
- [ ] 3–5 min demo video (recommended)
- [ ] Final end-to-end demo run before submission

---

## Immediate Blockers — Fix Before Demo (Critical Path)

> These are non-negotiable. Demo will crash without these.

- [ ] **Create `.env` file** — `neo4j_password=pramaa2026`, `GROQ_API_KEY=<key>`, `DATA_GOV_API_KEY=<key>`
  - `config.py` defaults to `password="password"` but Docker runs `pramaa2026` → Neo4j connection fails silently
- [ ] **Fix Asset ID split-brain** — pick ONE ID set and align all files
  - `constants.py` uses `ASSET_DRAIN_GALI7` — formalized CSV uses same ✅
  - `data/assets.csv` uses `ASSET_W45_GALI7_DRAIN` — DIFFERENT ❌
  - `load_seed_data.py` loads `final_formalized/` not `data/assets.csv`
  - **Fix**: align `ASSET_EVIDENCE_PHOTOS` in `constants.py` to use `final_formalized/` IDs
- [ ] **Add 3 missing API endpoints** called by UI:
  - [ ] `DELETE /ingest/demo-nodes` — Live Ingestion reset button → currently 404
  - [ ] `POST /assets/{asset_id}/set-verified` — Proof Chain verify button → currently 404
  - [ ] Confirm `GET /data/amrut-drainage` is registered in `main.py`
- [ ] **Startup auto-seed** — check if Neo4j is empty on boot; if yes, run `load_seed_data.py` automatically
  - Add `@app.on_event("startup")` handler in `backend/app/main.py`
- [ ] **Fix duplicate `groq_api_key`** entry in `config.py` (defined twice)

---

## Data Pipeline — Automated Scraping to `final_formalized/`

> Goal: one command (or scheduled job) fetches, transforms, and loads all data

### Stage 1 — Fix Existing Scripts (Windows Paths → Linux)

- [ ] Fix `data/scripts/transform_to_7_table_schema.py` — replace all `e:\\INDIA_INNOVATES\\Pramaan\\` with `Path(__file__).resolve().parents[2]`
- [ ] Fix `data/scripts/generate_final_datasets.py` — same path fix
- [ ] Fix `data/scripts/deep_data_extraction.py` — same path fix
- [ ] Move `DATA_GOV_API_KEY` from hardcoded string to `.env` in all `data/scripts/*.py`

### Stage 2 — Unified ETL Pipeline (`backend/scripts/auto_pipeline.py`)

- [ ] Create `backend/scripts/auto_pipeline.py` that orchestrates all sources in sequence:
  - [ ] **Source A: data.gov.in API** → fetch raw JSON for all catalog IDs:
    - AMRUT drainage: `6e38d0c0-045e-4dce-81d0-eca39519bb07`
    - PMAY housing: `e3b19e4d-e287-4d32-b53d-70e9617c7770`
    - Add SBM, statewise allocations resource IDs
    - Save to `data/resources/<name>.json`
  - [ ] **Source B: Ward Population CSV** (`c16ccda1...csv`) → parse → `regions.csv` (272 Delhi wards)
  - [ ] **Source C: Delhi Tenders MD** (`delhi_tenders_data.md`) → regex parse → `actors.csv` + `actors_enriched.csv`
  - [ ] **Source D: KML Water Bodies** (`watercensusmap.kml`) → parse → append to `assets.csv`
  - [ ] **Source E: Google News RSS** → scrape per-asset → append to `evidence.csv`
  - [ ] **Source F: PIB RSS Feed** (`https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3`) → scrape → append to `events.csv`
- [ ] All transforms write to `data/resources/data/final_formalized/` using **MERGE logic** (append only, never wipe)
- [ ] After transforms complete, auto-call `load_seed_data.py` → Neo4j

### Stage 3 — Scheduler Integration

- [ ] Add `apscheduler==3.10.4` and `watchdog==4.0.0` to `requirements.txt`
- [ ] Add APScheduler to `backend/app/main.py`:
  - [ ] `run_full_pipeline()` → daily at 2am
  - [ ] `scrape_news_evidence()` → every 6 hours (news evidence per active asset)
- [ ] Add file watcher (watchdog) → detect new CSV in `final_formalized/` → trigger `load_seed_data.py`

---

## Domain Coverage Gaps — Fill Missing Data

> These cause empty cards and broken chains in the demo

- [ ] **Ghost wards** — Ward 12 Rohini and Ward 28 Saket exist in `regions.csv` but have zero assets/beneficiaries
  - Add at least 2 assets + 1 beneficiary row each
- [ ] **`SCHEME_PMKISAN`** — 0 assets, 0 beneficiaries → add farmer beneficiary rows (Ward 45)
- [ ] **`SCHEME_JJBY`** — 0 assets, 0 beneficiaries → add insurance holder beneficiary rows
- [ ] **`SCHEME_AB` (Ayushman Bharat)** — 9 beneficiaries but 0 assets → add health camp asset node
- [ ] **`SCHEME_SFC_GRANT_2024`, `SCHEME_AMRUT`, `SCHEME_PMGSY`, `SCHEME_STREETLIGHT`** — have assets but 0 beneficiaries → add beneficiary rows
- [ ] **Thin domains** — PRD requires 5-10 nodes each for:
  - [ ] `ClimateHazard` — add 5 event rows (Delhi smog, flood, heatwave events)
  - [ ] `TechEvent` — add 5 event rows (Digital India, Smart City nodes)
  - [ ] `SocialEvent` — add 5 event rows (citizen protests, grievances)

---

## Agentic AI Implementation — Revised Plan

> **Updated March 19, 2026** — Based on analysis of what genuinely needs AI vs. what can be scripted

### Decision Framework (What Needs AI, What Doesn't)

| Component | Needs Agentic AI? | Reason |
|-----------|------------------|--------|
| data.gov.in fetch | ❌ No | Deterministic API call — script is better |
| CSV/JSON transform | ❌ No | Fixed schema — script is better, faster, cheaper |
| Gap detection | ❌ No | Pure Cypher query does this perfectly |
| News scraping | ❌ No | RSS + keyword filter already works |
| **Cross-source verification** | ✅ **YES** | Only LLM can judge "MCD says done — does news confirm?" |
| **Fuzzy asset-to-news linking** | ✅ **YES** | LLM needed for ambiguous text matching |
| **NL query routing** | ✅ **YES** | Already implemented — extend it |
| Photo geo-tagging | ⚠️ Partial | EXIF = script; fuzzy location = AI |

### Phase 1 — NOW (This Week): Scripted Pipeline

> Get data flowing reliably first. No agents yet.

- [ ] Complete `auto_pipeline.py` (scripted ETL, all 6 sources)
- [ ] Startup auto-seed
- [ ] APScheduler for daily fetch + 6-hourly news scrape
- [ ] Fill domain coverage gaps in CSVs

### Phase 2 — NEXT (After Demo Stable): Verification Agent 🔥

> This is the **core differentiator** — the "Pramaan" (attestation) concept itself.
> Demo story: *"The AI independently caught a discrepancy — MCD claimed the drain was complete, but our agent found a news article from last week showing residents still face waterlogging. We auto-flagged it and notified the councillor."*

- [ ] Build `backend/agents/verification_agent.py`:
  - [ ] **Step 1 — Perceive**: Read all `fully_verified` assets from Neo4j
  - [ ] **Step 2 — Fetch**: Google News RSS for each asset (asset name + ward)
  - [ ] **Step 3 — Judge** (LLM call to Groq):
    - Prompt: *"MCD claims [asset] is complete. Here are [N] news articles. Do they confirm or contradict?"*
    - Output: `{verdict: confirm|contradict|insufficient, confidence: 0.0-1.0, reason: "..."}`
  - [ ] **Step 4 — Act**:
    - `confirm` → set `asset.ai_verified = true`, `asset.ai_confidence = score`
    - `contradict` → set `asset.proof_status = "disputed"`, create `CONTRADICTS` relationship to NewsArticle
    - `insufficient` → set `asset.proof_status = "news_only"`
  - [ ] **Step 5 — Notify**: trigger WhatsApp/SMS via Twilio if verdict = `contradict`
- [ ] Add FastAPI endpoint: `POST /agents/verify/{asset_id}` — trigger single-asset verification
- [ ] Add FastAPI endpoint: `POST /agents/verify-all` — trigger full ward verification sweep
- [ ] Add to APScheduler: verification sweep every 6 hours
- [ ] Frontend: show "AI Verified ✅" or "AI Disputed ⚠️" badge on Proof Chain page

### Phase 3 — POST-MVP (v2.0): Full Multi-Agent System

> Only pursue if selected for exhibition booth or post-competition

- [ ] **Data Ingestion Agent** — autonomous monitoring of PIB, MCD portals, news feeds
  - [ ] LangGraph/CrewAI framework setup
  - [ ] Tool registry: web scraping, Neo4j read/write, LLM calls
  - [ ] Schedule-based + event-driven ingestion
  - [ ] Quality validation loop before graph insertion

- [ ] **Gap Detection Agent** — autonomous gap analysis with recommendations
  - [ ] Identify delivery chain breaks (budget allocated → no asset → no evidence)
  - [ ] Generate natural-language gap reports
  - [ ] Alert on newly detected gaps

- [ ] **Evidence Linking Agent** — fuzzy text-to-asset matching + photo pairing
  - [ ] Match news article mentions to specific asset IDs
  - [ ] Before/after photo pairing using date + geo proximity
  - [ ] Spatial matching (GPS bounding-box for street-level assets)
  - [ ] Temporal validation (construction start → end → evidence sequence)

- [ ] **Query Agent** — enhanced multi-step NL reasoning
  - [ ] Decompose complex questions into sub-queries
  - [ ] Multi-hop graph traversal with LLM reasoning
  - [ ] Explainable answers with cited graph paths

- [ ] **Agent Infrastructure**
  - [ ] Choose framework: LangGraph (recommended for graph-native projects) vs CrewAI
  - [ ] Agent base class with shared tools (Neo4j, RSS, Groq, Twilio)
  - [ ] Agent memory/context persistence across runs
  - [ ] Self-correction loops with human-in-the-loop override
  - [ ] Agent monitoring dashboard in Streamlit (status, last run, decisions log)
  - [ ] Agent-triggered FastAPI endpoints: `/agents/ingest/trigger`, `/agents/status`

---

## Completed

<!-- Move items here with date when done -->
- [x] Project scaffold created (all dirs, stub files, requirements) — Mar 8
- [x] Evidence photos moved from Windows paths to `frontend/static/evidence/` — Mar 19
- [x] Live Ingestion promoted to `frontend/pages/03_Live_Ingestion.py` — Mar 19
- [x] Voice input utility added (`frontend/utils/voice_input.py`) — Mar 19
- [x] `02_Proof_Chain.py` fully rewritten with trust tiers + PMAY/AMRUT panels — Mar 19
- [x] `01_Ward_Map.py` fully rewritten with premium UI + delivery score — Mar 19
- [x] `04_Micro_Accountability.py` promoted from page 07 — Mar 19
- [x] `components/topnav.py`, `utils/icons.py`, `utils/session.py` added — Mar 19
- [x] Domain coverage audit completed — identified 10 scheme/ward gaps — Mar 19
- [x] Agentic AI decision framework completed — Verification Agent identified as core differentiator — Mar 19

---

> **Architecture Decision (Mar 19, 2026):** Use scripted ETL pipeline for structured data (data.gov.in, CSVs, KML) — deterministic, fast, zero LLM cost. Use agentic AI selectively for tasks that genuinely require judgment: cross-source verification (Verification Agent), fuzzy text-to-asset linking, and NL query routing. The Verification Agent is the highest-priority agent — it IS the "Pramaan" (attestation) concept.
