# PRAMAAN v5 — Implementation Guide
**Last Updated:** 2026-03-25 · Branch: `feature/global-ontology-engine-v3`

---

## 🎯 What is PRAMAAN?

**Tagline:** *"From Events to Evidence — Making Governance Verifiable in Real Time"*

PRAMAAN is an **India Governance Intelligence & Proof System** that connects:
1. **National Events** (crises, policies) →
2. **Government Responses** (schemes triggered) →
3. **Ground-Level Delivery** (assets, beneficiaries) →
4. **Evidence & Proof** (photos, data sources) →
5. **Citizen Notifications** (WhatsApp alerts — mock in MVP)

It builds a **living proof chain** in a Neo4j knowledge graph, proving whether government schemes actually reached the ground.

---

## 🏗️ Architecture — 5 Layers

| Layer | What it Does | Neo4j Pattern |
|---|---|---|
| **1. Events** | 17 events across 7 domains (Climate, Economics, Defense, Technology, Society, Governance, Geopolitics) | `(Event)-[:CONNECTED_TO]->(Event)` |
| **2. Response** | Gov schemes: Type 1 (event-triggered: SDRF/NDRF) + Type 2 (ongoing: AMRUT, PMAY, PLI, etc.) | `(Event)-[:TRIGGERED]->(Response)` |
| **3. Delivery** | Delhi pilot — AMRUT drainage + PMAY housing with real data.gov.in data | `(Scheme)-[:FUNDS]->(Asset)-[:LOCATED_IN]->(Region)` |
| **4. Evidence** | Before/after photos, PIB press releases, data.gov.in records | `(Asset)-[:HAS_EVIDENCE]->(Evidence)` |
| **5. Citizen** | Mock WhatsApp notification card (MVP only) | `(Citizen)-[:RECEIVES]->(Notification)` |

---

## 🖥️ Tech Stack

| Component | Technology |
|---|---|
| Graph Database | Neo4j 5.18 (Docker or local) |
| Backend API | FastAPI (Python) — port 8000 |
| Frontend | Streamlit — port 8501 |
| AI / Insights | Groq (LLaMA 3.3 70B) + Google Gemini fallback |
| Data Sources | data.gov.in, PIB, NDMA, ISRO, IMD |
| Deployment | Docker Compose (Neo4j) |

---

## 📂 Project Structure

```
Pramaan/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app (auto-seeds graph on startup)
│   │   ├── config.py            # Settings from .env (pydantic-settings)
│   │   ├── neo4j_client.py      # Neo4j driver with auto-reconnect
│   │   ├── queries.py           # Cypher query library
│   │   ├── models.py            # Pydantic data models
│   │   ├── routers/
│   │   │   ├── ontology.py      # Graph CRUD + ontology endpoints
│   │   │   ├── scrape.py        # News scraping endpoints
│   │   │   └── ingest.py        # Data ingestion endpoints
│   │   └── services/
│   │       ├── ai_service.py          # Groq/Gemini LLM calls
│   │       ├── entity_resolver.py     # Entity dedup/resolution
│   │       ├── news_service.py        # News fetching
│   │       ├── scheduler.py           # Background task scheduling
│   │       └── verification_agent.py  # Evidence verification
│   └── scripts/
│       ├── load_ontology.py     # Seeds Neo4j graph from seed data
│       ├── load_govdata.py      # Loads data.gov.in datasets
│       └── setup_constraints.py # Neo4j index/constraint setup
├── frontend/
│   ├── main_app.py              # Streamlit entry (Home + navigation)
│   └── pages/
│       ├── 01_National_Intelligence.py  # Events map + ontology graph
│       ├── 02_Scheme_Tracker.py         # Type1/Type2 scheme panels
│       ├── 03_Delivery_Monitor.py       # Delhi pilot delivery chain
│       └── 04_Proof_and_Evidence.py     # Evidence, trust layer, citizen mock
├── data/                        # Datasets (structured, semi, unstructured)
├── config/pipeline_config.yaml  # Agentic ingestion pipeline config
├── docker-compose.yml           # Neo4j container definition
├── .env                         # Environment variables (secrets)
└── requirements.txt             # Python dependencies
```

---

## 🔑 Environment Variables — Status Check

