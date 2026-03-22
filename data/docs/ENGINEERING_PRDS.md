# PRAMAAN MVP Engineering PRDs

## PRD 1 – Ontology & Data Lead (Person 1)

**1. Objective**
Design and populate a clean, governance-focused ontology and seed dataset for 1 Delhi ward, enabling full delivery chains and the core queries for PRAMAAN’s MVP.

**2. Scope**
- Ontology refinement (for MVP slice)
- Data sourcing and curation for 1 ward
- Delivery Score definition
- Support for AI extraction and ingestion

**3. Responsibilities**

*   **Ontology (MVP subset)**
    *   Finalize the subset of entities and relationships we will actually implement now:
        *   Entities: Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event
        *   Relationships: funds, targets, benefits, located_in, built_by, represents, implements, proves, captured_at, lives_in, related_to
    *   Define required properties per entity for MVP (e.g., for Asset: id, name, type, ward_id, street_name, lat, lon, cost, start_date, end_date, **status** [planned, in_progress, completed]).
*   **Ward & chain selection**
    *   Choose one Delhi ward with enough public information and plausible data (even if some values are approximated/annotated).
    *   Identify 5 physical assets in that ward (roads, drains, lights, etc.).
    *   For each asset, construct complete delivery chains:
        *   Scheme → Actor(s) → Asset → Region (ward + gali) → Evidence (before & after).
*   **Seed data creation**
    *   Create CSV files in `/data`:
        *   `regions.csv`
        *   `schemes.csv`
        *   `actors.csv`
        *   `assets.csv`
        *   `beneficiaries.csv`
        *   `evidence.csv`
        *   `events.csv` (if needed)
    *   Ensure referential integrity (IDs line up across files) and consistent naming/IDs.
*   **Delivery Score & gaps logic**
    *   Define a simple, explainable Delivery Score formula, e.g.:
        *   `DeliveryScore(ward) = (assets_with_full_chain / total_assets) × 100`
    *   **Full Chain Definition**: A chain is "Full" if it connects: **Scheme → Actor → Asset → Region → Evidence**. (Beneficiary is optional for MVP).
    *   Define Gap types:
            *   Scheme targeted to ward, but no asset.
            *   Asset with no evidence.
*   **Support for AI extraction**
    *   Provide one PIB/news text about the chosen ward/asset with annotated expected entities.
    *   Document the target JSON structure for extraction to align with CSV/ontology.

**4. Acceptance criteria**
- [x] Ontology table (entities, properties, relationships) documented and agreed by team.
- [x] `data/resources/data/final_formalized/*.csv` present with:
    - [x] ≥5 full chains (drain, road, toilet, housing, streetlight).
    - [x] No broken references.
- [x] Delivery Score formula + gap definitions written in README or a short doc.
- [x] Seed data loads cleanly into Neo4j via `backend/scripts/load_seed_data.py`.
> ✅ **PRD 1 Complete** — Mar 19, 2026

---

## PRD 2 – Graph & Backend Lead (Person 2)

**1. Objective**
Implement the Neo4j graph + FastAPI backend that powers all MVP features: ward overview, proof chains, gaps, and ingestion.

**2. Scope**
- Neo4j schema & data loading
- Core Cypher queries
- FastAPI endpoints for querying & ingestion
- Basic caching/performance

**3. Responsibilities**

*   **Neo4j setup and schema**
    *   Set up a local Neo4j instance.
    *   Implement schema creation:
        *   Labels: Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event.
        *   Constraints: unique IDs per entity type, indexes on `ward_id`, `street_name` where useful.
    *   Implement `backend/scripts/load_seed_data.py` to ingest Person 1's CSVs into Neo4j.
*   **Core Cypher queries**
    *   Implement parameterized queries for MVP:
        *   **Q1_WardAssets**: given `ward_id`, return all assets with their schemes, actors, evidence presence flags, and beneficiary counts.
        *   **Q2_AssetChain**: given `asset_id`, return full chain:
            *   Scheme(s), actors, region, beneficiaries, evidence (before/after).
        *   **Q3_WardGaps**: given `ward_id`, return:
            *   Schemes targeted to ward without assets.
            *   Assets without evidence.
        *   **Q4_WardScore**: compute Delivery Score per ward using Person 1’s formula.
        *   **Q5_GaliAssets**: given `street_name`, return all assets and their status for that specific street/gali.
