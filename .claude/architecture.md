# PRAMAAN – Architecture Overview
> Last updated: March 19, 2026

## 1. Project Summary

**PRAMAAN** – *Proof-based Registry for Asset Mapping, Accountability & Nationwide Transparency* – is an AI-powered governance-tech platform that:

- Builds a **knowledge graph** of governance delivery for Delhi wards.
- Connects schemes, budgets, actors, assets, locations, beneficiaries, and evidence.
- Provides a **FastAPI** backend over a **Neo4j** graph.
- Exposes a **Streamlit** UI for:
  - Ward overview and Delivery Score
  - Asset proof chains with trust tiers
  - Live AI-powered news ingestion
  - Micro-accountability notifications (WhatsApp/SMS via Twilio)

The MVP targets **Ward 45, Shahdara South, Delhi** with 5 hero delivery chains, demoing at India Innovates 2026.

---

## 2. High-Level Architecture

PRAMAAN consists of five layers:

1. **Data Layer**
   - Seed CSVs in `data/resources/data/final_formalized/` (canonical source for Neo4j)
   - Raw CSVs in `data/` (legacy, not loaded into Neo4j)
   - Static government JSON files in `data/resources/` (served via govdata API)
   - ETL scripts in `data/scripts/` for fetching + transforming data.gov.in sources

2. **Knowledge Graph Layer (Neo4j)**
   - Neo4j running locally via Docker (`docker-compose.yml`)
   - 7 node types: Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event
   - 11+ relationship types: FUNDS, BUILT_BY, LOCATED_IN, PROVES, BENEFITS, etc.
   - Single source of truth for all queries and visualizations

3. **Backend API Layer (FastAPI)**
   - Python + FastAPI under `backend/app/`
   - Connects to Neo4j via `neo4j_client.py`
   - Services layer under `backend/app/services/` for AI and news logic
   - 8 routers covering wards, assets, ingest, questions, scrape, notifications, govdata, beneficiaries

4. **Frontend Layer (Streamlit)**
   - 4-page Streamlit app under `frontend/`
   - Shared components: `frontend/components/topnav.py`
   - Shared utilities: `frontend/utils/` (constants, icons, session, voice_input, geo_selector)
   - Evidence photos: `frontend/static/evidence/`

5. **AI Layer (Groq LLM)**
   - `ai/llm_extractor.py` — text → governance entities JSON (Groq llama-3.3-70b)
   - `backend/app/services/ai_service.py` — entity extraction used by scrape router
   - `backend/app/services/news_service.py` — Google News RSS scraping
   - NL query routing implemented in `backend/app/routers/questions.py`

All components run locally on a single machine for demo purposes.

---

## 3. Tech Stack

| Layer | Technology |
|-------|-----------|
| Graph DB | Neo4j 5 (Docker, local) |
| Backend | FastAPI + Uvicorn + Neo4j Python Driver |
| Frontend | Streamlit + Plotly + streamlit-folium + streamlit-agraph |
| AI / NLP | Groq API (llama-3.3-70b-versatile), MD5 response cache |
| News Scraping | feedparser (Google News RSS), requests, bs4 |
| Notifications | Twilio (WhatsApp/SMS) |
| Data Processing | Pandas, RapidFuzz (entity resolution) |
| Config | pydantic-settings + python-dotenv |
| Environment | Local dev + Docker (Neo4j only) |

---

## 4. Repository Structure (Actual — March 2026)

