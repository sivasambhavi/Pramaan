# PRAMAAN – Architecture Overview

## 1. Project Summary

**PRAMAAN** – *Proof-based Registry for Asset Mapping, Accountability & Nationwide Transparency* – is a governance-tech platform that:

- Builds a **knowledge graph** of governance delivery for a Delhi ward.
- Connects schemes, budgets, assets, locations, beneficiaries, and evidence.
- Provides a **FastAPI** backend over a **Neo4j** graph.
- Exposes a **Streamlit** UI for:
  - Ward overview and Delivery Score
  - Asset proof chains
  - Gap analysis
  - Live ingestion of AI-extracted entities from unstructured text

The MVP targets a **single ward**, with **5–8 complete delivery chains**, to demo at India Innovates 2026.

---

## 2. High-Level Architecture

PRAMAAN consists of four layers:

1. **Data Layer**
   - Source data stored as CSV files in `data/`.
   - Data is curated to represent:
     - One Delhi ward
     - Schemes, actors, assets, beneficiaries, evidence, events
   - A Python script loads CSVs into Neo4j.

2. **Knowledge Graph Layer (Neo4j)**
   - Neo4j graph database running locally.
   - Stores entities and relationships according to a governance ontology.
   - Acts as the single source of truth for all queries and visualizations.

3. **Backend API Layer (FastAPI)**
   - Python + FastAPI app under `backend/app/`.
   - Connects to Neo4j via the official Python driver.
   - Provides REST endpoints for:
     - Ward list + Delivery Scores
     - Ward assets
     - Asset proof chains
     - Gap analysis
     - Ingestion of AI-extracted entities

4. **Frontend & AI Layer (Streamlit + LLM)**
   - Streamlit multi-page UI under `frontend/`.
   - Calls FastAPI endpoints to render:
     - Ward overview
     - Asset chains
     - Gaps
     - Live ingestion flow
   - Uses an LLM (via `ai/`) to:
     - Extract entities/relations from a PIB/news text
     - Map simple NL questions to predefined query templates

All components run locally on a single machine for demo purposes.

---

## 3. Tech Stack

- **Language:** Python 3
- **Graph DB:** Neo4j (local instance)
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **AI / NLP:** Hosted LLM API (e.g., OpenAI/Anthropic), called from Python
- **Data Processing:** Pandas, RapidFuzz (for entity resolution)
- **Environment:** Local dev + demo laptop (no cloud dependency for MVP)

---

## 4. Repository Structure (Target)

```text
pramaan/
  backend/
    app/
      __init__.py
      main.py          # FastAPI app, includes routers
      config.py        # Neo4j + app config
      neo4j_client.py  # Neo4j driver + session helpers
      models.py        # Pydantic models
      queries.py       # Cypher query helper functions
      routers/
        __init__.py
        wards.py       # /wards, /wards/{ward_id}/gaps
        assets.py      # /assets/{asset_id}/chain
        ingest.py      # /ingest/entities
    scripts/
      load_seed_data.py  # CSV → Neo4j loader

  frontend/
    app.py             # Streamlit entry
    pages/
      01_🏙_Ward_Map.py
      02_🧷_Proof_Chain.py
      03_❓_Questions.py
      04_⚡_Live_Ingestion.py

  ai/
    __init__.py
    ai_extraction.py   # text → entities/relations JSON
    nl_query.py        # NL question → query template + params

  data/
    regions.csv
    schemes.csv
    actors.csv
    assets.csv
    beneficiaries.csv
    evidence.csv
    events.csv

  docs/
    claude/
      guardrails.md
      architecture.md

  .env.example         # NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
  .gitignore
  README.md
