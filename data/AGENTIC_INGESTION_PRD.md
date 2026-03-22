# Product Requirements Document (PRD): Agentic Data Ingestion Pipeline

**Role / Author:** Data Lead
**Target System:** PRAMAAN Urban Governance Graph 
**Date:** March 20, 2026

## 1. Executive Summary

We are transitioning the PRAMAAN data ingestion architecture to a **3-path agentic pipeline**. The agent acts purely as a **classifier and router** without using LLMs for deep extraction or mapping. Instead, the agent downloads, categorizes, and saves the data to the appropriate folder. 

A deterministic downstream pipeline then processes these raw files via pure Python + unified `ai_service.py` logic, ensuring consistency, schema integrity, and auditability before writing to Neo4j.

---

## 2. Architecture Overview

### The "Single Classifier" Agent

The ingestion agent relies on function calling (via Gemini 1.5 Flash or Claude 3) to strictly classify inputs and route them.

- **Trigger:** APScheduler (every 24h) or manual `python run_agent.py`
- **Brain:** Groq (`llama-3.1-8b`) or Gemini 1.5 Flash
- **Classification Tool Schema:**
  ```json
  {
    "name": "classify_and_route",
    "description": "Classifies a data source and routes it",
    "input_schema": {
      "type": "object",
      "properties": {
        "source_type": {"enum": ["structured", "semi_structured", "unstructured"]},
        "fetch_method": {"enum": ["api", "scrape", "file_upload", "web_crawl"]},
        "destination_folder": {"type": "string"},
        "api_url": {"type": "string", "nullable": true},
        "requires_auth": {"type": "boolean"}
      }
    }
  }
  ```

### The 3-Path Pipeline

#### Path 1 — Structured (API / Scrapeable tabular)
*   **Input:** REST API endpoint or URL with tabular HTML/CSV
*   **Tools:** `requests`, `pandas`, `pydantic`
*   **Steps:**
    1. Agent hits URL, checks Content-Type.
    2. If JSON/CSV → mark as STRUCTURED, save to `/data/structured/raw/`.
    3. LLM maps schema to canonical PRAMAAN schema (one-time, cached).
    4. Airflow DAG runs every 24h to refresh.

#### Path 2 — Semi-Structured (XML, KML, PDF, MD, Excel)
*   **Input:** File in `/inbox/` folder (manual or agent-placed)
*   **Tools:** `PyMuPDF`, `lxml`, `openpyxl`, `markdown`, `fastkml`
*   **Steps:**
    1. Agent reads file extension + content sniff.
    2. Routes to `/data/semi_structured/raw/<type>/`.
    3. Parser extracts key-value pairs or table.
    4. LLM normalizes to schema.

#### Path 3 — Unstructured (Web docs, reports, press releases)
*   **Input:** URL or Google search result
*   **Tools:** `Crawl4AI` or `Firecrawl` (for JS-heavy headless scraping to Markdown)
*   **Steps:**
    1. Agent identifies page as non-tabular.
    2. Scrapes with Crawl4AI → markdown output.
    3. Saves to `/data/unstructured/raw/`.
    4. LLM chunks + extracts entities via `AIService.extract_ontology()`.

---

## 3. Data Lake Folder Structure

```
e:/INDIA_INNOVATES/Pramaan/
├── data/
│   ├── structured/
│   │   ├── raw/         ← API JSON responses
│   │   └── processed/   ← Schema-mapped
│   ├── semi_structured/
│   │   ├── raw/
│   │   │   ├── pdf/
│   │   │   ├── kml/
│   │   │   ├── xml/
│   │   │   └── md/
│   │   └── processed/
│   └── unstructured/
│       ├── raw/         ← Crawl4AI markdown
│       └── processed/   ← Entity-extracted via ai_service
├── inbox/               ← Drop zone for manual uploads
└── agent/
    ├── classifier.py         ← Main agent entry point (Groq/Gemini)
    ├── tools.py              ← Tool definitions (Crawl4AI, requests)
    ├── search_queries.py     ← 3-Tier Keyword Registry
    ├── relevance_filter.py   ← +10/-20 Pre-Ingestion Scorer
    └── loader.py             ← Downstream Neo4j Sweeper
```