```text
Pramaan/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint, includes all routers
│   │   ├── config.py            # Neo4j + Groq + app config (pydantic-settings)
│   │   ├── neo4j_client.py      # Neo4j driver + session helpers
│   │   ├── models.py            # Pydantic request/response models
│   │   ├── queries.py           # Cypher query helper functions
│   │   ├── routers/
│   │   │   ├── wards.py         # GET /wards, GET /wards/{ward_id}/assets, /gaps, /score
│   │   │   ├── assets.py        # GET /assets/{asset_id}/chain
│   │   │   ├── ingest.py        # POST /ingest/entities, DELETE /ingest/demo-nodes
│   │   │   ├── questions.py     # GET /questions/hardcoded, POST /questions/custom
│   │   │   ├── scrape.py        # POST /scrape/news, POST /scrape/analyze
│   │   │   ├── notifications.py # POST /notify/whatsapp (Twilio)
│   │   │   ├── govdata.py       # GET /data/amrut-drainage, /pmay-housing, etc.
│   │   │   └── beneficiaries.py # GET /beneficiaries/{ward_id}
│   │   ├── services/
│   │   │   ├── ai_service.py    # LLM entity extraction (Groq)
│   │   │   └── news_service.py  # Google News RSS + PIB RSS scraping
│   │   └── utils/
│   │       └── stats_helper.py  # Delivery score calculations
│   ├── scripts/
│   │   ├── load_seed_data.py        # CSV → Neo4j loader (reads final_formalized/)
│   │   ├── setup_constraints.py     # Neo4j uniqueness constraints + indexes
│   │   ├── seed_multi_scheme.py     # Seed additional schemes
│   │   ├── cleanup_mistagged_assets.py  # Fix mis-tagged asset nodes
│   │   └── deep_data_extraction.py  # LLM-powered bulk extraction
│   └── utils/
│       └── stats.py
│
├── frontend/
│   ├── app.py                   # Streamlit entrypoint (branding + CSS + page links)
│   ├── pages/
│   │   ├── 01_Ward_Map.py       # Ward overview, delivery score, asset table, map
│   │   ├── 02_Proof_Chain.py    # Full chain: Scheme→Actor→Asset→Evidence→Beneficiary
│   │   ├── 03_Live_Ingestion.py # AI news scraping + manual ingestion to Neo4j
│   │   └── 04_Micro_Accountability.py  # WhatsApp alerts for verified assets
│   ├── components/
│   │   └── topnav.py            # Shared top navigation bar
│   ├── utils/
│   │   ├── constants.py         # Shared constants: scheme names, asset overrides, evidence photos
│   │   ├── icons.py             # Icon mappings for asset/scheme types
│   │   ├── session.py           # Streamlit session state helpers
│   │   ├── voice_input.py       # Groq Whisper voice-to-text utility
│   │   └── geo_selector.py      # Geographic region selector helpers
│   └── static/
│       └── evidence/            # Before/after geo-tagged photos for Ward 45 assets
│
├── ai/
│   └── llm_extractor.py         # Standalone LLM extractor (Groq, 7-table schema output)
│
├── data/
│   ├── resources/
│   │   ├── data/
│   │   │   └── final_formalized/    # ← CANONICAL seed data loaded into Neo4j
│   │   │       ├── regions.csv
│   │   │       ├── schemes.csv
│   │   │       ├── actors.csv
│   │   │       ├── assets.csv
│   │   │       ├── beneficiaries.csv
│   │   │       ├── evidence.csv
│   │   │       ├── events.csv
│   │   │       ├── scheme_allocations.csv
│   │   │       └── actors_enriched.csv
│   │   ├── amrut_storm_water_drainage.json  # data.gov.in — served via /data/amrut-drainage
│   │   ├── pmay_housing_data.json           # data.gov.in — served via /data/pmay-housing
│   │   ├── statewise_allocation.json        # data.gov.in — scheme fund releases
│   │   ├── credit_guarantee_scheme.json     # data.gov.in
│   │   └── sbm_toilets.json                 # NOTE: actually a pincode directory, not SBM data
│   ├── scripts/
│   │   ├── generate_final_datasets.py   # Generate formalized CSVs from raw sources
│   │   ├── transform_to_7_table_schema.py   # Transform raw → 7-table schema
│   │   ├── extract_amrut.py / extract_pmay.py  # data.gov.in API fetchers
│   │   └── [other ETL scripts]
│   ├── docs/
│   │   ├── DATA_MAPPING.md          # 4 strategic governance layers mapped to files
│   │   ├── DATA_EXTRACTION_PLAN.md  # ETL plan (NOTE: has Windows paths — needs fix)
│   │   └── ENGINEERING_PRDS.md      # Per-person PRDs with acceptance criteria
│   ├── residents.csv                # Resident data with phone numbers (privacy risk — mock in prod)
│   └── [legacy CSVs]                # data/assets.csv etc. — NOT loaded; use final_formalized/
│
├── .claude/                     # AI context files (not part of demo)
│   ├── architecture.md          # This file
│   ├── frontend_design.md       # CSS design system + color palette
│   ├── guardrails.md            # Claude behavior rules
│   ├── person_roles.md          # Team ownership: Sambhavi / Aparna / Sreenu
│   └── workflow-orchestration.md # Planning workflow
│
├── docs/
│   ├── todo.md                  # Active sprint tracker + blockers + architecture decisions
│   ├── GAPS_AND_ENHANCEMENTS.md # 65 identified gaps, categorized by priority
│   ├── AI_MAPPER_SPEC.md        # AI extraction JSON schema + ID generation rules
│   └── lessons.md               # Dev lessons log (needs update)
│
├── docker-compose.yml           # Neo4j local setup (password: pramaa2026)
├── requirements.txt             # All Python dependencies
├── .env                         # NEO4J_URI, NEO4J_PASSWORD, GROQ_API_KEY (not in git)
├── PRD.md                       # Master product vision (2113 lines)
└── README.md                    # Setup instructions + quick start
```

