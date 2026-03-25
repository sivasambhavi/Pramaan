# PRAMAAN: Unified Architecture & Alignment PRD 

**"One Graph That Proves What India Built."**

---

## 1. Problem Statement Alignment

PRAMAAN is built specifically to address **Domain 2: Digital Democracy**, focusing on the **Global Ontology Engine** and **Micro-Accountability Mapping** problem statements.

### How We Align:
*   **Global Ontology Engine**: We collect structured (CSVs), semi-structured (PDFs), and unstructured (News/PIB) data and map them into a unified, constantly updating **Governance Intelligence Graph** (Neo4j).
*   **Transparency & National Advantage**: By connecting siloed government systems (PFMS, eGramSwaraj, PIB), we create a "Shared Brain" for decision-makers to trace every rupee from a central scheme to a specific street-level asset.
*   **Micro-Accountability Mapping**: We have implemented a specific **Gali-level notification system**. When a new asset (e.g., a road in Gali 7) is verified, the system triggers a WhatsApp notification with "Before & After" proof only to the residents residing on that specific street.

---

## 2. End-to-End Architecture: Data to Graph

We use a **4-Step Decoupled Pipeline** to ensure the "Hunter" (Fetcher) is separated from the "Brain" (Cognitive Parser).

### Phase 1: The Hunter (Data Procurement)
*   **Tool**: `run_agent.py` + **Tavily Search API**.
*   **Action**: The agent autonomously searches whitelisted domains (PIB, MCD portals) for real-time feeds (e.g., "Ward 45 road work").
*   **Classification**: **Groq (Llama 3.1)** classifies input as Structured, Semi-Structured, or Unstructured.
*   **Storage**: Raw data is saved to `/data/unstructured/raw/` in Markdown format.

### Phase 2: The Brain (AI Mapping Engine)
*   **Tool**: `backend/app/services/ai_service.py` + **Groq/Gemini**.
*   **Action**: A downstream "Sweeper" finds raw files and sends them to the AI Service.
*   **Ontology Mapping**: The LLM extracts entities using a **Strict Ontology**:
    *   `Asset`: Roads, Drains, Streetlights.
    *   `Region`: Ward 45, Gali 7 (Hierarchical).
    *   `Scheme`: AMRUT, PMAY, SFC Grant.
    *   `Actor`: Contractors, Departments.
    *   `Beneficiary`: Residents, Impacted households.
    *   `Evidence`: Geo-tagged photos, News URLs.
*   **Canonical Mapping**: The AI uses a "Known ID Context" to ensure "Ward 45" always maps to `REG_W45` and doesn't create duplicate "Orphan" nodes.

### Phase 3: The Vault (Graph Engine & Validation)
*   **Tool**: **FastAPI** + **Neo4j**.
*   **Validation (6 Gates)**:
    1.  **Confidence Gate**: Drop extractions with <55% certainty.
    2.  **Hallucination Gate**: Sanity check costs (e.g., a drain shouldn't cost ₹500 Cr).
    3.  **Duplicate Gate**: Check if the asset already exists.
    4.  **ID Resolver**: Map LLM aliases (e.g., "Ward-45") to canonical IDs (`REG_W45`).
    5.  **Audit Stamp**: Stamping every node with `source_url`, `timestamp`, and `ai_model` for full data provenance.

### Phase 4: The Voice (Frontend & Notifications)
*   **Tool**: **Streamlit** + **Twilio API**.
*   **Micro-Accountability Trigger**: When an Evidence node links to an Asset, a Cypher query identifies residents on the same street and hits the Twilio WhatsApp API.

---

## 3. Frontend Experience: Page-by-Page Goals

### 1. Ward Map (The Strategic View)
*   **Goal**: Geospatial transparency.
*   **What it shows**: Map pins for all assets in a ward. Color-coded by status.
*   **Ultimate Insight**: The **"Delivery Score"** – a mathematical completeness score of how many assets have verifiable proof chains.

### 2. Proof Chain (The Traceability Engine)
*   **Goal**: Accountability.
*   **What it shows**: A vertical "Vertical Timeline" or "Dependency Tree". 
*   **The Path**: `Scheme` → `Actor` → `Asset` → `Evidence` → `Before/After Photos`.
*   **Ultimate Insight**: Proving exactly where the money went and showing the physical result.

### 3. Micro Accountability (The Citizen Bridge)
*   **Goal**: Last-mile engagement.
*   **What it shows**: Citizen-submitted grievances and a "Trigger Notification" panel.
*   **Action**: Officials can broadcast the "Before & After" proof directly to the WhatsApp numbers of residents on that specific street.

### 4. Agent Status (The Ingestion Lab)
*   **Goal**: Proving the "constantly updating" requirement.
*   **What it shows**: A live feed of the Hunter discovering a news article and the AI parsing it into a graph JSON in real-time.

---

## 4. Key IDs and Tools Summary

| Component | Tool / API | Canonical IDs / Mapping |
| :--- | :--- | :--- |
| **Search/Feeds** | Tavily Search API | Whitelisted: `pib.gov.in`, `mcdonline.nic.in` |
| **AI Extraction** | Groq (Llama-3.1-70B) | IDs: `SCH_PMAY`, `REG_W45`, `ACT_MCD` |
| **Graph DB** | Neo4j (Cypher) | Relations: `FUNDS`, `PROVES`, `LOCATED_IN` |
| **Media/Proof** | Twilio WhatsApp API | Triggered by `[:PROVES]` relationship in graph |
| **UI** | Streamlit | Dynamic Cypher-backed widgets |

---

## 5. Ultimate Goal Alignment
**Are we aligning with the problem statement?** 
**YES.** We aren't just building another dashboard. We are building the **connective tissue** that links disconnected government data points into a verifiable, audit-ready intelligence graph. By zooming from a National Scheme down to a single "Gali", we provide the most granular accountability engine ever designed for Indian Governance.
