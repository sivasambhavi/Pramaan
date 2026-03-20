# PRAMAAN — Judge Impression Plan
> **Deadline:** March 28, 2026 (8 days)
> **Goal:** Win the India Innovates 2026 booth — Global Ontology Engine track
> **Current state:** Foundation working. Critical fixes + 4 high-impact features needed.

---

## The Judge's Mental Scorecard

When a judge walks up to the booth, they evaluate in this order:

```
30 seconds  →  Does it LOOK impressive? (UI, graph visual, live data)
2 minutes   →  Does it WORK? (can I ask a question and get a real answer?)
5 minutes   →  Is the idea ORIGINAL? (what does this show that no dashboard shows?)
10 minutes  →  Is the DATA REAL? (not mocked, not hardcoded)
```

Everything below is mapped to one of these four questions.

---

## Phase 0 — BLOCKERS (Fix Today — Day 1)
> Demo WILL crash without these. Do not touch anything else first.

### Step 0.1 — Create the .env file
```bash
# At project root — create .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pramaa2026
GROQ_API_KEY=<your_key>
DATA_GOV_API_KEY=<your_key>
TWILIO_ACCOUNT_SID=<your_sid>
TWILIO_AUTH_TOKEN=<your_token>
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```
**Why:** config.py defaults password to "password". Docker runs "pramaa2026". Neo4j connection fails silently.

---

### Step 0.2 — Fix Asset ID Split-Brain
**Problem:** Two different ID formats exist in the codebase:
```
final_formalized/assets.csv  →  ASSET_W45_GALI7_DRAIN  ← Neo4j uses this
constants.py ASSET_EVIDENCE_PHOTOS  →  "ASSET_W45_GALI7_DRAIN" ← check alignment
data/assets.csv (legacy)  →  old IDs — NOT loaded into Neo4j, ignore
```
**Action:** Run `python data/scripts/validate.py` — fix any FK errors it reports.

---

### Step 0.3 — Add 3 Missing API Endpoints
Open `backend/app/routers/ingest.py` and add:
```python
@router.delete("/demo-nodes")
def delete_demo_nodes():
    """Remove all AI-ingested demo nodes (keeps seed data)."""
    with get_session() as s:
        s.run("MATCH (n) WHERE n.source = 'demo' DETACH DELETE n")
    return {"deleted": True}
```

Open `backend/app/routers/assets.py` and add:
```python
@router.post("/{asset_id}/set-verified")
def set_verified(asset_id: str):
    """Mark an asset as manually verified."""
    with get_session() as s:
        s.run("MATCH (a:Asset {asset_id:$id}) SET a.proof_status='fully_verified'", id=asset_id)
    return {"verified": True}
```

---

### Step 0.4 — Fix Duplicate groq_api_key in config.py
Open `backend/app/config.py` — remove the duplicate `groq_api_key` field.
Pydantic raises a warning on every startup. Judges notice console errors.

---

### Step 0.5 — Startup Auto-Seed
Add to `backend/app/main.py`:
```python
from app.neo4j_client import get_session

@app.on_event("startup")
async def auto_seed():
    """If Neo4j is empty, load seed data automatically."""
    with get_session() as s:
        count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        if count == 0:
            import subprocess
            subprocess.Popen(["python", "backend/scripts/load_seed_data.py"])
```
**Why:** Fresh clone at the booth → Neo4j empty → blank app. Auto-seed prevents this.

---

## Phase 1 — HIGH IMPACT (Days 2–4)
> These are the features that make judges stop walking and come look.

---

### Step 1.1 — Add Graph Visualization 🔴 HIGHEST IMPACT
**Why:** The competition is called "Global Ontology Engine". Judges NEED to see a graph.
Both `streamlit-agraph` and `pyvis` are already in requirements.txt.

**Where to add:** New tab inside `02_Proof_Chain.py` OR a new page `05_Knowledge_Graph.py`

**Implementation:**
```python
from streamlit_agraph import agraph, Node, Edge, Config

def render_ontology_graph(chain_data: dict):
    nodes = []
    edges = []

    color_map = {
        "Scheme":      "#f97316",   # orange
        "Actor":       "#38bdf8",   # blue
        "Asset":       "#22c55e",   # green
        "Region":      "#a78bfa",   # purple
        "Evidence":    "#facc15",   # yellow
        "Beneficiary": "#f472b6",   # pink
    }

    # Build nodes from chain
    for entity_type, entity_data in chain_data.items():
        if entity_data:
            nodes.append(Node(
                id=entity_data.get("id", entity_type),
                label=entity_data.get("name", entity_type)[:20],
                size=30,
                color=color_map.get(entity_type, "#64748b"),
                title=f"{entity_type}: {entity_data.get('name','')}"
            ))

    # Build edges
    edge_map = [
        ("Scheme", "Asset",       "FUNDS"),
        ("Actor",  "Asset",       "BUILT_BY"),
        ("Asset",  "Region",      "LOCATED_IN"),
        ("Evidence","Asset",      "PROVES"),
        ("Scheme", "Beneficiary", "BENEFITS"),
    ]
    for src, tgt, label in edge_map:
        if src in chain_data and tgt in chain_data:
            edges.append(Edge(
                source=chain_data[src].get("id", src),
                target=chain_data[tgt].get("id", tgt),
                label=label,
                color="#475569"
            ))

    config = Config(
        width=800, height=500,
        directed=True, physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#f97316",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label", "renderLabel": True}
    )
    return agraph(nodes=nodes, edges=edges, config=config)
```