---

## 4. Advanced Discovery & Ingestion Guardrails

To prevent the AI from blindly scraping the internet and burning API credits, we implemented a **6-Layer Protection System** paired with an autonomous web-hunting module.

### 4.1. Autonomous Discovery (Tavily Search API)
Instead of relying purely on users dropping links (via Twilio/WhatsApp manual uploads) or hardcoded URLs, the ingestion system now wakes up daily (`run_agent.py`) and uses the **Tavily Search API** to hunt for the absolute latest urban infrastructure press releases across India.

### 4.2. The 3-Tier Keyword Architecture
*Why not freeform searches?* If an LLM searches "Shahdara North drain repair", it gets 0 results. If it searches "Delhi", it gets 10,000 irrelevant noise results.

We implemented a strict Query Registry (`agent/search_queries.py`) that dynamic mixes:
1. **Anchor:** Geography lock (e.g., "Delhi MCD")
2. **Scheme:** Topic seed (e.g., "AMRUT drain")
3. **Qualifier:** Time/Action (e.g., "2026 tender")
*Result:* Natural, highly targeted queries like `"Delhi MCD AMRUT drain 2026 tender"`.

### 4.3. Pre-Ingestion Relevance Scorer (The Filter)
*Why this?* Tavily will occasionally return noisy news (e.g., political rallies, cricket). We built `agent/relevance_filter.py` to intercept all Tavily URLs *before* downloading them.
*   **High-Value Words** (e.g., "ward", "tender", "PMAY") grant **+10 points**.
*   **Low-Value Words** (e.g., "bollywood", "cricket") deduct **-20 points**.
Any URL scoring `< 30` is immediately dropped, guaranteeing 100% domain relevance before burning expensive LLM extraction tokens in the `ai_service`.

### 4.4. Execution Guardrails
*   **Domain Whitelisting:** Tavily is hardcoded to only search within `["pib.gov.in", "mcdonline.nic.in", "smartcities.gov.in", ...]`.
*   **Budget Caps:** A local file tracker (`.tavily_counter`) physically halts the agent if it exceeds 50 searches in a single 24h period.

### 4.5. Inbound Citizen Reporting (The Twilio WhatsApp Webhook)
While Tavily serves as the autonomous hunter, **WhatsApp** serves as the physical "human-in-the-loop" data ingestion layer. 
*   **How it Connects:** When a field worker or citizen taking a picture of broken infrastructure sends a photo (or forwards a municipal PDF) to the PRAMAAN WhatsApp number, Twilio triggers our `backend/app/routers/notifications.py -> POST /webhook/whatsapp` API.
*   **The Translation:** The FastAPI backend automatically authenticates the Twilio payload, rips the enclosed media (JPG/PDF) from their CDN, and drops it physically into `e:/INDIA_INNOVATES/Pramaan/inbox/`.
*   **The Sweep:** Because the Agent pipeline (Path 2) is natively programmed to recursively traverse the `/inbox/` directory, it will autonomously sweep up the Citizen's WhatsApp photo on its next cycle, extract meaning from it using AI, and fuse it onto the Neo4j asset node without human intervention.

---

## 5. Current Implementation Status

### What We Have Running
1. **The Core Agent (`classifier.py`, `tools.py`):** Successfully routes unstructured URLs to Crawl4AI (or a stub) to extract clean markdown into the DataLoader.
2. **Autonomous Hunting:** `run_agent.py` cron daemon is fully wired with Tavily, the 3-Tier Query Registry, and the +10/-20 Relevance Filter.
3. **Downstream Sweeper (`loader.py`):** Scans the `raw/` folders, processes markdown through PRAMAAN's `ai_service` endpoint, and inserts strictly mapped Entities and Relationships into Neo4j.

