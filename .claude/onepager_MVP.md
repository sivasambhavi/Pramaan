# PRAMAAÑ — MVP Scope
**Proof-based Registry for Asset Mapping, Accountability & Nationwide Transparency**
*"One Graph That Proves What India Built"*
India Innovates 2026 · Data Mining & Processing · Sprint: March 7–10, 2026

---

## What This MVP Proves

A working demo that:

- Connects fragmented governance data into a unified **knowledge graph**.
- Traces full delivery chains:
  **Scheme → Actor → Asset → Region → Beneficiary → Evidence**.
- Uses **AI (Groq LLM)** to extract entities from unstructured text.
- Answers **natural-language queries** (3 fixed questions, keyword-routed).
- Presents data through a **dark intelligence-platform UI** — not a generic dashboard.

All of this for **Ward 45, Shahdara South, Delhi** with real curated data.

---

## Data Scope — 1 Ward, Full Depth

| Dimension        | Target              | Actual (loaded)                                                        |
|-----------------|---------------------|-------------------------------------------------------------------------|
| Geography       | Ward 45 Shahdara    | REG_W45 · Shahdara South Zone · Delhi                                  |
| Delivery Chains | 5–8 complete chains | 5 key chains (drain, road, toilet, housing, streetlights)              |
| Physical Assets | 3–5 hero assets     | 57 total (5 hero + 51 water bodies as supporting data)                 |
| Evidence        | 10–15 pieces        | 15 pieces (before/after images + water body evidence)                  |
| Schemes         | 2–3 schemes         | 4 schemes: SFC, Swachh Bharat, PMAY, Local Lights                     |
| Actors          | 3–5 agencies        | 6 actors (MCD Works, Sanitation, Electrical, Councillor, 2 contractors)|
| Beneficiaries   | 5–10 groups         | 5 beneficiary groups (~750 people total)                               |
| Events          | 5 events            | 5 completion/inauguration events                                        |
| Graph Size      | ~100–150 nodes      | ~296 regions + 57 assets + 4 schemes + 6 actors + 15 evidence + ...    |

---

## 6 Screens

| # | Screen | File | Status |
|---|--------|------|--------|
| 1 | Ward Overview | `01_🏙_Ward_Map.py` | 🔲 Sreenu |
| 2 | Proof Chain Viewer | `02_🧷_Proof_Chain.py` | 🔲 Sreenu |
| 3 | Gap Analysis | `03_📊_Gap_Analysis.py` | 🔲 Sreenu |
| 4 | Delivery Graph | `04_🔗_Graph_View.py` | 🔲 Sreenu |
| 5 | Live Ingestion | `05_⚡_Live_Ingestion.py` | 🔲 Sreenu |
| 6 | NL Questions | `06_❓_Questions.py` | 🔲 Sreenu |

> All 6 stub files created ✅ · Design spec in `.claude/frontend_design.md` ✅ · Implementation pending

### 1. Ward Overview (`01_🏙_Ward_Map.py`) — 🔲 Sreenu
- Plotly **delivery score gauge** (0–100%, color-coded by range)
- 4 glassmorphism metric cards: ward name, total assets, proven, gaps
- Asset type **donut chart** (drain, road, toilet, housing, streetlight, water_body)
- Color-coded asset table — green/amber/red by evidence status
- Click asset row → navigates to Proof Chain screen

### 2. Proof Chain Viewer (`02_🧷_Proof_Chain.py`) — 🔲 Sreenu
- Asset selector dropdown
- Visual **timeline flow**: Scheme → Actor → Asset → Region → Evidence → Beneficiaries
- Each step: glass card with status icon (✅ / ❌)
- **Before / After image** comparison side by side
- Chain completeness **glowing progress bar**

### 3. Gap Analysis (`03_📊_Gap_Analysis.py`) — 🔲 Sreenu
- Per-scheme cards with **status-colored left border** (green/amber/red)
- Grouped by gap_type: `complete` / `partial` / `no_evidence` / `no_assets`
- Proven vs total assets **Plotly bar chart**
- "What would it take to reach 100%?" missing steps box

### 4. Delivery Graph Visualization (`04_🔗_Graph_View.py`) — 🔲 Sreenu
- Interactive **force-directed graph** (streamlit-agraph)
- Nodes color-coded by entity type (7 colors)
- Click node → sidebar shows properties
- Filter buttons: [All] [Schemes] [Assets] [Evidence]
- Node legend below graph

### 5. Live Ingestion (`05_⚡_Live_Ingestion.py`) — 🔲 Sreenu
- Split-screen: paste text left → extracted entities right
- **Demo Text** pre-fill button (offline reliability)
- Groq LLM extraction → MD5-cached for offline use
- Entity badge pills grouped by type
- Ingest button → writes to Neo4j → `st.balloons()` on success
- Shows `⚡ From cache` or `🤖 From LLM` source tag

