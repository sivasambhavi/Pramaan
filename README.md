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

## 5 Screens

| # | Screen | What It Shows |
|---|--------|--------------|
| 0 | **Pramaan** | Home — live stats: Funds Tracked, Verified Assets, Evidence, Events |
| 1 | **National Intelligence** | 17 events across 7 domains, cross-domain connections, live ingestion feed |
| 2 | **Scheme Tracker** | Type 1 (event-triggered) + Type 2 (ongoing) schemes, decision panel |
| 3 | **Delivery Monitor** | Delhi pilot — AMRUT + PMAY ground delivery with real data |
| 4 | **Proof & Evidence** | Before/after photos, data proof, trust layer, citizen mock |

---

## Architecture — 5 Layers

```
Layer 1: Events (17 events, 7 domains)
    ↓
Layer 2: Government Response (Type 1: SDRF/NDRF · Type 2: AMRUT/PMAY/PLI)
    ↓
Layer 3: Delivery (Scheme → Asset → Region — Delhi pilot)
    ↓
Layer 4: Evidence (Photos + PIB + data.gov.in)
    ↓
Layer 5: Citizen (mock UI — production-ready design)
```

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Graph DB | Neo4j 5.19 (Docker) |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit + streamlit-agraph + streamlit-folium |
| AI — Primary | Ollama (local) · llama3 · runs offline |
| AI — Fallback | Groq API · LLaMA 3.3 70B · used when Ollama is offline |
| AI — Tertiary | Google Gemini Flash · classification + validation |
| Ingestion | crawl4ai · agentic web crawler |
| Data | data.gov.in · PIB · NDMA · ISRO · IMD · UN · World Bank |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (for Neo4j)
- [Ollama](https://ollama.com/download) installed locally (primary LLM — free, runs offline)
- Groq API key — free at [console.groq.com](https://console.groq.com) (fallback if Ollama is offline)
- Google Gemini API key — free at [aistudio.google.com](https://aistudio.google.com/app/apikey) (tertiary fallback)
- data.gov.in API key — free at [data.gov.in](https://data.gov.in)

### 1. Clone & Install

```bash
git clone <repo-url>
cd Pramaan
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install & Start Ollama (primary LLM)

#### Linux / WSL (recommended)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3        # download the model (~4 GB, one-time)
ollama serve              # starts on http://localhost:11434
```

#### Windows (running Ollama on Windows, accessed from WSL)

1. Download and install from [ollama.com/download](https://ollama.com/download)

2. **Expose Ollama to WSL** — open PowerShell as Administrator and run:
```powershell
# Bind Ollama to all interfaces (not just localhost)
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "Machine")

# Kill and restart Ollama so it picks up the new setting
Get-Process | Where-Object {$_.Name -like "*ollama*"} | Stop-Process -Force
Start-Sleep 3
Start-Process "ollama" -ArgumentList "serve"

# Allow WSL traffic through Windows firewall
New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow
```

3. Verify Ollama is on `0.0.0.0`:
```powershell
netstat -ano | findstr 11434
# Should show: TCP  0.0.0.0:11434  ...  LISTENING
```

4. Find your WSL gateway IP and test from WSL:
```bash
# Get Windows host IP from WSL
ip route show default | awk '{print $3}'

# Test (replace with your gateway IP)
curl http://172.17.240.1:11434/
# Should return: Ollama is running
```

5. Update `.env` with the Windows host IP:
```env
OLLAMA_HOST=http://172.17.240.1:11434   # use your actual gateway IP
```

> If Ollama is not reachable, the system auto-falls back to Groq — everything still works.

### 3. Configure Environment

```bash
cp env.example .env       # then edit .env with your keys
```

Required keys:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:latest

GROQ_API_KEY=your_groq_key_here          # fallback LLM
GOOGLE_API_KEY=your_gemini_key_here      # tertiary LLM
GEMINI_API_KEY=your_gemini_key_here      # same key, used by agent/classifier.py

DATA_GOV_API_KEY=your_datagov_key_here
```

### 4. Start Neo4j

```bash
docker-compose up -d
```

Neo4j Browser: `http://localhost:7474` (login: `neo4j` / your password)

### 5. Seed the Graph

```bash
python backend/scripts/load_ontology.py
python backend/scripts/load_govdata.py
```

### 6. Start Backend

```bash
uvicorn backend.app.main:app --reload
# or: venv/bin/python -m uvicorn backend.app.main:app --reload
```

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

### 7. Start Frontend

```bash
streamlit run frontend/main_app.py
# or: venv/bin/streamlit run frontend/main_app.py
```

UI: `http://localhost:8501`

---

## Data Coverage

19 real government datasets from data.gov.in covering all 17 events:

| Domain | Events | Datasets |
|--------|--------|----------|
| Climate | Wayanad, Cyclone Dana, Chamoli, Joshimath, Delhi Floods | NDRF/SDRF, Lives Saved, Cyclone data, AMRUT, PMAY |
| Society | COVID Wave 2, Delhi Floods | COVID deaths/cases, Ayushman Bharat, SVANidhi, SBM |
| Economics | Tata Semi, IMEC | PLI applications + investments, FDI equity |
| Technology | Chandrayaan-3, Aditya-L1 | DoS budget, ISRO/VSSC budget, Semiconductor imports |
| Defense | Balakot, Manipur | Defence budget R&D + GDP % |
| Governance | Article 370, Joshimath | JK development investment, NDRF/SDRF |
| Geopolitics | G20, India-Canada, Russia-Ukraine, Gaza/Red Sea | FDI countrywise, Crude oil imports, Trade data |

---

## Key Directories

```
backend/app/          — FastAPI backend (routers, services, models)
backend/scripts/      — Neo4j seed loaders
frontend/             — Streamlit UI (5 screens)
frontend/static/evidence/  — Before/after delivery photos
data/resources/       — Real government data (19 datasets)
data/config/          — govdata_registry.json (dataset registry)
data/scripts/         — Data fetch + transform scripts
agent/                — Agentic ingestion pipeline
```

---

## License

MIT License · India Innovates 2026
