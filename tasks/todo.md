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
  - [ ] Implement ID filling logic: if AI-extracted JSON has missing IDs, generate them using ID rules (e.g., `REG_W45` pattern)
  - [ ] Validate extracted entities match 7-table schema before ingestion
  - [ ] Handle entity resolution (fuzzy matching for region/scheme names)
- [ ] Fix `config.py` key mismatch (`app_env` → `PRAMAAN_ENV`)
- [ ] Test all endpoints via `/docs` (Swagger UI)

---

## Sreenu – AI & Frontend

- [ ] **AI Mapper (Automation Ingestion Layer)**
  - [ ] Implement `ai_extraction.py` with Named Entity Recognition (NER)
  - [ ] Build LLM prompt that "forces" fragmented text/JSON into 7-table schema
  - [ ] Map extracted entities to canonical IDs:
    - [ ] "Ward 45" → `REG_W45` (Region mapping)
    - [ ] "Construction" → Asset entity type
    - [ ] Scheme names → canonical scheme IDs
    - [ ] Location aliases → normalized region IDs
  - [ ] Output JSON matching 7-table structure (regions, schemes, actors, assets, beneficiaries, evidence, events)
  - [ ] Cache LLM response for the main demo PIB text (offline reliability)

- [ ] **Live Ingestion Screen (AI Pass)**
  - [ ] Define JSON schema exactly matching 7-table columns (document in `ai/` or `docs/`)
  - [ ] Build `04_⚡_Live_Ingestion.py` with:
    - [ ] Text input area (paste PIB/news/fragmented JSON)
    - [ ] "Extract" button → calls `ai_extraction.py`
    - [ ] Display extracted JSON preview (entities + relations)
    - [ ] "Ingest" button → sends JSON to `POST /ingest/entities`
    - [ ] Show success/error feedback
    - [ ] Refresh ward/asset views to show new data
  - [ ] Integration with backend ingestion endpoint

- [ ] Implement `nl_query.py` — route 3 fixed questions to backend calls
- [ ] Build `01_🏙_Ward_Map.py` — ward overview + Delivery Score + asset list
- [ ] Build `02_🧷_Proof_Chain.py` — asset selector + full chain visualization
- [ ] Build `03_❓_Questions.py` — 3 fixed NL questions → backend → display results
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

---

## Future Work – Agentic AI Implementation (Post-MVP)

**Status:** Planned for post-MVP / v2.0 deep implementation  
**Timeline:** After India Innovates 2026 submission (if selected for exhibition booth)

### Agent Architecture Design

- [ ] Design multi-agent system architecture
  - [ ] Define agent roles and responsibilities
  - [ ] Design agent communication protocol
  - [ ] Plan agent orchestration workflow (LangGraph/CrewAI evaluation)
  - [ ] Document agent decision-making loops

### Core Agents Implementation

- [ ] **Data Ingestion Agent**
  - [ ] Monitor data sources (PIB, news, MCD portals)
  - [ ] Autonomous entity extraction from unstructured text
  - [ ] Schedule-based or event-driven ingestion
  - [ ] Quality validation before graph insertion

- [ ] **Verification Agent** (from ENGINEERING_PRDS.md)
  - [ ] Cross-check extracted entities against existing graph
  - [ ] Verify claims (e.g., "MCD says drain cleaned? News confirms? Yes/No")
  - [ ] Confidence scoring for extracted data
  - [ ] Flag discrepancies for human review

- [ ] **Gap Detection Agent**
  - [ ] Autonomous gap analysis (missing evidence, incomplete chains)
  - [ ] Proactive identification of delivery chain breaks
  - [ ] Generate gap reports with recommendations
  - [ ] Alert on new gaps as data is ingested

- [ ] **Query Agent** (Enhanced NL Query)
  - [ ] Autonomous question understanding and decomposition
  - [ ] Multi-step reasoning across graph
  - [ ] Query planning and optimization
  - [ ] Explainable answer generation with graph paths

- [ ] **Evidence Linking Agent**
  - [ ] Automatic geo-tagging and asset matching
  - [ ] Before/after photo pairing
  - [ ] Spatial matching (bounding-box for street-level assets)
  - [ ] Temporal validation (dates, sequences)

### Agent Infrastructure

- [ ] Agent framework setup
  - [ ] Choose framework (LangGraph, CrewAI, or custom)
  - [ ] Implement agent base class with common capabilities
  - [ ] Tool registry (web scraping, graph queries, LLM calls)
  - [ ] Agent memory/context management

- [ ] Agent orchestration
  - [ ] Workflow engine for agent coordination
  - [ ] Agent handoff protocols
  - [ ] Error handling and retry logic
  - [ ] Agent monitoring and logging

- [ ] Agent capabilities
  - [ ] Tool use integration (Neo4j queries, web scraping, LLM APIs)
  - [ ] Memory/context persistence across interactions
  - [ ] Self-correction and validation loops
  - [ ] Learning from corrections (feedback loop)

### Integration Points

- [ ] Integrate agents with existing FastAPI backend
  - [ ] Agent-triggered endpoints (e.g., `/agents/ingest/trigger`)
  - [ ] Agent status monitoring endpoints
  - [ ] Agent configuration management

- [ ] Frontend agent controls
  - [ ] Agent status dashboard in Streamlit
  - [ ] Manual agent triggers (e.g., "Run Verification Agent")
  - [ ] Agent activity logs and results display

### Testing & Validation

- [ ] Agent unit tests
- [ ] Multi-agent integration tests
- [ ] Agent performance benchmarks
- [ ] Agent accuracy validation (verification agent precision/recall)

### Documentation

- [ ] Agent architecture documentation
- [ ] Agent API documentation
- [ ] Agent workflow diagrams
- [ ] Agent configuration guide

---

**Note:** This agentic AI implementation is explicitly out of scope for the March 10 MVP. It represents a significant architectural evolution that would be pursued if PRAMAAN is selected for the exhibition booth or post-competition development.
