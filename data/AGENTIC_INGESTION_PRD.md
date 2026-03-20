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
- **Brain:** Gemini 1.5 Flash (via `google.generativeai`) or Claude 3
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
    ├── classifier.py    ← Main agent entry point (Gemini/Claude)
    ├── tools.py         ← Tool definitions (Crawl4AI, requests)
    └── router.py        ← Pipeline dispatcher
```

---

## 4. Current Repository State & Missing Pieces

### What We Have Running
- **Frontend:** Streamlit is running locally on port `8501`. Pages include Ward Map, Proof Chain, Live Ingestion, and Micro Accountability.
- **Backend:** FastAPI backend initialized. Start using `cd backend && uvicorn app.main:app --reload --port 8000`.
- **Core AI Service:** `ai_service.py` is fully unified and capable of generating the final Neo4j entities/relations arrays.

### What Has Been Implemented
1. **The `agent/` Directory:** We have successfully built the single-agent classifier (`classifier.py`), the `tools.py` module containing the asynchronous `Crawl4AI` logic, and the `run_agent.py` APScheduler daemon to orchestrate them daily.
2. **The `inbox/` Dropzone:** The data lake scaffolding has been minted, including `/inbox`, `/data/structured`, `/data/semi_structured`, and `/data/unstructured` (with their raw/processed counterparts).
3. **Crawl4AI Integration:** `scrape_with_crawl4ai()` has been written to asynchronously fetch and render Javascript-heavy SPAs into clean markdown.
4. **Downstream Sweeper (`agent/loader.py`):** The final piece of the pipeline has been built. It scans `/data/unstructured/raw/` for the agent's dropped files, parses them through PRAMAAN's unified `ai_service` via REST API, commits the extracted nodes to Neo4j, and archives the file to `/processed/`.

---

## 5. Next Steps / Go-Live

1. **Populate Inbox:** Drop sample PDFs or Excel files into `/inbox/` and expand `tools.py` to parse them.
2. **Schema Caching:** Map the raw JSON structures from Gov API tables to the canonical schema.
3. **End-to-End Test:** Run the pipeline locally for 2-3 days using `python run_agent.py --daemon` and watch for API ratelimits.
