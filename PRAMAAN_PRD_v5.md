# PRAMAAN v5 — Product Requirements Document
## India Governance Intelligence & Proof System

**Version:** 5.1
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
- **28 events** across 7 domains (expanded from 17 in v5.0)
- Cross-domain connections (gold edges)
- Real-time ingestion feed
- Events span 2023–2026 with coverage of geopolitical, climate, defense, and economic developments

**7 Domains:** Climate · Economics · Defense · Technology · Society · Governance · Geopolitics

**28 Events (sorted newest-first):**

| Event | Domain | Date |
|---|---|---|
| Iran War Ceasefire Talks | Geopolitics | Mar 2026 |
| Strait of Hormuz Blockade | Economics | Mar 2026 |
| Iran-US-Israel War | Geopolitics | Feb 2026 |
| Four Labour Codes Enforcement | Governance | Nov 2025 |
| India-US Defence Pact | Defense | Oct 2025 |
| S&P Sovereign Upgrade (BBB) | Economics | Aug 2025 |
| India-UK Trade Agreement (CETA) | Economics | Jul 2025 |
| First Indian on ISS (Shukla) | Technology | Jun 2025 |
| Twelve-Day War (Israel-Iran) | Geopolitics | Jun 2025 |
| India-Pakistan Diplomatic Crisis | Geopolitics | May 2025 |
| India-Pakistan Ceasefire | Geopolitics | May 2025 |
| Operation Sindoor | Defense | May 2025 |
| India-Pakistan LoC Skirmishes | Defense | Apr 2025 |
| Indus Waters Treaty Suspension | Governance | Apr 2025 |
| Pahalgam Terror Attack | Defense | Apr 2025 |
| India Extreme Weather 2025 | Climate | Jan 2025 |
| ISRO SpaDeX Docking | Technology | Jan 2025 |
| Cyclone Dana – Puri | Climate | Oct 2024 |
| Wayanad Landslide | Climate | Jul 2024 |
| Tata Semiconductor Fab | Economics | Feb 2024 |
| India-Canada Diplomatic Row | Geopolitics | Sep 2023 |
| G20 New Delhi Summit | Geopolitics | Sep 2023 |
| IMEC Corridor Signing | Economics | Sep 2023 |
| Aditya-L1 Solar Mission | Technology | Sep 2023 |
| Chandrayaan-3 Landing | Technology | Aug 2023 |
| Delhi Yamuna Floods | Society | Jul 2023 |
| Manipur Conflict | Defense | May 2023 |
| Joshimath Subsidence | Governance | Jan 2023 |

---

### Layer 2 — Government Response

```
(Event)-[:TRIGGERED {reason, confidence}]->(Response)
```

**IMPORTANT DISTINCTION — Two Response Types:**

#### Type 1: Event-Triggered Response Schemes
Directly activated by a crisis event. Stored as `scheme_type: "Type 1"` in Neo4j.

| Scheme ID | Name | Triggered By |
|---|---|---|
| SCH_NDRF_FUND | NDRF Fund | Wayanad, Chamoli, Cyclone Dana |
| SCH_SDRF | SDRF | Delhi Floods, Wayanad, Chamoli, Cyclone Dana, Joshimath |
| SCH_SPR | Strategic Petroleum Reserve | Hormuz Blockade, Iran War |
| SCH_CHABAHAR | Chabahar Port Development | Iran Ceasefire, Hormuz Blockade |
| SCH_ONGC_VIDESH | ONGC Videsh | Iran War, Hormuz Blockade |

#### Type 2: Structural/Implementation Schemes (Ongoing)
National schemes tracked for ground delivery. Stored as `scheme_type: "Type 2"` in Neo4j.

| Scheme ID | Name | Domain | Real Data Source |
|---|---|---|---|
| SCH_AMRUT | AMRUT | Urban Infrastructure | data.gov.in |
| SCH_PMAY | PMAY-U | Housing | data.gov.in |
| SCH_ISM | India-Saudi Maritime | Economics | data.gov.in |
| SCH_ISRO_BUDGET | ISRO Budget | Technology | data.gov.in |
| SCH_INSTC | INSTC Corridor | Geopolitics | data.gov.in |
| SCH_GREEN_H2 | Green Hydrogen Mission | Climate | data.gov.in |
| SCH_PLI_SOLAR | PLI Solar | Economics | data.gov.in |

