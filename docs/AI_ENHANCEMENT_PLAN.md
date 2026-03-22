# PRAMAAN — AI Enhancement Plan
> **Last updated:** March 20, 2026
> **Scope:** Detailed plan to evolve the current single-prompt AI into a multi-layer reasoning engine
> **Status:** Current AI = formatter. Target AI = reasoning engine.

---

## 1. Current AI — What Actually Exists

### Files and Their Roles

| File | What it does | What is missing |
|---|---|---|
| `ai/llm_extractor.py` | 1 prompt → key_fact + relevance + confidence for ONE asset | Narrow scope, only matches news to a single asset name |
| `backend/app/services/ai_service.py` | 1 prompt → entities[] + relations[] | One-shot, no validation, no retry, no graph awareness |
| `backend/app/routers/questions.py` | 5 hardcoded Cypher queries + 1 raw Cypher endpoint | Not NL→Cypher — caller must supply pre-written Cypher |
| `backend/app/routers/scrape.py` | RSS fetch → combine headlines → extract_governance_ontology | Single pass, no cross-source comparison, no dedup |

### The Core Problem

```
CURRENT ARCHITECTURE
────────────────────
  Text ──→ [1 LLM call] ──→ JSON
           (single prompt,
            no graph context,
            no verification,
            no memory)

TARGET ARCHITECTURE
────────────────────
  Text ──→ Extract ──→ Resolve ──→ Verify ──→ Store
                          ↑
                   Graph tells LLM
                what already exists
                (entity-aware, iterative)
```

**The honest problem:**
There is a single LLM call with a single prompt doing everything. That is not an AI layer — that is a formatter. The AI is pattern-matching text into JSON. It does not reason, verify, learn, or connect.

---

## 2. The 5 AI Layers to Build

```
Layer 5 — Agentic Loop          [post-hackathon]  plan → search → extract → verify → update
Layer 4 — Intelligence Engine   [post-hackathon]  anomaly detection, briefings, alerts
Layer 3 — Verification Agent    [P1 — 2 weeks]    confidence scoring, conflict detection
Layer 2 — NL → Cypher           [P0 — 2 days]     real natural language querying
Layer 1 — Smarter Extraction    [P0 — 2 days]     graph-aware, entity-resolving extraction
────────────────────────────────────────────────────────────────────────────────
Current — Single Prompt         [EXISTS]           text → JSON, one shot, blind
```

---

## 3. Layer 1 — Smarter Extraction

### Problem
The current prompt has no awareness of what is already in the graph.
Every extraction creates new entity IDs. Running the same article twice doubles the nodes.
There is no fuzzy matching, no entity resolution, no anchor to existing data.

### Current Code (ai_service.py)
```python
# CURRENT — blind extraction, no graph context
prompt = f"Extract entities from: {text}"
```

### Enhanced Approach — Graph-Aware Extraction
```python
# ENHANCED — extraction anchored to existing graph
existing_entities = neo4j.run(
    "MATCH (n) RETURN n.name, labels(n), n.region_id, n.asset_id, n.scheme_id LIMIT 150"
)

prompt = f"""
You are a governance data extraction AI with access to an existing knowledge graph.

TEXT TO EXTRACT FROM:
{text}

EXISTING ENTITIES IN GRAPH (match these exactly if the same entity is found):
{existing_entities}

RULES:
1. If an entity in the text matches an existing one, use its EXACT existing ID.
2. Only create new IDs for genuinely new entities not in the graph.
3. If the text states something DIFFERENT from existing graph data, set conflict=true and
   describe the discrepancy in a conflict_note field.
4. confidence = how certain you are this entity is real based on the text (0.0 to 1.0).
5. source = a short label for the text source (e.g. "PIB_2026_03", "GoogleNews").

Return JSON with entities[], relations[], and conflicts[].
"""
```

### What This Gives You
- No more duplicate nodes from re-processing the same source
- Extractions are anchored to the existing graph state
- Conflicts between new text and existing data are flagged automatically
- Source attribution is embedded at extraction time

