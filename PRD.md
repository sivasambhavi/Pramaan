# Product Requirements Document (PRD) v2.0
## Global Ontology Engine — Governance Delivery Proof Platform
### *"One Graph That Proves What India Built."*

**Version:** 2.0  
**Date:** March 7, 2026  
**Team:** 3 Data Engineers  
**Target:** India Innovates 2026 | Data Mining & Processing Domain  
**Venue:** Bharat Mandapam, New Delhi | March 28-29, 2026  
**Timeline:** 21 days build → 2-day showcase (exhibition booth format)

---

## 1. Executive Summary

### 1.1 Vision

Build an AI-powered Global Ontology Engine that mines data from government schemes, budgets, assets, locations, beneficiaries, and evidence — then uses NLP to map them into a unified ontology and build a live knowledge graph. On top of this graph, decision-makers can ask natural-language questions like *"For this ward or street, what was built, which scheme funded it, who benefited, and what is the before/after proof?"* — and receive explainable, graph-grounded answers in under 3 seconds.

### 1.2 Official Problem Statement

> "Design and develop an AI-powered Global Ontology Engine that can collect and understand structured data, unstructured content, and live real-time feeds from areas like geopolitics, economics, defense, technology, climate, and society—and then connect all of it into a single, unified, constantly updating intelligence graph, so decision-makers can get clear insights for strategy, transparency, and national advantage for India and the world."

### 1.3 Our Interpretation & Product Positioning

We are implementing the Global Ontology Engine idea inside **Digital Democracy & Governance Delivery**. The engine connects what no existing system in India connects today:

- **PFMS** tracks money flow — but can't show what was physically built
- **eGramSwaraj** tracks geo-tagged assets — but can't link back to beneficiaries
- **Viksit Bharat Dashboard** shows national aggregates — but can't zoom to a single street
- **myScheme** helps citizens discover schemes — but doesn't prove what was delivered
- **State BMS systems** track beneficiaries — but don't connect to physical infrastructure

**Our engine is the connective tissue** — the semantic intelligence layer that links Scheme → Budget → Implementation → Asset → Location → Beneficiary → Evidence into one traceable, queryable knowledge graph.

- **Not:** Another dashboard or data visualization tool
- **Is:** A semantic intelligence platform that acts as a "shared brain" connecting siloed government delivery systems
- **Unique Value:** Full-chain traceability from central budget to street-level proof, with explainable AI reasoning backed by knowledge graph paths

### 1.4 One-Line Pitch

*"PFMS knows the money. eGramSwaraj knows the asset. We know the whole story."*

### 1.5 Target Users (Event-Specific)

The India Innovates 2026 audience at Bharat Mandapam consists of:

- **Primary:** MCD officials, ministry bureaucrats, elected representatives (MPs, MLAs, Councillors) who need to prove governance delivery in their constituencies
- **Secondary:** Gov-tech investors, political party operatives, ecosystem builders seeking scalable governance solutions
- **Future (Post-Hackathon):** NITI Aayog, PMO strategic units, state planning commissions, CAG audit teams, think tanks

### 1.6 Why This Wins at This Event

Three gaps the original PRD left unfilled:

1. **Audience gap:** The original climate-food-security scenario had no natural audience at a political technology event organized by MCD. The governance delivery framing speaks directly to every person at the booth.
2. **Problem-feeling gap:** Nobody at the event is losing sleep over heatwave-to-crop-yield cascades. They ARE losing sleep over: "I spent ₹50 crore on my constituency, did the work, and nobody believes me."
3. **Emotional hook gap:** The original was abstract ("connect ministry dashboards"). The new framing is specific: "Gali No. 7 in Shahdara — which scheme paid for the road, which leader pushed for it, proof photo linked to the resident."

The architecture is identical. What changed is who cares about the output.

---

## 2. Product Goals & Success Metrics

### 2.1 Goals for v2.0 (Prototype)

1. **Full Chain Traceability:** Demonstrate end-to-end Scheme → Budget → Asset → Location → Beneficiary → Evidence chain for at least 2-3 Delhi wards
2. **Ontology Completeness:** Cover all 6 domains at architecture level (governance delivery deep, 5 others thin)
3. **AI Integration:** LLM-powered extraction from unstructured content (press releases, news articles, PIB) + NL query interface
4. **Gap Analysis:** Identify where delivery chains break — missing links reveal fund leakage, awareness gaps, or stalled implementation
5. **Explainability:** Every answer shows graph paths, source provenance, and confidence scores
6. **Demo-Ready:** Stable, impressive booth demo that works with unreliable WiFi at Bharat Mandapam

### 2.2 Success Metrics

**Technical:**
- Graph contains ≥500 nodes across ≥5 entity types
- ≥3 domains represented with real data (governance deep, 2+ thin)
- ≥8 competency questions answerable end-to-end
- Query response time <3 seconds for typical questions
- ≥15 complete delivery chains (scheme → evidence) for demo wards

*MVP vs v2.0 scope:* For the March 7–10 MVP submission, we target a **single Delhi ward** with **~100–150 nodes**, **~200–300 edges**, and **5–8 complete delivery chains**. The multi-ward and 500+ node targets above apply to the **v2.0 deep implementation** if we are selected for the exhibition booth.

**Business:**
- Top 300 selection for India Innovates exhibition booth
- At least 1 judge asks "Can we use this for our ward/constituency?"
- Interest from ≥1 potential government implementation partner
- Positive engagement from ≥3 booth visitors who pull out their phones to take photos

**Competition Differentiator:**
- Only team showing full-chain traceability (not just dashboards or chatbots)
- Only team with before/after evidence layer linked to knowledge graph

---

## 3. User Personas & Use Cases

### 3.1 Primary Persona: Elected Representative / MCD Official

**Profile:**
- Councillor, MLA, or senior MCD official responsible for ward-level development
- Needs to prove governance delivery to constituents and voters
- Currently relies on manual reports, scattered photos, and anecdotal evidence
- Struggles to connect scheme allocations to ground-level outcomes

**Jobs to be Done:**
1. Prove what was built in their constituency with traceable evidence chains
2. Identify which wards have gaps in scheme coverage or implementation
3. Generate constituency-level "report cards" linking budgets to outcomes
4. Respond to citizen queries with verifiable data ("Was a drain built in my gali?")

**Key User Stories:**
- "As a councillor, I want to show voters exactly what was built in Ward 45 this year, which scheme funded it, and photo proof — so I can demonstrate my work."
- "As an MCD commissioner, I want to see which wards have the lowest scheme penetration so I can redirect resources."
- "As a party strategist, I want to compare delivery performance across constituencies before elections."

### 3.2 Secondary Persona: Governance Auditor / Policy Analyst

**Profile:**
- Works in CAG, NITI Aayog, or state planning department
- Needs to audit scheme delivery efficiency and identify fund utilization gaps
- Currently cross-references multiple disconnected portals manually

**Jobs to be Done:**
1. Trace fund flow from central allocation to street-level asset
2. Identify schemes with high allocation but low delivery
3. Flag wards with missing evidence or incomplete delivery chains
4. Compare delivery efficiency across regions for the same scheme

### 3.3 Secondary Persona: Citizen / Journalist / RTI Activist

**Profile:**
- Wants to verify government claims about development work
- Files RTI queries that take weeks to get incomplete answers
- Needs a single source of truth for ward-level governance data

**Jobs to be Done:**
1. Check what government work was done on their street
2. Verify if claimed scheme benefits actually reached their area
3. Access before/after evidence for infrastructure projects

---

## 4. Product Architecture

### 4.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
                  FRONTEND / DEMO LAYER
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Map View    │  │  Question    │  │  Proof Chain     │  │
│  │  (Ward Map)  │  │  Interface   │  │  Visualizer      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────────────────┐  ┌────────────────────────┐  │
│  │  Delivery Graph          │  │ Live Ingestion Demo    │  │
│  │  Visualization (Graph UI)│  │ + Gap Analysis         │  │
│  └──────────────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                        │
│  ┌──────────────────┐        ┌─────────────────────────┐   │
│  │  NL Query Engine │        │  Gap Detection &        │   │
│  │  (LLM + KG)     │        │  Chain Completeness     │   │
│  └──────────────────┘        └─────────────────────────┘   │
│  ┌──────────────────┐        ┌─────────────────────────┐   │
│  │  Answer Generator│        │  Delivery Score         │   │
│  │  (LLM + Context) │        │  Calculator            │   │
│  └──────────────────┘        └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│              KNOWLEDGE GRAPH LAYER (Neo4j)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Core Ontology: Region, Scheme, Actor, Asset,        │  │
│  │                 Beneficiary, Event, Indicator,        │  │
│  │                 Evidence                              │  │
│  │                                                       │  │
│  │  Deep Domain: Governance Delivery                     │  │
│  │  Thin Domains: Climate | Geopolitics | Defense |      │  │
│  │                Technology | Society                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                  DATA & AI ETL LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Structured  │  │ Unstructured │  │  Evidence         │  │
│  │  Ingestion   │  │ LLM Extract  │  │  Linking          │  │
│  │  (CSV/API)   │  │ (NER+RE)     │  │  (Geo-matching)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Entity Resolution & Normalization Engine             │  │
│  │  (Name disambiguation, location alias mapping)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                            │
│  data.gov.in | PFMS | eGramSwaraj | delhi.data.gov.in      │
│  MCD Portal | PIB | News/RSS | Geo-tagged Photos            │
│  Union Budget | PMGSY | PMAY | Swachh Bharat Mission        │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack

