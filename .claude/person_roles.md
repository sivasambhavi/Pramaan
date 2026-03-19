# PRAMAAN – Team Roles & Ownership

Team size: 3  
Timeline: MVP by 10 March (India Innovates 2026 submission)

---

## Overview

Each person owns a clear vertical:

- **Sambhavi** – Ontology & Data
- **Aparna** – Graph & Backend
- **Sreenu** – AI & Frontend

Claude should respect these ownership boundaries and avoid large changes in an area unless that person is explicitly asking for them.

---

## Sambhavi – Ontology & Data Lead (6 years)

### Mission

Design the **governance ontology** slice and curate the **seed dataset** for the MVP ward so that PRAMAAN can demonstrate full delivery chains and Delivery Scores.

### Ownership

- Ontology design (MVP subset)
- Data sourcing and curation for 1 Delhi ward
- Delivery Score definition and gap criteria
- CSV files in `data/`

### Main Responsibilities

- Define entities and relationships for MVP:
  - Entities: Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event
  - Relationships: funds, targets, benefits, located_in, built_by, represents, implements, proves, captured_at, lives_in, related_to
- Choose a Delhi ward and identify 3–5 key assets.
- Build and maintain CSVs:
  - `data/regions.csv`
  - `data/schemes.csv`
  - `data/actors.csv`
  - `data/assets.csv`
  - `data/beneficiaries.csv`
  - `data/evidence.csv`
  - `data/events.csv` (optional)
- Define Delivery Score formula and gap types and document them clearly.
- Provide one or more PIB/news texts with annotated expected entities for AI extraction.

### Files Sambhavi Primarily Owns

- `data/*.csv`
- Ontology docs (in `docs/` or similar)
- Any notes on Delivery Score and gap logic

---

## Aparna – Graph & Backend Lead (8 years)

### Mission

Implement the **Neo4j schema** and **FastAPI backend** that powers all core queries, Delivery Scores, gaps, and ingestion.

### Ownership

- Neo4j data model and schema
- Data loading scripts
- Cypher queries for hero use cases
- FastAPI app and REST endpoints

### Main Responsibilities

- Set up Neo4j and implement:
  - Constraints and indexes for entity IDs
  - Load script to ingest CSVs into Neo4j (`scripts/load_seed_data.py`)
- Implement key Cypher queries:
  - Ward overview with Delivery Score
  - Ward assets list
  - Asset proof chain (scheme → asset → evidence → beneficiaries)
  - Ward gaps (missing assets/evidence)
- Build FastAPI backend:
  - `GET /health`
  - `GET /wards`
  - `GET /wards/{ward_id}/assets`
  - `GET /assets/{asset_id}/chain`
  - `GET /wards/{ward_id}/gaps`
  - `POST /ingest/entities` (AI ingestion)
- Ensure performance and stability for demo data.

### Files Aparna Primarily Owns

- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/neo4j_client.py`
- `backend/app/models.py`
- `backend/app/queries.py`
- `backend/app/routers/wards.py`
- `backend/app/routers/assets.py`
- `backend/app/routers/ingest.py`
- `backend/scripts/load_seed_data.py`

---

## Sreenu – AI & Frontend Lead (4 years)

### Mission

Build the **Streamlit UI** and **AI integration** so that PRAMAAN feels like an intelligent, polished demo: maps, proof chains, questions, and live ingestion.

### Ownership

- Streamlit multi-page app
- Integration with FastAPI endpoints
- LLM-based entity extraction
- NL query routing for 3 fixed questions

### Main Responsibilities

- Implement Streamlit app:
  - `01_Ward_Map.py` – ward overview + Delivery Score gauge + asset table + Folium map ✅
  - `02_Proof_Chain.py` – asset selector + full chain (Scheme→Actor→Asset→Evidence→Beneficiary) + before/after photos ✅
  - `03_Live_Ingestion.py` – auto-search news, AI extraction (Groq), one-click Neo4j ingest, voice input ✅
  - `04_Micro_Accountability.py` – WhatsApp/SMS alerts via Twilio for verified assets ✅
- Integrate with backend APIs using `requests`/`httpx`.
- Implement AI modules:
  - `ai/llm_extractor.py` – `extract_governance_entities(text) -> dict` using Groq
  - `ai/nl_query.py` – routing from 3 question types to backend calls
- Cache LLM responses (MD5 cache) for offline demo reliability.
- Polish UI for a smooth 3–4 minute demo flow.

### Files Sreenu Primarily Owns

- `frontend/app.py`
- `frontend/pages/01_Ward_Map.py`
- `frontend/pages/02_Proof_Chain.py`
- `frontend/pages/03_Live_Ingestion.py`
- `frontend/pages/04_Micro_Accountability.py`
- `frontend/utils/constants.py`
- `frontend/utils/voice_input.py`
- `ai/llm_extractor.py`
- `ai/nl_query.py`

---

## How Claude Should Use This

- When **Sambhavi** is asking a question, focus on:
  - `data/` and ontology documentation.
  - Avoid changing backend/frontend unless she explicitly asks.

- When **Aparna** is asking, focus on:
  - `backend/` and `scripts/load_seed_data.py`.
  - Avoid heavy UI changes or ontology redesign.

- When **Sreenu** is asking, focus on:
  - `frontend/` and `ai/`.
  - Treat backend schema and data model as contracts; don’t change them unless coordinated.

Claude should always assume this ownership unless the user explicitly states otherwise in the prompt.