### New File: `backend/app/services/entity_resolver.py`
```python
from rapidfuzz import fuzz

def resolve_entity(extracted_name: str, existing_nodes: list, threshold: int = 85) -> dict | None:
    """
    Fuzzy-match an extracted entity name against existing Neo4j nodes.
    Returns the best match if score >= threshold, else None.
    """
    best_match = None
    best_score = 0
    for node in existing_nodes:
        score = fuzz.token_sort_ratio(extracted_name.lower(), node["name"].lower())
        if score > best_score:
            best_score = score
            best_match = node
    if best_score >= threshold:
        return {"match": best_match, "score": best_score}
    return None
```

---

## 4. Layer 2 — Real NL → Cypher Pipeline

### Problem
`/questions/custom` accepts a pre-written Cypher string — not natural language.
The NL query capability shown in the UI is fake. Someone must write Cypher externally.
No judge or official at the booth can write Cypher.

### Current Flow (broken)
```
User types question → Frontend calls /questions/custom with Cypher string
                      (WHO WROTE THIS CYPHER? Nobody knows.)
```

### Target Flow
```
User types question → NL query service → LLM generates Cypher → Execute → Return answer + explanation
```

### New File: `backend/app/services/nl_query_service.py`

```python
SCHEMA_CONTEXT = """
Neo4j graph schema for PRAMAAN:

Node types:
  Region     (region_id, name, type[ward/street/city/zone], parent_region_id)
  Scheme     (scheme_id, name, ministry, category[roads/sanitation/housing/drainage])
  Actor      (actor_id, name, type[government/contractor/elected_rep])
  Asset      (asset_id, name, type[drain/road/toilet/housing/park/streetlight], status, cost, lat, lon)
  Beneficiary(beneficiary_id, scheme_id, region_id, count)
  Evidence   (evidence_id, asset_id, type[photo/report/certificate], url, confidence)
  Event      (event_id, name, event_type, date)

Relationships:
  (Scheme)-[:FUNDS]->(Asset)
  (Asset)-[:BUILT_BY]->(Actor)
  (Asset)-[:LOCATED_IN]->(Region)
  (Evidence)-[:PROVES]->(Asset)
  (Scheme)-[:BENEFITS]->(Beneficiary)
  (Asset)-[:MENTIONED_IN]->(Event)

Key IDs: REG_W45 = Ward 45 Shahdara Delhi, SCH_AMRUT = AMRUT scheme, SCH_PMAY = PMAY scheme
"""

FEW_SHOT_EXAMPLES = """
Q: Which drains were built in Ward 45?
A: {"cypher": "MATCH (a:Asset)-[:LOCATED_IN]->(r:Region) WHERE r.region_id='REG_W45' AND a.type='drain' RETURN a.name, a.status, a.cost", "explanation": "Finds all drain assets located in Ward 45"}

Q: Which schemes have no assets linked yet?
A: {"cypher": "MATCH (s:Scheme) WHERE NOT (s)-[:FUNDS]->(:Asset) RETURN s.name, s.ministry", "explanation": "Finds schemes that have not yet funded any asset"}

Q: Show funding gaps — assets with budget but no evidence of completion
A: {"cypher": "MATCH (s:Scheme)-[:FUNDS]->(a:Asset) WHERE NOT (:Evidence)-[:PROVES]->(a) AND a.cost > 0 RETURN s.name AS Scheme, a.name AS Asset, a.cost AS Budget, a.status AS Status ORDER BY a.cost DESC", "explanation": "Identifies assets that received funding but have no evidence linked"}

Q: Who built the most projects in Ward 45?
A: {"cypher": "MATCH (a:Asset)-[:LOCATED_IN]->(r:Region) WHERE r.region_id='REG_W45' MATCH (a)-[:BUILT_BY]->(act:Actor) RETURN act.name, count(a) AS projects ORDER BY projects DESC", "explanation": "Ranks actors by number of assets built in Ward 45"}
"""

def natural_language_to_cypher(question: str, groq_client) -> dict:
    prompt = f"""
{SCHEMA_CONTEXT}

Examples of question → Cypher:
{FEW_SHOT_EXAMPLES}

Now convert this question to a single valid Cypher query:
Question: {question}

Return ONLY valid JSON (no markdown):
{{"cypher": "MATCH ...", "explanation": "This query ...", "confidence": 0.9}}
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
```