*   **FastAPI service**
    *   Create backend/app with:
        *   `neo4j_client.py` – manages driver and sessions.
        *   `queries.py` – wraps Cypher queries into Python functions.
        *   `models.py` – Pydantic schemas for responses.
        *   `main.py` + `routers/` with endpoints:
            *   `GET /health` – returns OK.
            *   `GET /wards` – returns list of wards + Delivery Scores.
            *   `GET /wards/{ward_id}/assets` – returns assets + schemes + evidence flags.
            *   `GET /assets/{asset_id}/chain` – returns full chain.
            *   `GET /wards/{ward_id}/gaps` – returns gap info.
            *   `GET /streets/{street_name}/assets` – returns assets for a specific gali.
            *   `POST /ingest/entities` – receives JSON (entities/relations) from AI and writes to Neo4j.
*   **Ingestion support**
    *   In `POST /ingest/entities`:
        *   Upsert nodes and relationships following the ontology.
        *   Ensure no duplicate IDs (generate new IDs if AI didn’t provide).
        *   Provide a small test JSON example for Person 3.
*   **Performance & robustness**
    *   Ensure hero queries return in <3 seconds on the seed dataset.
    *   Handle errors gracefully (no crashes if ward or asset not found).

**4. Acceptance criteria**
- [x] `uvicorn backend.app.main:app --reload` runs locally.
- [x] Seed data loads via `backend/scripts/load_seed_data.py` without errors.
- [x] All core GET endpoints return valid JSON (wards, assets, chain, gaps, score).
- [x] `POST /ingest/entities` correctly creates/links AI-ingested assets/events in Neo4j.
- [x] 8 routers implemented: wards, assets, ingest, questions, scrape, notifications, govdata, beneficiaries.
> ✅ **PRD 2 Complete** — Mar 19, 2026
> ⚠️ **Open items:** `DELETE /ingest/demo-nodes` and `POST /assets/{id}/set-verified` endpoints still missing (→ 404)

---

## PRD 3 – AI & Frontend Lead (Person 3)

**1. Objective**
Build the Streamlit UI and AI integration that make PRAMAAN feel intelligent and demo-ready: ward view, proof-chain view, question interface, and live ingestion.

**2. Scope**
- Streamlit app with 4 pages
- Client integration with FastAPI endpoints
- LLM-based entity extraction for one sample text
- Simple NL query routing for 3 questions

**3. Responsibilities**

*   **Streamlit app structure**
    *   `frontend/app.py` — global CSS, branding, page config.
    *   `frontend/pages/01_Ward_Map.py` — ward overview, delivery score gauge, asset table, Folium map.
    *   `frontend/pages/02_Proof_Chain.py` — asset selector, full proof chain (Scheme→Actor→Asset→Evidence→Beneficiary), before/after photos, financial tracker.
    *   `frontend/pages/03_Live_Ingestion.py` — auto-search news, AI entity extraction (Groq), one-click Neo4j ingestion, voice input.
    *   `frontend/pages/04_Micro_Accountability.py` — WhatsApp/SMS notifications via Twilio for verified assets.
*   **Backend integration**
    *   Use `requests` or `httpx` to call FastAPI endpoints.
    *   Handle loading and error states cleanly (spinners, messages).
*   **AI extraction module**
    *   `ai/llm_extractor.py` — `extract_governance_entities(text: str) -> dict` using Groq (llama-3.3-70b).
    *   Parses and validates JSON. MD5 cache for offline demo mode.
*   **NL query routing**
    *   `ai/nl_query.py` — routes 3 fixed query patterns (ward summary, proof chain, gap analysis) plus custom Cypher via LLM.
*   **Demo polish**
    *   **Tagline**: "PRAMAAN: Tracing Government Promises to Ground Reality".
    *   Visual Delivery Score gauge, glassmorphism cards, consistent dark-theme colors.
    *   Demo path: Ward Map → Proof Chain → Live Ingestion → Micro Accountability.

**4. Acceptance criteria**
- [x] `streamlit run frontend/app.py` runs locally.
- [x] From UI, user can:
    - [x] See Ward 45 delivery score + asset breakdown (01_Ward_Map.py — 1,066 lines).
    - [x] Select asset and view full proof chain with before/after images (02_Proof_Chain.py — 1,720 lines).
    - [x] Auto-search news, extract entities with AI, and ingest to Neo4j (03_Live_Ingestion.py — 390 lines).
    - [x] Trigger WhatsApp/SMS notifications for verified assets (04_Micro_Accountability.py — 285 lines).
- [x] LLM dependency is optional (Groq API with MD5 cache for offline demo).
- [x] Voice input utility added (`frontend/utils/voice_input.py`).
> ✅ **PRD 3 Complete** — Mar 19, 2026
