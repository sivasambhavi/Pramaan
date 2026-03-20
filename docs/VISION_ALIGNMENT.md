# PRAMAAN — Vision Alignment Investigation
> **Last updated:** March 20, 2026
> **Scope:** Full audit of current codebase vs. the official problem statement
> **Verdict:** ~20% aligned to full vision — but built on the right foundation

---

## 1. The Vision (Official Problem Statement)

> *"Design and develop an AI-powered Global Ontology Engine that can collect and understand structured data, unstructured content, and live real-time feeds from areas like geopolitics, economics, defense, technology, climate, and society — and then connect all of it into a single, unified, constantly updating intelligence graph, so decision-makers can get clear insights for strategy, transparency, and national advantage for India and the world."*

---

## 2. Our Interpretation (from PRD.md §1.3)

We implement the Global Ontology Engine inside **Digital Democracy & Governance Delivery**.

The engine connects what no existing system in India connects today:

| Existing System | What it does | What it cannot do |
|---|---|---|
| PFMS | Tracks money flow | Cannot show what was physically built |
| eGramSwaraj | Tracks geo-tagged assets | Cannot link back to beneficiaries |
| Viksit Bharat Dashboard | Shows national aggregates | Cannot zoom to a single street |
| myScheme | Helps citizens find schemes | Does not prove what was delivered |
| State BMS | Tracks beneficiaries | Does not connect to physical infrastructure |

**PRAMAAN is the connective tissue** — a semantic intelligence layer that links:

```
Scheme → Budget → Implementation → Asset → Location → Beneficiary → Evidence
```

into one traceable, queryable knowledge graph.

---

## 3. Alignment Scoring by Dimension

### 3.1 Domain Coverage — What the Engine Can Reason About

| Domain | Vision Requires | What Exists Now | Coverage |
|---|---|---|---|
| **Governance / Society** | Deep coverage | 7-entity ontology, Ward 45 Delhi, 5 schemes, 272 wards | ✅ 70% |
| **Economics** | National budget flows, fiscal policy, trade data | Scheme fund allocations only (AMRUT, PMAY amounts) | 🟡 15% |
| **Geopolitics** | Treaties, borders, diplomatic events, UN resolutions, sanctions | Zero | ❌ 0% |
| **Defense** | Military assets, procurement, threat intelligence, security incidents | Zero | ❌ 0% |
| **Technology** | Patent filings, R&D spends, startup ecosystem, digital adoption | Zero | ❌ 0% |
| **Climate** | Weather events, emissions data, disaster reports, air quality | Zero | ❌ 0% |

**Domain Score: 14 / 60 → ~23%**

---

### 3.2 Data Ingestion — How Data Enters the Graph

| Capability | Vision Requires | What Exists Now | Coverage |
|---|---|---|---|
| Structured data (CSV, API) | Multi-source, automated, scheduled | fetch_govdata.py + transform_to_7_table_schema.py — data.gov.in + census CSV | ✅ 60% |
| Unstructured content (articles, PDFs, reports) | NLP parsing at scale | Groq LLM extraction from pasted news/PIB text — works end-to-end | 🟡 55% |
| Live real-time feeds | Streaming, continuous, event-driven | On-demand RSS only — no scheduler running, no WebSocket, no Kafka | 🟡 15% |
| Global feeds (international) | Reuters, UN data, World Bank, geopolitical APIs | Google News RSS (India-only) and PIB only | ❌ 5% |
| Image / video understanding | Satellite imagery, CCTV feeds, drone surveys | EXIF extraction from geo-tagged photos only | ❌ 10% |

**Ingestion Score: 29 / 50 → ~29%**

> **Key weakness:** Real-time is not real-time. It is on-demand. The scheduler (apscheduler) is proposed but not wired into main.py. No background thread is running.

---

### 3.3 The Ontology — How Knowledge is Modelled

| Capability | Vision Requires | What Exists Now | Coverage |
|---|---|---|---|
| Unified entity model | Cross-domain nodes with shared relationships | 7 governance nodes: Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event | 🟡 30% |
| Cross-domain relationships | Geopolitics → Economics → Society linkages | Only governance relationships: FUNDS, BUILT_BY, PROVES, BENEFITS, LOCATED_IN | ❌ 10% |
| Temporal versioning | Graph evolves over time, history of changes preserved per node | MERGE overwrites — no temporal snapshot or versioning capability | ❌ 0% |
| Confidence scoring | Every edge has a source attribution + trust score | No confidence scores stored in Neo4j nodes or relationships | ❌ 0% |
| Conflict detection | Two sources disagree → flagged and surfaced to user | Not implemented anywhere | ❌ 0% |
| Global entity resolution | "Delhi" = same node regardless of which source mentions it | Planned (Geo Resolution Agent designed in GEO_MASTER_IMPLEMENTATION.md) | 🟡 10% |

**Ontology Score: 10 / 60 → ~17%**

> **Key weakness:** The ontology is governance-only. Expanding to 6 domains requires new node types, new relationship types, and a cross-domain linking layer that does not exist yet.

