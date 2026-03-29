# PRAMAAN v5 – Architecture Overview
> Last updated: March 24, 2026

## 1. Project Summary

**PRAMAAN v5** – *India Governance Intelligence & Proof System* – is an AI-powered knowledge graph platform that:

- Connects 17 national events across 7 domains to government responses, scheme delivery, and ground-level proof.
- Builds a 5-layer proof chain: Event → Response → Scheme → Asset → Evidence.
- Provides a **FastAPI** backend over a **Neo4j** graph.
- Exposes a **Streamlit** UI across 5 screens (Home + 4 pages).

The MVP demonstrates the full proof chain with a Delhi pilot (AMRUT + PMAY, anchored to Delhi Yamuna Floods 2023), demoing at India Innovates 2026.

---

## 2. High-Level Architecture

```
data.gov.in / PIB / NDMA / ISRO / IMD
        ↓ (fetch scripts + agentic ingestion)
   Neo4j Knowledge Graph
        ↓ (FastAPI REST)
   Streamlit UI  ←→  FastAPI  ←→  Neo4j
```

**8 Node Types:** Domain · Event · Response · Scheme · Actor · Asset · Region · Evidence

**Key Relationship Types:** CONNECTED_TO · TRIGGERED · FUNDS · LOCATED_IN · HAS_EVIDENCE · BUILT_BY · BENEFITS

---

## 3. 5-Layer Proof Chain

```
Layer 1: Events (17 events, 7 domains)
    ↓ [:TRIGGERED]
Layer 2: Government Response
    Type 1 — Event-triggered: SDRF, NDRF
    Type 2 — Ongoing: AMRUT, PMAY, PLI, Ayushman, SVANidhi, SBM
    ↓ [:FUNDS]
Layer 3: Delivery (Delhi pilot)
    Scheme → Asset → Region
    ↓ [:HAS_EVIDENCE]
Layer 4: Evidence
    Photo (if available) | Data proof (data.gov.in)
    ↓
Layer 5: Citizen (mock UI — production-ready design)
```

---

## 4. Tech Stack

| Layer | Technology |
|-------|-----------|
| Graph DB | Neo4j 5.18 (Docker, local) |
| Backend | FastAPI + Uvicorn + Neo4j Python Driver |
| Frontend | Streamlit + streamlit-agraph + Plotly |
| AI / NLP | Groq API (llama-3.3-70b-versatile) |
| News Scraping | Google News RSS + PIB RSS |
| Data | data.gov.in API (19 datasets) |
| Config | pydantic-settings + python-dotenv |
| Environment | Local dev + Docker (Neo4j only) |

---

## 5. Repository Structure

