# PRAMAAN — Gaps, Enhancements & Suggestions
> Compiled from full project audit — March 17, 2026
> Covers: UI, Data, AI, Governance, Architecture, Vision alignment

---

## STATUS LEGEND
- 🔴 Critical — blocks demo or core story
- 🟡 Important — adds credibility or completeness
- 🟢 Enhancement — good to have, Phase 2+
- ✅ Fixed/Done

---

## PART 1 — UI STRUCTURE

### Missing Pages
| # | Item | Priority | Effort |
|---|---|---|---|
| 1.1 | `04_⚡_Live_Ingestion.py` — `hidden_Live_Ingestion.py` is fully built but sitting in `frontend/` not `frontend/pages/`. Not visible in sidebar. Moving it makes the entire demo story complete. | 🔴 Critical | 30 min |
| 1.2 | `05_📊_Delivery_Graph.py` — PRD specified but skip entirely. Proof Chain already covers this visually. | ✅ Skip | — |

### Page Restructure (6 → 3)
| # | Item | Priority | Effort |
|---|---|---|---|
| 1.3 | **Remove Home page** (`app.py`) — pure navigation, wastes a click. Open on Dashboard by default. | 🟡 Important | 30 min |
| 1.4 | **Merge Questions page into Proof Chain** — both explore the same asset truth. Put NL query box at bottom of Proof Chain. | 🟡 Important | 2 hrs |
| 1.5 | **Hide or fix WhatsApp page** (`07_💬_Micro_Accountability.py`) — broken without live Twilio credentials. Demo risk. Either wire Twilio with a real demo number or move out of `pages/`. | 🔴 Critical | 30 min |

### Ideal 3-Page Final Structure
```
Page 1: Intelligence Dashboard  (current Ward Map)
Page 2: Proof Explorer          (Proof Chain + Questions merged)
Page 3: Live Feed               (hidden_Live_Ingestion promoted)
```

---

## PART 2 — LIVE INGESTION ENHANCEMENTS

| # | Item | Priority | Effort |
|---|---|---|---|
| 2.1 | **Photo Upload with EXIF GPS Matching** — citizen uploads geo-tagged phone photo → `exifread` reads GPS coordinates → matched to nearest Neo4j asset (within radius) → creates Evidence node → upgrades asset `proof_status` to `fully_verified`. `exifread` already in `requirements.txt`. | 🔴 Critical | 4–5 hrs |
| 2.2 | **Voice-to-Text Input** — record audio in browser → send to Groq Whisper API (`whisper-large-v3`) → transcribed text lands in existing input box → same extraction pipeline runs. Groq API key already in use. | 🟡 Important | 2 hrs |
| 2.3 | **Background Feed Polling** — instead of manual trigger, a background service polls Google News RSS every N minutes for configured queries and auto-ingests new articles. | 🟢 Phase 2 | 1 day |
| 2.4 | **Offline Cache Mode** — already partially built (`load_cache()` function exists). Wire it fully so demo works without internet. | 🟡 Important | 1 hr |

---

## PART 3 — DATA GAPS

### Seed Data Scale
| # | Item | Priority | Effort |
|---|---|---|---|
| 3.1 | **Expand to 300+ nodes** — current CSVs have ~112 rows total. PRD Section 15.1 Go/No-Go requires ≥300 nodes for demo readiness. Run `backend/scripts/seed_multi_scheme.py` or extend CSVs. | 🔴 Critical | 2–3 hrs |
| 3.2 | **Before/After photos for more assets** — currently only manually curated assets in `constants.py` have photo evidence. Needs real photo submission pipeline (see 2.1). | 🟡 Important | Tied to 2.1 |
| 3.3 | **Real GPS coordinates for all assets** — Ward Map currently uses random offsets around a fixed coordinate. CSV `lat/lon` fields exist but are mostly empty. | 🟡 Important | 2 hrs |
| 3.4 | **`sbm_toilets.json` is wrong data** — file is actually an All India Pincode Directory. Replace with real SBM toilet dataset from data.gov.in. | 🟡 Important | 1 hr |