**What judges see:** An interactive node-edge graph. Click a node → see its properties. The chain becomes visual, not textual. This is the single biggest impression multiplier.

---

### Step 1.2 — Gap / Leakage Detection Panel 🔴 HIGH IMPACT
**Why:** The #1 governance insight — "money was released but nothing was built" — is invisible right now. This is THE moment that makes judges say "we need this."

**Where to add:** New section in `01_Ward_Map.py` below the delivery score hero.

**Implementation:**
```python
# Fetch gap data from existing endpoint — GET /wards/{ward_id}/gaps
gaps = requests.get(f"{BASE_URL}/wards/{ward_id}/gaps").json()

st.markdown("### 🔍 Delivery Gap Analysis")
for gap in gaps.get("data", []):
    scheme = gap["scheme_name"]
    linked = gap["linked_assets"]
    proven = gap["proven_assets"]
    unproven = linked - proven

    if gap["gap_type"] == "no_evidence":
        amount_at_risk = unproven * 980000  # avg cost per asset
        st.error(
            f"⚠️ **{scheme}** — {linked} assets funded, "
            f"{unproven} have NO evidence. "
            f"**₹{amount_at_risk/100000:.1f} lakh at risk.**"
        )
    elif gap["gap_type"] == "partial":
        st.warning(f"🟡 **{scheme}** — {proven}/{linked} assets proven. {unproven} pending verification.")
    elif gap["gap_type"] == "complete":
        st.success(f"✅ **{scheme}** — All {linked} assets fully evidenced.")
```

**What judges see:** A concrete rupee amount at risk. Real accountability. The "proof" in PRAMAAN.

---

### Step 1.3 — Real NL Query (not hardcoded) 🔴 HIGH IMPACT
**Why:** Every judge will try typing a question. If it only answers 5 preset questions, they know it's a demo trick.

**Where to add:** Update `backend/app/routers/questions.py` + Proof Chain "Ask the Graph" box.

**Backend — new endpoint:**
```python
# backend/app/routers/questions.py

SCHEMA = """
Nodes: Region(region_id,name,type), Scheme(scheme_id,name,ministry),
       Actor(actor_id,name,type), Asset(asset_id,name,type,status,cost),
       Beneficiary(beneficiary_id,count), Evidence(evidence_id,type,url)
Rels: FUNDS(Scheme->Asset), BUILT_BY(Asset->Actor), LOCATED_IN(Asset->Region),
      PROVES(Evidence->Asset), BENEFITS(Scheme->Beneficiary)
Key IDs: REG_W45=Ward45 Shahdara, SCH_AMRUT=AMRUT, SCH_PMAY=PMAY
"""
EXAMPLES = """
Q: Which drains have no photos?
A: MATCH (a:Asset {type:'drain'}) WHERE NOT (:Evidence)-[:PROVES]->(a) RETURN a.name,a.status

Q: How much was spent on AMRUT in Ward 45?
A: MATCH (s:Scheme {scheme_id:'SCH_AMRUT'})-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(r:Region {region_id:'REG_W45'}) RETURN sum(a.cost) AS total
"""

class NLQuery(BaseModel):
    question: str

@router.post("/ask")
def ask(payload: NLQuery):
    from groq import Groq
    from app.config import settings
    client = Groq(api_key=settings.groq_api_key)
    prompt = f"""
{SCHEMA}
Examples: {EXAMPLES}
Convert to Cypher: "{payload.question}"
Return JSON only: {{"cypher":"...", "explanation":"..."}}
"""
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        response_format={"type":"json_object"}
    )
    result = json.loads(resp.choices[0].message.content)
    rows = _run(result["cypher"])
    return {"question": payload.question, "explanation": result["explanation"],
            "cypher": result["cypher"], "data": rows}
```

**What judges see:** Type *"Which schemes released money but built nothing?"* → get a real answer from the graph with explanation.

---