### Update `questions.py` — Add Real NL Endpoint
```python
@router.post("/ask")
def ask_natural_language(payload: NLQuery):
    """Convert natural language question to Cypher and execute against Neo4j."""
    result = nl_query_service.natural_language_to_cypher(payload.question)
    cypher = result["cypher"]
    explanation = result["explanation"]
    data = _run(cypher)
    return {
        "question": payload.question,
        "cypher": cypher,
        "explanation": explanation,
        "data": data,
        "confidence": result.get("confidence", 0.0)
    }
```

### What This Gives You
- Any judge at the booth can type any question in plain English
- The Cypher generated is shown transparently (explainability)
- Confidence score indicates how well the question mapped to the schema
- Schema + few-shot examples prevent hallucinated node types

---

## 5. Layer 3 — Verification Agent (THE CORE)

### Problem
Two news articles make contradictory claims about the same asset.
The graph has no way to detect or flag this.
"Pramaan" means attestation — but nothing is being attested.
Every extracted entity is treated as equally true regardless of source quality.

### Concept — Confidence Aggregation + Conflict Detection

```
Source 1 (PIB Press Release):  "AMRUT drain in Gali 7 completed — ₹12 lakh"  → confidence 0.85
Source 2 (Google News):        "AMRUT drain in Gali 7 completed — ₹15 lakh"  → conflict FLAGGED
Source 3 (MCD Inspection PDF): "AMRUT drain in Gali 7 completed — ₹12 lakh"  → confidence 0.96 (corroborated)

Result: Asset shows PARTIALLY VERIFIED (cost conflict) with 2/3 sources agreeing
```

### New File: `backend/app/services/verification_agent.py`

```python
class VerificationAgent:
    """
    When a new extraction arrives, cross-check it against the existing graph.
    Aggregate confidence when sources agree.
    Flag conflicts when sources disagree.
    Update trust tiers in Neo4j.
    """

    TRUST_TIERS = {
        (0.0, 0.5):  "UNVERIFIED",
        (0.5, 0.8):  "PARTIALLY_VERIFIED",
        (0.8, 1.0):  "FULLY_VERIFIED"
    }

    def verify(self, extracted_entity: dict, neo4j_session) -> dict:
        # Step 1: Find matching node in Neo4j using entity resolver
        existing = self.find_matching_node(extracted_entity, neo4j_session)

        if not existing:
            # New entity — store with initial confidence from extraction
            return {
                "action": "CREATE",
                "entity": extracted_entity,
                "confidence": extracted_entity.get("confidence", 0.5)
            }

        # Step 2: Detect property conflicts
        conflicts = self.detect_conflicts(existing, extracted_entity)

        if conflicts:
            # Step 3: Flag conflict — do NOT overwrite existing data
            self.flag_conflict(
                existing["id"],
                conflicts,
                new_source=extracted_entity.get("source", "unknown"),
                neo4j_session=neo4j_session
            )
            return {
                "action": "CONFLICT_FLAGGED",
                "entity_id": existing["id"],
                "conflicts": conflicts
            }

        # Step 4: Corroboration — second source confirms → raise confidence
        new_confidence = self.aggregate_confidence(
            old=existing.get("confidence", 0.5),
            new=extracted_entity.get("confidence", 0.5)
        )
        self.update_neo4j_confidence(existing["id"], new_confidence, neo4j_session)

        return {
            "action": "CORROBORATED",
            "entity_id": existing["id"],
            "old_confidence": existing.get("confidence"),
            "new_confidence": new_confidence,
            "trust_tier": self.get_trust_tier(new_confidence)
        }

    def aggregate_confidence(self, old: float, new: float) -> float:
        """Bayesian update — more agreeing sources = higher confidence, caps at 0.99."""
        return round(1 - (1 - old) * (1 - new), 4)

    def detect_conflicts(self, existing: dict, incoming: dict) -> list:
        """Compare key properties — flag significant numerical or status divergence."""
        conflicts = []
        # Cost conflict: >20% difference
        if existing.get("cost") and incoming.get("cost"):
            delta = abs(existing["cost"] - incoming["cost"]) / existing["cost"]
            if delta > 0.2:
                conflicts.append({
                    "field": "cost",
                    "existing": existing["cost"],
                    "incoming": incoming["cost"],
                    "delta_pct": round(delta * 100, 1)
                })
        # Status conflict: completed vs ongoing vs planned
        if existing.get("status") and incoming.get("status"):
            if existing["status"] != incoming["status"]:
                conflicts.append({
                    "field": "status",
                    "existing": existing["status"],
                    "incoming": incoming["status"]
                })
        return conflicts

    def get_trust_tier(self, confidence: float) -> str:
        for (low, high), tier in self.TRUST_TIERS.items():
            if low <= confidence < high:
                return tier
        return "FULLY_VERIFIED"
```

