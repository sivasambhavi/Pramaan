# PRAMAAN — Product Requirements Document v3.1
## AI-Powered Global Ontology Engine · India Intelligence Graph

**Version:** 3.1
**Date:** March 24, 2026
**Competition:** India Innovates 2026 · Data Mining & Processing Domain
**Venue:** Bharat Mandapam, New Delhi · March 28–29, 2026

---

## 1. Problem Statement

India's government produces terabytes of policy data every year — PIB press releases, Parliament Q&A, data.gov.in datasets, NDMA disaster reports, ISRO mission updates, budget documents, scheme performance data.

**None of it is connected.**

A policy analyst trying to understand the relationship between the Wayanad landslide, NDRF funding allocation, NDRF-SDRF reforms, and Parliament no-confidence debates has to manually piece together information from 6 different government portals over 2 days.

A journalist investigating India's semiconductor strategy must separately track the PLI scheme, Tata fab investment, semiconductor import trends, and IMEC corridor signing — all from different ministries, in different formats, with no shared vocabulary.

**The cost of this fragmentation:**
- Policy decisions made without cross-domain context
- Accountability gaps hidden across siloed databases
- Research that takes weeks instead of minutes
- No single "source of truth" for India's national intelligence

---

## 2. Product Vision

> **PRAMAAN is the intelligence layer that connects India's government data — so any analyst, policymaker, or researcher can ask a question about any national event and get a verified, cited answer in seconds, not weeks.**

PRAMAAN builds a live knowledge graph over India's national events, actors, schemes, policies, and impacts — across 7 domains — backed by real government data sources. Every node is real. Every edge is evidence-backed.

---

## 3. Core Insight

The insight is not just aggregation — it's **ontological linkage**.

| What exists today | What PRAMAAN adds |
|---|---|
| data.gov.in — raw datasets | Structured nodes in a queryable graph |
| PIB press releases | Evidence nodes linked to specific events |
| Google News | Cross-domain causal chains |
| Wikipedia | Government-source-only, verified provenance |
| Ministries' portals | Unified vocabulary across all domains |

Example cross-domain insight PRAMAAN makes visible:
- **G20 Summit (Geopolitics) → IMEC Signing (Economics)** — signed on the same sidelines
- **Balakot Airstrikes (Defense) → Article 370 Abrogation (Governance)** — same 2019 strategic window
- **COVID Second Wave (Society) → Chamoli Glacier Burst (Climate)** — concurrent 2021 crises that overwhelmed the same NDRF resources

---

## 4. Target Users

### Primary
| User | Use Case | Value |
|---|---|---|
| **Policy analysts** (NITI Aayog, ORF, PRS) | Cross-domain research before briefs | 2 days → 10 seconds |
| **Government officials** | Decision support before Parliament sessions | Cited, structured intelligence |
| **Investigative journalists** | Finding cross-domain leads | Connections they'd never find manually |

### Secondary
| User | Use Case |
|---|---|
| **UPSC / competitive exam prep** | Every event mapped with actors, schemes, evidence |
| **Academic researchers** | Causal chain analysis across policy domains |
| **Civil society / NGOs** | Accountability tracking with evidence |

---

## 5. Product Architecture

### 5.1 Data Layer

**Structured data** — fetched via data.gov.in API (no LLM required)
- 14 national datasets mapped to 15 events
- COVID deaths, NDRF rescue stats, NDRF-SDRF funds, PLI applications, semiconductor imports, defence budget, FDI inflows, J&K development investment, cyclone frequency data
- ETL pipeline: `fetch_govdata.py → transform.py → validate_ontology.py → load_govdata.py`
- All nodes prefixed `DG_` to distinguish from hand-curated seed data

**Unstructured data** — scraped from official government URLs
- Source whitelist v1: pib.gov.in, ndma.gov.in, isro.gov.in, imd.gov.in, ndrf.gov.in, nrsc.gov.in, ndap.niti.gov.in
- Saved as raw text with metadata headers to `data/resources/unstructured/raw/`
- Idempotent — skips already-fetched files

**Hand-curated ontology** — `seed_graph.json`
- 15 events, 7 domains, 30 actors, 20 schemes/policies, 20 regions
- Cross-domain connections with explicit reasoning
- Source of ground truth for all graph relationships

### 5.2 Graph Layer — Neo4j Knowledge Graph

**Node types:**