```
Pramaan/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint + /stats + /health
│   │   ├── config.py            # Neo4j + Groq + app config
│   │   ├── neo4j_client.py      # Neo4j driver + session helpers
│   │   ├── models.py            # Pydantic request/response models
│   │   ├── queries.py           # Cypher query helpers
│   │   ├── routers/
│   │   │   ├── ontology.py      # /ontology/events, /domains, /graph, /cross-domain
│   │   │   └── scrape.py        # /scrape/news, /scrape/analyze
│   │   ├── services/
│   │   │   ├── ai_service.py    # Unified LLM extraction (Groq primary, Gemini fallback)
│   │   │   ├── news_service.py  # Google News RSS scraping
│   │   │   ├── scheduler.py     # APScheduler for daily ingestion job
│   │   │   ├── verification_agent.py  # Evidence verification + trust scoring
│   │   │   └── entity_resolver.py     # Static + fuzzy entity ID resolution
│   │   └── utils/
│   │       └── retry.py
│   └── scripts/
│       ├── load_ontology.py     # Seeds Neo4j from seed_graph.json
│       ├── load_govdata.py      # Loads govdata JSONs into Neo4j
│       └── setup_constraints.py # Neo4j uniqueness constraints + indexes
│
├── frontend/
│   ├── main_app.py              # Streamlit entrypoint + Home screen (5 screens)
│   ├── pages/
│   │   ├── 01_Intelligence_Map.py   # National Intelligence — 17 events, live feed
│   │   ├── 02_Ontology_Graph.py     # Scheme Tracker — Type 1/2 schemes, decision panel
│   │   ├── 03_Live_Feed.py          # Delivery Monitor — Delhi pilot, AMRUT + PMAY
│   │   └── 04_Decision_Brief.py     # Proof & Evidence — photos, data proof, trust layer
│   ├── components/
│   │   └── topnav.py            # Shared top navigation
│   ├── utils/
│   │   ├── events.py            # CRITICAL: single source of truth for all 17 events
│   │   ├── api.py               # safe_get() wrapper for backend calls
│   │   ├── constants.py         # Shared constants
│   │   ├── icons.py             # Icon mappings
│   │   ├── session.py           # Streamlit session state helpers
│   │   ├── voice_input.py       # Voice input (bonus feature)
│   │   └── geo_selector.py      # Geographic selector helpers
│   └── static/
│       └── evidence/            # Before/after delivery photos (18 images)
│
├── agent/
│   ├── classifier.py            # Gemini-powered source classifier (3-path routing)
│   ├── loader.py                # Downstream sweeper → FastAPI ingest
│   ├── tools.py                 # Tool definitions for 3-path pipeline
│   ├── search_queries.py        # Priority + domain queries for daily_job
│   └── relevance_filter.py      # Relevance scoring (Validation Gate 1)
│
├── data/
│   ├── config/
│   │   └── govdata_registry.json    # Central registry — 24 datasets, all 17 events mapped
│   ├── resources/
│   │   ├── ontology/
│   │   │   ├── seed_graph.json      # CRITICAL: all 17 events + 7 domains + schemes
│   │   │   └── govdata_nodes.json   # Govdata-specific node definitions
│   │   ├── structured/govdata/      # 19 fetched real government datasets
│   │   └── unstructured/raw/        # PIB/ISRO/NDMA evidence text files
│   └── scripts/
│       ├── fetch_govdata.py         # Fetches datasets from data.gov.in
│       ├── fetch_unstructured.py    # Fetches unstructured sources
│       ├── transform.py             # Data transformation utilities
│       ├── validate_ontology.py     # Validates seed_graph.json before loading
│       └── pipeline.py              # Main ETL pipeline
│
├── .claude/                     # AI context files
├── docker-compose.yml           # Neo4j 5.18 local setup
├── requirements.txt
├── run_agent.py                 # APScheduler daily ingestion job
└── README.md
```

---

## 6. Key Data Flows

### Flow 1 — Seed Data (JSON → Neo4j)
```
data/resources/ontology/seed_graph.json
    → backend/scripts/load_ontology.py
    → Neo4j (MERGE nodes + relationships)
```

### Flow 2 — Govdata (data.gov.in → Neo4j)
```
data/config/govdata_registry.json
    → data/scripts/fetch_govdata.py (API fetch)
    → data/resources/structured/govdata/*.json
    → backend/scripts/load_govdata.py
    → Neo4j
```

### Flow 3 — UI Query (Streamlit → FastAPI → Neo4j)
```
frontend/pages/*.py
    → safe_get("http://localhost:8000/...")
    → backend/app/routers/*.py
    → Neo4j Cypher
    → JSON → rendered in Streamlit
```

### Flow 4 — Live Ingestion (News → AI → Neo4j)
```
run_agent.py daily_job() / button trigger
    → agent/classifier.py (route source)
    → backend/app/services/news_service.py (RSS)
    → backend/app/services/ai_service.py (Groq extraction)
    → POST /ingest/entities → Neo4j
    → UI refresh
```

---

## 7. Environment Setup

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pramaa2026
GROQ_API_KEY=your_groq_key_here
DATA_GOV_API_KEY=your_datagov_key_here
GOOGLE_API_KEY=your_google_key_here
```

```bash
docker-compose up -d
python backend/scripts/load_ontology.py
python backend/scripts/load_govdata.py
uvicorn backend.app.main:app --reload
streamlit run frontend/main_app.py
```