**Core Platform:**
- **Graph Database:** Neo4j (Community Edition / Aura Free Tier)
- **Backend:** Python 3.10+, FastAPI
- **LLM Services:** GROK/GEMINI (via API)
- **Data Processing:** Pandas, Python scripts
- **Entity Resolution:** Custom Python + fuzzy matching (FuzzyWuzzy/RapidFuzz)

**Infrastructure:**
- **Development:** Local Neo4j + FastAPI dev server
- **Demo Day:** Local Neo4j with pre-loaded graph (WiFi-independent) + cached LLM responses as fallback
- **Production (Future):** AWS Neptune / Neo4j Enterprise on MeghRaj cloud

**Frontend:**
- **Option A (Primary):** Streamlit — fastest to demo, map widgets built in
- **Option B (Stretch):** React + Leaflet for map + Neo4j Bloom for graph viz

---

## 5. Core Ontology Design

### 5.1 Core Entity Types

| Entity | Description | Key Properties | Example |
|--------|-------------|----------------|---------|
| **Region** | Geographic area (hierarchical) | name, type (country/state/district/constituency/ward/street), coordinates, population, ward_number | "Ward 45, Shahdara", "Gali No. 7" |
| **Scheme** | Government scheme/program | name, ministry, budget_allocated, budget_released, budget_utilized, target_beneficiaries, launch_date, category | "PMAY", "SFC Grant", "Swachh Bharat" |
| **Actor** | Organization/person/entity | name, type (ministry/department/agency/contractor/elected_rep), designation, constituency | "MCD East Zone", "Ward Councillor X" |
| **Asset** | Physical thing built/delivered | name, type (road/drain/streetlight/toilet/house/park), geo_coordinates, construction_start, construction_end, cost, status, contractor | "Drain in Gali 7, Shahdara, ₹12L" |
| **Beneficiary** | Aggregated beneficiary data | count, demographic_segment, ward, scheme, year | "450 households, Ward 45, PMAY, 2025" |
| **Event** | Time-bound governance occurrence | name, date, type (inauguration/inspection/complaint/milestone), description | "Road completed Ward 45, March 2025" |
| **Indicator** | Measurable metric | name, value, unit, timestamp, ward, scheme | "Scheme utilization rate 78%, Ward 45" |
| **Evidence** | Proof of delivery | type (photo/certificate/geo_tag), url, capture_date, geo_coordinates, before_or_after, linked_asset | "Before photo, Gali 7, Jan 2024" |

### 5.2 Core Relationships

| Relation | From → To | Meaning | Example |
|----------|-----------|---------|---------|
| **funds** | Scheme → Asset | Scheme provided budget for asset | SFC Grant → Drain in Gali 7 |
| **targets** | Scheme → Region | Scheme covers this region | PMAY → Ward 45, Shahdara |
| **benefits** | Scheme → Beneficiary | Scheme delivered to beneficiaries | PM-KISAN → 450 farmers, Ward 45 |
| **located_in** | Asset → Region | Asset physically in region (ward/street) | Drain → Gali 7, Ward 45 |
| **built_by** | Asset → Actor | Contractor/agency that built it | Drain → MCD East Zone |
| **represents** | Actor → Region | Elected rep for this constituency | Councillor X → Ward 45 |
| **implements** | Actor → Scheme | Actor executes this scheme | MCD → SFC Grant |
| **proves** | Evidence → Asset | Photo/certificate proves asset exists | Before/After photo → Drain |
| **captured_at** | Evidence → Region | Evidence geo-tagged to location | Photo → Gali 7, Shahdara |
| **measures** | Indicator → (Scheme + Region) | Metric tracks delivery in area | Utilization rate → SFC + Ward 45 |
| **occurred_at** | Event → Region | Event happened at location | Inauguration → Ward 45 |
| **related_to** | Event → Asset/Scheme | Event connected to specific asset | Inauguration → New Drain |
| **lives_in** | Beneficiary → Region | Beneficiary resides in area | 450 households → Ward 45 |
| **allocated_to** | Actor → Scheme | Actor allocated budget | Finance Ministry → PMAY |

### 5.3 Domain Tags

**Deep Domain — Governance Delivery:**
- `GovernanceScheme`: Central/state/municipal schemes
- `InfrastructureAsset`: Roads, drains, streetlights, buildings
- `WelfareDelivery`: Cash transfers, subsidies, housing
- `DeliveryEvent`: Inaugurations, inspections, completions

**Thin Domains (5-10 nodes each, proves architecture scales):**
- `ClimateHazard`: Heatwaves, floods affecting asset durability
- `GeopoliticsEvent`: Trade agreements affecting material costs
- `DefenseEvent`: Border infrastructure, dual-use asset tracking
- `TechEvent`: Digital India infrastructure, smart city nodes
- `SocialEvent`: Protests about poor infrastructure, citizen movements

### 5.4 The Delivery Chain (Core Graph Pattern)

This is the key innovation — a traceable chain that no existing system provides:

```
Central Budget → Scheme Allocation → State Release → District/Ward Budget
       ↓
   Implementing Agency (Actor) → Contractor (Actor)
       ↓
   Asset (built at geo-coordinates) → located_in → Ward → Street
       ↓
   Evidence (before photo, after photo, completion certificate)
       ↓
   Beneficiary (households/individuals in that ward)
       ↓
   Indicator (utilization rate, satisfaction, completion %)
```

**When a link is missing, the graph reveals the gap:**
- Budget allocated but no asset recorded → **fund leakage or stalling**
- Asset built but no beneficiary linkage → **delivery without reach**
- Asset claimed but no evidence → **unverified claim**
- High scheme count but low utilization → **awareness gap**

---

## 6. Data Sources & Procurement Strategy

This section defines the concrete data sources that PRAMAAÑ will use, how they map to the ontology, and how they are treated as **structured**, **semi-structured**, or **unstructured** inputs into the unified Neo4j knowledge graph.

All external sources ultimately flow into a **single Neo4j database** following the ontology in Section 5. We do not maintain multiple runtime databases; raw sources are stored as files, and the graph is the canonical store.

---

### 6.1 Structured Data Sources (Backbone)

These are tabular or API-based sources that map cleanly into CSVs and then into Neo4j.

#### 6.1.1 data.gov.in (Open Government Data Platform)

- **Type:** Structured (CSV / JSON via REST API).  
- **What:** National and state/district-level datasets for schemes and indicators (e.g., PM-KISAN, PMAY, Swachh Bharat, PMGSY).  
- **Fields used (indicative):**
  - Scheme codes and names.  
  - Beneficiary counts by district.  
  - Basic financials (allocation, utilization).  
- **Ontology mapping:**
  - `Scheme` nodes (base list and metadata).  
  - `Indicator` nodes for high-level metrics (optional for MVP).  
- **MVP usage:**
  - Seed 2–3 schemes in `schemes.csv` with realistic names and categories.  
  - Provide national context (e.g., PMAY exists and has X houses, but we focus on 1 ward slice).

#### 6.1.2 delhi.data.gov.in (Delhi Open Data Portal)

- **Type:** Structured (CSV / Excel downloads).  
- **What:** Ward-level or locality-level data on infrastructure, sanitation, roads, parks, etc.  
- **Fields used (indicative):**
  - Ward codes and names.  
  - Asset lists (roads, drains, streetlights) with coordinates or locality labels.  
- **Ontology mapping:**
  - `Region` nodes for the chosen ward and streets/gallis.  
  - `Asset` nodes for 3–5 demo assets in the chosen ward.  
- **MVP usage:**
  - Primary source for the **demo ward and asset list**, curated into:
    - `regions.csv`  
    - `assets.csv`.

#### 6.1.3 Union Budget & Scheme Portals (indiabudget.gov.in, PMGSY, etc.)

- **Type:** Structured / semi-structured (Excel, PDFs with tables, portal reports).  
- **What:** Scheme-level budgets and in some cases project-level details (PMGSY roads).  
- **Fields used (indicative):**
  - Scheme budget allocation and utilization (national or state level).  
  - Road/project metadata (name, cost, contractor, dates).  
- **Ontology mapping:**
  - `Scheme` properties: `budget_allocated`, `budget_utilized`, `year`.  
  - `Asset` properties: `cost`, `contractor`, `start_date`, `end_date`.  
- **MVP usage:**
  - Small, curated values to make demo chains feel realistic (e.g., “Drain in Gali 7 – cost ₹12L, funded by SFC Grant 2024”).

> **Implementation note:** For MVP, we do **not** build full scrapers. Instead, we manually curate small CSV slices from these sources into `data/` that align with our ontology.

---

### 6.2 Semi-Structured Data Sources (HTML Tables & Dashboards)

These have structure but require parsing or manual extraction.

#### 6.2.1 eGramSwaraj Portal (egramswaraj.gov.in)

- **Type:** HTML reports with embedded tables; some downloadable CSVs.  
- **What:** Rural development project lists, geo-tagged assets, fund utilization reports.  
- **Ontology mapping:**
  - Potential future mapping to `Region` (Gram Panchayat), `Asset`, `Scheme`, `Evidence`.  
- **MVP usage:**
  - Reference and future extension; optionally, 1–2 sample rural chains for demonstration of scalability beyond urban wards.

#### 6.2.2 PFMS Dashboard (pfmsdashboard.gov.in)

