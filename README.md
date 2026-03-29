# PRAMAAN v5 — India Governance Intelligence & Proof System

> *"From Events to Evidence — Making Governance Verifiable in Real Time"*

PRAMAAN connects national events, government responses, and ground-level delivery into a unified intelligence graph — enabling real-time visibility, verification, and decision-making for governance.

Built for **India Innovates 2026** · Digital Democracy Domain
**Team:** Aparna · Sambhavi · Sreenu
**Venue:** Bharat Mandapam, New Delhi · March 28–29, 2026

---

## What It Does

PRAMAAN builds a live knowledge graph over India's national events, government responses, scheme delivery, and proof — across 7 domains. Every node is real. Every edge is evidence-backed.

**The proof chain:**
```
Event → Government Response → Scheme → Asset → Evidence
```

**Example:**
> Delhi Yamuna Floods (Jul 2023)
> → SDRF activated
> → AMRUT: 3 drainage projects in Delhi (2 completed ✅, 1 in progress ⚠️)
> → PMAY: 17,067 houses, ₹401 Cr, 100% occupied ✅

---

## 7 Screens

| # | Screen | What It Shows |
|---|--------|--------------|
| 0 | **Pramaan Home** | Live stats: Funds Tracked, Verified Assets, Evidence, Events — animated hero |
| 1 | **Live Ingestion** | Agentic 3-path ingestion pipeline · Run Agent button · auto-scheduler (15m/1h/6h/24h) · Crawl4AI + Gemini classifier · LLM chain status |
| 2 | **Global Intelligence** | 28 events across 7 domains on interactive map, cross-domain connections, blast score heatmap |
| 3 | **Decision Engine** | Interactive Neo4j knowledge graph — 9 node types, 10+ edge types, AI decision brief |
| 4 | **Delivery Monitor** | Type 1 (event-triggered) + Type 2 (ongoing) schemes, Plotly delivery charts, Delhi pilot |
| 5 | **Crisis Monitor** | Active crisis timeline, India exposure radar, scenario analysis (Best/Base/Worst), impact cascade |
| 6 | **Intelligence Verdict** | AI-generated strategic decisions, national exposure, advantage windows, cross-domain proof chain |
| 7 | **Proof & Evidence** | Before/after photos, AI intelligence brief (Groq LLaMA 3.3 70B), data trust layer, citizen mock |

---

## Architecture — 5 Layers