> PRAMAAN clearly distinguishes Type 1 from Type 2. This is a core system design decision — not all schemes are event-triggered, and the UI makes this explicit with visual color coding (red = Type 1 Emergency, green = Type 2 Structural).

---

### Layer 3 — Delivery

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
- `New Event Ingested: Cyclone Alert — PIB Source`
- `New Evidence Added: Delhi Drainage Project — data.gov.in`

**Backend flow:**
```
Pre-seeded data → Button/Timer trigger → Neo4j update → UI refresh
```

**Judge positioning:**
> *"In MVP, ingestion is simulated to demonstrate continuous updating. In production, automated agents and APIs handle this continuously."*

---

## 7. UI — 6 SCREENS

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

### Screen 1: National Intelligence (Intelligence Map)

**Purpose:** Show all 28 events across 7 domains with government response and live feed.

**Shows:**
- Event map / ontology graph (7 domains, 28 events)
- Cross-domain gold edges
- Government response connections
- Live ingestion feed (button + auto-timer)

**Insight panel:**
> *"Repeated climate events stress the same infrastructure systems"*

---

### Screen 2: Crisis Tracker

**Purpose:** Real-time crisis monitoring — focused on active geopolitical and security events.

**Shows:**
- Active crisis events with severity indicators
- Crisis timeline and escalation status
- Cross-domain impact propagation
- Backend: `/crisis` router with crisis-specific Neo4j queries

---

### Screen 3: Intelligence Verdict

**Purpose:** AI-powered verdict and decision brief for selected events.

**Shows:**
- Per-event AI-generated intelligence brief
- Key actors, evidence sources, strategic implications
- Confidence scores and provenance chain
- Backend: `/verdict` router

---

### Screen 4: Scheme Delivery Monitor

**Purpose:** Per-event scheme delivery analysis with graphical impact metrics.

**Key UX behaviours:**
- Dropdown defaults to **"— Select an event —"** on initial load (no auto-selection)
- Selecting an event loads full delivery data from Neo4j via `/ontology/events/{event_id}`
- Proof chain summary pill row showing counts (Impacts · Schemes · Actors · Evidence · Cross-links)

**Graphical representation (v5.1 redesign):**

| Section | Visualization |
|---|---|
| Measured Impacts (numeric) | Plotly horizontal bar chart — bar length = magnitude, color = domain accent |
| Measured Impacts (non-numeric) | KPI text chips — bold value + label + description |
| Scheme Budgets | Plotly horizontal bar chart — red = Type 1 Emergency, green = Type 2 Structural |
| Scheme Cards | Grouped by Type 1 / Type 2 with utilization progress bar |

**Impact data handling:**
- `impact.type = null` in Neo4j → label falls back to `impact.id` (e.g. `IMP_INDIA_IMPORT_BILL` → "India Import Bill")
- String values like `"-3.2%"` handled by stripping non-numeric characters before float conversion
- Non-numeric values displayed as KPI chips rather than bar chart entries

**Scheme card details per card:**
- Scheme name + status badge (Active / At Risk / Partially Operational / Inactive)
- Budget in ₹ Crore
- Ministry
- Utilization % progress bar (if available)
- Description (120 chars)

**Cross-domain section:** Shows connected events from other domains with domain color coding.

---

### Screen 5: Proof & Evidence

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

All events have real government data. Full registry:

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
| Crude Oil Petroleum Imports | Iran War, Hormuz Blockade | data.gov.in |
| Merchandise + Services Trade | Hormuz Blockade | data.gov.in |
| Strategic Petroleum Reserve | Iran War, Hormuz Blockade | data.gov.in |
| Chabahar Port Trade Data | Iran Ceasefire | data.gov.in |
| AMRUT Storm Water Drainage | Delhi Floods | data.gov.in |
| PMAY Housing | Delhi Floods | data.gov.in |

---

## 11. METRICS DISPLAYED

| Metric | Where |
|---|---|
| Funds Tracked (₹ Cr) | Home |
| Verified Assets % | Home + Scheme Delivery |
| Evidence Count | Home + Proof & Evidence |
| Events Tracked | Home + National Intelligence |
| Live Updates Count | National Intelligence |
| Delivery % per Scheme | Scheme Delivery |
| Impact bar charts (Plotly) | Scheme Delivery |
| Budget comparison chart (Plotly) | Scheme Delivery |

---

## 12. NEO4J DATA MODEL — KEY PROPERTIES