| Variable | Status | Notes |
|---|---|---|
| `NEO4J_URI` | ✅ Set | `bolt://localhost:7687` |
| `NEO4J_USER` | ✅ Set | `neo4j` |
| `NEO4J_PASSWORD` | ✅ Set | `pramaa2026` (matches docker-compose) |
| `GROQ_API_KEY` | ✅ Set | Active key present |
| `GOOGLE_API_KEY` | ✅ Set | Gemini fallback key present |
| `DATA_GOV_API_KEY` | ✅ Set | data.gov.in API key present |
| `TWILIO_ACCOUNT_SID` | ✅ Set | Active SID |
| `TWILIO_AUTH_TOKEN` | ✅ Set | Active token |
| `TWILIO_FROM_NUMBER` | ⚠️ Check | `.env` has `+14155238886` but `env.example` expects `whatsapp:+14155238886` prefix |
| `TAVILY_API_KEY` | ✅ Set | For agentic web search (extra — not in env.example) |
| `API_BASE_URL` | ✅ Set | `http://localhost:8000` |
| `PRAMAAN_ENV` | ✅ Set | `development` |

> **⚠️ Action Item:** Verify if Twilio number needs `whatsapp:` prefix for WhatsApp sandbox functionality.

---

## 🚀 Startup Sequence

### Step 1: Start Neo4j
```bash
docker-compose up -d
```
> Neo4j available at: http://localhost:7474 (browser) / bolt://localhost:7687 (driver)

### Step 2: Start Backend (FastAPI)
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
> On first start, backend auto-seeds the graph if fewer than 5 nodes exist.

### Step 3: Start Frontend (Streamlit)
```bash
cd frontend
streamlit run main_app.py
```
> Frontend at: http://localhost:8501

---

## 📺 UI Screens (5 Pages)

| # | Screen | Purpose |
|---|---|---|
| 0 | **Home** | Landing — animated logo, countUp stats (Funds, Verified Assets, Evidence, Events), "Launch PRAMAAN" CTA |
| 1 | **National Intelligence** | Event map / ontology graph (7 domains, 17 events), cross-domain edges, live ingestion feed |
| 2 | **Scheme Tracker** | Type 1 (Event Response) + Type 2 (Implementation) scheme panels, decision engine |
| 3 | **Delivery Monitor** | Delhi pilot: AMRUT drainage + PMAY housing, scheme→ward→asset chain |
| 4 | **Proof & Evidence** | Evidence per asset, PIB/ISRO/NDMA sources, trust layer, citizen WhatsApp mock |

---

## 📊 Key Data Points

- **17 Events** across **7 Domains**
- **Delhi Pilot:** AMRUT (3 drainage projects, 2 complete / 1 in-progress, ₹5.38 Cr) + PMAY (17,067 houses, 100% complete, ₹401.79 Cr)
- **Real Data Sources:** 19 datasets from data.gov.in covering all events
- **Evidence Types:** Before/after photos, PIB releases, data.gov.in records, ISRO/NDMA sources
- **Trust Layer:** Every node has `source` + `confidence` (high/medium/low)

---

## 🔧 What We Are Implementing (v3 Branch)

### Current Status
- [x] Neo4j started and connected (Docker — port 7474/7687)
- [x] Backend running on port 8000 (`/health` → ok)
- [x] Frontend running on port 8501
- [x] Graph seeded with ontology data (15,341 nodes, 16,958 edges)
- [x] `backend/.env` synced with all API keys (GROQ, Gemini, Tavily, data.gov.in)
- [ ] All 5 UI screens functional — needs visual verification
- [ ] Live ingestion feed working
- [ ] Evidence verification operational

### Graph Stats (from `/stats`)
| Metric | Value |
|---|---|
| Events | 27 |
| Actors | 49 |
| Evidence Nodes | 10 |
| Schemes | 8 |
| Assets | 1,661 |
| Verified Assets | 1,439 |
| Total Nodes | 15,341 |
| Total Edges | 16,958 |
| Funds Tracked | ₹0 Cr (needs budget_crore property on Scheme nodes) |

### Progress Log
| Date | Action | Status |
|---|---|---|
| 2026-03-25 | Branch `feature/global-ontology-engine-v3` created from v2 | ✅ Done |
| 2026-03-25 | PRD v5 reviewed, Guide created | ✅ Done |
| 2026-03-25 | Neo4j, Backend, Frontend started & verified | ✅ Done |
| 2026-03-25 | `backend/.env` updated with all API keys | ✅ Done |

---

*This guide will be continuously updated as we implement and verify each component.*