---

### 3.4 Intelligence Layer — How Insights Are Derived

| Capability | Vision Requires | What Exists Now | Coverage |
|---|---|---|---|
| Natural language querying | Ask anything, get graph-backed answer with reasoning path | 5 hardcoded queries + 1 Groq custom Cypher endpoint (/questions/custom) | 🟡 25% |
| Pattern detection | "Funds released but no assets built = possible leakage" | Not implemented — no anomaly logic | ❌ 0% |
| Trend analysis | "Infrastructure spend up 40% in East Delhi over 3 years" | Not implemented — no temporal data | ❌ 0% |
| Predictive insights | "At current delivery rate, ward completion in X months" | Not implemented | ❌ 0% |
| Contradiction detection | "Ministry says 1,000 houses built. Graph shows 400." | Not implemented | ❌ 0% |
| Strategic AI summaries | Auto-generated briefings for decision-makers | Not implemented | ❌ 0% |
| Alert engine | "New scheme announced. 3 wards not yet covered." | Not implemented | ❌ 0% |

**Intelligence Score: 6 / 70 → ~9%**

> **Key weakness:** This is the most critical gap. A "Global Ontology Engine" must do more than store and retrieve — it must reason. Currently PRAMAAN is a query tool, not a reasoning engine.

---

### 3.5 Scale & Reach — Geographic and Data Volume

| Capability | Vision Requires | What Exists Now | Coverage |
|---|---|---|---|
| Geographic scale | India-wide + global | 1 Delhi ward (Ward 45, Shahdara) at demo level | ❌ 1% |
| Data volume | Millions of nodes across domains | ~150 nodes, ~300 edges in Neo4j | ❌ 0.1% |
| Update frequency | Constantly updating as new events occur | Manual trigger only — user must press a button | ❌ 5% |
| Multi-user access | Concurrent decision-makers, role-based dashboards | Single-user Streamlit app | 🟡 10% |
| API for external consumers | External systems can query the intelligence graph | FastAPI with 8 routers — fully queryable | ✅ 60% |

**Scale Score: 15 / 50 → ~15%**

---

## 4. Overall Alignment Score

```
╔══════════════════════════════════════════════════════════╗
║  DIMENSION                SCORE   WEIGHT   WEIGHTED     ║
║  ──────────────────────────────────────────────────────  ║
║  Domain Coverage           23%     25%       5.8%       ║
║  Data Ingestion            29%     20%       5.8%       ║
║  Ontology Design           17%     25%       4.3%       ║
║  Intelligence Layer         9%     20%       1.8%       ║
║  Scale & Reach             15%     10%       1.5%       ║
║  ──────────────────────────────────────────────────────  ║
║  OVERALL ALIGNMENT                          19.2%       ║
╚══════════════════════════════════════════════════════════╝
```

**Honest verdict: ~20% aligned to the full vision.**

---

## 5. What Makes This 20% Meaningful

The 20% built is the right 20% — the architectural foundation.

```
FULL VISION (100%)
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  WHAT IS BUILT ✅  (the foundation)                       │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Knowledge graph engine              (Neo4j)        │  │
│  │  AI entity extraction pipeline       (Groq LLM)     │  │
│  │  Multi-source ingestion              (CSV, JSON, RSS)│  │
│  │  7-entity governance ontology        (7-table schema)│  │
│  │  REST API for external consumption   (FastAPI)       │  │
│  │  Proof chain traceability            (4-page UI)     │  │
│  │  Natural language query interface    (basic)         │  │
│  │  Micro-accountability notifications  (Twilio)        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  WHAT IS MISSING ❌  (to reach 100%)                      │
│  ──────────────────────────────────────────────────────    │
│  5 more domains  (geopolitics, defense, technology,        │
│                   climate, full economics)                  │
│  Real-time streaming ingestion  (Kafka / WebSocket)        │
│  Cross-domain relationship modelling                        │
│  Intelligence layer  (patterns, anomalies, alerts)         │
│  Temporal graph versioning  (history per node/edge)        │
│  Confidence + conflict scoring on every relationship       │
│  National → Global geographic scale                        │
│  Strategic AI briefings for decision-makers                │
└────────────────────────────────────────────────────────────┘
```

**The architecture is correct. The engine is built. The fuel tank is small.**

---

## 6. What PRAMAAN Does Well Right Now

| Strength | Evidence in Codebase |
|---|---|
| Correct graph architecture | Neo4j with MERGE-based ingestion, Cypher queries, relationship traversal |
| Working AI extraction | Groq llama-3.3-70b extracts governance entities from raw text in <3 seconds |
| End-to-end pipeline proven | CSV → transform → validate → Neo4j → FastAPI → Streamlit works |
| Source attribution exists | Every entity carries source_type and source_url fields |
| Evidence-to-asset linkage | Geo-tagged before/after photos linked to Neo4j asset nodes |
| Extensible ontology | Adding new node types to 7-table schema is a 1-day task per domain |
| API-first backend | 8 FastAPI routers — ready for external dashboard consumers or mobile apps |