| Type | Count | Description |
|---|---|---|
| Domain | 7 | Climate, Economics, Geopolitics, Defense, Technology, Society, Governance |
| Event | 15 | High-impact national incidents 2019–2024 |
| Actor | 30 | NDMA, ISRO, MHA, Army, RBI, MEA, etc. |
| Region | 20 | States and cities affected |
| Scheme | 12 | PM schemes, NDRF, AMRUT, PLI, etc. |
| Policy | 8 | Article 370, AFSPA, NPE 2020, etc. |
| Impact | 54 | Measured outcomes (40 from data.gov.in API) |
| Evidence | 34 | Source citations (PIB, NDMA, ISRO, data.gov.in) |
| **Total** | **179** | **261 relationships** |

**Relationship types:** `TRIGGERED`, `CAUSED`, `IMPACTED`, `ACTIVATED`, `GOVERNED_BY`, `MANAGED_BY`, `FUNDED_BY`, `PROVEN_BY`, `CONNECTED_TO`, `OCCURRED_IN`, `BELONGS_TO`

### 5.3 Backend — FastAPI

Base URL: `http://localhost:8000`

| Endpoint | Purpose |
|---|---|
| `GET /stats` | Live graph statistics for home page |
| `GET /ontology/events` | All 15 events with impact counts |
| `GET /ontology/events/{id}` | Full event subgraph (impacts, actors, schemes, evidence, connections) |
| `GET /ontology/graph` | Complete graph for visualization |
| `GET /ontology/cross-domain` | All 14 cross-domain CONNECTED_TO links |
| `GET /ontology/domains` | Domain summary with event counts |
| `GET /scrape/news?q=` | Google News RSS scrape with relevance scoring |

### 5.4 Frontend — Streamlit (4 pages)

#### Page 1: Intelligence Map
- World map visualization of 15 events
- Domain filter, severity filter
- Click event → side panel with impacts, actors, cross-domain links
- "View in Ontology Graph →" deep-link

#### Page 2: Ontology Graph
- Interactive Neo4j graph via streamlit-agraph
- Node type toggles (8 types)
- Event focus mode — ego network highlight
- Cross-domain links toggle (gold dashed edges)
- Click node → detail panel with properties
- "View in Live Feed →" deep-link

#### Page 3: Live Feed
- Event selector with domain grouping
- Impact cards with `LIVE · data.gov.in` provenance badges
- Evidence cards with source citations
- Cross-domain connection cards

#### Page 4: Decision Brief
- Event + query selector (text + voice input via Groq Whisper)
- Groq LLaMA 3.3 70B generates structured intelligence brief
- Streams response in real-time
- Data provenance bar: `X impacts · LIVE · N from data.gov.in · N evidence · N cross-domain links`
- Evidence confidence tier shown per fact: `[data.gov.in] 100%` vs `[News] 75%` vs `[Curated] 90%`
- Intelligence gap indicator: flags if event has sparse cross-domain coverage
- "Share Brief →" action: one-tap WhatsApp share of the generated brief
- Raw ontology context expander

---

## 6. Data Provenance Model

All data in PRAMAAN is traceable to its source. Three tiers with explicit confidence levels:

**Tier 1 — Hand-curated seed** (`seed_graph.json`)
- Research-backed ontology nodes with explicit reasoning
- Confidence: 90% — human-reviewed, cross-referenced
- No badge — baseline knowledge graph

**Tier 2 — Live data.gov.in API** (`govdata_nodes.json`, prefix `DG_`)
- Real government datasets via UUID-based API
- Confidence: 100% — official government publication
- `source = "data.gov.in"` set on all loaded nodes
- Displayed with cyan `LIVE · data.gov.in` badge in UI
- LLM context explicitly tags these values as `[data.gov.in]`

**Tier 3 — News / unstructured scrape**
- Google News RSS + official gov page scrapes
- Confidence: 75% — filtered, not primary source
- Displayed with relevance score in evidence cards

**Confidence display rule:** Every fact cited in a Decision Brief shows its tier badge inline so the reader always knows how trusted the number is.

**Source domain whitelist (v1):**
`pib.gov.in, ndma.gov.in, isro.gov.in, imd.gov.in, ndrf.gov.in, nrsc.gov.in, ndap.niti.gov.in`

**Intelligence Gap Detection:**
PRAMAAN actively flags weak coverage — events with fewer than 2 cross-domain links or fewer than 2 evidence nodes are marked as "intelligence gaps" requiring enrichment. This turns absence of data into a signal, not silence.

---

## 7. The 15 Events (Scope)

