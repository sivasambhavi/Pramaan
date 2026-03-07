# PRAMAAÑ — MVP Scope  
**Proof-based Registry for Asset Mapping, Accountability & Nationwide Transparency**  
*"One Graph That Proves What India Built"*  
India Innovates 2026 · Data Mining & Processing · Sprint: March 7–10, 2026

---

## What This MVP Proves

A working demo that:

- Connects fragmented governance data into a unified **knowledge graph**.  
- Traces full delivery chains:  
  **Scheme → Budget → Asset → Region → Beneficiary → Evidence**.  
- Uses **AI** to extract entities from unstructured text.  
- Answers **natural-language queries** (3 fixed questions).  

All of this for a **single Delhi ward** with realistic data.

---

## Data Scope — 1 Ward, Full Depth

| Dimension        | Target              | Details                                                                 |
|-----------------|---------------------|-------------------------------------------------------------------------|
| Geography       | 1 Delhi ward        | Ward 45 Shahdara (or best-available ward based on data)                |
| Delivery Chains | 5–8 complete chains | Each: Scheme → Budget → Asset → Location → Beneficiary → Evidence      |
| Physical Assets | 3–5 assets          | Roads, drains, streetlights with full metadata + geo-coordinates       |
| Evidence        | 10–15 pieces        | Before/after photos, completion certificates, geo-tagged proof         |
| Schemes         | 2–3 schemes         | SFC Grant, PMAY, Swachh Bharat or similar, covering demo assets        |
| Thin Domains    | 5 nodes total       | 1 climate + 1 tech + 1 geopolitics + 1 defense + 1 society             |
| Graph Size      | ~100–150 nodes      | ~200–300 edges across 8 entity types and 14 relationship types         |

Thin domains are only to **prove global scalability** of the ontology and architecture.

---

## 5 Must-Have Screens

### 1. Ward Overview

- Shows:  
  - Ward info  
  - Delivery Score  
  - List of all assets with status indicators  
- Interaction:  
  - Click any asset → opens **Proof Chain** view

### 2. Proof Chain Viewer

- Shows full chain for selected asset:  
  **Scheme → Budget → Agency → Asset → Location → Evidence → Beneficiaries**  
- UI:  
  - Visual flow or timeline diagram  
  - Before/after photos shown side by side

### 3. Gap Analysis

- Shows:  
  - Schemes with no linked assets  
  - Assets with missing evidence  
  - Delivery Score formula breakdown  
- UI:  
  - Color-coded status:  
    - Green = proven  
    - Yellow = partial  
    - Red = gap

### 4. Delivery Graph Visualization

- Shows:  
  - An interactive graph-style view of the delivery network for the ward or a selected asset.  
  - Nodes: schemes, assets, regions, actors, beneficiaries, evidence.  
  - Edges: funds, located_in, built_by, benefits, proves, etc.  
- UI:  
  - Force-directed or network layout that **looks like a real intelligence system** (knowledge graph UI).  
  - Click a node to highlight its immediate neighborhood and show details on the side panel.  
- Purpose:  
  - Visually prove that PRAMAAÑ is a **graph-native intelligence platform**, not just a set of tables and charts.

### 5. Live Ingestion

- Flow:  
  - Paste PIB/news text  
  - AI extracts entities  
  - Show extracted JSON  
  - Click **Ingest** → graph updates  
  - Re-query to show new data in the UI  
- Note:  
  - Real-time extraction demo, but **cached** for offline reliability

---

## Natural Language Queries (3 Fixed Questions)

- **Q1:**  
  *“What was built in Ward 45 in last 2 years?”*  
  → Returns asset list with scheme, cost, status, and evidence count.

- **Q2:**  
  *“For Gali 7, show full delivery chain.”*  
  → Returns complete chain with graph path visualization.

- **Q3:**  
  *“Which schemes have low delivery scores?”*  
  → Returns ranked gap analysis with missing links.

---

## Technical Deliverables

| Component        | Spec                                      |
|-----------------|-------------------------------------------|
| Neo4j Graph     | ~100–150 nodes, ~200–300 edges           |
| Cypher Queries  | 8 working parameterized queries          |
| FastAPI Backend | 6–8 REST endpoints                       |
| Streamlit UI    | 4 pages (overview, chain, gaps, ingest)  |
| AI Extraction   | 1 sample text, cached for offline use    |
| Performance     | Response time < 3 seconds, offline-capable demo |

---

## Submission Deliverables (by March 10)

- GitHub repo with **README** + setup instructions  
- **Unstop** form filled completely  
- **7–10 slide PPT** covering:
  - Problem
  - Solution
  - Architecture
  - Demo flow
  - Team
- **3–5 min demo video** (recommended, if time permits)

---

## Explicitly Out of Scope (Post-Submission If Shortlisted)

These are **not** required for the MVP:

- Multiple wards
- Real-time data feeds
- Graph analytics (centrality, communities, etc.)
- Advanced NL query (only 3 fixed questions now)
- Mobile UI
- Authentication / access control
- Production deployment
- Extensive thin-domain coverage
- Multi-language support

---

**PRAMAAÑ** · Global Ontology Engine · India Innovates 2026  
Data Mining & Processing · Team of 3 Data Engineers
