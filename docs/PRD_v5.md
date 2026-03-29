# PRAMAAN V5 — Product Requirements Document
**Status:** Demo-Ready
**Date:** 2026-03-27
**Branch:** `feature/v5-demo-safe`

---

## 1. Product Overview

PRAMAAN is India's intelligence-grade geopolitical risk and scheme-delivery analytics platform. V5 delivers a **fully live, graph-computed risk engine** over a curated 31-event ontology spanning 2023–2026, with automatic hourly data ingestion, dynamic blast scoring, and scheme-beneficiary traceability.

---

## 2. What's New in V5

| Capability | Before V5 | V5 |
|---|---|---|
| Severity labels | Hardcoded strings (`critical/high/medium/low`) | Dynamic float scores (0–10) computed from graph topology |
| Blast score refresh | None | Hourly via APScheduler Step 8 |
| New 2026 events | — | 7 curated events with full subgraphs |
| Beneficiary model | Zero nodes | 19 Beneficiary nodes across all 19 schemes |
| Scheme type classification | None | Type 1 (Emergency) / Type 2 (Structural) on all schemes |
| Hollow event purge | 4 hollow events in graph | Removed (EVT_MANIPUR_2023, EVT_JOSHIMATH_2023, EVT_IMEC_2023, EVT_TATA_SEMI_2024) |
| Pipeline gaps | 5 known gaps | All 5 fixed (PROVEN_BY direction, KNOWN_IDS_CONTEXT, entity resolver, CONNECTED_TO inference, blast_score refresh) |

---

## 3. Graph Ontology — Current State (2026-03-27)

### 3.1 Node Counts
| Node Type | Count |
|---|---|
| Events | 40 |
| Schemes | 19 |
| Beneficiary | 19 |
| Impact | 92 |
| Evidence | 72 |
| Domain | 7 |

### 3.2 Relationship Counts
| Relationship | Count |
|---|---|
| CONNECTED_TO | 46 |
| CAUSED (Event→Impact) | 92 |
| PROVEN_BY (Event→Evidence) | 72 |
| TRIGGERED (Event→Scheme) | ~35 |
| BENEFITS (Scheme→Beneficiary) | 19 |

### 3.3 Curated Event Registry (31 canonical events)

**2026 (10 events)**
| Event ID | Name | Domain | Blast Score | Severity |
|---|---|---|---|---|
| EVT_IRAN_WAR_2026 | Iran-US-Israel War | Geopolitics | 8.2 | high |
| EVT_INDIA_SEMI_MICRON_2026 | India Semiconductor Mission — Micron Fab | Technology | 8.1 | high |
| EVT_ARUNACHAL_STANDOFF_2026 | Arunachal Pradesh PLA Standoff | Defense | 7.5 | high |
| EVT_RUPEE_INR_CRISIS_2026 | Rupee Depreciation Crisis | Economics | 7.1 | high |
| EVT_US_INDIA_TRADE_2026 | US-India Strategic Trade Framework | Economics | 7.0 | high |
| EVT_INDIA_CLIMATE_TARGETS_2026 | India 2030 Climate Targets Review | Climate | 7.0 | high |
| EVT_HORMUZ_BLOCKADE_2026 | Strait of Hormuz Blockade | Economics | 6.3 | medium |
| EVT_AI_REGULATION_ACT_2026 | India AI Regulation Act 2026 | Governance | 6.0 | medium |
| EVT_TEESTA_TREATY_2026 | Teesta Water Treaty Signed | Geopolitics | 6.0 | medium |
| EVT_IRAN_CEASEFIRE_TALKS_2026 | Iran War Ceasefire Talks | Geopolitics | 2.7 | low |

**2025 (12 events)**
- Operation Sindoor, Pahalgam Terror Attack, India-Pakistan Ceasefire, India-Pakistan Diplomatic Crisis, Twelve-Day War (Israel-Iran), ISRO SpaDeX Docking, India Extreme Weather, India-UK Trade Agreement, India-US Defence Pact, S&P Sovereign Upgrade, Four Labour Codes Enforcement, Indus Waters Treaty Suspension, LoC Skirmishes, Shukla ISS

**2024 (2 events)**
- Cyclone Dana – Puri, Wayanad Landslide

**2023 (7 events)**
- Chandrayaan-3 Landing, Aditya-L1 Solar Mission, G20 New Delhi Summit, India-Canada Diplomatic Row, Delhi Yamuna Floods, Gaza Red Sea Crisis

### 3.4 Seven Domains
Economics · Geopolitics · Defense · Technology · Climate · Governance · Society

---

## 4. Blast Score Engine

### 4.1 Design Philosophy
Severity is not a human label — it is a **computed property of the event's graph neighborhood**. An event becomes critical when the graph grows around it: more impacts branch off it, more evidence corroborates it, more events connect to it across domains.

### 4.2 Six Scoring Components