### Scheme nodes
```
(Scheme {
    scheme_id,
    name,
    budget_crore,
    ministry,
    status,           // active | at_risk | partially_operational | inactive
    scheme_type,      // "Type 1" | "Type 2"  ← added in v5.1
    utilization_pct,
    description
})
```

### Impact nodes
```
(Impact {
    id,
    type,             // may be null — UI falls back to id-derived label
    value,            // numeric or string (e.g. "-3.2%")
    unit,
    description,
    source
})
```

---

## 13. SYSTEM OPERATION (FOR JUDGES)

> *"PRAMAAN uses:*
> - *Pre-seeded real government data for structure*
> - *Simulated ingestion to demonstrate real-time behavior*
> - *Source-backed evidence for proof validation*
>
> *In production: automated agents and APIs update the graph continuously."*

---

## 14. SCALABILITY

> *"The same ontology supports all domains and regions across India. Scaling requires only adding new data — no redesign needed."*

---

## 15. DIFFERENTIATION

| Existing Systems | PRAMAAN |
|---|---|
| Show data | Connects data |
| Track schemes | Verifies delivery |
| Report numbers | Proves outcomes |
| Static dashboards | Live proof chain |
| Emoji/text metrics | Plotly graphical impact charts |

---

## 16. TECH STACK

| Layer | Technology |
|---|---|
| Graph Database | Neo4j 5.18 |
| Backend | FastAPI (Python) |
| Frontend | Streamlit 1.55.0 |
| Charts | Plotly 6.6.0 (horizontal bar charts) |
| AI / Insights | Groq · LLaMA 3.3 70B |
| Data Sources | data.gov.in · PIB · NDMA · ISRO · IMD |
| Deployment | Docker Compose |

---

## 17. MVP SCOPE

### INCLUDED
- **28 events**, 7 domains, real data (expanded from 17 in v5.0)
- 5-layer proof chain (Layers 1–4 fully built)
- Layer 5 Citizen — mock UI card
- 6-page UI + home screen
- Real-time ingestion (button + timer)
- Insights Engine (2–3 insights + 1 decision)
- Trust Layer (source + confidence)
- Type 1 / Type 2 scheme distinction — visual color coding throughout
- `scheme_type` property on all scheme nodes in Neo4j
- Plotly graphical impact and budget charts on Scheme Delivery
- Smart dropdown: no auto-select on initial load (user must choose an event)
- Iran War / Ceasefire / Hormuz Blockade events with full impact + scheme data
- Operation Sindoor, Pahalgam, India-Pakistan crisis chain fully modelled
- Crisis Tracker and Intelligence Verdict screens

### NOT INCLUDED
- Full India coverage
- Full automation pipelines
- Large-scale ML
- Real citizen notifications

---

## 18. CHANGELOG

### v5.1 (March 2026)
- **Events expanded:** 17 → 28 events; added Iran War, Hormuz Blockade, Iran Ceasefire, Operation Sindoor, Pahalgam, India-Pakistan chain, LoC Skirmishes, Indus Waters, Shukla ISS, Twelve-Day War, S&P Upgrade, CETA, Labour Codes, India-US Defence Pact, SpaDeX
- **Scheme Delivery redesign:** Replaced raw HTML rendering bug (st.markdown with 4-space indented HTML) with `st.html()` throughout
- **Plotly charts:** Horizontal bar charts for numeric impact values; budget comparison chart for schemes (red=Type 1, green=Type 2)
- **Type 1/Type 2 visual split:** Scheme cards grouped by type with color-coded headers and utilization bars
- **`scheme_type` Neo4j property:** Seeded on all scheme nodes via seed_scheme_types.py
- **Impact null handling:** `impact.type=null` nodes now render with fallback label derived from `impact.id`
- **Dropdown UX:** Scheme Delivery no longer auto-selects Iran Ceasefire on load; `include_none=True` in `render_event_dropdown()` shows placeholder until user makes a selection
- **New screens:** Crisis Tracker + Intelligence Verdict pages added
- **Delhi Pilot tab:** Removed from Scheme Delivery (standalone delivery chain still in Neo4j)

### v5.0 (March 2026)
- Initial MVP with 17 events, 5-layer proof chain, Delhi pilot
- 4-page UI: Home · National Intelligence · Scheme Tracker · Proof & Evidence

---

## 19. FINAL DEMO LINE

> *"PRAMAAN transforms governance from assumption to proof — in real time."*

---

## 20. ONE-LINE SUMMARY

> Build less. Show impact. Prove it.
