# PRAMAAN v5 — Product Requirements Document
## India Governance Intelligence & Proof System

**Version:** 5.0
**Date:** March 2026
**Competition:** India Innovates 2026 · Digital Democracy Domain
**Venue:** Bharat Mandapam, New Delhi · March 28–29, 2026
**Status:** MVP FINAL — Demo Ready

---

## 1. TAGLINE

> *"From Events to Evidence — Making Governance Verifiable in Real Time"*

---

## 2. VISION

PRAMAAN connects national events, government responses, and ground-level delivery into a unified intelligence graph — enabling real-time visibility, verification, and decision-making for governance.

> It is not a dashboard. It is a **living proof chain**.

---

## 3. PROBLEM STATEMENT

India generates massive governance data across:
- Events (crises, policies, developments)
- Government responses (schemes, policies, missions)
- Implementation (assets, beneficiaries, funds)

**The gap:** No system connects events → responses → delivery → proof, verifies if schemes reach the ground, or generates decision-making insights from this chain.

---

## 4. CORE INSIGHT

> Events expose problems.
> Government responds.
> Schemes deliver solutions.
> PRAMAAN proves whether it actually happened.

---

## 5. ARCHITECTURE — 5 LAYERS

### Layer 1 — Events
```
(Event)-[:CONNECTED_TO]->(Event)
```
- 17 events across 7 domains
- Cross-domain connections (gold edges)
- Real-time ingestion feed

**7 Domains:** Climate · Economics · Defense · Technology · Society · Governance · Geopolitics

**17 Events:**
| Event | Domain | Date |
|---|---|---|
| Wayanad Landslide | Climate | Jul 2024 |
| Cyclone Dana – Puri | Climate | Oct 2024 |
| Chamoli Glacier Burst | Climate | Feb 2021 |
| Joshimath Subsidence | Governance | Jan 2023 |
| Delhi Yamuna Floods | Society | Jul 2023 |
| COVID Second Wave | Society | Apr 2021 |
| Manipur Conflict | Defense | May 2023 |
| Balakot Airstrikes | Defense | Feb 2019 |
| Article 370 Abrogation | Governance | Aug 2019 |
| Tata Semiconductor Fab | Economics | Feb 2024 |
| IMEC Corridor Signing | Economics | Sep 2023 |
| G20 New Delhi Summit | Geopolitics | Sep 2023 |
| India-Canada Diplomatic Row | Geopolitics | Sep 2023 |
| Chandrayaan-3 Landing | Technology | Aug 2023 |
| Aditya-L1 Solar Mission | Technology | Sep 2023 |
| Russia–Ukraine War | Geopolitics | Feb 2022 |
| Gaza War & Red Sea Crisis | Geopolitics | Oct 2023 |

---

### Layer 2 — Government Response

```
(Event)-[:TRIGGERED {reason, confidence}]->(Response)
```

**IMPORTANT DISTINCTION — Two Response Types:**

#### Type 1: Event-Triggered Response Schemes
Directly activated by a crisis event.

| Scheme | Triggered By |
|---|---|
| SDRF | Delhi Floods, Wayanad, Chamoli, Cyclone Dana, Joshimath |
| NDRF | Wayanad, Chamoli, Cyclone Dana |

#### Type 2: Implementation Schemes (Ongoing)
National schemes tracked for ground delivery. Connected via governance need — not forced event links.

| Scheme | Domain | Real Data Source |
|---|---|---|
| AMRUT | Urban Infrastructure | data.gov.in |
| PMAY | Housing | data.gov.in |
| PLI | Manufacturing | data.gov.in |
| Ayushman Bharat | Health | data.gov.in |
| PM SVANidhi | Vendor Relief | data.gov.in |
| SBM | Sanitation | data.gov.in |

> PRAMAAN clearly distinguishes Type 1 from Type 2. This is a core system design decision — not all schemes are event-triggered, and the UI makes this explicit.

---

### Layer 3 — Delivery (Delhi Pilot)

```
(Scheme)-[:FUNDS]->(Asset)
(Asset)-[:LOCATED_IN]->(Region)
```

**Anchor Event:** Delhi Yamuna Floods (Jul 2023)

**Delivery Chain:**
```
Delhi Yamuna Floods
    → SDRF activated (Type 1 response)
    → AMRUT: 3 drainage projects, Delhi
        → 2 completed (₹2.01 Cr) ✅
        → 1 in progress (₹3.37 Cr) ⚠️
    → PMAY: 17,067 houses, Delhi
        → 17,067 completed (₹401.79 Cr) ✅
        → 100% occupied ✅
```

**Real Data Sources:** data.gov.in (AMRUT storm water drainage, PMAY-U housing)