### Data Quality Issues
| # | Item | Priority | Effort |
|---|---|---|---|
| 3.5 | **Financial Integrity Tracker bars are hardcoded** — Sanctioned/Released/Verified percentages (92%, 85%) are hardcoded in Proof Chain. Not real treasury data. Either remove the chart or wire it to real budget release data. | 🟡 Important | 1 hr to remove / 1 day to wire real data |
| 3.6 | **`sync_evidence_to_neo4j()` bug** — `asset_id` was used inside function but not passed as parameter. Fixed — `asset_id: str` param added and Cypher corrected. | ✅ Fixed | — |
| 3.7 | **PMAY `/data/pmay-housing` endpoint** — added, returns Delhi row + national subtotal + all 36 states. | ✅ Fixed | — |

---

## PART 4 — DATA GOVERNANCE (Currently Zero Infrastructure)

### Node-Level Provenance
| # | Item | Priority | Effort |
|---|---|---|---|
| 4.1 | **Add provenance fields to every node** — every node in the graph should carry: `source_type` (official_csv / ai_extract / news_rss / photo_exif / manual), `source_url`, `ingested_at`, `ingested_by`, `confidence` (0.0–1.0), `version`. | 🔴 Critical | 2 hrs |
| 4.2 | **Store LLM confidence on nodes** — LLM already returns `confidence: 0.85` in every extraction response. It's just not being saved to the node. Wire it through `IngestEntity` → `models.py` → `queries.py`. | 🔴 Critical | 30 min |
| 4.3 | **Display trust tier badge in Proof Chain UI** — show `Official` / `AI Extracted` / `News Only` / `Unverified` badge on each chain node. | 🟡 Important | 1 hr |

### Trust Hierarchy
```
TIER 1 — Official      (confidence: 1.0)   data.gov.in, PIB, Budget docs, Satellite
TIER 2 — Verified      (confidence: 0.8–0.9) Geo-tagged photos, Cross-validated news
TIER 3 — AI Extracted  (confidence: 0.5–0.7) LLM extraction, Single-source claims
TIER 4 — Unverified    (confidence: < 0.5)   Manual paste, Flagged, Contradicted
```

### Conflict & Lineage
| # | Item | Priority | Effort |
|---|---|---|---|
| 4.4 | **Conflict detection** — when a new fact contradicts an existing node, create a `CONTRADICTS` edge between the two claims, flag both for human review, show both in Proof Chain with confidence scores. Don't silently overwrite. | 🟢 Phase 2 | 1 day |
| 4.5 | **Node versioning** — when a node is updated, preserve the old version. `version: int` field + optional `previous_state` log. | 🟢 Phase 2 | 1 day |
| 4.6 | **Full audit trail** — record who changed what node, when, from what source. | 🟢 Phase 2 | 1 day |
| 4.7 | **Access control** — currently any user running the app can write to Neo4j. Need read vs write vs admin roles. | 🟢 Phase 2 | 2 days |

---

## PART 5 — AI GOVERNANCE (Currently Zero Infrastructure)

### Immediate (MVP)
| # | Item | Priority | Effort |
|---|---|---|---|
| 5.1 | **Store confidence on every AI-extracted node** — same as 4.2. Critical for credibility. | 🔴 Critical | 30 min |
| 5.2 | **Store extraction source text** — every AI node should store the original text chunk it was extracted from. Enables "why did AI think this?" | 🟡 Important | 1 hr |
| 5.3 | **Store AI model + prompt version** — `ai_model: "llama-3.3-70b-versatile"`, `ai_prompt_version: "v1.0"` on every AI-extracted node. Enables reproducibility. | 🟡 Important | 30 min |