### Neo4j Changes Required
Add `confidence`, `source_ids`, and `conflict_flag` to all nodes:
```cypher
-- Add to all MERGE statements in load_seed_data.py and ingest.py
MERGE (a:Asset {asset_id: $id})
SET a.confidence = coalesce(a.confidence, $confidence),
    a.source_ids = coalesce(a.source_ids, []) + [$source],
    a.conflict_flag = false,
    a.trust_tier = $trust_tier
```

### What This Gives You
- The trust tier badges (FULLY VERIFIED / PARTIALLY VERIFIED / UNVERIFIED) are backed by real data
- When 3 sources confirm a fact, confidence rises automatically
- When sources disagree, a conflict is surfaced — not silently overwritten
- This IS the "Pramaan" (attestation) concept made real

---

## 6. Layer 4 — Intelligence Engine

### Problem
The graph holds all the data but nobody is reading patterns across it.
The most valuable insights — fund leakage signals, dark wards, stalled assets — are invisible.
The graph answers questions but does not proactively surface what matters.

### New File: `backend/app/services/intelligence_service.py`

```python
ANOMALY_QUERIES = {
    "funding_gap": {
        "description": "Assets that received funding but are not completed",
        "cypher": """
            MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region)
            WHERE a.status <> 'completed' AND a.cost > 100000
            RETURN s.name AS scheme, a.name AS asset, a.cost AS budget,
                   a.status AS status, r.name AS ward
            ORDER BY a.cost DESC LIMIT 10
        """
    },
    "evidence_gap": {
        "description": "Assets with no evidence of delivery",
        "cypher": """
            MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
            WHERE NOT (:Evidence)-[:PROVES]->(a)
            RETURN a.name AS asset, a.type AS type, a.status AS status, r.name AS ward
        """
    },
    "dark_wards": {
        "description": "Wards with no assets recorded — zero delivery",
        "cypher": """
            MATCH (r:Region {type:'ward'})
            WHERE NOT (:Asset)-[:LOCATED_IN]->(r)
            RETURN r.name AS ward, r.region_id AS id
        """
    },
    "unlinked_schemes": {
        "description": "Schemes with no assets funded",
        "cypher": """
            MATCH (s:Scheme)
            WHERE NOT (s)-[:FUNDS]->(:Asset)
            RETURN s.name AS scheme, s.ministry AS ministry, s.category AS category
        """
    },
    "low_confidence_assets": {
        "description": "Assets with low verification confidence — need more evidence",
        "cypher": """
            MATCH (a:Asset)
            WHERE a.confidence < 0.6 OR a.confidence IS NULL
            RETURN a.name AS asset, a.type AS type,
                   coalesce(a.confidence, 0) AS confidence,
                   coalesce(a.trust_tier, 'UNVERIFIED') AS tier
            ORDER BY confidence ASC LIMIT 15
        """
    }
}

def generate_intelligence_briefing(ward_id: str, groq_client) -> dict:
    """
    Run all anomaly queries, collect results, ask LLM to generate
    a strategic briefing for a government official.
    """
    anomalies = {}
    for key, query_def in ANOMALY_QUERIES.items():
        rows = neo4j.run(query_def["cypher"], ward_id=ward_id)
        anomalies[key] = {"description": query_def["description"], "data": rows}

    # LLM interprets the patterns
    prompt = f"""
You are a governance intelligence analyst reviewing delivery data for ward {ward_id}.

DATA FINDINGS:
{json.dumps(anomalies, indent=2)}

Write a 4-point strategic briefing for a senior government official.
- Point 1: Most critical funding/delivery risk (name specific assets and amounts)
- Point 2: Verification gaps (assets with no evidence)
- Point 3: What is working well (completed assets with evidence)
- Point 4: Recommended immediate action

Be specific. Use actual names and numbers from the data. Keep each point to 2 sentences.
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600
    )

    return {
        "ward_id": ward_id,
        "briefing": response.choices[0].message.content,
        "anomalies": anomalies,
        "generated_at": datetime.utcnow().isoformat()
    }
```