---

### Layer 4 — Evidence

```
(Asset)-[:HAS_EVIDENCE]->(Evidence)
```

**Evidence Types:**
- Before/After Photo (if available)
- PIB press release
- data.gov.in dataset record
- ISRO/NDMA source text

**Display Rule:**
> If image exists → show before/after photo
> If no image → show data proof (source, numbers, link)

---

### Layer 5 — Citizen (MVP: Mock UI Only)

```
(Citizen)-[:LIVES_ON]->(Region)
(Citizen)-[:RECEIVES]->(Notification)
```

**MVP Scope:** Static UI card showing simulated WhatsApp notification.
**Production:** Real beneficiary notifications via agents.

> *"In MVP, citizen layer is a simulated display. In production, field agents push verified notifications to beneficiaries."*

---

## 6. REAL-TIME INGESTION

**Purpose:** Show system is live and continuously updating.

**Triggers:** Button-triggered AND auto-timer (both).

**What happens:**
1. New event appears in graph
2. New response linked
3. New evidence added
4. UI refreshes with notification

**Example UI messages:**
- `🔄 New Event Ingested: Cyclone Alert — PIB Source`
- `🔄 New Evidence Added: Delhi Drainage Project — data.gov.in`

**Backend flow:**
```
Pre-seeded data → Button/Timer trigger → Neo4j update → UI refresh
```

**Judge positioning:**
> *"In MVP, ingestion is simulated to demonstrate continuous updating. In production, automated agents and APIs handle this continuously."*

---

## 7. UI — 5 SCREENS

---

### Screen 0: PRAMAAN (Home)

**Purpose:** Landing page — sets the narrative before the demo.

**Shows:**
- Logo + animated title
- Tagline: *"From Events to Evidence — Making Governance Verifiable in Real Time"*

**v5 Stats (animated countUp):**
| Stat | Source |
|---|---|
| Funds Tracked (₹ Cr) | Sum of scheme budgets in Neo4j |
| Verified Assets | Assets with status=completed |
| Evidence Nodes | Evidence count in Neo4j |
| Events Tracked | Event count across 7 domains |

**CTA:** "Enter Dashboard →" → goes to National Intelligence

---

### Screen 1: National Intelligence

**Purpose:** Show all 17 events across 7 domains with government response and live feed.

**Shows:**
- Event map / ontology graph (7 domains, 17 events)
- Cross-domain gold edges
- Government response connections
- 🔄 Live ingestion feed (button + auto-timer)

**Insight panel:**
> *"Repeated climate events stress the same infrastructure systems"*

---

### Screen 2: Scheme Tracker

**Purpose:** Show scheme intelligence and decision engine.

**Two-panel structure:**

**Panel A — Event Response Schemes (Type 1):**
| Scheme | Triggered By | Amount Released |
|---|---|---|
| SDRF | Delhi Floods 2023 | ₹X Cr |
| NDRF | Wayanad Landslide 2024 | ₹X Cr |

**Panel B — Implementation Schemes (Type 2):**
| Scheme | Delivery % | Evidence % |
|---|---|---|
| AMRUT | 67% | X% |
| PMAY | 100% | X% |
| PLI | X% | X% |

**Decision Panel (AMRUT — accountability gap):**
> *"₹5.38 Cr allocated for Delhi drainage — 1 of 3 projects unverified*
> *→ Recommendation: Investigate Ward drainage project"*

**MUST SHOW:** DATA → INSIGHT → DECISION

---

### Screen 3: Delivery Monitor

**Purpose:** Show ground-level delivery in Delhi pilot.

**Shows:**
- Scheme → Ward → Asset chain
- Delhi AMRUT: 3 drainage projects (2 complete, 1 in progress)
- Delhi PMAY: 17,067 houses (100% complete)
- Delivery score per scheme
- 🔄 Live update: `"New Asset Verified — Delhi Drainage"`

**PMAY proof moment:**
> *"₹401.79 Cr released — 17,067 houses — 100% occupied ✅"*

---

### Screen 4: Proof & Evidence

**Purpose:** Show the actual proof — before/after, evidence nodes, citizen mock.

**Shows:**
- Evidence per asset (photo if available, data proof if not)
- PIB / ISRO / NDMA source links
- Trust layer: source + confidence score per node
- Citizen mock: simulated WhatsApp notification card

**Trust layer display:**
> *"34 Evidence nodes | 14 LIVE | 0 hallucinated"*
> *"All connections are source-backed or confidence-scored"*

---

## 8. INSIGHTS ENGINE

**Outputs:**
1. Risk Insight — pattern of repeated stress
2. Pattern Insight — cross-domain correlation
3. Decision Recommendation — actionable output