---

## 7. Critical Gaps (Blocking Full Vision)

### Gap 1 — Only 1 of 6 Domains Covered
**Current:** Governance delivery only (schemes, assets, wards).
**Required:** Geopolitics, Economics, Defense, Technology, Climate, Society — each needs its own node types, data sources, and relationship patterns.
**Effort:** 2–4 weeks per domain for data + ontology design.
**File to update:** `ai/llm_extractor.py` (new entity types), `backend/scripts/load_seed_data.py` (new loaders), `data/config/govdata_registry.json` (new API sources).

### Gap 2 — No Real Intelligence Layer
**Current:** 5 pre-written Cypher queries + one Groq-to-Cypher prompt in `backend/app/routers/questions.py`.
**Required:** Anomaly detection (leakage signals), trend analysis, contradiction surfacing, AI-generated strategic briefings.
**Effort:** 4–8 weeks for a proper reasoning layer over the graph.
**New component needed:** `backend/app/services/intelligence_service.py`.

### Gap 3 — Real-Time is Not Real-Time
**Current:** User clicks a button → RSS scrape → LLM extraction → ingest.
**Required:** Background scheduler continuously pulling feeds, detecting new events, updating the graph automatically.
**Effort:** 1–2 weeks.
**Fix:** Wire `apscheduler` into `backend/app/main.py` startup event (already in `requirements.txt`).

### Gap 4 — No Temporal Versioning
**Current:** `MERGE` in Neo4j overwrites node properties — history is lost.
**Required:** Every relationship and property change must be time-stamped and preserved for audit.
**Effort:** 3–4 weeks (requires schema redesign with versioned edges or a shadow history table).

### Gap 5 — No Confidence or Conflict Scoring
**Current:** All ingested data is treated as equally true.
**Required:** Every node and relationship must carry a confidence score, source provenance, and flag when two sources disagree.
**Effort:** 2–3 weeks (add `confidence`, `source_id`, `conflict_flag` to all Cypher MERGE statements in `backend/app/routers/ingest.py`).

### Gap 6 — Scale is Demonstration-Level Only
**Current:** Ward 45, Shahdara — ~150 nodes, ~300 edges.
**Required:** National scale (748 districts, 100,000+ wards), eventually global.
**Effort:** Infrastructure and data sourcing challenge — 3–6 months post-hackathon.

---

## 8. Roadmap to Close the Gap

| Phase | Timeline | What to Build | Alignment After |
|---|---|---|---|
| **Phase 1 — Demo Ready** | Now → Mar 28, 2026 | Fix Delhi geo-hierarchy, run validate.py, seed data cleanly, stable booth demo | 20% → 25% |
| **Phase 2 — Domain Expansion** | Apr–Jun 2026 | Add Economics (RBI, MoF data), Climate (IMD, NDMA), national ward coverage | 25% → 40% |
| **Phase 3 — Intelligence Layer** | Jul–Sep 2026 | Anomaly detection, contradiction engine, strategic briefing generator, alert API | 40% → 60% |
| **Phase 4 — Real-Time + Scale** | Oct 2026–Mar 2027 | Background streaming, temporal versioning, confidence scoring, multi-state | 60% → 75% |
| **Phase 5 — Global Vision** | 2027+ | All 6 domains, international feeds, multi-tenancy, public API, global scale | 75% → 95% |

---

## 9. What to Say at the Booth (March 28)

When judges ask *"How aligned is this with the problem statement?"* the honest answer is:

> *"We have built the engine. Today it runs on one domain — governance delivery in Delhi — because that is where we have real data and real impact. The ontology is designed to be domain-agnostic. Adding geopolitics or climate is a data and schema expansion problem, not an architecture problem. What we are demonstrating today is that the approach works: live data in, knowledge graph updated, questions answered, proof surfaced. That is the hardest part, and it works."*

---

## 10. Summary Table

| Layer | Vision Requires | We Have | Gap |
|---|---|---|---|
| **Ingestion** | Live multi-source, multi-domain feeds | On-demand RSS + CSVs | No streaming, no global feeds |
| **Ontology** | 6 domains, cross-domain relationships | 1 domain, 7 governance entities | 5 domains + temporal versioning missing |
| **Intelligence** | Pattern detection, anomaly alerts, strategic briefings | Static Cypher queries + basic NL | Full reasoning layer missing |
| **Data Governance** | Trust scores, audit trail, conflict detection | Zero governance infrastructure | Everything missing |
| **Decision Layer** | NL query, strategic dashboards, alerts | 4-page Streamlit UI, basic NL query | Alerts + strategy layer missing |
| **Scale** | National/global, millions of nodes | 1 ward, ~150 nodes | 3 orders of magnitude below target |

**Overall alignment: ~20%** — architecture is correct, surface area needs expanding.

---

*Generated: March 20, 2026*
*Source: Full codebase audit vs. official India Innovates 2026 problem statement*