| Component | Max Weight | Cypher Signal |
|---|---|---|
| Impact count | 3.0 | `count(DISTINCT i)` where `(e)-[:CAUSED]->(i:Impact)` |
| Evidence volume | 2.0 | `count(DISTINCT ev)` where `(e)-[:PROVEN_BY]->(ev:Evidence)` |
| Evidence velocity (24h) | 1.5 | Evidence nodes with `ingested_at >= now-24h` |
| Cross-domain connections | 2.0 | `count(DISTINCT other)` where `(e)-[:CONNECTED_TO]-(other:Event)` |
| Domain breadth | 0.5 | `count(DISTINCT d2)` where `(e)-[:ALSO_IN]->(d2:Domain)` |
| Source confidence | 1.0 | `avg(ev.confidence)` |
| **Total** | **10.0** | |

### 4.3 Score Thresholds
```
≥ 8.5  →  critical
≥ 6.5  →  high
≥ 4.0  →  medium
< 4.0  →  low
```

### 4.4 API Endpoint
```
GET /ontology/blast-scores
→ { scores: [...], by_id: {event_id: row}, total: N }

Each row: { event_id, name, blast_score, computed_severity,
            impact_count, evidence_count, connection_count,
            cross_domain_count, recent_evidence }
```

### 4.5 Persistence
- `BLAST_SCORE_CYPHER` in `backend/app/queries.py` — single source of truth
- Writes `e.blast_score` back to Event nodes on every run
- Shared between `GET /ontology/blast-scores` endpoint and APScheduler Step 8
- Refreshed **every hour** via `_update_blast_scores()` in scheduler

### 4.6 Current Scores (as of 2026-03-27)
- 6 events → **high** (scores 6.3–8.2)
- 8 events → **medium** (scores 4.0–6.0)
- 26 events → **low** (scores < 4.0)

---

## 5. Scheme Delivery & Beneficiary Model

### 5.1 Scheme Classification
All 19 schemes carry a `scheme_type` property:
- **Type 1** — Emergency / Reactive (activated by crisis events)
- **Type 2** — Structural / Long-term (capability-building programs)

### 5.2 Scheme Registry

| Scheme ID | Name | Type |
|---|---|---|
| SCH_NDRF_FUND | NDRF Emergency Fund | 1 |
| SCH_PMKISAN | PM-KISAN | 2 |
| SCH_PMFBY | PM Fasal Bima Yojana | 1 |
| SCH_JJBY | Jeevan Jyoti Bima Yojana | 1 |
| SCH_NRLM | National Rural Livelihoods Mission | 2 |
| SCH_MGNREGS | MGNREGS | 1 |
| SCH_PLI_SOLAR | PLI Solar | 2 |
| SCH_GREEN_H2 | Green Hydrogen Mission | 2 |
| SCH_ONGC_VIDESH | ONGC Videsh Strategic Reserve | 2 |
| SCH_INSTC | INSTC Corridor | 2 |
| SCH_CHABAHAR | Chabahar Port Development | 2 |
| SCH_SPR | Strategic Petroleum Reserve | 1 |
| SCH_STARTUP_INDIA | Startup India | 2 |
| SCH_MSME_REVIVAL | MSME Revival Package | 1 |
| SCH_AGRI_INFRA | Agriculture Infrastructure Fund | 2 |
| SCH_ISM | India Semiconductor Mission | 2 |
| SCH_PLI_SEMI | PLI for Semiconductors | 2 |
| SCH_DIGITAL_INDIA | Digital India Programme | 2 |
| SCH_BORDER_INFRA | Border Infrastructure Development | 1 |

### 5.3 Beneficiary Model
```
(Scheme)-[:BENEFITS]->(Beneficiary {
    scheme_id,
    count,          # integer — number of direct beneficiaries
    description     # text description of beneficiary population
})
```

Every scheme has exactly one Beneficiary node. The `beneficiary_count` field in the API response is read from this node.

### 5.4 Verified Beneficiary Counts

**Iran War event (EVT_IRAN_WAR_2026) — 6 schemes:**
| Scheme | Beneficiary Count |
|---|---|
| SCH_SPR | 220,000,000 |
| SCH_ONGC_VIDESH | 75,000 |
| SCH_PLI_SOLAR | 82,000 |
| SCH_INSTC | 12,400 |
| SCH_CHABAHAR | 8,200 |
| SCH_GREEN_H2 | 1,800 |

**India Semiconductor Mission (EVT_INDIA_SEMI_MICRON_2026) — 2 schemes:**
| Scheme | Beneficiary Count |
|---|---|
| SCH_ISM | 35,000 |
| SCH_PLI_SEMI | 5,000 |

**Rupee Depreciation Crisis (EVT_RUPEE_INR_CRISIS_2026) — 2 schemes:**
| Scheme | Beneficiary Count |
|---|---|
| SCH_SPR | 220,000,000 |
| SCH_ONGC_VIDESH | 75,000 |

---

## 6. Data Ingestion Pipeline (8-Step Scheduler)