**Examples:**
> *"Flood-prone regions receiving repeated infrastructure investment without completion verification"*
> *"Chandrayaan-3 success correlates with 3-year DoS budget increase of ₹4,200 Cr"*
> *"Recommendation: Prioritise AMRUT Ward drainage completion before monsoon 2026"*

---

## 9. TRUST LAYER

Each node in the graph includes:
- `source` — data.gov.in / PIB / NDMA / ISRO / IMD
- `confidence` — high / medium / low

UI display on every page:
> *"All connections are source-backed or confidence-scored"*

---

## 10. REAL DATA COVERAGE

All 17 events have real government data. Full registry:

| Dataset | Events Covered | Source |
|---|---|---|
| NDRF/SDRF Funds | Wayanad, Chamoli, Joshimath, Delhi Floods, Cyclone Dana | data.gov.in |
| NDRF Lives Saved | Wayanad, Chamoli, Cyclone Dana | data.gov.in |
| Cyclone Frequency | Cyclone Dana | data.gov.in |
| Cyclone Damage | Cyclone Dana, Chamoli | data.gov.in |
| COVID Deaths + Cases | COVID Wave 2 | data.gov.in |
| Ayushman Bharat | COVID Wave 2 | data.gov.in |
| PM SVANidhi | COVID Wave 2 | data.gov.in |
| SBM Toilets | COVID Wave 2 | data.gov.in |
| PLI Applications + Investments | Tata Semi, IMEC | data.gov.in |
| Semiconductor Imports | Tata Semi | data.gov.in |
| FDI Equity + Countrywise | G20, IMEC, India-Canada | data.gov.in |
| Defence Budget R&D + GDP | Balakot, Manipur | data.gov.in |
| JK Development Investment | Article 370 | data.gov.in |
| DoS Budget Allocation | Chandrayaan-3, Aditya-L1 | data.gov.in |
| ISRO/VSSC Budget | Chandrayaan-3, Aditya-L1 | data.gov.in |
| Crude Oil Petroleum Imports | Russia-Ukraine | data.gov.in |
| Merchandise + Services Trade | Gaza/Red Sea | data.gov.in |
| AMRUT Storm Water Drainage | Delhi Floods | data.gov.in |
| PMAY Housing | Delhi Floods | data.gov.in |

---

## 11. METRICS DISPLAYED

| Metric | Where |
|---|---|
| Funds Tracked (₹ Cr) | Home |
| Verified Assets % | Home + Delivery Monitor |
| Evidence Count | Home + Proof & Evidence |
| Events Tracked | Home + National Intelligence |
| Live Updates Count | National Intelligence |
| Delivery % per Scheme | Scheme Tracker + Delivery Monitor |

---

## 12. SYSTEM OPERATION (FOR JUDGES)

> *"PRAMAAN uses:*
> - *Pre-seeded real government data for structure*
> - *Simulated ingestion to demonstrate real-time behavior*
> - *Source-backed evidence for proof validation*
>
> *In production: automated agents and APIs update the graph continuously."*

---

## 13. SCALABILITY

> *"The same ontology supports all domains and regions across India. Scaling requires only adding new data — no redesign needed."*

---

## 14. DIFFERENTIATION

| Existing Systems | PRAMAAN |
|---|---|
| Show data | Connects data |
| Track schemes | Verifies delivery |
| Report numbers | Proves outcomes |
| Static dashboards | Live proof chain |

---

## 15. TECH STACK

| Layer | Technology |
|---|---|
| Graph Database | Neo4j 5.18 |
| Backend | FastAPI (Python) |
| Frontend | Streamlit |
| AI / Insights | Groq · LLaMA 3.3 70B |
| Data Sources | data.gov.in · PIB · NDMA · ISRO · IMD |
| Deployment | Docker Compose |

---

## 16. MVP SCOPE

### INCLUDED
- 17 events, 7 domains, real data
- 5-layer proof chain (Layers 1–4 fully built)
- Layer 5 Citizen — mock UI card
- Delhi pilot — AMRUT + PMAY with real data
- 4-page UI + home screen
- Real-time ingestion (button + timer)
- Insights Engine (2–3 insights + 1 decision)
- Trust Layer (source + confidence)
- Type 1 / Type 2 scheme distinction

### NOT INCLUDED
- Full India coverage
- Full automation pipelines
- Large-scale ML
- Real citizen notifications

---

## 17. FINAL DEMO LINE

> *"PRAMAAN transforms governance from assumption to proof — in real time."*

---

## 18. ONE-LINE SUMMARY

> Build less. Show impact. Prove it.