### Phase 2
| # | Item | Priority | Effort |
|---|---|---|---|
| 5.4 | **Human-in-the-loop review queue** — AI extractions with `confidence < 0.6` go to a review queue instead of auto-writing to graph. Human accepts / rejects / edits before it enters. | 🟢 Phase 2 | 1 day |
| 5.5 | **Hallucination guard** — before writing AI-extracted node, validate: does the scheme_id exist? Is the region a known ward? Is the cost in a realistic range? Does the source URL respond? Flag failures, lower confidence. | 🟢 Phase 2 | 1 day |
| 5.6 | **LLM audit log** — log every LLM call: model, input tokens, output tokens, confidence, entities extracted, source, result (accepted/rejected). | 🟢 Phase 2 | Half day |
| 5.7 | **Contradiction detection** — before ingesting, check if extracted claim contradicts existing nodes. Alert and create `CONTRADICTS` relationship if so. | 🟢 Phase 2 | 1 day |

---

## PART 6 — ONTOLOGY EXPANSION (Vision Alignment)

### Current Ontology (Governance-only, 7 types)
```
Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event
```

### Phase 2 Additions (Bridge to Global Vision)
| # | Item | Priority | Effort |
|---|---|---|---|
| 6.1 | **Add `Claim` node type** — represents any statement/allegation with a source and confidence. The atomic unit of the intelligence engine. | 🟡 Important | 2 hrs |
| 6.2 | **Add `Agreement` node type** — treaties, MOUs, trade deals, alliance pacts. Foundation for geopolitics domain. | 🟡 Important | 2 hrs |
| 6.3 | **Add `Technology` node type** — weapon systems, AI models, satellites, chips. Foundation for defense/tech domain. | 🟡 Important | 2 hrs |
| 6.4 | **Add `Metric` node type** — GDP, temperature, unemployment, defense spend. Foundation for economics/climate domain. | 🟡 Important | 2 hrs |
| 6.5 | **New edge types** — `CONTRADICTS`, `RATIFIED_BY`, `ENABLES`, `SANCTIONS`, `COMPETES_WITH`, `INFLUENCES`. | 🟡 Important | 2 hrs |
| 6.6 | **Temporal versioning on edges** — every relationship needs a `valid_from` and `valid_to` date. India-Russia relationship in 2022 ≠ 2026. | 🟢 Phase 2 | 1 day |

### Phase 3 — Cross-Domain Intelligence
| # | Item | Priority | Effort |
|---|---|---|---|
| 6.7 | **Cross-domain signal correlation** — detect patterns across domains (sanction → trade drop → defense spend change). | 🟢 Phase 3 | 1 week |
| 6.8 | **Pattern detection & anomaly alerts** — fire alerts when a cluster of signals in the graph matches a defined pattern. | 🟢 Phase 3 | 1 week |
| 6.9 | **Scenario modeling** — "what if India imposes tariffs on X?" → graph propagation to downstream nodes. | 🟢 Phase 3 | 2 weeks |

---

## PART 7 — AGENTIC AI (Post-MVP Vision)

> Full design in `docs/todo.md` under "Future Work — Agentic AI Implementation"

| # | Agent | What It Does | Priority |
|---|---|---|---|
| 7.1 | **Data Ingestion Agent** | Monitors PIB, news, MCD portals autonomously. Schedule/event-driven ingestion. Quality validation before graph write. | 🟢 Phase 2 |
| 7.2 | **Verification Agent** | Cross-checks AI-extracted entities against existing graph. Confidence scoring. Flags discrepancies for human review. | 🟢 Phase 2 |
| 7.3 | **Gap Detection Agent** | Autonomous gap analysis — missing evidence, broken chains. Proactive alerts on new gaps as data is ingested. | 🟢 Phase 2 |
| 7.4 | **Query Agent** | Multi-step reasoning across graph. Autonomous question decomposition. Explainable answer generation with graph paths. | 🟢 Phase 2 |
| 7.5 | **Evidence Linking Agent** | Automatic geo-tagging and asset matching. Before/after photo pairing. Temporal validation. | 🟢 Phase 2 |