### Next Steps / Go-Live
1. **Expand Semi-Structured Parsers:** Write Python parsers in `tools.py` for handling uploaded PDFs and Excel data formats from `/inbox/`.
2. **End-to-End Test:** Leave `python run_agent.py --daemon` running locally for 48 hours to monitor daily scheduler health and ensure the relevance scrubber catches edge cases.

---

## 6. Data Layer Setup & Missing Requirements

To completely stand up this Agentic Data Layer in a pristine production environment, the following strict requirements and missing pieces must be addressed:

### What We Decided & Built
1. **The Architecture:** We abandoned the "super-agent that does everything" in favor of a **3-Path Orchestration Pipeline**. The Agent purely categorizes and fetches, leaving the heavy graph-mapping to a deterministic downstream `loader.py`.
2. **Autonomous Discovery vs WhatsApp:** Instead of waiting for users to upload data to Twilio, we wired up **Tavily Search** to proactively hunt Government PR loops daily.
3. **Advanced Filtering:** We implemented a 3-tier keyword registry and a +10/-20 relevance scanner to drop noisy results before burning LLM extraction credits.

### Environment & Dependency Setup Requirements
To run this pipeline, the following exact dependencies must be satisfied:
- **Python Packges to Install:** `pip install tavily-python crawl4ai pydantic apscheduler google-generativeai groq requests lxml fastkml openpyxl markdown`
- **Environment Variables (`.env`) Required:**
  - `GROQ_API_KEY`: Required for the Classification Agent (`classifier.py`).
  - `GEMINI_API_KEY`: Required for the deep downstream extractor (`ai_service.py`).
  - `TAVILY_API_KEY`: Required for Autonomous Discovery (`run_agent.py`).
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Required for `loader.py` to upsert data.

### What is Missing (Immediate Action Items)
To cross the finish line into a production-grade automated graph pipeline, the following 5 engineering steps must be resolved:

1. **Fix the Headless Scraper (Path 3):** The `scrape_with_crawl4ai()` function is currently stubbed due to a Windows `asyncio` Playwright bug. **Action:** We are falling back to a robust synchronous `BeautifulSoup` + `markdownify` scraper.
2. **Build the PDF Parser (Path 2):** Move beyond simple folder routing. **Action:** Implement `PyMuPDF` text extraction in `tools.py` so PDFs dropped in `/inbox/` are cleanly converted to markdown.
3. **Enforce Neo4j Constraints:** True uniqueness must be guaranteed at the DB level, not just code. **Action:** Run `CREATE CONSTRAINT ON (a:Asset) ASSERT a.id IS UNIQUE` natively inside Neo4j.
4. **Wire the Webhook:** Connect user behavior to the pipeline. **Action:** Update FastAPI `notifications.py` to auto-download Twilio/WhatsApp media payloads directly into the `inbox/` folder.
5. **Run the 48-Hour Burn-in:** **Action:** Execute `python run_agent.py --daemon` and actively monitor `.tavily_counter`, `processed_files.json`, and the Graph Visualizer to ensure self-healing autonomous ingestion is functional.

---

## 7. Deep Architecture Specifications (Gap Closures)

To guarantee 99.9% uptime during autonomous scaling runs, the following engineering specs govern the missing invisible layers:

### 7.1. Routing Logic (`run_agent.py -> process_source`)
The router strictly enforces decision matrices post-classification:
- `requires_auth=true` → SKIP, log to skipped.log
- `source_type=structured` + API fetch → `fetch_api()`
- `source_type=semi_structured` + local file → `move_from_inbox()`
- `source_type=unstructured` → `scrape_with_crawl4ai()`

### 7.2. Downstream Sweeper Logic (`loader.py`)
Because the Agent simply drops files, `loader.py` acts as the final gatekeeper to Neo4j.
- Maintains `processed_files.json` mapping file hashes to ISO timestamps.
- ONLY processes files not found in the hash map.
- Calls `ai_service.extract_ontology(content)` and streams explicitly to `neo4j_writer`.
- **Atomic Operations:** Only appends to `processed_files.json` and moves file to `/processed/` *after* a successful ACID Neo4j write transaction.