### New API Endpoint: `GET /intelligence/briefing/{ward_id}`
```python
@router.get("/briefing/{ward_id}")
def get_ward_briefing(ward_id: str):
    """Generate an AI intelligence briefing for a ward based on graph anomaly analysis."""
    return intelligence_service.generate_intelligence_briefing(ward_id)
```

### What This Gives You
- The graph proactively surfaces what matters — not just what was asked
- "₹45 lakh was released for 3 drain projects in Ward 45 — none have completion evidence" is auto-generated
- This is the first step toward a genuine reasoning engine

---

## 7. Layer 5 — Agentic Loop (Post-Hackathon)

### Problem
All AI is currently reactive — user asks, AI answers.
A real Global Ontology Engine is proactive — it monitors, detects, and alerts.
Single-step extraction cannot handle multi-step reasoning.

### Target — Multi-Step Agent

```
USER: "Give me full intelligence on AMRUT delivery in Shahdara"

AGENT EXECUTION PLAN:
  Step 1 [query_graph]       → Get all AMRUT assets in Shahdara from Neo4j
  Step 2 [check_evidence]    → Which of these have Evidence nodes linked?
  Step 3 [fetch_news]        → Fetch live news: "AMRUT Shahdara Delhi 2026"
  Step 4 [extract_entities]  → Run ai_service on news results
  Step 5 [verify_entities]   → Run verification_agent on extracted vs graph
  Step 6 [generate_briefing] → LLM synthesises all findings into briefing

Each step result feeds into the next step's context.
NOT: one LLM call that tries to do all of this blindly.
```

### New File: `backend/app/services/intelligence_agent.py`

```python
class IntelligenceAgent:
    """
    Multi-step agent that plans, executes, and synthesises
    graph queries + live news + AI extraction into a unified answer.
    """

    AVAILABLE_TOOLS = {
        "query_graph":        "Run a Cypher query against Neo4j",
        "fetch_news":         "Search Google News RSS for a query string",
        "extract_entities":   "Run LLM extraction on a text block",
        "verify_entity":      "Cross-check an extracted entity against the graph",
        "generate_briefing":  "Generate a strategic summary from collected data"
    }

    def run(self, user_question: str) -> dict:
        # Step 1: LLM creates an execution plan
        plan = self._create_plan(user_question)

        # Step 2: Execute each step, feeding output into next step's context
        context = {"question": user_question, "results": []}
        for step in plan["steps"]:
            result = self._execute_tool(step["tool"], step["input"], context)
            context["results"].append({"step": step["tool"], "output": result})

        # Step 3: Final synthesis
        return self._synthesize(context)

    def _create_plan(self, question: str) -> dict:
        prompt = f"""
You are an intelligence agent with these tools: {self.AVAILABLE_TOOLS}

User question: {question}

Create a step-by-step execution plan. Return JSON:
{{"steps": [{{"tool": "tool_name", "input": "what to pass", "reason": "why this step"}}]}}
Use minimum steps needed. Maximum 6 steps.
"""
        # Call Groq → parse plan
        ...
```