- **Type:** HTML dashboards + limited CSV exports.  
- **What:** Scheme-wise fund releases by state/district; DBT payments.  
- **Ontology mapping:**
  - `Scheme` nodes with `funds` relations and financial indicators.  
- **MVP usage:**
  - High-level numbers to justify use cases (e.g., “₹X crore released to Delhi under scheme Y”), but not deeply integrated into the ward graph due to granularity.

> **Implementation note:** In the MVP, semi-structured sources are mainly **conceptual drivers**. Where needed, 1–2 example rows will be manually turned into structured CSV entries and loaded into Neo4j.

---

### 6.3 Unstructured Data Sources (NLP / LLM Extraction Target)

These are the primary inputs for the **AI extraction pipeline**.

#### 6.3.1 PIB Press Releases (pib.gov.in)

- **Type:** Unstructured/semistructured text (HTML pages).  
- **What:** Official announcements of scheme launches, milestones, beneficiary counts, and project completions.  
- **Key entities to extract:**
  - Scheme names and abbreviations.  
  - Region names (states, districts, cities, wards where mentioned).  
  - Project descriptions (roads, drains, public buildings).  
  - Dates and event types (inauguration, completion, review meetings).  
  - Actor names (ministers, departments, implementing agencies).  
- **Ontology mapping via AI:**
  - `Scheme`, `Region`, `Asset`, `Actor`, `Event`, and `Evidence` where photo references exist.  
- **MVP usage:**
  - At least **one exemplar PIB release** about the chosen city/ward or a similar urban project.  
  - Used as the main text in the **Live Ingestion** demo:
    - Paste PIB text → `extract_governance_entities` → `POST /ingest/entities` → new nodes/edges in Neo4j.

#### 6.3.2 MCD Social Media & Press Releases

- **Type:** Unstructured text + images.  
- **What:** Ward-level announcements, inauguration posts, before/after pictures, local achievements.  
- **Key entities to extract:**
  - Ward numbers, street names, neighborhoods.  
  - Asset types (road, drain, park, streetlight).  
  - Leader/official names.  
  - Dates, slogans, and sometimes costs.  
- **Ontology mapping:**
  - Text → `Asset`, `Region`, `Actor`, `Event` nodes and relationships.  
  - Images → `Evidence` nodes linked to assets and regions.  
- **MVP usage:**
  - 10–15 curated before/after photos and captions feed into `evidence.csv` and then into Neo4j.  
  - Optionally, one MCD press note as a second unstructured example for extraction.

#### 6.3.3 News Articles (The Hindu, Indian Express, NDTV, etc.)

- **Type:** Unstructured text (news stories).  
- **What:** Coverage of infrastructure projects, governance failures/successes, citizen grievances.  
- **Key entities to extract:**
  - Location (ward/locality names).  
  - Project descriptions, costs, contractors.  
  - Timelines and delays.  
- **MVP usage:**
  - Optional enrichments: one or two articles used to show that PRAMAAÑ can absorb information **beyond official press releases**, still mapped into the same graph.

---

### 6.4 Evidence Layer Sources

These provide the **“proof” nodes** in the graph.

#### 6.4.1 Scheme & Portal Geo-tagged Photos

- **Type:** Image files (JPEG/PNG), sometimes with EXIF metadata.  
- **What:** Before/after photos from:
  - PMGSY roads  
  - PMAY houses  
  - Swachh Bharat toilets  
  - eGramSwaraj rural assets  
  - MCD social media posts  
- **Ontology mapping:**
  - Each curated photo becomes an `Evidence` node:
    - `evidence_id`, `type` (photo), `url_or_path`, `before_or_after`, `capture_date`.  
  - Linked via:
    - `(:Evidence)-[:PROVES]->(:Asset)`  
    - `(:Evidence)-[:CAPTURED_AT]->(:Region)`
- **MVP usage:**
  - 10–15 curated, manually-tagged images stored locally and referenced from `evidence.csv`.  
  - These drive the visual “Before vs After” experience in the Proof Chain Viewer.

> **Note:** For MVP, we do not rely on automatic EXIF reading. Spatial/temporal mapping is done manually for demo assets.

---

### 6.5 Storage & Integration Strategy

- **Raw Data Storage:**
  - Structured/semi-structured sources are downloaded or copied into `data/raw/` as CSV/Excel/text.  
  - PIB/news text is stored as `.txt` files in `data/raw/unstructured/`.  
  - Images are stored under `data/raw/images/`.

- **Canonical Graph Store:**
  - All curated and AI-enriched data is transformed into ontology-aligned CSVs in `data/`, then loaded into a **single Neo4j database** using `scripts/load_seed_data.py` and the ingestion API.
  - Neo4j is the **only runtime database** for PRAMAAÑ; there is no separate warehouse or per-source DB.

- **Provenance:**
  - Nodes and relationships include `source` and (where useful) `source_id` properties:
    - Example: `source: "delhi.data.gov.in"`, `source: "PIB"`, `source: "MCD_social"`  
  - This allows queries like: “show me all assets in Ward 45 where the proof came from MCD social media vs scheme portal photos.”

This strategy lets PRAMAAÑ demonstrate that it can **ingest structured, semi-structured, and unstructured data sources into one ontology-driven knowledge graph**, while keeping the implementation realistic for the MVP timeline.

### 6.6 Linking Data Sources into One Graph

All structured, semi-structured, and unstructured sources are linked inside a **single Neo4j graph** through three mechanisms:

1. **Canonical IDs per ontology entity**
   - Every node type has a stable ID generated or normalized by PRAMAAÑ:
     - `Region.region_id` – e.g., `WARD_45_SHAHDARA`, `STREET_W45_GALI7`.
     - `Scheme.scheme_id` – e.g., `SCHEME_PMAY`, `SCHEME_SFC_GRANT_2024`.
     - `Asset.asset_id` – e.g., `ASSET_W45_GALI7_DRAIN_2024`.
     - `Actor.actor_id`, `Beneficiary.beneficiary_id`, `Evidence.evidence_id`, `Event.event_id`.
   - During ETL and AI ingestion, external identifiers (codes in CSVs, names in PIB text) are **mapped or hashed** into these canonical IDs so that different sources referring to the same thing hit the same node.

2. **Entity Resolution & Normalization**
   - A small **entity resolution layer** (Python + RapidFuzz) reconciles:
     - Region aliases (e.g., “Ward 45”, “W-45”, “Shahdara Ward 45” → `WARD_45_SHAHDARA`).
     - Street aliases (e.g., “Gali No. 7”, “Gali 7”, “Street 7”).  
     - Scheme name variations (“Pradhan Mantri Awas Yojana”, “PMAY-U”).  
   - Rules:
     - Prefer official codes from structured data (Delhi portal, scheme codes) when available.
     - Fuzzy match PIB/news text to existing regions and schemes with a confidence threshold.
   - If confidence is low, the ingestion pipeline can:
     - Either skip that entity for MVP, or
     - Create a new node with a `confidence` property and a `needs_review = true` flag.

3. **Provenance Properties**
   - Every node and relationship stores a `source` field (and optionally `source_id`):
     - `source: "delhi.data.gov.in"`, `source: "PIB"`, `source: "MCD_social"`, etc.
   - This allows:
     - Explaining to users *where* each part of a delivery chain came from.
     - Answering meta-questions like:
       - “Which assets in this ward are only backed by social media proof vs scheme portal proof?”
   - Provenance is part of the **Explainability** story: every PRAMAAÑ answer can be traced back to specific sources.

#### Linking examples

- A road in Ward 45 found in a Delhi CSV and also mentioned in a PIB release:
  - Both are normalized to the same `asset_id` and `Region.region_id`, so they become a single `Asset` node with multiple `source` references and enriched properties.
- A before/after photo from MCD social media:
  - Stored as an `Evidence` node with `source = "MCD_social"`, linked via:
    - `(:Evidence)-[:PROVES]->(:Asset {asset_id: 'ASSET_W45_GALI7_DRAIN_2024'})`
    - `(:Evidence)-[:CAPTURED_AT]->(:Region {region_id: 'STREET_W45_GALI7'})`

With these rules, “linking” is not ad hoc; it is a **systematic process of ID normalization, fuzzy matching, and provenance tracking**, all inside one graph.

### 6.7 Data Procurement Challenges & Mitigations

| Challenge | Severity | Impact on Demo | Mitigation Strategy |
|-----------|----------|----------------|---------------------|
| **Ward-level data scarcity** — less than half of India's Municipal Corporations publish budgets online; ward-level scheme data is fragmented across PDFs and internal portals | HIGH | Could leave graph too sparse for compelling demo | Focus on 2–3 specific Delhi wards where MCD has published the most data; supplement with manual data curation from press releases and social media |
| **Location name inconsistency** — same district listed as "Kadapa," "Y.S.R.," and "Cuddapah" across datasets; wards may be numbered differently across portals | HIGH | Entity resolution failures break graph linkages | Build manual alias dictionary for demo scope (20–30 ward names + variants); use fuzzy matching library (RapidFuzz) for automated fallback |
| **Output vs outcome data** — government data tracks "toilets built" not "toilets used"; official numbers may overstate delivery | MEDIUM | Graph may reflect official claims, not ground truth | Explicitly label all data with source provenance and confidence; add "verification_status" property to Evidence nodes; acknowledge limitation in demo narrative |
| **Data format fragmentation** — PFMS in one format, eGramSwaraj in another, scheme portals in yet another; no common join keys | HIGH | ETL pipelines become complex and brittle | Standardize on a common internal schema early (Day 1–2); build per-source adapters; use Region (ward number + state) as the canonical join key |
| **eGovernance data access restrictions** — bulk downloads often unavailable; data visible on portals but not downloadable | MEDIUM | Limits data volume for graph | Use web scraping for public portals where legally permitted; supplement with data.gov.in API; manually curate critical gaps |
| **Geo-tagging accuracy** — GPS drift of 10–50 meters in government geo-tagged photos | LOW | Photo-to-asset matching may have errors | Use bounding-box matching (street-level), not point matching; manually verify for demo wards |
| **Data freshness** — many datasets last updated months or years ago | MEDIUM | Demo data may show old information | Acknowledge data freshness in UI ("Last updated: [date]"); use most recent available; supplement with recent news/PIB extractions |