| # | Event | Domain | Year | Severity |
|---|---|---|---|---|
| 1 | Wayanad Landslide | Climate | 2024 | Critical |
| 2 | Cyclone Dana – Puri | Climate | 2024 | Critical |
| 3 | Chamoli Glacier Burst | Climate | 2021 | Critical |
| 4 | Joshimath Subsidence | Governance | 2023 | High |
| 5 | Article 370 Abrogation | Governance | 2019 | High |
| 6 | Delhi Yamuna Floods | Society | 2023 | Critical |
| 7 | COVID Second Wave | Society | 2021 | Critical |
| 8 | Manipur Conflict | Defense | 2023 | Critical |
| 9 | Balakot Airstrikes | Defense | 2019 | Critical |
| 10 | Tata Semiconductor Fab | Economics | 2024 | High |
| 11 | IMEC Corridor Signing | Economics | 2023 | High |
| 12 | G20 New Delhi Summit | Geopolitics | 2023 | High |
| 13 | India-Canada Diplomatic Row | Geopolitics | 2023 | High |
| 14 | Chandrayaan-3 Landing | Technology | 2023 | High |
| 15 | Aditya-L1 Solar Mission | Technology | 2023 | High |

---

## 8. Tech Stack

| Layer | Technology |
|---|---|
| Knowledge Graph | Neo4j (local) |
| Backend API | FastAPI + Python 3.12 |
| Frontend | Streamlit |
| Graph Visualization | streamlit-agraph (vis.js) |
| AI / LLM (text) | Groq · LLaMA 3.3 70B |
| AI / LLM (voice) | Groq · Whisper (speech-to-text) |
| News Scraping | feedparser (Google News RSS) |
| Structured Data | data.gov.in API |
| Notifications | Twilio WhatsApp API (v4.0) |
| Env Config | python-dotenv |

---

## 9. Business Model (Post-Competition)

### Revenue Streams

**SaaS Subscription**
- Think tanks, research orgs, policy institutes
- Pricing: ₹50K–₹5L/year depending on query volume and domain coverage
- Target: ORF, PRS Legislative Research, The Wire, Mint, CPR India

**Government Contract**
- Decision support tool for ministries / PMO
- Integration with NIC data infrastructure
- Pricing: custom enterprise contract

**API Product**
- Developer API for building on top of the India Intelligence Graph
- Pricing: per-query or per-seat

**EdTech / UPSC**
- Curated event packs with full actor/scheme/evidence chains
- WhiteLabel for major UPSC preparation platforms

### Defensibility
1. **Data moat** — curated cross-domain knowledge graph takes months to build; raw data alone doesn't give you the connections
2. **Source trust** — government-only sources; no hallucinated data
3. **Network effect** — more events → more cross-domain connections → more insight density

---

## 10. Competitive Landscape

| Product | What they do | What PRAMAAN adds |
|---|---|---|
| data.gov.in | Raw datasets | Context, connections, queryable |
| PIB / Press releases | Unstructured text | Structured, linked to events |
| Google News | News aggregation | Verified, cited, cross-domain |
| Wikipedia | Encyclopedic | Government-source-only, live data |
| NITI Aayog dashboards | Scheme KPIs | Cross-domain causal linkage |

**No direct competitor** builds a cross-domain, evidence-backed, AI-queryable knowledge graph over India's national events.

---

## 11. Demo Flow (Competition)

1. **Home** — countUp animation: 15 events · 30 actors · 34 evidence · 179 nodes
2. **Intelligence Map** — open Wayanad Landslide, show impacts + cross-domain link to Cyclone Dana (same NDRF framework)
3. **Ontology Graph** — show G20 → IMEC gold edge (same summit sidelines), click to see reason
4. **Live Feed** — open COVID Second Wave, show `LIVE · data.gov.in` badges on 3 real government data points (10.6M cases, 524K deaths, disaster relief funds)
5. **Decision Brief** — open Tata Semiconductor Fab, query: *"Provide a quantitative impact assessment using official government data"* — LLM streams citing ₹3,201 Cr investment, ₹20.7B imports, 154 PLI applications — all from data.gov.in API

**Pitch line:** *"India has 1.4 billion people and a government that generates terabytes of policy data. None of it is connected. PRAMAAN is the intelligence layer that connects it."*

---

## 11b. Competition Alignment Score

> Requirement A — Global Ontology Engine (official problem statement)