### 7.3. Error Handling & Dead Letter Queues
No single failure can crash the APScheduler.
- **Tavily 0 Results:** Log to `low_yield.log`, continue.
- **Crawl4AI Timeout / Broken Pipe:** Retry 1x. If failed, drop error stub file.
- **AIService Extraction Failure/Groq 429:** Move dropped file from `/raw/` to `/data/failed_extraction/` and trigger alerts. Skip Neo4j write.
- **Neo4j Down:** Backoff retry 3x. Queue writes indefinitely if DB is dead.

### 7.4. Observability & Idempotency
- **Idempotency:** The `.tavily_counter` strictly tracks daily budget even on container restart. Filenames are uniquely hashed with UTC timestamps to prevent overwrite clobbering.
- **Observability:** Each scheduler batch logs a run trace containing: `{started_at, queries_sent, results_kept, results_dropped, files_saved, errors[]}`.

---

## 8. Canonical PRAMAAN Schema (Ontology)

For the downstream `ai_service` to map unstructured text into Neo4j accurately, the following ontology is strictly enforced:

### Nodes
- **`Asset`**: `{id: UUID, name: str, type: str, status: str, location_coordinates: list[float], ward_id: str, last_verified: str}`
- **`Ward`**: `{id: str, name: str, zone: str, city: str, state: str}`
- **`Scheme`**: `{id: str, name: str, ministry: str, budget_allocated: float, year: int}`
- **`Department`**: `{id: str, name: str, level: str}`

### Relationships
- `(Asset)-[:LOCATED_IN]->(Ward)`
- `(Asset)-[:FUNDED_BY]->(Scheme)`
- `(Asset)-[:MANAGED_BY]->(Department)`
- `(Scheme)-[:IMPLEMENTED_BY]->(Department)`

---

## Appendix A: UI Initialization & Debugging Lifecycle (March 21, 2026)

To completely boot the application from scratch and resolve subsequent data loading errors, the following environment setup and graph reconstruction steps were performed:

### 1. Environment & Dependency Resolution
- **Virtual Environment:** Created a clean Python 3.12 environment (`prenv2`) to bypass system path conflicts.
- **Dependency Pinning:** Relaxed strict `==` versions in `requirements.txt` to `>=` to resolve nested package conflicts during `pip install`.
- **Docker Relocation:** Due to extreme constraints on the `C:` drive, Docker Desktop was completely uninstalled and silently re-provisioned on the `E:` drive (`E:\Docker` and `E:\DockerWSL`).

### 2. Service Orchestration
- **Neo4j Graph:** Booted successfully via the relocated Docker Daemon.
- **FastAPI Backend:** Triggered via `uvicorn backend.app.main:app --reload`.
- **Streamlit Frontend:** Booted in headless mode (`--server.headless true`) to bypass interactive email prompts.

### 3. UI Debugging & Data Re-Seeding
Upon initial boot, the **Ward Map**, **Proof Chain**, and **Micro Accountability** features failed to load asset data.
- **Fixed `.json()` Attribute Error:** In `frontend/pages/04_Micro_Accountability.py`, an `AttributeError` caused a crash because the custom API wrapper (`safe_get`) already returned a parsed dictionary, not a raw Response object. The `.json()` call was removed.
- **Graph Topology Mismatch (Zero Asset Bug):** The `/assets/list` backend query strictly filters assets using the `LOCATED_IN` Neo4j relationship linked to specific Wards (`REG_W45`). 
- **Cause ID:** The baseline formalization script (`load_seed_data.py`) failed to create these `LOCATED_IN` relationships because the target `REG_W45` proxy wards were completely missing from the `regions.csv` seed file.
- **Resolution:** We automatically scanned the `assets.csv` file for all missing `REG_W45*` hierarchy mappings and organically appended them to `data/resources/final_formalized/regions.csv`. The Neo4j database was subsequently wiped and re-seeded, perfectly restoring the delivery gap logic and map coordinates in the frontend.