---

## PART 8 — BACKEND GAPS

| # | Item | Priority | Effort |
|---|---|---|---|
| 8.1 | **`config.py` key mismatch** — `app_env` vs `PRAMAAN_ENV` inconsistency noted in todo.md. | 🟡 Important | 30 min |
| 8.2 | **`DELETE /ingest/demo-nodes`** — endpoint called in Live Ingestion UI developer tools but may not be implemented in backend router. | 🟡 Important | 1 hr |
| 8.3 | **No rate limiting on LLM calls** — if user spams the extract button, unlimited Groq API calls fire. Add debounce or rate limit. | 🟡 Important | 1 hr |
| 8.4 | **No input sanitization on `/questions/custom`** — LLM-generated Cypher runs directly on Neo4j. Needs a whitelist/safety check. | 🟡 Important | 1 hr |

---

## PART 9 — COMPLETE PRIORITIZED BACKLOG (All Items)

> All 46 open items across all parts, ordered by phase and priority.
> ✅ = already fixed | 🔴 Critical | 🟡 Important | 🟢 Phase 2/3

---

### 🔴 PHASE 1 — MVP / Demo Ready (Do These Now)

| # | Ref | What | Effort |
|---|---|---|---|
| 1 | 1.1 | Promote `hidden_Live_Ingestion.py` → `pages/04_⚡_Live_Ingestion.py` | 30 min |
| 2 | 1.5 | Hide or fix WhatsApp page — demo risk without live Twilio | 30 min |
| 3 | 4.2 | Store LLM confidence on nodes — already returned, just not saved | 30 min |
| 4 | 8.1 | Fix `config.py` key mismatch (`app_env` vs `PRAMAAN_ENV`) | 30 min |
| 5 | 3.1 | Expand seed data to 300+ nodes — PRD Go/No-Go gate | 2–3 hrs |
| 6 | 4.1 | Add `source_type`, `ingested_at`, `ingested_by` to every ingest node | 2 hrs |
| 7 | 4.3 | Show trust tier badge (Official / AI / Unverified) in Proof Chain UI | 1 hr |
| 8 | 2.1 | Photo upload with EXIF GPS matching → auto-upgrade asset proof_status | 4–5 hrs |
| 9 | 2.2 | Voice-to-text via Groq Whisper API | 2 hrs |
| 10 | 2.4 | Wire offline cache mode fully in Live Ingestion | 1 hr |
| 11 | 3.3 | Add real GPS lat/lon for all assets in CSV | 2 hrs |
| 12 | 3.5 | Fix or remove hardcoded Financial Integrity Tracker bars in Proof Chain | 1 hr |
| 13 | 8.2 | Implement `DELETE /ingest/demo-nodes` endpoint (called in UI, may not exist) | 1 hr |
| 14 | 8.3 | Add rate limiting / debounce on LLM extract button | 1 hr |
| 15 | 8.4 | Add safety check on `/questions/custom` — LLM Cypher runs directly on Neo4j | 1 hr |

---

### 🟡 PHASE 1.5 — UX & Data Quality (Before First Real User)

