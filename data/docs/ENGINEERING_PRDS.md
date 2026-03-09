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
- [x] `data/*.csv` present with:
    - [x] ≥5 full chains.
    - [x] No broken references.
- [x] Delivery Score formula + gap definitions written in README or a short doc.
- [x] Seed data loads cleanly into Neo4j (Person 2 confirms).

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
    *   Implement `scripts/load_seed_data.py` to ingest Person 1’s CSVs into Neo4j.
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
- [x] `uvicorn backend.app.main:app` runs locally.
- [x] Seed data loads via script without errors.
- [x] All 4 GET endpoints return valid JSON and pass basic tests.
- [x] `POST /ingest/entities` correctly creates/links at least one AI-ingested asset/event and can be seen in queries.

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
    *   Create `frontend/app.py` and `frontend/pages/`:
        *   `01_🏙_Ward_Map.py`:
            *   Calls `GET /wards`.
            *   Shows ward(s) in a table or basic map-like view.
            *   Clicking a ward sets selected ward in session state.
        *   `02_🧷_Proof_Chain.py`:
            *   Uses selected ward to call `GET /wards/{ward_id}/assets`.
            *   Shows list of assets; click asset → call `GET /assets/{asset_id}/chain`.
            *   Renders chain as:
                *   Scheme, actors, region, beneficiaries.
                *   Before/after evidence images.
                *   Simple timeline or bullet-chain.
        *   `03_❓_Questions.py`:
            *   Text input + 3 buttons for fixed questions:
                *   “What was built in Ward X?”
                *   “For Gali Y, show full delivery chain.”
                *   “Which schemes have low delivery scores?”
            *   Map each button/question to a predefined call to backend queries.
            *   Display answers with a short explanation and (if possible) a mini chain/graph view.
        *   `04_⚡_Live_Ingestion.py`:
            *   **Input**: Text area for reports OR a **News URL**.
            *   **The "Evidence Trick"**: If a URL is provided, scrape the text using the **`newspaper3k`** library (more robust than requests).
            *   **Verification Agent**: AI must check the scrappings against the Graph. (e.g., "MCD says Drain cleaned? News confirms? Yes/No").
            *   **UI Result**: Show a "Verified by AI" badge next to the asset once ingested.
            *   “Ingest” button: call `POST /ingest/entities`.
            *   Then re-call relevant GET endpoints to show updated state.
*   **Backend integration**
    *   Use `requests` or `httpx` to call FastAPI endpoints.
    *   Handle loading and error states cleanly (spinners, messages).
*   **AI extraction module**
    *   Implement `ai/ai_extraction.py`:
        *   Function: `extract_governance_entities(text: str) -> dict`
        *   Calls chosen LLM API with a prompt that asks for JSON with fields: schemes, regions, assets, events, actors, evidence references.
        *   Parses and validates JSON.
        *   Cache the response for the main demo text in a local file so you can bypass the LLM in offline mode.
*   **NL query routing**
    *   Implement `ai/nl_query.py`:
        *   For MVP, handle only 3 query patterns:
            *   Ward summary, gali chain, scheme gaps.
        *   Either:
            *   Use simple string matching/regex to decide which call to make, or
            *   Use LLM to classify into one of `{WARD_SUMMARY, GALI_CHAIN, SCHEME_GAPS}` and extract ward/street names.
        *   In Streamlit “Questions” page, call `nl_query` and then the appropriate backend endpoint.
*   **Demo polish**
    *   Ensure UI is clean, with:
        *   **Tagline**: "PRAMAAN: Tracing Government Promises to Ground Reality".
        *   **Visual Delivery Score**: Show a gauge or progress bar for Ward performance (e.g., Karol Bagh: 63% ██████████░░░░░░).
        *   Consistent colors and fonts.
        *   **Prioritization**:
            *   **Must-Have**: Seed data, Neo4j, Ward assets, Proof chain, Delivery Score.
            *   **Nice-to-Have**: Automated news verification, full LLM query routing (fixed buttons are a safe fallback).
        *   Make the 3–4 minute demo path obvious:
            *   Ward → assets → one chain → question → live ingestion.

**4. Acceptance criteria**
- [x] `streamlit run frontend/app.py` runs locally.
- [x] From UI, user can:
    - [x] See ward(s) and Delivery Score.
    - [x] Click asset and view full chain with images.
    - [x] Trigger each of the 3 fixed questions and see correct responses.
    - [x] Paste demo PIB text, see extracted entities, ingest, and see updated data.
- [x] LLM dependency is optional at demo time (thanks to cached responses).
