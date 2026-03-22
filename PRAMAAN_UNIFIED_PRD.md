# PRAMAAN Unified Architecture & UI PRD

**Document Purpose**: This document connects the dots across the entire PRAMAAN repository. It defines exactly *why* the Agent exists, *why* the AI/LLM exists, how data flows through the three structured divisions, and how this architecture ultimately drives each page of the User Interface (UI).

---

## 1. The Core Philosophy: Why Agent? Why AI?

To build an automated, self-sustaining governance graph, we strictly decoupled the "Hunting" of data from the "Understanding" of data.

*   **Why is the Agent here?** The Ingestion Agent is our **Fetcher and Router**. It is a lightweight, autonomous system that monitors WhatsApp webhooks for citizen uploads, crawls government portals (PIB, eGramSwaraj), and executes web searches. It does *not* do deep intelligence mapping. Its only job is to procure raw data and decide what "shape" that data is.
*   **Why is the AI/LLM here?** The AI is our **Cognitive Parser**. Raw text, PDFs, and HTML are useless to a Neo4j Graph. The LLM's job is to read the raw files collected by the Agent, map the messy data to our strict Governance Ontology, validate the relationships, and format it for database insertion.

---

## 2. Module Architecture: How We Connect the Dots

### Module 1: The Agentic Router (Data Procurement)
1.  **Ingestion Triggers**: The agent wakes up via cron jobs (searching the web using Tavily) or intercepts live WhatsApp messages via a Twilio API webhook.
2.  **Classification**: The Agent evaluates the payload—is it a spreadsheet, a PDF report, or a raw news article?
3.  **The Three Divisions**: The Agent routes the raw file into one of three structural buckets:
    *   `/data/structured/raw/`: CSVs, JSONs, and direct API tabular feeds.
    *   `/data/semi_structured/raw/`: PDFs, KML files, and Excel sheets.
    *   `/data/unstructured/raw/`: Scraped markdown from news websites, public relations text, and citizen WhatsApp images.

### Module 2: The AI/LLM Mapping Engine (Data Extraction)
1.  **The Sweeper**: A downstream Python daemon constantly monitors the three `raw/` folders.
2.  **Extraction**: When a new file appears, the Sweeper sends the content to the LLM (Gemini/Groq). 
3.  **Ontology Mapping**: The LLM extracts Named Entities (NER) and Relations. It maps a news article into strict PRAMAAN nodes: `Asset`, `Region`, `Scheme`, `Beneficiary`, `Actor`, and `Evidence`.
4.  **Validation**: Before committing, the code validates the LLM's output against known constraints (e.g., "Does Ward 45 actually exist? Is this a valid scheme?").

### Module 3: Neo4j Graph Engine (Data Loading)
1.  **Insertion**: The validated JSON payload is converted into Cypher queries.
2.  **Graph Construction**: Neo4j builds the physical relationships (e.g., linking a newly discovered `Evidence` photo directly to the `Asset` node with a `[:PROVES]` edge).

---

## 3. UI Expectations: What We Want on Each Slide/Page

The Streamlit UI is the final consumer of the Neo4j Graph. As the Agent and AI continuously feed the graph, the UI dynamically reflects the ground truth.

### Page 1: Ward Map
*   **What it does:** Provides a geospatial, top-down view of governance delivery.
*   **Expectation from Graph:** Pulls all `Asset` nodes mapping to `Region` nodes.
*   **UI Experience:** Users select a specific Ward from the dropdowns. They see a map plotted with color-coded pins (Red = Delayed, Green = Completed). Side panels show the overall "Delivery Score" derived mathematically from the completeness of the asset's proof chain.

### Page 2: Proof Chain
*   **What it does:** The core transparency engine. It answers "Where did the money go, and where is the proof?"
*   **Expectation from Graph:** Executes deep Cypher graph traversals. When a user clicks an Asset, the query traces the path: `Scheme` -> `Actor` -> `Asset` -> `Evidence` -> `Beneficiary`.
*   **UI Experience:** A clean, vertical timeline or dependency tree. It visually displays the Before/After photos (Evidence), the executing contractor (Actor), the budget spent (Scheme), and the calculated number of impacted citizens (Beneficiaries).

### Page 3: Micro Accountability
*   **What it does:** Bridges the gap between the top-down scheme and bottom-up citizen feedback.
*   **Expectation from Graph:** Pulls citizen-submitted `Event` or `Evidence` nodes connected to `Asset` nodes.
*   **UI Experience:** Displays citizen grievances and WhatsApp proof submissions. Includes action buttons allowing Officials to trigger SMS/WhatsApp broadcasts to local beneficiaries to update them on asset repair statuses.

### Page 4: Live Ingestion (The Agent View)
*   **What it does:** Proves that the platform is autonomously updating.
*   **Expectation from Graph:** Monitors the ingestion logs and recent Neo4j commits.
*   **UI Experience:** A live, scrolling terminal-like feed revealing the Agent discovering a news article, routing it to `/unstructured/raw/`, the AI mapping the text into JSON, and the successful commit to Neo4j.

---

## 4. Strict Requirements: What is Required vs. Not Required

### What IS Required:
*   **Strict Separation of Concerns**: The Agent *never* writes directly to Neo4j. The LLM *never* crawls the web. The pipeline must flow linearly: Agent -> Raw Folders -> AI Mapper -> Validation -> Neo4j.
*   **Graph Completeness**: Assets must never be orphaned. The AI Mapper must guarantee that every new asset binds to a valid `Region` (Ward) and `Scheme`.
*   **Data Provenance**: Every Evidence node in the graph must carry a `source` tag (e.g., "WhatsApp Upload", "PIB Press Release") so users know exactly *how* the data was obtained.

### What is NOT Required:
*   **Dynamic Schema Adjustments**: The Agent and AI are not permitted to invent new node types. The Ontology (Asset, Scheme, Region, Actor, Evidence, Beneficiary, Event) is strictly locked.
*   **Real-time AI Chatbots on the Map**: The UI relies on deterministic, pre-calculated Cypher queries for the Ward Map and Proof Chain to guarantee sub-second load times. We are not generating Neo4j queries on the fly from user prompts in the primary views.