```
Layer 1: Events (28 events, 7 domains, cross-domain connections)
    ↓
Layer 2: Government Response (Type 1: SDRF/NDRF · Type 2: AMRUT/PMAY/PLI)
    ↓
Layer 3: Delivery (Scheme → Asset → Region — Delhi pilot: Ward 45 & 46)
    ↓
Layer 4: Evidence (Before/after photos + PIB + data.gov.in + trust scoring)
    ↓
Layer 5: Citizen (mock UI — WhatsApp-style notifications, field report)
```

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Graph DB | Neo4j 5.19 (Docker) — 9 node types, 10+ edge types |
| Backend | FastAPI + Uvicorn — 20+ REST endpoints |
| Frontend | Streamlit + streamlit-agraph + streamlit-folium + Plotly |
| AI — Primary | Groq API · LLaMA 3.3 70B · streaming briefs + verdict generation |
| AI — Fallback | Google Gemini 2.0 Flash · classification + fallback briefs |
| AI — Local | Ollama (optional) · llama3 · runs fully offline |
| Ingestion Agent | crawl4ai · headless JS scraper → Markdown · Gemini 1.5 Flash classifier |
| Ingestion Scheduler | APScheduler · auto-triggers every 15m / 1h / 6h / 24h |
| Ingestion Pipeline | 3-path: Structured (API) · Semi-structured (PDF/XML) · Unstructured (web crawl) |
| Data | data.gov.in · PIB · NDMA · ISRO · IMD · UN · World Bank |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (for Neo4j)
- Groq API key — free at [console.groq.com](https://console.groq.com) (primary LLM)
- Google Gemini API key — free at [aistudio.google.com](https://aistudio.google.com/app/apikey) (fallback)
- [Ollama](https://ollama.com/download) (optional — local offline LLM)
- data.gov.in API key — free at [data.gov.in](https://data.gov.in)

### 1. Clone & Install

```bash
git clone <repo-url>
cd Pramaan
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp env.example .env       # then edit .env with your keys
```

Required keys:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

GROQ_API_KEY=your_groq_key_here          # primary LLM — get free at console.groq.com
GOOGLE_API_KEY=your_gemini_key_here      # fallback LLM
GEMINI_API_KEY=your_gemini_key_here      # same key, used by classifier

DATA_GOV_API_KEY=your_datagov_key_here

# Optional — only needed if running Ollama locally
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:latest
```

### 3. Start Neo4j

```bash
docker-compose up -d
```

Neo4j Browser: `http://localhost:7474` (login: `neo4j` / your password)

> The backend auto-seeds the graph on first startup — no manual seed step needed.

### 4. Start Backend

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

### 5. Start Frontend

```bash
cd frontend
streamlit run main_app.py --server.port 8501
```

UI: `http://localhost:8501`

---

### Optional: Ollama (Local Offline LLM)

Ollama is optional. If not configured, Groq is used automatically.

#### Linux / WSL
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3        # ~4 GB, one-time download
ollama serve              # starts on http://localhost:11434
```

#### Windows (accessed from WSL)

1. Download and install from [ollama.com/download](https://ollama.com/download)
2. Expose Ollama to WSL — open PowerShell as Administrator:
```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "Machine")
Get-Process | Where-Object {$_.Name -like "*ollama*"} | Stop-Process -Force
Start-Sleep 3
Start-Process "ollama" -ArgumentList "serve"
New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow
```
3. Find WSL gateway IP and update `.env`:
```bash
ip route show default | awk '{print $3}'
# Use that IP: OLLAMA_HOST=http://172.x.x.x:11434
```

---

## Data Coverage

18 real government datasets from data.gov.in covering all 28 events:

| Domain | Events (sample) | Datasets |
|--------|-----------------|----------|
| Climate | Wayanad 2024, Cyclone Dana, Delhi Floods 2023, Chamoli, Joshimath | NDRF/SDRF, Lives Saved, Cyclone data, AMRUT, PMAY |
| Society | COVID Wave 2, Delhi Floods, Manipur 2023 | COVID deaths/cases, Ayushman Bharat, SVANidhi, SBM |
| Economics | Tata Semi 2024, IMEC 2023, India-UK CETA 2025, Rupee Crisis 2026 | PLI investments, FDI equity, Trade data |
| Technology | Chandrayaan-3, Aditya-L1, SPADEX 2025, India Semiconductor 2026 | DoS budget, ISRO/VSSC budget, Semiconductor imports |
| Defense | Balakot, Twelve-Day War 2025, Arunachal Standoff 2026 | Defence budget R&D, Military expenditure |
| Governance | Article 370, Joshimath, Labour Codes 2025, AI Regulation 2026 | JK development investment, NDRF/SDRF |
| Geopolitics | G20, Iran-US-Israel War 2025, Teesta Treaty 2026, US-India Trade 2026 | Crude oil imports, FDI, Trade data |

---

## Agentic Ingestion Pipeline

PRAMAAN's Live Ingestion screen is powered by a **3-path agentic pipeline** that classifies, routes, and loads governance data into the Neo4j knowledge graph automatically.

### Architecture

```
Trigger (Button / APScheduler)
        ↓
  agent/classifier.py
  Brain: Gemini 1.5 Flash (function calling)
  Tool: classify_and_route → { source_type, fetch_method, destination }
        ↓
  ┌─────────────────────────────────────────────────────┐
  │ Path 1 — Structured      │ Path 2 — Semi-Structured │ Path 3 — Unstructured    │
  │ REST API / tabular CSV   │ PDF / XML / Excel / KML  │ Web docs / press releases│
  │ requests + pandas        │ PyMuPDF / lxml / openpyxl│ Crawl4AI (JS → Markdown) │
  │ → /data/structured/raw/  │ → /data/semi_structured/ │ → /data/unstructured/raw/│
  └─────────────────────────────────────────────────────┘
        ↓
  agent/loader.py (downstream sweeper)
  Scans raw folders → ai_service.extract_ontology()
  → Canonical PRAMAAN nodes + edges → Neo4j
  → Archive to /processed/
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent brain | Gemini 1.5 Flash — function calling classifier |
| Web scraper | **Crawl4AI** — async headless JS rendering → clean Markdown |
| Structured fetch | `requests` + `pandas` + `pydantic` |
| Semi-structured parse | `PyMuPDF` · `lxml` · `openpyxl` · `markdown` · `fastkml` |
| Scheduler | **APScheduler** — 15m / 1h / 6h / 24h intervals |
| Entity extraction | `ai_service.py` → `AIService.extract_ontology()` |
| Graph commit | Neo4j via `neo4j-driver` — constraints + indexes |
| Confidence scoring | `verification_agent.py` — hallucination check on extracted entities |

### Ingestion Flow in UI

The **Live Ingestion** page exposes the full pipeline:

1. **Run Agent** — triggers `POST /ingest/agentic` with a topic prompt
2. **Agent Trace** — streams step-by-step agent actions to the UI
3. **Auto-Scheduler** — configurable timer (15m/1h/6h/24h) runs ingestion continuously
4. **Recent Feed** — shows last N ingested nodes with source + timestamp
5. **LLM Chain Status** — live badge showing Ollama / Groq / Gemini availability

> In MVP, the scheduler runs curated demo topics. In production, it crawls live PIB press releases, NDMA alerts, data.gov.in API updates, and IMD bulletins automatically.

---

## LLM Chain

PRAMAAN uses a 3-tier LLM fallback chain:

```
Groq LLaMA 3.3 70B  →  (rate limit)  →  Groq LLaMA 3.1 8B  →  (rate limit)
→  Groq Mixtral 8x7B  →  (rate limit)  →  Google Gemini 2.0 Flash
```

Ollama (local llama3) is available as an optional offline layer if configured via `OLLAMA_HOST`.

---

## Key Directories

```
backend/app/               — FastAPI backend (routers, services, models)
backend/app/routers/       — ontology, crisis, verdict, agentic, ingest, scrape, citizen_report
backend/scripts/           — Neo4j seed loaders (connections, schemes, Iran enrichment)
frontend/                  — Streamlit UI (7 screens + home)
frontend/pages/            — One file per screen
frontend/components/       — topnav, ontology_model
frontend/utils/            — api, events, constants, geo_selector, session, voice_input
frontend/static/evidence/  — Before/after delivery photos (Delhi Ward 45 & 46)
data/resources/            — Real government datasets (18 datasets)
data/config/               — govdata_registry.json
scripts/                   — seed_2026_events.py, simulate_live.py
agent/                     — Agentic ingestion pipeline (crawl4ai)
```

---

## MVP Scope

| Feature | Status |
|---------|--------|
| 28 events, 7 domains | ✅ Complete |
| Interactive Neo4j knowledge graph | ✅ Complete |
| Global Intelligence map (Folium) | ✅ Complete |
| Crisis Monitor with scenario analysis | ✅ Complete |
| Intelligence Verdict (AI decisions + proof chain) | ✅ Complete |
| Scheme Delivery with Type 1/Type 2 split | ✅ Complete |
| Proof & Evidence with live AI briefs | ✅ Complete — Groq streaming, session-cached |
| Data trust layer + hallucination check | ✅ Complete |
| Before/after delivery photos (Delhi pilot) | ✅ Complete |
| Agentic ingestion with auto-scheduler | ✅ Complete (demo topics) |
| Full India geographic coverage | 🔄 Delhi pilot — expandable |
| Live citizen notifications | 🔄 Mock UI — production-ready design |

---

## License

MIT License · India Innovates 2026