| # | Ref | What | Effort |
|---|---|---|---|
| 16 | 1.3 | Remove Home page — open on Dashboard by default | 30 min |
| 17 | 1.4 | Merge Questions page into Proof Chain — NL query box at bottom | 2 hrs |
| 18 | 3.2 | Wire real photo submission pipeline for Before/After evidence | Tied to 2.1 |
| 19 | 3.4 | Replace `sbm_toilets.json` (pincode directory) with real SBM toilet data from data.gov.in | 1 hr |
| 20 | 5.2 | Store extraction source text on every AI node — "why did AI extract this?" | 1 hr |
| 21 | 5.3 | Store `ai_model` + `ai_prompt_version` on every AI-extracted node | 30 min |
| 22 | 6.1 | Add `Claim` node type to ontology — atomic unit of intelligence engine | 2 hrs |
| 23 | 6.2 | Add `Agreement` node type — treaties, MOUs, trade deals | 2 hrs |
| 24 | 6.3 | Add `Technology` node type — weapon systems, AI models, chips, satellites | 2 hrs |
| 25 | 6.4 | Add `Metric` node type — GDP, temperature, unemployment, defense spend | 2 hrs |
| 26 | 6.5 | Add new edge types: `CONTRADICTS`, `RATIFIED_BY`, `ENABLES`, `SANCTIONS`, `COMPETES_WITH`, `INFLUENCES` | 2 hrs |

---

### 🟢 PHASE 2 — Intelligence Layer (Post-MVP)

| # | Ref | What | Effort |
|---|---|---|---|
| 27 | 2.3 | Background feed polling — auto-watch Google News RSS every N minutes | 1 day |
| 28 | 4.4 | Conflict detection — create `CONTRADICTS` edge when facts clash, flag for review | 1 day |
| 29 | 4.5 | Node versioning — preserve old version when node is updated | 1 day |
| 30 | 4.6 | Full audit trail — record who changed what node, when, from what source | 1 day |
| 31 | 4.7 | Access control — read vs write vs admin roles for Neo4j | 2 days |
| 32 | 5.1 | Human-in-the-loop review queue — confidence < 0.6 goes to review before writing | 1 day |
| 33 | 5.4 | Hallucination guard — validate scheme_id, region, cost range, source URL before write | 1 day |
| 34 | 5.5 | LLM audit log — model, tokens, confidence, result per call | Half day |
| 35 | 5.6 | Contradiction detection — check new claim against existing graph before ingesting | 1 day |
| 36 | 6.6 | Temporal versioning on edges — `valid_from` / `valid_to` on every relationship | 1 day |
| 37 | 7.1 | **Data Ingestion Agent** — autonomous monitor of PIB, news, MCD portals | 1 week |
| 38 | 7.2 | **Verification Agent** — cross-check AI entities against graph, confidence scoring | 1 week |
| 39 | 7.3 | **Gap Detection Agent** — autonomous gap analysis, proactive alerts | 1 week |
| 40 | 7.4 | **Query Agent** — multi-step reasoning, explainable answers with graph paths | 1 week |
| 41 | 7.5 | **Evidence Linking Agent** — auto geo-tagging, before/after photo pairing | 1 week |

---

### 🟢 PHASE 3 — Global Vision (Scale-up)

| # | Ref | What | Effort |
|---|---|---|---|
| 42 | 6.7 | Cross-domain signal correlation — sanction → trade drop → defense spend | 1–2 weeks |
| 43 | 6.8 | Pattern detection & anomaly alerts — fire when cluster of signals matches pattern | 1–2 weeks |
| 44 | 6.9 | Scenario modeling — "what if India imposes tariffs on X?" → graph propagation | 2–3 weeks |
| 45 | — | National intelligence dashboard — geopolitics, economics, defense in one view | 2–3 weeks |
| 46 | — | API access layer — external consumers (government, think tanks, researchers) | 1 week |

---

### Already Fixed ✅
| Ref | What |
|---|---|
| 3.6 | `sync_evidence_to_neo4j()` bug — `asset_id` param added, Cypher fixed, call re-enabled |
| 3.7 | `GET /data/pmay-housing` endpoint added — Delhi + national PMAY data from data.gov.in |
| 1.2 | `05_📊_Delivery_Graph.py` — decided to skip, Proof Chain covers this |

---

## PART 10 — VISION ALIGNMENT SUMMARY

