# Implementation Plan: Pramaan V5 Dynamic Transformation

# Implementation Plan: 10/10 Master Architecture (True Agentic Graph)

# Implementation Plan: Pramaan V5 Demo Survival Protocol

## Phase 0: Initialization
1. **Branch Management:** Run `git checkout -b feature/v5-demo-safe` before executing any operations to protect the [main](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/main_app.py#191-207) branch.

## Phase 1: Database Purge
1. **Graph Cleanup:** Execute `DETACH DELETE` in Neo4j to permanently remove the 4 hollow events: `EVT_MANIPUR_2023`, `EVT_JOSHIMATH_2023`, `EVT_IMEC_2023`, and `EVT_TATA_SEMI_2024`.
2. **UI Cleanup:** Safely remove these exact 4 events from the `EVENTS` map in [frontend/utils/events.py](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/utils/events.py) so they vanish from the dropdowns and the map.

## Phase 2: Structured Demo Seeding
*We will not use the live web scraper. We will strictly control the data to ensure the 10 AM demo is visually perfect and error-free.*
1. **Neo4j Seed Script:** Write a targeted Python script to inject 2 massive new 2026 events (e.g., "India Semiconductor Mission" and "Rupee Crisis") directly into the Graph with perfect canonical nodes and edges.
2. **Curated Intelligence Tying:** Safely append these 2 new event IDs to the existing 400 lines of curated dictionaries (`NEEDS_MAP`, `WATCH_POINTS`, `CROSS_PAIRS`) inside [national_intelligence.py](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/pages/national_intelligence.py). This guarantees the dashboard tabs light up flawlessly for the new events without breaking the architecture.
3. **Map Tying:** Safely add the GPS coordinates for the 2 new events to the `MAP_EVENTS` array in [events.py](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/utils/events.py).

## Phase 3: Final Verification & PRD
- Verify the map renders perfectly, tabs display rich curated intelligence, and the 4 hollow events are completely gone.
- Write the V5 PRD documenting the current robust demo state (including the blast score engine and scheme beneficiary models).

---

# Agentic Ingestion Pipeline — Implementation

## Overview

The Live Ingestion screen is backed by a fully implemented **3-path agentic ingestion pipeline**. The agent acts as a **classifier and router** — it does not do deep extraction itself. A deterministic downstream sweeper (`agent/loader.py`) handles extraction, schema mapping, and Neo4j writes.

## Components Built

| File | Role |
|------|------|
| `agent/classifier.py` | Main agent entry — Gemini 1.5 Flash function calling, classifies input topics |
| `agent/tools.py` | Tool definitions — async Crawl4AI scraper, API fetcher |
| `agent/loader.py` | Downstream sweeper — scans raw folders, calls ai_service, commits to Neo4j |
| `run_agent.py` | APScheduler daemon — 24h default, configurable |
| `backend/app/routers/agentic.py` | FastAPI endpoint `POST /ingest/agentic` — wires UI to agent |
| `backend/app/services/ai_service.py` | `extract_ontology()` — canonical node/edge extraction |
| `backend/app/services/verification_agent.py` | Confidence scoring on extracted entities |
| `backend/app/services/scheduler.py` | APScheduler integration for auto-ingestion |

## 3-Path Pipeline

### Path 1 — Structured (API / tabular)
- **Input:** REST API (data.gov.in, RBI, ISRO) or CSV/JSON URL
- **Tools:** `requests`, `pandas`, `pydantic`
- **Flow:** Agent fetches → saves to `/data/structured/raw/` → loader maps schema → Neo4j

### Path 2 — Semi-Structured (PDF / XML / Excel / KML)
- **Input:** Files in `/inbox/` dropzone or agent-fetched
- **Tools:** `PyMuPDF`, `lxml`, `openpyxl`, `markdown`, `fastkml`
- **Flow:** Agent routes → saves to `/data/semi_structured/raw/<type>/` → loader extracts → Neo4j

### Path 3 — Unstructured (Web docs / press releases)
- **Input:** URL or topic string
- **Tools:** **Crawl4AI** (async headless JS → Markdown) + **Firecrawl** fallback
- **Flow:** Agent scrapes → saves to `/data/unstructured/raw/` → loader chunks + extracts via `ai_service.extract_ontology()` → Neo4j → archived to `/processed/`

## Ingestion Trigger Flow

```
UI: Run Agent button / Auto-Scheduler (15m/1h/6h/24h)
        ↓
POST /ingest/agentic {topic: "..."}
        ↓
classifier.py → classify_and_route() → {source_type, fetch_method, destination}
        ↓
tools.py → fetch/scrape → save raw file
        ↓
loader.py → ai_service.extract_ontology() → nodes[] + edges[]
        ↓
Neo4j MERGE (constraints + indexes) → UI feed refresh
```

## Data Lake Structure

```
data/
├── structured/
│   ├── raw/            ← API JSON responses (data.gov.in, RBI, ISRO)
│   └── processed/      ← Schema-mapped canonical files
├── semi_structured/
│   ├── raw/
│   │   ├── pdf/        ← Ministry reports, NDMA bulletins
│   │   ├── kml/        ← Geo overlays
│   │   ├── xml/        ← PIB feeds
│   │   └── md/         ← Markdown documents
│   └── processed/
└── unstructured/
    ├── raw/            ← Crawl4AI markdown output
    └── processed/      ← Entity-extracted + archived
inbox/                  ← Manual file drop zone
```

## MVP vs Production

| Aspect | MVP (Demo) | Production |
|--------|-----------|------------|
| Topics | 8 curated demo topics | Live PIB, NDMA, data.gov.in, IMD |
| Scheduler | Manual + 15m–24h timer | Continuous 24h daemon |
| Crawl4AI | Integrated, tested | Full JS-SPA scraping |
| Gemini classifier | Function calling, working | Same — scale to Claude 3 |
| Neo4j writes | MERGE with dedup | Same + conflict resolution |