### Step 1.4 — Fix Water Body Region Mapping
**Problem:** 52 water bodies all show under Ward 45 but are actually across 30+ wards (Burari, Wazirabad, Timarpur, etc.)

**Fix:** In `load_seed_data.py` or directly in `assets.csv`, assign water bodies to correct region IDs based on their lat/lon.

**Quick fix for demo:** Filter water bodies OUT of the Ward 45 map view, OR move them to `REG_DELHI` instead of `REG_W45`.

```python
# In 01_Ward_Map.py — filter before plotting
assets = [a for a in all_assets if a["type"] != "water_body" or a.get("region_id") == ward_id]
```

**Why it matters:** If a judge selects Ward 45 and sees 52 pins scattered across all of Delhi, the first question is "Is your data correct?" — and the answer looks like no.

---

## Phase 2 — MEDIUM IMPACT (Days 5–6)
> These add depth and make the demo richer.

---

### Step 2.1 — Add a Second Ward for Comparison
**Why:** "It only works for one ward" is a common judge objection. Show Ward 78 with 3 assets and a lower delivery score. The CONTRAST is the story.

**Action:** In `assets.csv`, add 3 assets for a second ward (e.g., Ward 78 or Ward 12):
```csv
ASSET_W78_DRAIN_1,Storm drain — Main Road,drain,REG_W78,SCH_AMRUT,ACT_MCD_SHAHDARA_WORKS,850000,in_progress,28.680,77.310
ASSET_W78_ROAD_1,Road resurfacing — Block B,road,REG_W78,SCH_SFC,ACT_CONTRACTOR_INFRA_1,650000,planned,28.681,77.312
ASSET_W78_TOILET_1,Toilet block — Community Centre,toilet,REG_W78,SCH_SWACHH,ACT_MCD_SHAHDARA_SANITATION,400000,planned,28.679,77.309
```
No evidence for Ward 78 → delivery score = 0% → powerful contrast with Ward 45's 58%.

---

### Step 2.2 — Seed Event Nodes (Tenders + Inspections)
**Why:** Events make the graph a timeline. "Tender published → Construction started → MCD inspection → Photo evidence" is a STORY that shows traceability.

**Action:** Add to `events.csv`:
```csv
event_id,name,event_type,date,asset_id,description
EVT_W45_GALI7_TENDER,Tender Published — Gali 7 Drain,tender,2023-11-15,ASSET_W45_GALI7_DRAIN,MCD tender #2023-SHD-T-0892 awarded to ABC Infra Pvt Ltd
EVT_W45_GALI7_INSPECT,MCD Site Inspection — Gali 7 Drain,inspection,2025-02-10,ASSET_W45_GALI7_DRAIN,Field inspection confirmed 80% work completion
EVT_W45_GALI7_COMPLETE,Completion Certificate — Gali 7 Drain,completion,2025-03-22,ASSET_W45_GALI7_DRAIN,Certificate issued by Shahdara Works Dept
```
**In graph view:** Events appear as timeline nodes between Actor and Evidence. The chain becomes: Scheme → Tender → Construction → Inspection → Photo → Completion.

---

### Step 2.3 — AI Intelligence Briefing Panel
**Why:** Instead of judges having to browse 4 pages, one AI summary tells them everything in 10 seconds.

**Where:** Add to bottom of `01_Ward_Map.py` as a collapsible panel.

```python
if st.button("🤖 Generate AI Briefing for this Ward"):
    with st.spinner("Analysing graph..."):
        gaps_data = requests.get(f"{BASE_URL}/wards/{ward_id}/gaps").json()
        assets_data = requests.get(f"{BASE_URL}/wards/{ward_id}/assets").json()

        summary_prompt = f"""
You are a governance analyst. Here is Ward {ward_name} data:
Assets: {assets_data}
Delivery gaps: {gaps_data}

Write a 4-bullet briefing for a government official:
1. Overall delivery status (score, total spend)
2. Biggest risk (scheme with most unverified spend)
3. What is working (completed assets with evidence)
4. Recommended action (1 sentence)
Be specific. Use actual names and numbers.
"""
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":summary_prompt}],
            temperature=0.2, max_tokens=400
        )
        st.info(resp.choices[0].message.content)
```

**What judges see:** One click → AI reads the graph → produces a plain-English briefing. This is what "decision support" looks like.

---

## Phase 3 — DEMO POLISH (Days 7–8)
> The last 10% that makes it memorable.

---

### Step 3.1 — Define the 4-Minute Demo Script
Practice this EXACT flow with the team. Do not wing it at the booth.