---
6. Backend & Graph Platform Design (FastAPI + Neo4j)
6.1 Role of the Backend
The backend is the execution engine sitting on top of the ontology. It:
​

Materializes the ontology into a live Neo4j graph.

Provides stable, versioned REST APIs for ward overview, asset chains, gap analysis, and ingestion.

Encapsulates all Cypher logic so the UI and AI layers never talk to Neo4j directly.
​

The design goal is: ontology-centric, query-first APIs that are simple to call but powerful enough to answer governance questions.

6.2 Backend Components
All backend code lives under backend/app/ and is organized as:

main.py – FastAPI app entrypoint, router registration, global middleware.

config.py – Centralized configuration (Neo4j URI, credentials, environment flags).

neo4j_client.py – Neo4j driver initialization and query helpers.

models.py – Pydantic models for request/response schemas.

queries.py – All Cypher query strings and Python wrappers.

routers/

wards.py – Ward-level endpoints (overview, gaps).

assets.py – Asset-level endpoints (proof chains).

ingest.py – Ingestion endpoint for AI-extracted entities.

There is also a utility script:

scripts/load_seed_data.py – One-time and repeatable script for CSV → Neo4j loading.

This separation ensures the backend can evolve without breaking the ontology.
​

6.3 Neo4j Schema & Mapping to Ontology
The Neo4j schema mirrors the ontology (Section 5):

6.3.1 Node Labels
:Region

:Scheme

:Actor

:Asset

:Beneficiary

:Evidence

:Event

(Optional for thin domains: :ClimateHazard, :TechEvent, etc.)

Each label has a stable primary key property:

Region.region_id

Scheme.scheme_id

Actor.actor_id

Asset.asset_id

Beneficiary.beneficiary_id

Evidence.evidence_id

Event.event_id

Constraints:

CREATE CONSTRAINT region_id_unique IF NOT EXISTS FOR (r:Region) REQUIRE r.region_id IS UNIQUE;

Same pattern for other labels.

6.3.2 Relationship Types
Exact relationship types used in Neo4j:

:FUNDS (Scheme → Asset)

:TARGETS (Scheme → Region)

:BENEFITS (Scheme → Beneficiary)

:LOCATED_IN (Asset → Region)

:BUILT_BY (Asset → Actor)

:REPRESENTS (Actor → Region)

:IMPLEMENTS (Actor → Scheme)

:PROVES (Evidence → Asset)

:CAPTURED_AT (Evidence → Region)

:LIVES_IN (Beneficiary → Region)

:RELATED_TO (Event → Asset/Scheme/Region)

Each relationship can carry useful properties (e.g. FUNDS {amount, year}, TARGETS {start_year}), but MVP only uses a minimal set.
​

6.4 Data Loading: CSV → Graph
The script scripts/load_seed_data.py performs these steps:

Load Regions

Read regions.csv (city, ward, gali).

Create (:Region {region_id, name, type, ward_code, lat, lon}).

Link streets to wards using [:LOCATED_IN] if hierarchical modeling is used.

Load Schemes

Read schemes.csv.

Create (:Scheme {scheme_id, name, ministry, category, budget_allocated, budget_utilized, year}).

Load Actors

Read actors.csv.

Create (:Actor {actor_id, name, type, designation, region_id}).

Link (:Actor)-[:REPRESENTS]->(:Region) and (:Actor)-[:IMPLEMENTS]->(:Scheme) as needed.

Load Assets

Read assets.csv.

Create (:Asset {asset_id, name, type, ward_id, street_name, lat, lon, cost, construction_start, construction_end, status}).

Link:

(:Asset)-[:LOCATED_IN]->(:Region) (ward and/or gali).

(:Scheme)-[:FUNDS]->(:Asset) for each scheme funding it.

(:Asset)-[:BUILT_BY]->(:Actor) for implementing agency/contractor.

Load Beneficiaries

Read beneficiaries.csv.

Create (:Beneficiary {beneficiary_id, description, count, ward_id, scheme_id}).

Link:

(:Scheme)-[:BENEFITS]->(:Beneficiary)

(:Beneficiary)-[:LIVES_IN]->(:Region).

Load Evidence

Read evidence.csv.

Create (:Evidence {evidence_id, type, url_or_path, before_or_after, capture_date}).

Link:

(:Evidence)-[:PROVES]->(:Asset)

(:Evidence)-[:CAPTURED_AT]->(:Region).

Load Events (optional)

Read events.csv.

Create (:Event {event_id, name, type, date, description}).

Link to assets/schemes/regions via :RELATED_TO.

The loader enforces referential integrity: missing IDs are logged and skipped rather than creating dangling nodes.

6.5 Core Cypher Queries (Hero Use Cases)
All queries are encapsulated in queries.py as functions that return Python dicts/lists.

6.5.1 Ward Overview with Delivery Score
Goal: For each ward, compute:

Number of assets

Number of schemes

Number of assets with “full chains”

Delivery Score = full_chain_assets / total_assets × 100

Cypher (conceptual):

text
MATCH (w:Region {type: 'ward'})
OPTIONAL MATCH (a:Asset)-[:LOCATED_IN]->(w)
WITH w, collect(a) AS assets
WITH w,
     assets,
     size(assets) AS total_assets

// full chain: asset has Scheme, Evidence, Beneficiary
UNWIND assets AS asset
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(asset)
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(asset)
OPTIONAL MATCH (asset)<-[:BENEFITS]-(s2:Scheme)<-[:BENEFITS]-(b:Beneficiary)-[:LIVES_IN]->(w)
WITH w, total_assets,
     collect(DISTINCT asset) AS assets2,
     collect(DISTINCT CASE WHEN s IS NOT NULL
                            AND e IS NOT NULL
                            AND b IS NOT NULL
                      THEN asset END) AS full_chain_assets
WITH w, total_assets, size([x IN full_chain_assets WHERE x IS NOT NULL]) AS num_full
RETURN w.region_id AS ward_id,
       w.name AS ward_name,
       total_assets,
       num_full,
       CASE WHEN total_assets = 0 THEN 0.0
            ELSE 100.0 * num_full / total_assets END AS delivery_score;
This query becomes get_wards_with_scores().

6.5.2 Ward Assets List
Goal: List all assets in a ward with key attributes and flags.

Returns: asset_id, name, type, scheme_names, has_evidence, status.

Cypher (conceptual):

text
MATCH (w:Region {region_id: $ward_id})
MATCH (a:Asset)-[:LOCATED_IN]->(w)
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
RETURN a.asset_id AS asset_id,
       a.name AS name,
       a.type AS type,
       collect(DISTINCT s.name) AS schemes,
       a.status AS status,
       CASE WHEN count(e) > 0 THEN true ELSE false END AS has_evidence;
6.5.3 Asset Proof Chain
Goal: Given an asset, return full chain:

Scheme(s), Actors, Regions (ward + gali), Beneficiaries, Evidence.

Cypher (conceptual):

text
MATCH (a:Asset {asset_id: $asset_id})
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
OPTIONAL MATCH (a)-[:LOCATED_IN]->(w:Region {type:'ward'})
OPTIONAL MATCH (a)-[:LOCATED_IN]->(g:Region {type:'street'})
OPTIONAL MATCH (a)-[:BUILT_BY]->(act:Actor)
OPTIONAL MATCH (a)<-[:PROVES]-(e:Evidence)
OPTIONAL MATCH (s)-[:BENEFITS]->(b:Beneficiary)-[:LIVES_IN]->(w)
RETURN a, collect(DISTINCT s) AS schemes,
       w, g,
       collect(DISTINCT act) AS actors,
       collect(DISTINCT b) AS beneficiaries,
       collect(DISTINCT e) AS evidence;
The backend transforms this into a nested JSON for the UI.

6.5.4 Ward Gaps
Goal: For a ward, detect:

Schemes that target ward but have no assets.

Assets in ward with no evidence.

Conceptual queries:

Schemes without assets:

text
MATCH (s:Scheme)-[:TARGETS]->(w:Region {region_id: $ward_id})
OPTIONAL MATCH (s)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(w)
WITH s, count(a) AS asset_count
WHERE asset_count = 0
RETURN s.scheme_id, s.name;
Assets without evidence:

text
MATCH (w:Region {region_id: $ward_id})
MATCH (a:Asset)-[:LOCATED_IN]->(w)
OPTIONAL MATCH (a)<-[:PROVES]-(e:Evidence)
WITH a, count(e) AS evidence_count
WHERE evidence_count = 0
RETURN a.asset_id, a.name;
6.6 FastAPI Endpoints & Models
models.py defines Pydantic models like:

WardSummary – ward_id, name, delivery_score, asset_count, scheme_count.

AssetSummary – asset_id, name, type, schemes, status, has_evidence.

AssetChain – nested structure for chain.

GapSummary – arrays of SchemeGap and AssetGap.

IngestResult – counts of created/updated nodes/edges.

Routers:

GET /health – simple health check.

GET /wards – returns List[WardSummary].

GET /wards/{ward_id}/assets – returns List[AssetSummary].

GET /assets/{asset_id}/chain – returns AssetChain.

GET /wards/{ward_id}/gaps – returns GapSummary.

POST /ingest/entities – accepts JSON aligned to ontology, returns IngestResult.

All endpoints are designed to be simple to consume from Streamlit.

7. AI & Experience Design (Streamlit + LLM)
7.1 Role of the Experience Layer
The AI & UI layer turns the ontology and backend into a visceral experience:

Politicians and officials see ward-level Delivery Scores and proof chains.

Visual graph view makes it feel like a real intelligence system.

Live ingestion shows the graph “learning” from new text.

This layer focuses on clarity and trust, not just fancy widgets.

7.2 Streamlit Application Structure
All UI code lives in frontend/:

app.py

Sets st.set_page_config, global layout, logo, and tagline.

Provides navigation and context (e.g., selected ward).

pages/01_🏙_Ward_Map.py – Ward Overview

pages/02_🧷_Proof_Chain.py – Asset proof chain viewer

pages/03_❓_Questions.py – NL questions (3 fixed)

pages/04_⚡_Live_Ingestion.py – AI extraction + ingestion

pages/05_🕸_Delivery_Graph.py – Delivery Graph Visualization

Each page calls FastAPI endpoints via requests or httpx.

7.3 Screen Designs
7.3.1 Ward Overview (01_🏙_Ward_Map.py)
Data Source: GET /wards.

Layout:

Top: Ward name + large Delivery Score metric.

