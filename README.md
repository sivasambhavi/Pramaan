# 🛡️ PRAMAAN — Governance Delivery Proof Engine

> **"One Graph That Proves What India Built."**

PRAMAAN is an AI-powered Knowledge Graph platform that bridges the gap between government scheme allocations and ground-level infrastructure delivery. It provides full-chain traceability from central budgets to street-level proof — ensuring micro-accountability in governance.

Built for the **India Innovates 2026 Hackathon** · Data Mining & Processing Track
**Team:** Aparna · Sambhavi · Sreenu

---

## 🎯 What It Does

Given a Delhi ward, PRAMAAN answers:
- *"₹12 lakh was sanctioned under AMRUT for a drain in Gali 7 — was it actually built?"*
- *"Which schemes in Ward 45 have zero evidence of delivery?"*
- *"Show me the full chain: Budget → Agency → Asset → Photo Proof → Beneficiaries."*

It does this by unifying fragmented government data (CSVs, JSONs, KML, news, PIB releases) into a single **Neo4j knowledge graph** — then letting anyone interrogate it.

---

## 🖥️ 4 Demo Screens

| # | Screen | What It Shows |
|---|--------|--------------|
| 1 | **Ward Map** | Delivery score gauge, asset coverage map, scheme breakdown for Ward 45 Shahdara |
| 2 | **Proof Chain** | Full traceability: Scheme → Actor → Asset → Before/After Photos → Beneficiaries |
| 3 | **Live Ingestion** | AI extracts governance entities from live news → ingests into Neo4j in one click |
| 4 | **Micro Accountability** | Triggers WhatsApp/SMS alerts to councillors for verified/disputed assets |

---

## 🏗️ Architecture

```
News / PIB / CSVs / KML / data.gov.in
        ↓ (ETL scripts + Groq LLM)
   Neo4j Knowledge Graph
        ↓ (FastAPI REST)
   Streamlit UI  ←→  FastAPI  ←→  Neo4j
```

**7 Node Types:** Region · Scheme · Actor · Asset · Beneficiary · Evidence · Event

**11 Relationship Types:** FUNDS · BUILT_BY · LOCATED_IN · PROVES · BENEFITS · MENTIONS · CONTRADICTS · TARGETS · IMPLEMENTS · CAPTURES · LIVES_IN

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Graph DB | Neo4j 5 (Docker) |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit + Plotly + Folium |
| AI / LLM | Groq API (llama-3.3-70b) |
| News Scraping | Google News RSS + PIB RSS |
| Notifications | Twilio (WhatsApp/SMS) |
| Data | Pandas · RapidFuzz · data.gov.in API |

---

## 🏃 Quick Start

### Prerequisites
- Python 3.10+
- Docker (for Neo4j)
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Install

```bash
git clone <repo-url>
cd Pramaan
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

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
python backend/scripts/load_seed_data.py
```

Loads all 9 CSVs from `data/resources/data/final_formalized/` into Neo4j (~300+ nodes).

### 5. Start the Backend

```bash
uvicorn backend.app.main:app --reload
```

API available at `http://localhost:8000` · Swagger docs at `http://localhost:8000/docs`

### 6. Start the Frontend

```bash
streamlit run frontend/app.py
```

UI available at `http://localhost:8501`

---

## 📁 Key Directories

```
backend/app/routers/   — 8 FastAPI routers (wards, assets, ingest, questions, scrape, notifications, govdata, beneficiaries)
frontend/pages/        — 4 Streamlit pages (Ward Map, Proof Chain, Live Ingestion, Micro Accountability)
data/resources/data/final_formalized/  — canonical seed CSVs loaded into Neo4j
data/resources/        — raw JSON from data.gov.in (AMRUT, PMAY, statewise allocations)
docs/                  — todo tracker, gap analysis, AI mapper spec
```

---

## 📊 What's Loaded (Ward 45, Shahdara South)

| Entity | Count |
|--------|-------|
| Regions (wards + streets) | 296 |
| Assets | 57 (5 hero + 51 water bodies + 1 park) |
| Schemes | 8 (AMRUT, PMAY, SFC, SBM, PMKISAN, JJBY, AB, PMGSY) |
| Actors | 6 (MCD Works, Sanitation, Electrical, Councillor, 2 contractors) |
| Evidence | 15 (before/after photos + water body evidence) |
| Beneficiaries | 5 groups (~750 people) |
| Events | 5 (completion + inauguration events) |

---

## 🔑 Demo Flow (3–4 minutes)

1. **Ward Map** → show Ward 45 delivery score + asset breakdown
2. **Proof Chain** → select "Gali No. 7 Drain" → trace full chain → show before/after photos
3. **Live Ingestion** → auto-search news for "Ward 45 drain" → AI extracts entities → ingest to graph
4. **Micro Accountability** → trigger WhatsApp alert for verified asset

---

## 📄 License

MIT License · India Innovates 2026
