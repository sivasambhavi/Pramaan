# 🛡️ PRAMAAN — Governance Delivery Proof Engine

> **"One Graph That Proves What India Built."**

PRAMAAN is an AI-powered Knowledge Graph platform designed to bridge the gap between government scheme allocations and ground-level infrastructure delivery. It provides full-chain traceability from central budgets to street-level proof, ensuring micro-accountability in governance.

Built for the **India Innovates 2026 Hackathon**.

---

## 🚀 Key Features

- **📍 Ward Map**: Visualize infrastructure assets (roads, drains, streetlights) across Delhi wards with real-time delivery scores and coverage gaps.
- **🖇️ Proof Chain**: A deep-trace visualizer that links every rupee from **Scheme → Implementing Agency → Physical Asset → Evidence → Beneficiary**.
- **🔎 Governance Audit**: A natural-language interface to interrogate the knowledge graph. Ask complex questions about funding, construction status, and verification proof.
- **🤖 AI-Powered Ingestion**: Automatically extracts governance entities and relationships from PIB releases, news articles, and social media posts using LLMs.

---

## 🛠️ Technology Stack

- **Graph Database**: [Neo4j](https://neo4j.com/) (Knowledge Graph & RAG)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Frontend**: [Streamlit](https://streamlit.io/) (Dashboard & UI)
- **AI/LLM**: Groq AI / Gemini (Entity Extraction & NL Querying)
- **Data**: Pandas, RapidFuzz (Entity Resolution)

---

## 🏃 Quick Start

### 1. Prerequisites

- Python 3.10+
- Docker (for Neo4j)

### 2. Setup Neo4j

Start the Neo4j database using Docker Compose:

```bash
docker-compose up -d
```

### 3. Environment Setup

Configure your `.env` file in the root directory (see `.env.example` if available):

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pramaa2026
GROQ_API_KEY=your_key_here
```

### 4. Run the Backend (FastAPI)

```bash
uvicorn app.main:app --app-dir backend --reload
```
The API will be available at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### 5. Run the Frontend (Streamlit)

In a separate terminal:

```bash
streamlit run frontend/app.py
```
The UI will be accessible at `http://localhost:8501`.

---

## 📊 Progress Update (March 2026)

- [x] **Core Ontology**: Implemented mapping for Regions, Schemes, Assets, and Evidence.
- [x] **Integrated Stack**: Backend and Frontend are fully communicating.
- [x] **Ward Analysis**: Successfully mapped DMC Ward No. 45 (Shahdara) with 75% delivery score verification.
- [x] **Proof Chain Verification**: Verified end-to-end traceability for critical urban infrastructure (drains, roads).

---

## 📄 License

This project is licensed under the MIT License.