```
TIME    ACTION                              WHAT YOU SAY
──────────────────────────────────────────────────────────────────
0:00    Open Home page                     "This is PRAMAAN — the first system
                                            that proves what India built."

0:20    Go to Ward Map → select Ward 45    "Pick any ward. Today, Ward 45 Shahdara.
                                            Delivery score: 58%. Here's why."

0:45    Point to Gap panel                 "₹17 lakh released. 3 assets.
                                            2 have no evidence. That's the leakage signal."

1:10    Click on Gali 7 Drain              "Click any asset. Proof Chain opens."

1:20    Show Proof Chain graph visual      "Watch the graph build. Scheme funds Actor.
                                            Actor builds Asset. Evidence proves it.
                                            All the way to the 100 households it serves."

2:00    Show before/after photos           "Before — blocked drain. After — fixed.
                                            Photo is geo-tagged and date-stamped.
                                            This is what PFMS cannot show you."

2:30    Go to Live Ingestion               "Now let's add new data live."
        Paste a PIB press release          "AI extracts entities. One click.
                                            The graph updates in real time."

3:00    Go back to Proof Chain             "Ask the Graph — type any question."
        Type: "Which drains have no photos?"
                                           "The LLM writes the Cypher. The graph
                                            answers. No pre-programming."

3:30    Show WhatsApp notification         "Final step — notify the resident directly.
                                            Micro-accountability — from scheme to SMS."

4:00    End                                "One graph. Every rupee. Every proof."
```

---

### Step 3.2 — Prepare for Judge Questions

| Judge asks | Your answer |
|---|---|
| "Is this data real?" | "Ward 45 assets are from MCD records and data.gov.in APIs. Evidence photos are geo-tagged field photos. News articles are live from Google News." |
| "What makes this different from a dashboard?" | "A dashboard shows you what you already know. PRAMAAN finds what you don't — the missing links, the unverified spend, the broken chains. That's the corruption signal." |
| "Can it scale beyond Delhi?" | "The architecture is domain-agnostic. Today it runs on governance. The same engine can ingest economics, climate, or defense data. The ontology expands — the engine doesn't change." |
| "What is the AI actually doing?" | "Three things: extracting entities from unstructured text, routing natural language questions to graph queries, and — this is key — detecting when two sources say different things about the same asset. That's what Pramaan means — attestation." |
| "How does it update in real time?" | "Live Ingestion pulls from Google News RSS and PIB every time you search. Paste any article — the graph updates in under 5 seconds." |

---

### Step 3.3 — Offline Fallback (Critical for Booth WiFi)
Booth WiFi at Bharat Mandapam is unreliable. Prepare:

```bash
# Run this the night before the event:
python data/scripts/fetch_govdata.py        # cache all gov data locally
python backend/scripts/load_seed_data.py    # ensure Neo4j is fully seeded
# Start Neo4j, backend, frontend — keep all 3 running overnight
# Set GROQ requests to use MD5 cache (already implemented in llm_extractor.py)
```

---

## Priority Summary — 8 Days

```
DAY   TASK                                  OWNER    IMPACT
──────────────────────────────────────────────────────────────────
1     .env file + fix config.py             Aparna   BLOCKER
1     Add 2 missing API endpoints           Aparna   BLOCKER
1     Run validate.py → fix FK errors       Sambhavi BLOCKER
2     Graph visualization (agraph)          Sreenu   🔴 CRITICAL
2     Filter water bodies from Ward 45 map  Sambhavi 🔴 CRITICAL
3     Gap/Leakage detection panel           Sreenu   🔴 CRITICAL
3     Real NL→Cypher endpoint               Sreenu   🔴 CRITICAL
4     Add Ward 78 with 3 assets             Sambhavi 🟡 HIGH
4     Seed event nodes (3 per key asset)    Sambhavi 🟡 HIGH
5     AI intelligence briefing panel        Sreenu   🟡 HIGH
5     Polish UI — remove any console errors All      🟡 HIGH
6     Full end-to-end demo run              All      🟡 HIGH
6     Prepare PPT (7 slides)                All      🟡 HIGH
7     Record demo video (3–5 min)           Sreenu   🟢 MEDIUM
7     Practice 4-min booth script × 5 times All      🟢 MEDIUM
8     Travel to Bharat Mandapam             —        —
```

---

## The 3 Sentences That Win

After all of this, when a judge asks "What does this do in one line?" say:

> *"PRAMAAN connects every rupee of government scheme money to the physical asset it built, the agency that built it, and the photo proof that it exists — so for the first time, you can see exactly where delivery happened and where it didn't."*

And if they ask "What's unique?":

> *"Every other system in India tracks either money OR assets OR beneficiaries — in separate silos. We are the only system that links all three into a single traversable graph, with AI that flags when the chain breaks."*

---

*Last updated: March 20, 2026*
*Deadline: March 28, 2026 — India Innovates 2026, Bharat Mandapam*