| Layer | Vision Requires | Current State | Gap |
|---|---|---|---|
| Ingestion | Live multi-source feeds | On-demand RSS scraper | Background polling missing |
| Ontology | Multi-domain (6 domains) | Governance-only (1 domain) | 5 domains missing |
| Intelligence | Pattern detection, anomaly alerts | Static queries only | Full intelligence layer missing |
| Governance | Trust scores, audit trail, conflict detection | Zero governance infrastructure | Everything missing |
| Decision Layer | NL query, strategic dashboards, alerts | 4 pages, NL query works | Alerts + strategy layer missing |
| Data Scale | Global / national scale | 112 CSV rows, 2 wards | Scale gap |

**Overall alignment: ~55%** — architecture is correct, surface area needs expanding.

---

## PART 11 — NEWLY DISCOVERED GAPS (Deep Codebase Scan — March 17, 2026)

> Items not captured in Parts 1–10. Found by scanning every file in the repo.

---

### 🔴 CRITICAL — Will break demo or expose data

| # | Where | What | Fix |
|---|---|---|---|
| 11.1 | Root | **No `.env` file exists** — project won't start. `config.py` defaults `groq_api_key=""` and `neo4j_password="password"`. First-time setup will silently fail. | Create `.env` with real keys + create `.env.example` as template |
| 11.2 | `docker-compose.yml` vs `config.py` | **Password mismatch** — Docker sets `NEO4J_AUTH: neo4j/pramaa2026` but `config.py` default is `neo4j_password: str = "password"`. If running via Docker without `.env`, app can't connect to Neo4j. | Set `neo4j_password: str = "pramaa2026"` in config.py or document in `.env.example` |
| 11.3 | `data/residents.csv` | **Real phone numbers of team members** — Sambhavi's (`+919966236799`) and Siddharth's (`+919100209204`) real numbers are in the CSV. If Twilio is wired during demo, they receive actual WhatsApp messages. Security + demo embarrassment risk. | Replace with fake demo numbers (`+919999900001`, etc.) |
| 11.4 | `backend/app/config.py` | **`groq_api_key` is declared twice** (lines 8 and 10) — second declaration silently shadows the first. Python won't error but it's a bug. | Remove the duplicate line |
| 11.5 | `frontend/app.py` | **CSS page-hide targets wrong page** — `nth-child(4)` hides the 4th sidebar item which is `07_💬_Micro_Accountability.py`, NOT Live Ingestion (which isn't even in `pages/` yet). The hide logic is broken. | Fix after promoting Live Ingestion: use correct nth-child or hide by page name |
| 11.6 | `frontend/pages/` | **Page numbering gap** — Pages are `01, 02, 06, 07`. Numbers 03, 04, 05 are missing. Streamlit sidebar shows them out of order/with gaps. Looks unfinished. | Renumber all pages sequentially when promoting Live Ingestion |

---

### 🟡 IMPORTANT — Correctness and credibility issues

| # | Where | What | Fix |
|---|---|---|---|
| 11.7 | `frontend/utils/constants.py` | **Delivery score is hardcoded in demo override dict** — `ASSET_VERIFICATION_OVERRIDE` forces specific assets to `fully_verified`/`partially_verified`/`unverified`, and the Ward Map score (37.5%) is computed from this dict, not from actual Neo4j graph data. Changing seed data won't change the score. | Remove override dict; compute score from live graph query only |
| 11.8 | `ai/llm_extractor.py` + `backend/app/services/ai_service.py` | **Duplicate AI extraction implementations** — Two separate files doing the same job. `hidden_Live_Ingestion.py` uses `llm_extractor.py`; `scrape.py` router uses `ai_service.py`. They have different prompts and different output formats, causing inconsistent extractions. | Consolidate into one: `backend/app/services/ai_service.py` as the single source |
| 11.9 | `backend/app/routers/ingest.py` | **`DELETE /ingest/demo-nodes` is missing** — Live Ingestion UI calls this endpoint (developer tools "Clear Graph"). The endpoint doesn't exist in `ingest.py`. Results in 404 silently. | Add `DELETE /ingest/demo-nodes` endpoint that removes nodes with `source_type="demo"` |
| 11.10 | `data/residents.csv` | **`Resident` nodes are not seeded into Neo4j** — `notifications.py` does `MATCH (res:Resident {opt_in: true})` but no seed script loads `residents.csv` into Neo4j. WhatsApp notification will always return "no opted-in residents". | Add `Resident` node loading to `load_seed_data.py` + wire `RESIDES_ON` relationships |
| 11.11 | `data/cache/last_autosearch.json` | **Offline cache is empty** — File exists but contains `{"entities": [], "relations": [], "articles": []}`. The offline demo fallback won't work — it'll show a blank result. | Pre-populate cache with a real extraction result from a successful news scrape |
| 11.12 | `ai/` folder | **`nl_query.py` doesn't exist** — Referenced in `PENDING_AI_TASKS.md`, `todo.md`, `AI_MAPPER_SPEC.md` and `ENGINEERING_PRDS.md` as a core file (`ai/nl_query.py`). It was never created. The Questions page works via direct backend calls, not via this module. Either create it or remove all references from docs. | Create stub or delete references from docs |

---

### 🟢 CLEANUP — Messy project structure

| # | Where | What | Fix |
|---|---|---|---|
| 11.13 | Project root | **14 before/after evidence images in project root** — `before_w45_gali7_drain.png`, `after_w45_park.jpeg`, etc. are all in `/Pramaan/` root. They're served via `constants.py` absolute paths. Should be in `frontend/static/evidence/` like the other 4 static images. | Move to `frontend/static/evidence/`, update `_img()` path in `constants.py` |
| 11.14 | Project root | **3 debug/diagnostic scripts in root** — `diag_hierarchy.py`, `test_query.py`, `check_neo4j_local.py` are dev scripts scattered in root. These aren't part of the app. | Move to `backend/scripts/debug/` or add to `.gitignore` |
| 11.15 | `data/scripts/` | **14 ETL scripts with no documentation or run order** — `generate_seed_data.py`, `extract_amrut.py`, `transform_to_7_table_schema.py`, etc. No README, no documented order, no pipeline. New developer can't reproduce the data. | Add `data/scripts/README.md` with: what each script does, run order, output files |
| 11.16 | `data/docs/graph_model.json` | **Undocumented JSON graph schema** — A visual graph model JSON exists with `style`, `nodes`, `relationships` keys. Likely a yFiles/Arrows.app export. Not referenced anywhere in code or docs. | Document what it is and either use it or remove it |
| 11.17 | `data/resources/README.md` | **Completely empty** — Just says `# Pramaan`. 10+ raw data files in the folder with no explanation. | Populate with a table: filename → what it contains → used by |
| 11.18 | `docs/PENDING_AI_TASKS.md` | **Mostly obsolete** — Written when AI was a stub. Most tasks are done (Groq integration, Live Ingestion, extraction). Still has checklist items marked pending that are completed. | Archive as `PENDING_AI_TASKS_ARCHIVED.md` or delete; replace with current state |
| 11.19 | `docs/todo.md` | **Sprint tasks marked pending but sprint deadline passed (Mar 10)** — Team sprint board still shows all tasks unchecked. Misleading. | Update to reflect current completion status |

---

### Summary of Part 11

| Severity | Count |
|---|---|
| 🔴 Critical (demo-breaking or data-exposing) | 6 |
| 🟡 Important (correctness issues) | 6 |
| 🟢 Cleanup (structure/docs debt) | 7 |
| **Total new items** | **19** |

---

### Updated Grand Total

| | Count |
|---|---|
| Parts 1–10 (previously known) | 46 items |
| Part 11 (newly discovered) | 19 items |
| Already fixed ✅ | 3 items |
| **Total open items** | **65 items** |

---

*Last updated: March 17, 2026*
*Source: Full project audit conversation with AI coding assistant*