---

## 8. Implementation Priority

| Priority | Layer | File to Create/Update | Time Estimate | Demo Impact |
|---|---|---|---|---|
| 🔴 P0 | Layer 1 — Graph-Aware Extraction | Update `ai_service.py` + new `entity_resolver.py` | 2 days | Stops duplicate nodes |
| 🔴 P0 | Layer 2 — NL → Cypher | New `nl_query_service.py` + update `questions.py` | 2 days | Real NL querying at booth |
| 🟡 P1 | Layer 3 — Verification Agent (partial) | New `verification_agent.py` + update ingest.py | 3 days | Trust tiers backed by real data |
| 🟡 P1 | Layer 4 — Intelligence Engine (3 anomaly queries) | New `intelligence_service.py` + new router endpoint | 2 days | "Funding gap detected" wow moment |
| 🟢 P2 | Layer 3 — Full Verification Agent | Complete `verification_agent.py` | Post-booth | Core product differentiator |
| 🟢 P2 | Layer 5 — Agentic Loop | New `intelligence_agent.py` | Post-booth | Full vision realised |

**Total for booth-ready AI: ~9 days of focused work**

---

## 9. New Files to Create

```
backend/app/services/
├── ai_service.py              ← UPDATE: add graph-aware extraction
├── entity_resolver.py         ← NEW: fuzzy entity matching (RapidFuzz)
├── nl_query_service.py        ← NEW: NL → Cypher with schema + few-shot
├── verification_agent.py      ← NEW: confidence aggregation + conflict detection
├── intelligence_service.py    ← NEW: anomaly queries + LLM briefing generator
└── intelligence_agent.py      ← NEW (post-booth): multi-step agentic loop

backend/app/routers/
├── questions.py               ← UPDATE: add POST /questions/ask (NL query)
└── intelligence.py            ← NEW: GET /intelligence/briefing/{ward_id}
```

---

## 10. What This Unlocks at the Booth

| Judge asks | Current answer | Enhanced answer |
|---|---|---|
| "Can it verify claims?" | "We show confidence scores" | "Yes — when 2+ sources confirm the same asset, confidence rises automatically. When sources disagree, a conflict is flagged and shown." |
| "Can I ask it questions?" | "Here are 5 preset queries" | "Type anything — 'which schemes have no delivery proof?' — it generates the Cypher, runs it, and explains the result." |
| "Does it find problems automatically?" | "No, you have to query" | "Yes — here is today's briefing: ₹45 lakh released for 3 drains in Ward 45, none have completion evidence. That is a leakage signal." |
| "How is this different from a dashboard?" | Hard to answer | "A dashboard shows what you already know. This finds what you don't — gaps, conflicts, and unverified claims — automatically." |

---

## 11. Summary

| Layer | Status | What It Does |
|---|---|---|
| Single-prompt extraction | ✅ EXISTS | Text → JSON, one-shot, blind to graph |
| Graph-aware extraction | ❌ NOT BUILT | Anchors extraction to existing nodes, detects conflicts |
| NL → Cypher | ❌ NOT BUILT | Real natural language querying with schema context |
| Verification Agent | ❌ NOT BUILT | Confidence aggregation, conflict flagging, trust tiers |
| Intelligence Engine | ❌ NOT BUILT | Anomaly detection, leakage signals, AI briefings |
| Agentic Loop | ❌ NOT BUILT | Multi-step plan → execute → synthesise cycle |

**Current AI depth: 1 layer (extraction only)**
**Target AI depth: 5 layers (extraction → resolution → verification → intelligence → agency)**

---

*Generated: March 20, 2026*
*Source: Full audit of ai/llm_extractor.py, ai_service.py, questions.py, scrape.py*