### 6. NL Questions (`06_❓_Questions.py`) — 🔲 Sreenu
- **3 quick-question pill chips** (pre-wired to backend)
- Free-text input with keyword routing
- Answer rendered by type:
  - `asset_list` → Plotly bar chart by asset type
  - `proof_chain` → chain step cards
  - `gap_analysis` → delivery gauge + gap table
- Source citation: `Source: Neo4j · Ward 45 · REG_W45`

---

## Natural Language Queries (3 Fixed Questions) — ✅ Backend Done

- **Q1:** *"What was built in Ward 45 in last 2 years?"* ✅
  → 51 assets, grouped by type with scheme, cost, status.

- **Q2:** *"For Gali 7, show full delivery chain."* ✅
  → Full chain: SFC → MCD → Drain → Gali No.7 → 2 evidence → 200 beneficiaries.

- **Q3:** *"Which schemes have low delivery scores?"* ✅
  → Gap analysis: 19.6% delivery score, SFC partial (10/51 proven).

Keyword routing supports multiple phrasings per question. Q3 checked before Q1 to prevent keyword conflicts.

---

## Technical Deliverables

| Component         | Spec                                                              | Status     |
|------------------|-------------------------------------------------------------------|------------|
| Neo4j Graph      | 7 node types, 10 relationship types, domain-specific PKs         | ✅ Done     |
| Cypher Queries   | 5 parameterised queries (wards, assets, gaps, score, chain)      | ✅ Done     |
| FastAPI Backend  | 7 endpoints (/health, /wards, /assets, /gaps, /score, /chain, /ingest) | ✅ Done |
| Data Loader      | CSV → Neo4j, 7 CSVs, relative path, no hardcoding               | ✅ Done     |
| Constraints      | 7 uniqueness constraints + 6 indexes (domain-specific PKs)       | ✅ Done     |
| AI Extraction    | Groq LLM (llama-3.3-70b), MD5 cache, 7-table schema output      | ✅ Done     |
| NL Query Routing | Keyword routing, 3 questions, multiple phrasings supported       | ✅ Done     |
| Pydantic Models  | Node models + API models, PK/FK documented                       | ✅ Done     |
| Graph Model      | Arrows.app JSON committed to `data/docs/graph_model.json`        | ✅ Done     |
| Streamlit UI     | 6 pages (dark intelligence theme, glassmorphism, Plotly, agraph) | 🔲 Sreenu  |
| Performance      | Response < 3 seconds, offline-capable (cache + local Neo4j)      | ✅ Backend  |

---

## UI Design Direction

- **Theme:** Dark governance-intelligence platform (Palantir / Grafana aesthetic)
- **Key elements:** Glassmorphism cards, glowing status indicators, gradient headers, pulse animations
- **Graph UI:** streamlit-agraph force-directed, node glow on hover, entity-colored nodes
- **Charts:** Plotly dark theme (gauge, donut, bar) — no default Streamlit charts
- **Font:** Inter (Google Fonts)
- **Full spec:** `.claude/frontend_design.md`

---

## Tech Stack

| Layer      | Technology                                              |
|-----------|---------------------------------------------------------|
| Graph DB  | Neo4j 5 (Docker, local)                                 |
| Backend   | FastAPI + Uvicorn + Neo4j Python Driver                 |
| AI        | Groq API (llama-3.3-70b-versatile), MD5 response cache  |
| Frontend  | Streamlit + Plotly + streamlit-agraph + streamlit-extras|
| Data      | Pandas + RapidFuzz (entity resolution)                  |
| Config    | pydantic-settings + python-dotenv                       |

---

## Submission Deliverables (by March 10)

- [ ] GitHub repo with **README** + setup instructions
- [ ] **Unstop** form filled completely
- [ ] **7–10 slide PPT** covering:
  - [ ] Problem
  - [ ] Solution + architecture
  - [ ] Live demo flow (6 screens)
  - [ ] Team
- [ ] **3–5 min demo video** (recommended)

> **What's ready to demo:** Neo4j graph ✅ · FastAPI all 7 endpoints ✅ · AI extraction ✅ · NL queries ✅ · 6 UI stubs ✅

---

## Explicitly Out of Scope (Post-MVP)

- Multiple wards
- Real-time data feeds
- Agentic AI (see `tasks/todo.md` Future Work section)
- Graph analytics (centrality, communities)
- Mobile UI
- Authentication / access control
- Production deployment
- Multi-language support

---

**PRAMAAÑ** · Global Ontology Engine · India Innovates 2026
Data Mining & Processing · Team of 3 · Aparna · Sambhavi · Sreenu