Left: summary cards (# assets, # schemes, # assets with evidence).

Center: table of assets (name, type, schemes, status, evidence flag).

Optional: simple map or ward graphic.

Interactions:

Clicking an asset row stores asset_id in st.session_state and navigates to Proof Chain Viewer.

7.3.2 Proof Chain Viewer (02_🧷_Proof_Chain.py)
Data Source:

Uses asset_id from state.

Calls GET /assets/{asset_id}/chain.

Layout:

Left: textual summary:

Asset name, type, location, schemes, cost, dates, contractor.

Middle: timeline or vertical chain:

“Scheme sanctioned” → “Work started” → “Work completed” → “Evidence collected” → “Beneficiaries.”

Right: evidence images:

Before photo (labelled, date).

After photo (labelled, date).

Goal: Give a story-like narrative of one asset’s delivery.

7.3.3 Gap Analysis (could be part of Ward Overview or separate)
Data Source: GET /wards/{ward_id}/gaps.

Layout:

Two sections:

“Schemes announced, nothing visible”: list of schemes with no assets.

“Assets with weak proof”: list of assets with no evidence.

Color-coded:

Green = full chain.

Yellow = partial.

Red = gap.

Goal: Show where delivery chains break, not just where they exist.

7.3.4 Delivery Graph Visualization (05_🕸_Delivery_Graph.py)
Data Source:

Either GET /assets/{asset_id}/chain or a dedicated graph endpoint.

Layout:

Center: network graph (using pyvis or similar) with:

Node colors by type (scheme, asset, region, actor, beneficiary, evidence).

Edge labels (FUNDS, LOCATED_IN, PROVES, etc.).

Side panel: details of whichever node is clicked.

Goal: Make PRAMAAÑ look and feel like a knowledge-graph intelligence console.

7.3.5 Live Ingestion (04_⚡_Live_Ingestion.py)
Data Source: ai_extraction.py + POST /ingest/entities.

Flow:

Paste PIB/news text into a text area.

Click Extract & Preview:

Calls extract_governance_entities(text); shows JSON / tables of proposed schemes, assets, regions, actors, events, evidence.

Click Ingest into Graph:

Sends JSON to backend ingestion endpoint.

Shows a small success summary (nodes/edges created).

Offer a button to “View updated assets” which navigates back to Ward Overview.

Offline Mode:

For the main demo text, load a pre-computed JSON from disk instead of calling the LLM.

7.4 AI Modules in Detail
7.4.1 ai_extraction.py
Function:

python
def extract_governance_entities(text: str) -> dict:
    ...
Input: raw PIB/news text.

Behavior:

Calls LLM with a prompt that explains the ontology and asks for a structured JSON:

schemes: list of {scheme_id?, name, ministry, category}

assets: list of {asset_id?, name, type, ward_name, street_name, cost?}

regions: list of {region_id?, name, type}

actors: list of {actor_id?, name, type, role}

evidence: list of {evidence_id?, type, url_or_caption, before_or_after}

events: list of {event_id?, name, type, date}

Validates JSON, fills missing IDs (e.g., with deterministic hashes).

Output: dict ready to send to POST /ingest/entities.

7.4.2 nl_query.py
For MVP, not a full NL engine—just a router:

Predefined 3 buttons or query types:

WARD_SUMMARY → calls GET /wards.

GALI_CHAIN → asks user for street name, maps to asset, calls GET /assets/{asset_id}/chain.

SCHEME_GAPS → calls GET /wards/{ward_id}/gaps.

Optional: if you want, you can still call an LLM to rephrase outputs into natural language, but the core routing is deterministic, not magic.

7.5 Offline & Demo Resilience
Cache extraction result for one main PIB text in e.g. ai/cache/demo_extraction.json.

In ai_extraction.py, if offline_mode is on, return the cached JSON instead of calling the LLM.

For NL questions, you can completely bypass LLM and just map buttons → queries → human-written answer templates.



---

## 7. Flagship Scenario (v2.0 Deep Implementation)

### 7.1 Chosen Scenario

**"Governance Delivery Proof — What Was Built in Your Ward"**

**Geographic Scope:** MVP (March 7–10): 1 Delhi ward (e.g., Ward 45 Shahdara). v2.0 deep implementation (post-selection): 2-3 Delhi wards (recommended: Ward 45 Shahdara, Ward 68 Karol Bagh, one South Delhi ward) — chosen for data availability and MCD relevance.

**Why this scenario:**
- Directly relevant to MCD (event organizer)
- Every person at the booth cares about ward-level delivery
- Real data available from Delhi open data portal and MCD social media
- Demonstrates full ontology chain (Scheme → Budget → Asset → Location → Beneficiary → Evidence)
- Creates emotional reaction: "That's MY ward!"

### 7.2 Demo Data Coverage (v2.0 Deep Implementation)

*For the MVP, we implement this scenario for a single ward with ~100–150 nodes and 5–8 complete chains; the multi-ward numbers below are post-selection stretch targets.*

**Per Ward (target: 2-3 wards):**
- 3-5 schemes active in that ward (PMAY, SFC, Swachh Bharat, AMRUT, smart city components)
- 5-8 assets (roads, drains, streetlights, toilets, parks, buildings)
- Budget allocation and release figures for each scheme
- Implementing agency and contractor where available
- 10-15 beneficiary aggregates (households covered by scheme in that ward)
- 5-7 before/after evidence pairs (geo-tagged photos)
- 3-5 events (inaugurations, inspections, milestones)
- 2-3 indicators per ward (scheme utilization rate, completion %, fund release ratio)

**Total Demo Graph Target:**
- ≥500 nodes across 8 entity types
- ≥1,500 edges across 14 relationship types
- ≥15 complete delivery chains (scheme → evidence)
- ≥15 before/after evidence pairs

### 7.3 Competency Questions (Must Answer End-to-End)

1. **"What assets were built in Ward 45, Shahdara in the last 2 years?"**
   → Returns: List of assets with type, cost, scheme, status, evidence availability

2. **"Which scheme funded the drain in Gali No. 7, Shahdara?"**
   → Returns: SFC Grant, ₹12 lakh, MCD East Zone implemented, completed March 2025

3. **"Show me the before/after proof for the road resurfacing in Ward 45."**
   → Returns: Before photo (Jan 2024), after photo (March 2025), geo-coordinates match

4. **"How much budget was allocated vs actually spent in Ward 45 under PMAY?"**
   → Returns: Allocated ₹2.5 Cr, Released ₹1.8 Cr, Utilized ₹1.2 Cr, Utilization rate 48%

5. **"Which wards have the lowest scheme penetration in East Delhi?"**
   → Returns: Ranked list of wards by delivery score (composite of chains, evidence, utilization)

6. **"Who is responsible for implementing Swachh Bharat in Ward 68?"**
   → Returns: Actor chain — MCD → Karol Bagh Zone → Ward Sanitation Officer → Contractor Y

7. **"Show me the full delivery chain for the streetlights on MG Road, Karol Bagh."**
   → Returns: Visual graph trace — Central Budget → AMRUT → MCD → Zone → Contractor → 12 streetlights → Geo-tagged → 200 households nearby → Before/after photos

8. **"Where are the gaps? Which assets have no evidence linked?"**
   → Returns: List of assets missing before/after photos, flagged as "unverified delivery"

### 7.4 Supporting Scenarios (Thin Coverage — "One Deep, Five Thin")

To prove the architecture is global and multi-domain:

**Climate (5-10 nodes):**
- 2-3 climate events (heatwave, flood) affecting Delhi/NCR
- Link: ClimateHazard → damages → Asset (how climate affects built infrastructure)
- Demo question: "Which ward assets are at risk from monsoon flooding?"

**Geopolitics (3-5 nodes):**
- 1-2 trade events affecting construction material prices
- Link: GeopoliticsEvent → impacts → Indicator (steel/cement prices) → affects → Asset (cost overrun)

**Defense (3-5 nodes):**
- 1-2 dual-use infrastructure nodes (border roads, strategic bridges)
- Link: DefenseEvent → located_in → Region → also has → GovernanceScheme assets

**Technology (5-8 nodes):**
- Smart city/Digital India components deployed in Delhi
- Link: TechEvent → implements → Asset (WiFi hotspot, digital kiosk)

**Society (3-5 nodes):**
- Citizen protests about poor infrastructure
- Link: SocialEvent → occurred_at → Region → related_to → Asset (complained about)

**When judges ask "How is this global?"** → Show thin domains + say: "Same ontology, any domain, any country. Replace 'MCD Ward 45' with 'District 5, Nairobi' or 'Borough of Hackney, London' — the graph structure is identical."

---

## 8. Detailed Requirements

### 8.1 Functional Requirements

**FR-1: Data Ingestion**
- FR-1.1: System shall ingest CSV files with ward-level scheme, asset, and beneficiary data
- FR-1.2: System shall parse unstructured text (PIB releases, news articles, MCD posts) using LLM for entity extraction
- FR-1.3: System shall normalize entity names using alias dictionary and fuzzy matching (e.g., "Shahdara" = "शाहदरा" = "Shah Dara")
- FR-1.4: System shall support incremental updates without full graph rebuild
- FR-1.5: System shall timestamp all data with ingestion_date, source_date, and source_url
- FR-1.6: System shall link geo-tagged photos to nearest Asset node using bounding-box spatial matching

**FR-2: Knowledge Graph**
- FR-2.1: Graph shall implement all 8 core entity types and 14 relationship types per ontology
- FR-2.2: Each node shall have unique ID, type label, domain tag, and provenance metadata
- FR-2.3: System shall maintain provenance (source, confidence score, last_verified) for each node/edge
- FR-2.4: Graph shall support multi-hop traversal queries (≥5 hops for full delivery chain)
- FR-2.5: System shall calculate "Chain Completeness Score" per ward (% of assets with full scheme→evidence chain)
- FR-2.6: System shall detect and flag incomplete delivery chains (missing links)

**FR-3: LLM-Powered Extraction**
- FR-3.1: System shall extract entities (Region, Scheme, Actor, Asset, Event, Indicator) from unstructured text
- FR-3.2: System shall identify relationships between extracted entities
- FR-3.3: System shall map extracted entities to ontology schema with confidence scores
- FR-3.4: System shall handle Hindi and English mixed-language content
- FR-3.5: Extraction results shall be cached for deterministic demo behavior

**FR-4: Natural Language Query**
- FR-4.1: User shall ask questions in natural language (English + Hindi keywords)
- FR-4.2: System shall classify question into one of 8-10 pre-built query templates
- FR-4.3: System shall extract parameters (ward name, scheme name, date range) from natural language
- FR-4.4: System shall return structured answer + natural language explanation + graph path visualization
- FR-4.5: System shall cite sources and show confidence for all factual claims

**FR-5: Gap Analysis & Delivery Scoring**
- FR-5.1: System shall calculate per-ward "Delivery Score" (composite metric)
- FR-5.2: System shall identify assets with missing evidence (unverified claims)
- FR-5.3: System shall identify schemes with budget allocated but no assets recorded (stalled implementation)
- FR-5.4: System shall rank wards by scheme penetration density
- FR-5.5: System shall highlight "model wards" (high delivery score) vs "gap wards" (low score)

**FR-6: Evidence Management**
- FR-6.1: System shall store and display before/after photo pairs linked to specific assets
- FR-6.2: System shall show evidence on a map view with geo-coordinates
- FR-6.3: System shall display evidence timeline (before date → construction → after date)

### 8.2 Non-Functional Requirements

**NFR-1: Performance**
- Query response time: <3 seconds for typical queries, <5 seconds for complex multi-hop
- Graph size: Support ≥10,000 nodes and ≥50,000 edges
- Ingestion: Process ≥100 documents per hour via LLM extraction

**NFR-2: Reliability**
- System uptime: 99% during 2-day demo period
- Demo MUST work offline (pre-loaded graph + cached LLM responses)
- Data accuracy: ≥85% entity extraction precision on government text
- Graph consistency: No orphaned nodes or dangling edges

**NFR-3: Usability**
- Non-technical users (councillors, officers) can ask questions without training
- Pre-loaded example questions visible in UI sidebar
- Map-based navigation for geographic exploration
- Graph visualizations are interpretable with labeled nodes and edges

**NFR-4: Explainability**
- All answers include source attribution (portal name, date, URL)
- Graph reasoning paths are visible and interactive
- Confidence scores displayed for LLM-extracted data (vs structured source data)
- Chain Completeness Score shown per ward

**NFR-5: Demo Resilience**
- Offline mode: Full demo functional without internet (pre-loaded Neo4j + cached responses)
- Fallback: Recorded video demo (4-5 minutes) if live system fails
- Backup laptop with identical setup
- Pre-tested with ≥10 rehearsals before event

---

## 9. API Specifications

### 9.1 Core APIs

**Ingestion APIs:**
```
POST /api/v1/ingest/structured
Body: {file: CSV, entity_type: "Scheme"|"Asset"|"Beneficiary"|"Region"}
Response: {nodes_created: int, edges_created: int, errors: [], warnings: []}

POST /api/v1/ingest/unstructured
Body: {text: string, source: string, source_url: string, date: string}
Response: {entities: [{type, name, properties, confidence}], relations: [{from, relation, to, confidence}]}

POST /api/v1/ingest/evidence
Body: {image_url: string, geo_lat: float, geo_lng: float, capture_date: string, before_or_after: "before"|"after"}
Response: {evidence_id: string, linked_asset_id: string, match_confidence: float}
```

**Query APIs:**
```
GET /api/v1/query/ward_assets?ward=45&zone=shahdara&years=2
Response: {assets: [{name, type, cost, scheme, status, evidence_count, chain_complete: bool}]}

GET /api/v1/query/scheme_coverage?scheme=PMAY&region=east_delhi
Response: {wards: [{ward_number, budget_allocated, budget_utilized, assets_built, beneficiaries, utilization_rate}]}

GET /api/v1/query/delivery_chain?asset_id=123
Response: {chain: [{node_type, node_name, relationship, next_node}], completeness_score: float, missing_links: []}

GET /api/v1/query/gap_analysis?region=east_delhi
Response: {gap_wards: [{ward, missing_evidence_count, stalled_schemes, delivery_score}], model_wards: [{ward, delivery_score}]}

POST /api/v1/query/natural_language
Body: {question: string}
Response: {answer: string, explanation: string, sources: [], graph_path: {nodes: [], edges: []}, confidence: float}
```

**Graph APIs:**
```
GET /api/v1/graph/neighbors?node_id=123&depth=2
Response: {nodes: [], edges: []}

GET /api/v1/graph/path?from_id=123&to_id=456
Response: {path: [{node, edge, node, ...}], hops: int}

GET /api/v1/graph/ward_map?zone=shahdara
Response: {wards: [{ward_number, geo_boundary, delivery_score, asset_count, scheme_count}]}
```

### 9.2 LLM Service APIs (Internal)

```
POST /llm/extract_entities
Body: {text: string, schema: ontology_schema, language: "en"|"hi"|"mixed"}
Response: {entities: [{type, name, properties, confidence}], relations: [{from, relation, to, confidence}]}

POST /llm/classify_question
Body: {question: string, available_templates: [query_templates]}
Response: {template_id: string, parameters: {ward: string, scheme: string, ...}, confidence: float}

POST /llm/generate_explanation
Body: {query_result: {}, question: string, graph_path: {}}
Response: {explanation: string, key_findings: [], confidence: float}
```

---

## 10. Demo Script & Narrative

### 10.1 The Booth Demo Story (5-7 minutes, judge walks up)

**Hook (30 seconds):**
- Poster behind booth: *"One Graph That Proves What India Built."*
- Opening line: "Sir/Ma'am, ₹50,000 crore is spent on Delhi's development every year. Can you tell me what was built on YOUR street? Nobody can. We built the system that answers that question."

**Act 1: The Problem (1 minute):**
- Show the comparison table: PFMS, eGramSwaraj, Viksit Bharat dashboard — each tracks one piece
- "Money is tracked here. Assets are tracked there. Beneficiaries somewhere else. Nobody connects them."
- "We built the graph that connects ALL of them."

**Act 2: The Map View (1.5 minutes):**
- Show Delhi ward map, color-coded by Delivery Score
- Green wards (high delivery), red wards (gaps)
- Click Ward 45, Shahdara — zoom in
- Show all assets, schemes, and evidence linked to that ward
- "This ward has 8 assets built across 4 schemes. 6 have evidence. 2 are unverified."

**Act 3: The Proof Chain — The Jaw-Drop Moment (2 minutes):**
- Click on "Drain in Gali No. 7, Shahdara"
- Full chain appears: Central Budget → SFC Grant → ₹12 lakh → MCD East Zone → Contractor → Drain → Geo-coordinates → Before photo (broken road, stagnant water, Jan 2024) → After photo (new drain, clean road, March 2025) → 120 households benefited
- "This is the FULL story. Nobody else shows you this."
- Judge reaction target: pulls out phone to photograph the screen

**Act 4: Natural Language Query (1 minute):**
- Type: "Which wards in East Delhi have the most unverified assets?"
- System returns ranked list with gap analysis
- "This isn't just proof of what was done. It's a map of what WASN'T done."

**Act 5: Live Ingestion (30 seconds):**
- Paste a PIB press release about a new scheme announcement
- Watch LLM extract entities in real-time
- New nodes appear on graph
- "The engine is alive. Feed it any government text — it grows the graph automatically."

**Act 6: The Global Architecture (30 seconds):**
- Show thin domain nodes (climate, geopolitics, defense, tech, society)
- "Same engine works for climate resilience, defense infrastructure, trade impact analysis"
- "Replace Delhi with Nairobi or London — same graph, same ontology"

**Close (30 seconds):**
- "One graph. Full chain. Street-level proof."
- "We're three data engineers who built this in 3 weeks. Imagine what a ministry can do with it in 3 months."
- Hand over one-pager with QR code to project repo/demo

### 10.2 Fallback Plans

| Failure Scenario | Fallback |
|------------------|----------|
| WiFi down at Bharat Mandapam | Pre-loaded local Neo4j + cached LLM responses; demo runs fully offline |
| Live demo crashes | Recorded screen demo video (4-5 min), play on laptop |
| Neo4j goes down | Static slides with screenshots + architecture walkthrough |
| Judge asks question outside demo scope | Redirect: "Great question — let me show you what we CAN trace today, and explain how this extends" |
| Backup laptop | Identical setup on second machine; USB drive with full project |

---

## 11. Evaluation Criteria Mapping

### 11.1 India Innovates Judging Criteria

| Criterion | How We Address It | Evidence in Demo |
|-----------|-------------------|------------------|
| **Product Clarity & Impact** | Clear value prop: "One graph that proves what India built" — full-chain traceability from budget to street-level proof | Opening narrative + Proof Chain visualization + before/after evidence |
| **Innovation & Scalability** | Novel: Only system connecting PFMS + eGramSwaraj + Evidence into one graph via LLM-powered ontology; Scalable: same architecture for any country/domain | Comparison table vs existing systems + thin domain coverage + "replace Delhi with Nairobi" line |
| **Feasibility & Execution** | Working prototype with real Delhi data, not mockups; 500+ nodes, 15+ complete chains | Live demo of query, ingestion, gap analysis; real ward numbers and scheme names |
| **Relevance to Domain** | Directly implements "Global Ontology Engine" problem statement — data mining from structured + unstructured sources into unified intelligence graph | Explicit slide mapping our architecture to problem statement keywords |

### 11.2 Key Differentiators from Competition

- **Not a dashboard:** We're the intelligence layer that makes dashboards smart
- **Not just NLP/chatbot:** Every answer is backed by graph paths, not hallucination
- **Not a data visualization:** We connect data that was never connected before
- **Not ward-specific:** Architecture is domain-agnostic and globally extensible
- **Not static:** Continuously updating from live feeds and NLP extraction
- **The unique feature nobody else has:** Before/after EVIDENCE linked to knowledge graph nodes

---

## 12. Work Breakdown & Team Structure

### 12.1 Team Roles

**Person A: Ontology & Data Curation Lead - Siva Sambhavi**
- Owns: Ontology design, data sourcing, manual curation, evidence collection
- Skills: Domain research, data cleaning, semantic modeling
- Critical task: Curate 15+ complete delivery chains with real data for 2-3 wards
- Time: 30% ontology design, 50% data curation, 20% validation

**Person B: Data & Graph Platform Lead - K Aparna**
- Owns: Neo4j setup, ETL pipelines, Cypher queries, entity resolution, API development
- Skills: Python, Neo4j/Cypher, data engineering, FastAPI
- Critical task: Build robust ETL that handles format fragmentation across sources
- Time: 20% infra, 50% ETL + entity resolution, 30% query optimization + API

**Person C: AI & Experience Lead - C Sreenu**
- Owns: LLM integration, NL interface, extraction pipeline, Streamlit UI
- Skills: Python, LLM APIs, prompt engineering, Streamlit, basic mapping
- Critical task: Achieve ≥85% extraction accuracy on government text
- Time: 35% LLM services, 35% UI/demo, 30% integration + caching

### 12.2 Phase 1: Foundation 

**All Team:**
- [ ] Finalize 2-3 target Delhi wards based on data availability audit
- [ ] Set up shared repo, dev environment, Neo4j instance
- [ ] Agree on API contracts between components
- [ ] Register data.gov.in API key and test access

**Person A: Siva Sambhavi**
- [ ] Finalize ontology document (8 entities, 14 relations, properties)
- [ ] Create visual ontology diagram
- [ ] Write 8-10 competency questions for governance delivery scenario
- [ ] Begin data audit: download available datasets for target wards
- [ ] Build location alias dictionary for Delhi wards (name variants)
- [ ] Start evidence collection: find 15+ before/after photo pairs from MCD social media

**Person B: K Aparna**
- [ ] Provision Neo4j instance (local + Aura backup)
- [ ] Implement core schema (constraints, indexes, unique IDs)
- [ ] Write sample data loader scripts for each entity type
- [ ] Build CSV adapters for data.gov.in, delhi.data.gov.in, PFMS formats
- [ ] Implement entity resolution module (alias dictionary + fuzzy matching)

**Person C: C Sreenu**
- [ ] Set up FastAPI project skeleton with all endpoint stubs
- [ ] Test LLM API access (Claude/GPT-4)
- [ ] Write entity extraction prompts for government text (PIB format, news format, MCD post format)
- [ ] Build extraction prompt testing harness (input text → extracted JSON → validation)
- [ ] Create basic Streamlit UI wireframe

### 12.3 Phase 2: Deep Implementation 

**Person A:**
- [ ] Curate complete delivery chain data for Ward 1 (all entities + relationships)
- [ ] Curate complete delivery chain data for Ward 2
- [ ] Manually create 30-50 high-quality seed nodes with verified data
- [ ] Collect and tag 15+ before/after photo pairs with metadata
- [ ] Write test queries to validate competency questions against loaded data
- [ ] Begin thin domain data collection (5-10 nodes per domain)

**Person B:**
- [ ] Build full ETL pipelines for all structured sources
- [ ] Load Ward 1 and Ward 2 data into Neo4j
- [ ] Implement 8-10 parameterized Cypher queries for competency questions
- [ ] Build Delivery Score calculation (Chain Completeness algorithm)
- [ ] Build Gap Analysis queries (missing evidence, stalled schemes)
- [ ] Expose all REST endpoints
- [ ] Set up query result caching for demo reliability

**Person C:**
- [ ] Build LLM extraction service: text → entities + relations JSON
- [ ] Integrate extraction with Person B's ingestion pipeline
- [ ] Process 20-30 PIB releases and news articles for target wards
- [ ] Build NL query classifier: question → template selection + parameter extraction
- [ ] Build answer generation: query result → natural language explanation
- [ ] Cache all LLM responses for offline demo mode

### 12.4 Phase 3: Integration & Polish 

**All Team:**
- [ ] End-to-end integration test: data → graph → query → answer → visualization
- [ ] Fix integration bugs and edge cases
- [ ] Load thin domain data (5-10 nodes per remaining domain)

**Person A:**
- [ ] Add cross-domain query examples (climate → asset vulnerability)
- [ ] Prepare ontology documentation poster for booth
- [ ] Create one-pager handout for booth visitors
- [ ] Verify all demo data accuracy

**Person B:**
- [ ] Optimize slow queries
- [ ] Build offline mode (export graph snapshot for demo laptop)
- [ ] Create backup/restore scripts
- [ ] Load all evidence (photos) and link to asset nodes
- [ ] Stress test: all 8 competency questions returning correct answers

**Person C:**
- [ ] Build complete Streamlit UI with all 5 screens:
  - Screen 1: Map View (Delhi ward map, color-coded by Delivery Score)
  - Screen 2: Question Interface (NL input + pre-loaded examples)
  - Screen 3: Proof Chain Visualizer (full chain for any asset)
  - Screen 4: Live Ingestion Demo (paste text, watch graph grow)
  - Screen 5: Delivery Graph Visualization (Interactive graph-style view of the delivery network for the ward or a selected asset.)
- [ ] Polish error handling and loading states
- [ ] Build offline mode for LLM (cached responses)

### 12.5 Phase 4: Demo Prep (Days 18-21)

**All Team:**
- [ ] Create compelling demo script (5-7 minute booth narrative)
- [ ] Rehearse live demo ≥10 times with different "judge personas"
- [ ] Record fallback video demo (4-5 minutes)
- [ ] Prepare slide deck: Architecture, Comparison Table, Demo Screenshots
- [ ] Create booth poster and one-pager handout
- [ ] Test on demo laptop (offline mode verified)
- [ ] Pack backup laptop, power strips, portable WiFi hotspot
- [ ] Final data verification: all competency questions returning correct, sourced answers

---

## 13. Risks & Mitigations

### 13.1 Data Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Ward-level data unavailable for target wards** | HIGH | MEDIUM | Audit data availability BEFORE choosing wards (Day 1); have 5 candidate wards, pick best 2-3 |
| **Data format fragmentation** breaks ETL | HIGH | HIGH | Build per-source adapters; standardize internal schema early; budget 3 extra days for data cleaning |
| **Location name inconsistency** breaks entity resolution | HIGH | HIGH | Manual alias dictionary for demo scope; fuzzy matching fallback; test with known variants |
| **Evidence photos unavailable or low quality** | MEDIUM | MEDIUM | Start collecting Day 1; MCD social media is abundant; curate 20 to use best 15 |
| **Government portal down during data collection** | MEDIUM | LOW | Download and cache all data locally as soon as possible; don't depend on live access |

### 13.2 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **LLM extraction accuracy too low** on government text | HIGH | MEDIUM | Test prompts on 10 sample documents by Day 5; fall back to structured-only if <70% accuracy |
| **Neo4j performance issues** with complex multi-hop queries | MEDIUM | LOW | Pre-compute delivery chains; add indexes; limit graph depth in demo queries |
| **Live demo failure** (WiFi, crashes, bugs) | HIGH | MEDIUM | Offline mode mandatory; cached LLM responses; recorded video backup; 10+ rehearsals |
| **Integration bugs** between graph, API, and UI | MEDIUM | HIGH | Daily integration tests from Day 10; clear API contracts; Person B as integration owner |
| **LLM costs** exceed budget during development | LOW | MEDIUM | Use Claude Haiku/GPT-3.5 for development; switch to GPT-4/Claude Sonnet only for final demo data |

### 13.3 Scope Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Trying to cover too many wards** | HIGH | Maximum 3 wards deep; quality over quantity |
| **Over-engineering ontology** | MEDIUM | Start with 8 entities, expand only if time permits |
| **UI polish consuming too much time** | MEDIUM | Streamlit MVP is sufficient; judges care about intelligence, not CSS |
| **Thin domains taking too much time** | LOW | Thin means THIN: 5-10 nodes max per domain, add last |

---

## 14. Implementation Challenges & Known Limitations

### 14.1 Acknowledged Limitations (Be Transparent in Demo)

1. **Data reflects official government claims, not independent verification.** The graph shows what the government reports as built. Where independent survey data disagrees with official numbers, we flag the discrepancy but cannot resolve it.

2. **Ward-level granularity is prototype scope.** Street-level resolution depends on geo-tagged data availability. For the demo, 2-3 wards are deeply covered; others are shown as "extendable."

3. **NLP extraction is semi-supervised.** For the demo, extracted entities are validated by the team. Production deployment would require a human-in-the-loop validation workflow.

4. **Before/after evidence is manually curated.** Automated evidence matching (photo → asset → scheme) at scale requires computer vision capabilities not in v2.0 scope.

5. **Real-time feed integration is simulated.** The "live ingestion" demo processes pre-selected documents. True real-time RSS/API streaming is v0.3 roadmap.

### 14.2 Known Technical Debt

- Entity resolution is dictionary-based (not ML-based) — works for demo scope, not at scale
- No authentication or access control — not needed for demo, required for production
- LLM responses not audited for hallucination — mitigated by graph-grounding (answers must trace to nodes)
- No automated data refresh pipeline — manual ingestion for v2.0

---

## 15. Success Definition & Go/No-Go

### 15.1 Minimum Viable Demo (Go Criteria)

By Day 17, we MUST have:
- [ ] Working Neo4j graph with ≥300 nodes, ≥5 entity types
- [ ] At least 2 wards with complete delivery chain data
- [ ] At least 5 competency questions answerable end-to-end
- [ ] At least 10 before/after evidence pairs linked to assets
- [ ] LLM extraction working for PIB/news text
- [ ] Basic Streamlit UI with map view + question interface + proof chain
- [ ] Offline mode tested and verified
- [ ] One complete demo script rehearsed ≥5 times

If any of the above is missing → prioritize ruthlessly. Cut thin domains first, then cut wards to 2, then cut to 3 competency questions.

### 15.2 Stretch Goals (Nice to Have)

- [ ] Interactive graph visualization (Neo4j Bloom or D3.js)
- [ ] Hindi language support for NL queries
- [ ] Mobile-responsive UI
- [ ] Ward comparison view (side-by-side delivery scores)
- [ ] Export ward "report card" as PDF
- [ ] Advanced analytics (PageRank for influential actors, community detection for scheme clusters)
- [ ] Real-time RSS ingestion from PIB feed

---

## 16. Post-Hackathon Roadmap

### 16.1 v0.3 — Delhi Full Coverage (Q2 2026)
- Expand to all 272 Delhi MCD wards
- Automate data collection via scheduled scrapers + API integrations
- Build ML-based entity resolution (replace dictionary approach)
- Add user authentication and role-based access
- Integrate with Delhi government's internal data systems

### 16.2 v0.4 — Multi-State Expansion (Q3 2026)
- Template the ontology for any Indian state
- Add state-specific scheme adapters (Maharashtra, Karnataka, Tamil Nadu)
- Build computer vision module for automated before/after photo matching
- Deploy on MeghRaj government cloud
- Add CAG audit module for scheme performance scoring

### 16.3 v1.0 — National Platform (Q4 2026)
- All Indian states and UTs covered
- Real-time data feeds from PFMS, eGramSwaraj, scheme portals
- Advanced scenario simulation ("What if we increase PMAY budget by 20% in these wards?")
- Multi-language support (12+ Indian languages)
- Commercial licensing model for state governments
- API marketplace for third-party integrations (news feeds, social media, satellite imagery)

### 16.4 v2.0 — Global Platform (2027)
- Multi-country ontology expansion (start with SAARC, then Africa, Southeast Asia)
- Global data source connectors (World Bank, UN SDG indicators)
- Cross-country governance delivery benchmarking
- Commercial SaaS model for international organizations

---

## 17. Competitive Landscape Summary

| System | Tracks Money | Tracks Assets | Tracks Beneficiaries | Full Chain | Street-Level | Evidence/Proof | NL Query |
|--------|:-----------:|:------------:|:-------------------:|:----------:|:-----------:|:-------------:|:--------:|
| PFMS | ✅ | ❌ | Partial | ❌ | ❌ | ❌ | ❌ |
| eGramSwaraj | Partial | ✅ | ❌ | ❌ | ❌ | Geo-tags | ❌ |
| Viksit Bharat Dashboard | ❌ | ❌ | Aggregates | ❌ | ❌ | ❌ | ❌ |
| myScheme | ❌ | ❌ | Discovery | ❌ | ❌ | ❌ | ❌ |
| State BMS (Tripura) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Tapasya/Zoho | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Our Ontology Engine** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** |

---

## 18. Appendices

### 18.1 Glossary

- **Ontology:** A formal specification of entity types and their relationships in a domain
- **Knowledge Graph (KG):** A graph-structured database of entities connected by typed relationships
- **Delivery Chain:** The complete traceable path from central budget allocation to street-level evidence of delivery
- **Chain Completeness Score:** Percentage of assets in a ward that have a full delivery chain (scheme → evidence)
- **Delivery Score:** Composite metric for a ward combining chain completeness, utilization rate, evidence coverage, and beneficiary reach
- **Entity Resolution:** The process of determining that two differently-named references point to the same real-world entity
- **Cypher:** Neo4j's query language for graph pattern matching
- **RAG:** Retrieval-Augmented Generation — LLM + knowledge retrieval for grounded answers
- **Competency Question:** A test question the ontology must be able to answer correctly

### 18.2 Reference Architecture Inspirations

- **GDELT Project:** Global event database and knowledge graph at scale
- **Enterprise LLM+KG Systems:** Modern architectures for trusted AI in regulated organizations
- **India Stack:** JAM Trinity (Jan Dhan-Aadhaar-Mobile) as infrastructure for digital governance
- **eGramSwaraj:** Geo-tagged asset monitoring as proof that government is moving toward spatial tracking
- **PFMS 2.0:** CGA's planned transformation indicating government appetite for better financial data systems

### 18.3 Key Data Portal URLs

| Portal | URL | Data Type |
|--------|-----|-----------|
| Open Government Data India | data.gov.in | 100K+ datasets via API |
| Delhi Open Data | delhi.data.gov.in | Delhi-specific ward data |
| PFMS Dashboard | pfmsdashboard.gov.in | Fund flow tracking |
| eGramSwaraj | egramswaraj.gov.in | Rural asset + geo-tags |
| PIB Releases | pib.gov.in | Official press releases |
| PMGSY | pmgsy.nic.in | Road-level geo-tagged data |
| India Budget | indiabudget.gov.in | Scheme-wise allocations |
| myScheme | myscheme.gov.in | Scheme eligibility discovery |
| Transforming India | transformingindia.mygov.in | National aggregate dashboard |

---

## Document Control

**Prepared by:** Team Lead  
**Version:** 2.0 (Major revision — governance delivery framing)  
**Date:** March 7, 2026  
**Previous Version:** 0.1 (Feb 19, 2026 — climate-food-security framing)  
**Next Review:** March 10, 2026 (after data availability audit)

**Change Log:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-02-19 | Team Lead | Initial draft with climate-food-security scenario |
| 2.0 | 2026-03-07 | Team Lead | Major pivot: governance delivery proof framing; new personas (elected reps, MCD officials); new demo scenario (ward-level delivery chains); new data sources (Delhi-specific); evidence layer added; gap analysis feature added; competitive landscape analysis; data procurement challenges documented; 21-day timeline |

---

**End of PRD v2.0**