| What the Problem Demands | What PRAMAAN v3.1 Has | Old System Had | Status |
|---|---|---|---|
| **Collect structured data** | data.gov.in API → 14 datasets, ETL pipeline (`fetch_govdata → transform → validate → load`) | data.gov.in API → ward-level AMRUT/PMAY | ✅ Done — stronger than before |
| **Collect unstructured data** | `fetch_unstructured.py` scrapes NDMA/ISRO/PIB; `run_agent.py` with Crawl4AI for URL crawling; agent relevance filter | Tavily + Crawl4AI → ward assets | ✅ Done — national scope now |
| **Collect real-time feeds** | Google News RSS via `/scrape/news`; APScheduler daemon in `run_agent.py --daemon` (daily at 02:00) | APScheduler 24h daemon | ✅ Done — scheduler exists, RSS live |
| **Covers all 6 domains** | 7 domains: Climate, Economics, Geopolitics, Defense, Technology, Society, Governance | Only Governance / Civic delivery | ✅ Done — full domain coverage |
| **Single unified graph** | Neo4j: 179 nodes, 261 edges, 7 domains, 15 events, 8 entity types | Neo4j: ward-level 7-entity ontology | ✅ Done — national graph |
| **Constantly updating** | `run_agent.py --daemon` + APScheduler cron; ETL pipeline re-runnable; MERGE (not CREATE) for idempotency | `run_agent.py --daemon` | ⚠️ Partial — daemon exists but data.gov.in fetch is still manual trigger |
| **Decision-maker insights** | Decision Brief: Groq LLaMA 3.3 70B streams structured brief with cited numbers, source tiers, cross-domain context | Ward Map delivery score (gauge chart) | ✅ Done — significantly stronger |
| **Strategy & transparency** | Cross-domain causal chains (14 links), evidence provenance tiers (100%/90%/75%), `LIVE · data.gov.in` badges | Proof Chain lineage for ward assets | ✅ Done — national causal intelligence |
| **National advantage angle** | 15 events across Defense, Geopolitics, Economics, Technology — Balakot, G20, IMEC, Semiconductor, Chandrayaan | Links PFMS, PIB, eGramSwaraj (ward-level) | ✅ Done — direct national scope |

**Overall: 8/8 requirements addressed. 1 partial (scheduling automation).**

The one gap vs the old system: the old system had the daemon actively running ward queries. The current system has the same daemon but the data.gov.in ETL is triggered manually. Hooking `pipeline.py` into the APScheduler `daily_job()` would close this completely.

---

## 12. Feature Backlog (Inherited from v1 Ward System)

These features existed in the original PRAMAAN ward-level proof system and have been evaluated for reuse at national scale. Prioritised below.

### Competition Quick Wins (Before March 28)

| Feature | Origin | Value | Effort |
|---|---|---|---|
| **Evidence confidence scoring** | Old proof chain — per-source trust levels | Differentiates PRAMAAN from raw news; every Decision Brief fact shows tier badge | 2 hrs |
| **Intelligence gap detection** | Old gap analysis Cypher queries | "Which events have no cross-domain links?" — turns missing data into a signal | 3 hrs |
| **Voice input for queries** | Old Page 03 Live Ingestion — Groq Whisper | Analyst speaks query → Whisper transcribes → Decision Brief generated | 3 hrs |
| **WhatsApp "Share Brief" button** | Old Micro-Accountability — Twilio | One-tap share of generated brief to WhatsApp; shows citizen-notification loop | 2 hrs |

### v4.0 (3 months post-competition)

- Expand to 50+ events across all 7 domains
- Live scheduled ETL pipeline (cron-based daily fetch from data.gov.in)
- v2 source whitelist: mygov.in, pmindia.gov.in, mohfw.gov.in, mea.gov.in
- REST API for external consumers (think tanks, media orgs)
- Graph diff — "what changed this week" feed
- **Twilio WhatsApp notification layer** — when new intelligence is added for a tracked event, subscribed analysts get an automated brief summary
- **Actor-level beneficiary impact** — "How many citizens were reached by NDMA's actions?" using population multiplier logic from v1 ward system
- **Fuzzy entity resolution** — RapidFuzz normalization for ministry/actor name variants (MEA = "Ministry of External Affairs" = "विदेश मंत्रालय")

### v5.0 (6 months)

- Natural language graph query — no UI required, pure API
- Multi-language support (Hindi, Tamil, Telugu)
- **Before/after evidence pairs for climate events** — satellite imagery (ISRO NRSC) + news photos attached to Impact nodes; inspired by v1 before/after proof system
- **Citizen query interface** — "What schemes benefited my state?" → state-level drill-down from national events
- State-level ontology expansion — every state as a Region node with its own event/scheme/actor subgraph
- Monetisation: API keys, rate limits, billing dashboard
