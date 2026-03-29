# Claude Guardrails for PRAMAAN

## Project Overview

PRAMAAN – **Proof-based Registry for Asset Mapping, Accountability & Nationwide Transparency** – is a governance-tech app that:

- Loads governance delivery data for 1 Delhi ward into a **Neo4j** knowledge graph.
- Exposes **FastAPI** endpoints for queries and ingestion.
- Provides a **Streamlit** UI for ward overview, proof chains, live ingestion, and micro-accountability.
- Uses an **LLM** (Groq llama-3.3-70b) to extract entities/relations from PIB/news text and map them into the ontology.

The goal is to ship a **stable demo** for the India Innovates 2026 submission (MVP delivered Mar 19, 2026).

---

## Architecture (Must Stay Stable)

Claude MUST respect this architecture unless explicitly told otherwise:

- **Backend**
  - Language: Python 3
  - Framework: FastAPI
  - Location: `backend/app/`
  - Key files:
    - `main.py` – FastAPI entrypoint, includes routers
    - `neo4j_client.py` – Neo4j driver and session helpers
    - `models.py` – Pydantic models
    - `queries.py` – Cypher query helpers
    - `routers/wards.py` – ward-related endpoints
    - `routers/assets.py` – asset-related endpoints
    - `routers/ingest.py` – ingestion endpoints
    - `routers/scrape.py` – news scraping + AI extraction
    - `routers/govdata.py` – static data.gov.in JSON endpoints
    - `routers/notifications.py` – Twilio WhatsApp/SMS
    - `routers/questions.py` – NL query routing

- **Graph Layer**
  - DB: Neo4j (local)
  - Accessed only through `neo4j_client.py` and `queries.py`

- **Frontend**
  - Framework: Streamlit
  - Entry: `frontend/app.py`
  - Multi-page structure in `frontend/pages/`

- **AI**
  - Location: `ai/`
  - `llm_extractor.py` – Groq LLM entity extraction (`extract_governance_entities`)
  - `nl_query.py` – NL question → query-template mapping

- **Data**
  - Location: `data/`
  - Canonical CSVs in `data/resources/data/final_formalized/`
  - Loaded by `backend/scripts/load_seed_data.py`

Claude must NOT introduce new core frameworks (e.g., Django, Flask, full LangChain stack) or change this folder layout unless explicitly asked.

---

## Core Constraints

1. **No major structural changes**
   - Do NOT:
     - Move files between top-level folders.
     - Introduce new services or frameworks.
     - Split the app into microservices.
   - DO:
     - Add/modify functions and modules inside this existing structure.

2. **No dependency sprawl**
   - Do NOT:
     - Add heavy new dependencies (Kafka, Celery, Redis, etc.) without explicit request.
   - Prefer:
     - Standard Python + existing libs (FastAPI, Neo4j driver, Streamlit, Pandas, RapidFuzz, LLM SDK).

3. **Simplicity first**
   - Keep code simple and explicit.
   - Avoid complex class hierarchies, generic repositories, or over-engineered patterns.
   - Favor straightforward functions over “clever” abstractions.

4. **Minimal impact**
   - Only touch files necessary for the requested change.
   - Before editing more than 2–3 files, explain the plan and wait for user confirmation.

---

## How Claude Should Work

### 1. Plan First

For any non-trivial change (more than one function):

- Write a short plan (3–5 bullet points) describing:
  - Which files will change.
  - What functions/endpoints will be added/modified.
- Wait for user confirmation if the change spans multiple modules.

### 2. Focused Tasks

User will give **specific tasks**, e.g.:

- “Implement `GET /wards` in `backend/app/routers/wards.py` using an existing helper in `queries.py`.”
- “Create a Streamlit page that calls `/wards/{ward_id}/assets` and shows a table.”
- “Implement `extract_governance_entities(text)` in `ai_extraction.py` that returns JSON in a specific schema.”

Claude should:

- Stick to those files and functions.
- Avoid refactoring unrelated code.

### 3. Show Diffs Clearly

When modifying code:

- Show only the relevant snippets:
  - Indicate file path.
  - Provide updated code blocks.
- Avoid dumping the entire file when only a small part changed, unless requested.

---

## Verification Before “Done”

Claude should never consider a task “done” without explicit verification steps.

When completing a task, Claude should:

- Suggest how to run/check it, e.g.:
  - Backend:
    - `uvicorn backend.app.main:app --reload`
    - Test `/health` and the new endpoint.
  - Frontend:
    - `streamlit run frontend/app.py`
    - Navigate to the relevant page and confirm behavior.
  - Neo4j:
    - Run a simple Cypher query in Neo4j Browser to confirm nodes/relationships.

If tests or checks already exist, Claude should mention them and ensure they pass, but not invent a full CI setup.

---

## Things Claude MUST NOT Do

- Do NOT:
  - Change the overall architecture without being explicitly asked.
  - Introduce authentication, authorization, or user management.
  - Add new external services (message queues, separate databases, etc.).
  - Rewrite the project to use a different framework (Django, Flask, Next.js, etc.).
  - Perform large-scale “refactors” across many files near the deadline.

- Do NOT:
  - Remove or rename existing public endpoints without explicit instructions.
  - Change environment/config handling (`.env`, `config.py`) unless requested.

---

## Things Claude SHOULD Do

- Generate boilerplate that fits into the existing structure:
  - FastAPI routers and handlers.
  - Neo4j query helper functions.
  - Streamlit page code that calls existing endpoints.
- Implement specific functions/queries/endpoints from clear specs.
- Suggest small, incremental improvements:
  - Better error handling in a specific endpoint.
  - Clearer variable names or comments where helpful.
- Always consider:
  - “Is this the simplest working solution?”  
  - “Does this respect the project architecture and conventions?”

---

## Team Ownership (for context)

- **Sambhavi – Ontology & Data**
  - Owns: `data/`, ontology docs, Delivery Score definitions.
- **Aparna – Graph & Backend**
  - Owns: `backend/`, `scripts/load_seed_data.py`, Neo4j schema and queries.
- **Sreenu – AI & Frontend**
  - Owns: `frontend/`, `ai/`, Streamlit UI and LLM integration.

Claude should avoid making big changes in an area without that owner’s explicit prompt.

---