The `job_news_refresh()` function runs **every hour** via APScheduler.

```
Step 1 — Fetch RSS / GovData headlines
Step 2 — Deduplicate against DB
Step 3 — AI extraction (entity + relation extraction via Claude)
Step 4 — 4-gate validation
          Gate 1: Label allowlist
          Gate 2: Confidence threshold (≥ 0.7)
          Gate 3: Entity resolver (canonical ID mapping)
          Gate 4: Endpoint existence check
Step 5 — Merge entities into Neo4j (MERGE idempotent)
Step 6 — Merge relations into Neo4j (MERGE idempotent)
Step 7 — CONNECTED_TO cross-domain inference
          (new Event IDs from Step 5 → infer edges to related Events
           via shared Domain / Impact / Actor nodes)
Step 8 — Blast score refresh
          (recomputes e.blast_score for all 40 events using
           BLAST_SCORE_CYPHER; writes back to graph)
```

### 6.1 Five Pipeline Gaps Fixed in V5
1. **PROVEN_BY direction** — AI prompt corrected from `PROVES` to `PROVEN_BY`
2. **KNOWN_IDS_CONTEXT** — All 25+ canonical event IDs injected into AI context
3. **Entity resolver** — 170 entries (up from 133), all EVT_* IDs with aliases
4. **Step 7 CONNECTED_TO** — New events now get cross-domain edges automatically
5. **Step 8 blast_score** — Hourly refresh ensures dynamic severity stays current

---

## 7. Frontend Architecture

### 7.1 Pages
| Page | Key Feature |
|---|---|
| Intelligence Map | 31 events on Folium map, radius = computed_severity |
| National Intelligence | Curated NEEDS_MAP, WATCH_POINTS, ESCALATION_CHAIN per event |
| Ontology Graph | Interactive Neo4j subgraph, blast score badge, scheme decision panel |
| Crisis Tracker | Event timeline, live feed, severity distribution |
| Scheme Delivery | Event→Scheme→Beneficiary drill-down, Type 1/2 badges |
| Intelligence Verdict | Threat assessment with dynamic blast score card |
| Proof & Evidence | Evidence chain with source confidence visualization |

### 7.2 Single Source of Truth
`frontend/utils/events.py` — 31 canonical events with GPS, domain, color, date.
Adding an event here auto-propagates to Intelligence Map, Live Feed, Decision Brief, and all counters.

### 7.3 Dynamic Severity in UI
- `GET /ontology/blast-scores` fetched at page load
- If API data available: use `computed_severity` and `blast_score` from graph
- Fallback: manual approximation using static severity + connection count

---

## 8. Phase Completion Status

| Phase | Task | Status |
|---|---|---|
| Phase 0 | Create `feature/v5-demo-safe` branch | ✅ Done |
| Phase 1 | DETACH DELETE 4 hollow events (64 edges removed) | ✅ Done |
| Phase 1 | Mirror removal in `frontend/utils/events.py` | ✅ Done |
| Phase 2 | Seed 3 missing schemes (PLI_SEMI, DIGITAL_INDIA, BORDER_INFRA) | ✅ Done |
| Phase 2 | Seed 7 new 2026 events with full subgraphs | ✅ Done |
| Phase 2 | Seed 19 Beneficiary nodes across all schemes | ✅ Done |
| Phase 2 | Blast score engine (queries.py + ontology.py + scheduler.py) | ✅ Done |
| Phase 3 | Verify beneficiary counts — Iran War + new events | ✅ Verified |
| Phase 3 | Write V5 PRD | ✅ This document |

---

## 9. Demo Checklist

Before the 10 AM demo, verify:

- [ ] `GET /health` → `{"status": "ok"}`
- [ ] `GET /ontology/blast-scores` → 40 events, scores populated
- [ ] Intelligence Map renders 31 markers with correct colors
- [ ] Iran War event → 6 schemes, all with non-zero `beneficiary_count`
- [ ] Micron Fab event → 2 schemes, non-zero `beneficiary_count`
- [ ] Arunachal Standoff → blast score 7.5, BORDER_INFRA scheme visible
- [ ] Scheduler logs show Step 8 running hourly
- [ ] Neo4j Browser: `MATCH (n) RETURN count(n)` → ≥ 170 nodes

---

## 10. Known Limitations

1. **8 auto-ingested events** (lowercase IDs like `evt_cyclone_ditwah`) have blast scores of 0.7 — they were auto-ingested without curated Impacts/Evidence and remain in the graph but do not appear in `frontend/utils/events.py` dropdowns.
2. **`critical` threshold** (≥8.5) not yet reached — Iran War at 8.2 is closest. Will breach critical once hourly ingestion adds more Evidence nodes for 2026 events.
3. **Evidence velocity** component contributes 0 for seeded events (no `ingested_at` timestamp on MERGE-seeded Evidence nodes). Automatically improves as live scheduler adds new Evidence.