---

## 5. Key Data Flows

### Flow 1 — Seed Data (CSV → Neo4j)
```
data/resources/data/final_formalized/*.csv
    → backend/scripts/load_seed_data.py
    → Neo4j (MERGE nodes + relationships)
```

### Flow 2 — UI Query (Streamlit → FastAPI → Neo4j)
```
frontend/pages/*.py
    → requests.get("http://localhost:8000/...")
    → backend/app/routers/*.py
    → backend/app/queries.py (Cypher)
    → Neo4j
    → JSON response → rendered in Streamlit
```

### Flow 3 — Live Ingestion (News → AI → Neo4j)
```
User pastes text / URL  OR  auto-search triggers
    → backend/app/services/news_service.py (RSS scrape)
    → backend/app/services/ai_service.py (Groq LLM extraction)
    → POST /ingest/entities
    → backend/app/routers/ingest.py (MERGE to Neo4j)
```

### Flow 4 — Static Gov Data (JSON → FastAPI → UI)
```
data/resources/*.json (pre-fetched from data.gov.in)
    → backend/app/routers/govdata.py
    → GET /data/amrut-drainage | /data/pmay-housing
    → frontend/pages/02_Proof_Chain.py (AMRUT/PMAY panels)
```

---

## 6. Critical Known Issues (as of March 19, 2026)

| Issue | Impact | Fix Location |
|-------|--------|-------------|
| `.env` file missing | Neo4j connection fails on fresh clone | Create `.env` with `neo4j_password=pramaa2026` |
| Asset ID split-brain | `data/assets.csv` uses `ASSET_W45_GALI7_DRAIN`; `final_formalized/` uses `ASSET_DRAIN_GALI7` | Align `constants.py` to `final_formalized/` IDs |
| `DELETE /ingest/demo-nodes` missing | Live Ingestion reset button → 404 | Add to `backend/app/routers/ingest.py` |
| `POST /assets/{id}/set-verified` missing | Proof Chain verify button → 404 | Add to `backend/app/routers/assets.py` |
| Duplicate `groq_api_key` in `config.py` | Pydantic warning on startup | Remove duplicate field |
| `data/scripts/*.py` have Windows paths | ETL scripts crash on Linux | Replace `e:\\INDIA_INNOVATES\\` with `Path(__file__)` |
| `sbm_toilets.json` is pincode data | Wrong data served | Replace with real SBM data or remove endpoint |

---

## 7. Environment Setup

```env
# .env (required at project root)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pramaa2026
GROQ_API_KEY=your_groq_key_here
DATA_GOV_API_KEY=your_datagov_key_here
```

```bash
# Start Neo4j
docker-compose up -d

# Seed data
python backend/scripts/load_seed_data.py

# Start backend
uvicorn backend.app.main:app --app-dir . --reload

# Start frontend (separate terminal)
streamlit run frontend/app.py
```
