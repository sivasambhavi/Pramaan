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
| Graph DB | Neo4j 5.18 (Docker) |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit + streamlit-agraph |
| AI / Insights | Groq API (LLaMA 3.3 70B) |
| Data | data.gov.in · PIB · NDMA · ISRO · IMD |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (for Neo4j)
- Groq API key (free at [console.groq.com](https://console.groq.com))
- data.gov.in API key (free at [data.gov.in](https://data.gov.in))

### 1. Clone & Install

```bash
git clone <repo-url>
cd Pramaan
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pramaa2026
GROQ_API_KEY=your_groq_key_here
DATA_GOV_API_KEY=your_datagov_key_here
```

### 3. Start Neo4j

```bash
docker-compose up -d
```

Neo4j Browser: `http://localhost:7474` (login: `neo4j` / `pramaa2026`)

### 4. Seed the Graph

```bash
python backend/scripts/load_ontology.py
python backend/scripts/load_govdata.py
```

### 5. Start Backend

```bash
uvicorn backend.app.main:app --reload
```

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

### 6. Start Frontend

```bash
streamlit run frontend/main_app.py
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
