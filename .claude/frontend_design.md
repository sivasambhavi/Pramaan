# PRAMAAN – Frontend Design Plan
**Owner:** Sreenu
**Stack:** Streamlit + Plotly + streamlit-agraph + streamlit-extras
**Theme:** Dark governance-intelligence platform (not a data dashboard)
**Demo target:** 3–4 min smooth walkthrough, offline-capable

---

## Global Design System

### Color Palette
| Purpose | Color | Hex |
|---|---|---|
| Background | Dark navy | `#0E1117` |
| Card/panel | Dark slate | `#1A1F2E` |
| Primary accent | Electric blue | `#4C8EDA` |
| Success / proven | Green | `#2ECC71` |
| Warning / partial | Amber | `#F39C12` |
| Danger / missing | Red | `#E74C3C` |
| Text primary | White | `#FFFFFF` |
| Text secondary | Light grey | `#A0AEB4` |

### Typography
- Headings: bold, white
- Subheadings: light grey
- Metric values: large, electric blue or status color

### Layout
- All pages: `st.set_page_config(layout="wide")`
- Sidebar: navigation only, collapsible
- Main area: 2–3 column grid per screen
- Cards: use `st.container()` with custom CSS border/background

### Custom CSS (inject once in `app.py`)

Paste this entire block into `app.py` before any page content. It applies globally across all pages.

```python
st.markdown("""
<style>
/* ── Base ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, .stApp {
  background-color: #0A0F1E;
  font-family: 'Inter', sans-serif;
  color: #E2E8F0;
}

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0D1226 0%, #111827 100%);
  border-right: 1px solid rgba(76, 142, 218, 0.2);
}
[data-testid="stSidebar"] .stMarkdown h1 {
  color: #4C8EDA;
  font-size: 1.1rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ── Page header banner ───────────────────────────── */
.page-header {
  background: linear-gradient(135deg, #0D1B3E 0%, #0A2A5E 60%, #0E1117 100%);
  border-bottom: 2px solid #4C8EDA;
  border-radius: 0 0 16px 16px;
  padding: 24px 32px;
  margin-bottom: 24px;
}
.page-header h1 {
  color: #FFFFFF;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0;
}
.page-header p {
  color: #A0AEB4;
  font-size: 0.9rem;
  margin: 4px 0 0 0;
}

/* ── Glassmorphism cards ──────────────────────────── */
.glass-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px 24px;
  margin: 8px 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.glass-card:hover {
  border-color: rgba(76, 142, 218, 0.4);
  box-shadow: 0 8px 32px rgba(76, 142, 218, 0.15);
}

/* ── Metric cards ─────────────────────────────────── */
.metric-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
}
.metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: #4C8EDA;
}
.metric-label {
  font-size: 0.8rem;
  color: #A0AEB4;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Status indicators with glow ─────────────────── */
.status-green {
  color: #2ECC71;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(46, 204, 113, 0.6);
}
.status-amber {
  color: #F39C12;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(243, 156, 18, 0.6);
}
.status-red {
  color: #E74C3C;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(231, 76, 60, 0.6);
}

/* ── Status badge pills ───────────────────────────── */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.badge-green  { background: rgba(46, 204, 113, 0.15); color: #2ECC71; border: 1px solid rgba(46, 204, 113, 0.4); }
.badge-amber  { background: rgba(243, 156, 18, 0.15);  color: #F39C12; border: 1px solid rgba(243, 156, 18, 0.4); }
.badge-red    { background: rgba(231, 76, 60, 0.15);   color: #E74C3C; border: 1px solid rgba(231, 76, 60, 0.4); }
.badge-blue   { background: rgba(76, 142, 218, 0.15);  color: #4C8EDA; border: 1px solid rgba(76, 142, 218, 0.4); }

/* ── Proof chain step cards ───────────────────────── */
.chain-step {
  background: rgba(76, 142, 218, 0.06);
  border-left: 3px solid #4C8EDA;
  border-radius: 0 10px 10px 0;
  padding: 12px 18px;
  margin: 6px 0;
  transition: background 0.2s ease;
}
.chain-step:hover {
  background: rgba(76, 142, 218, 0.12);
}
.chain-step-missing {
  border-left-color: #E74C3C;
  background: rgba(231, 76, 60, 0.06);
}

/* ── Evidence image frame ─────────────────────────── */
.evidence-frame {
  border: 2px solid rgba(76, 142, 218, 0.3);
  border-radius: 12px;
  overflow: hidden;
  background: #0D1226;
}
.evidence-label {
  background: rgba(76, 142, 218, 0.15);
  color: #4C8EDA;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 6px 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Live ingestion pulse animation ──────────────── */
@keyframes pulse-glow {
  0%   { box-shadow: 0 0 0 0 rgba(76, 142, 218, 0.5); }
  70%  { box-shadow: 0 0 0 12px rgba(76, 142, 218, 0); }
  100% { box-shadow: 0 0 0 0 rgba(76, 142, 218, 0); }
}
.extracting {
  animation: pulse-glow 1.5s infinite;
  border-radius: 8px;
}

/* ── Chat / Q&A bubble ────────────────────────────── */
.answer-bubble {
  background: rgba(76, 142, 218, 0.08);
  border: 1px solid rgba(76, 142, 218, 0.2);
  border-radius: 0 16px 16px 16px;
  padding: 16px 20px;
  margin: 12px 0;
}
.question-bubble {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px 16px 0 16px;
  padding: 12px 16px;
  margin: 8px 0;
  text-align: right;
}

/* ── Divider ──────────────────────────────────────── */
.neon-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #4C8EDA, transparent);
  border: none;
  margin: 24px 0;
}

/* ── Streamlit overrides ──────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, #1A3A6E, #2563EB);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }

[data-testid="stMetric"] {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  padding: 12px;
}
[data-testid="stMetricValue"] { color: #4C8EDA; }

div[data-testid="stDataFrame"] {
  background: rgba(255,255,255,0.02);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.06);
}
</style>
""", unsafe_allow_html=True)
```

### Page header helper (use at top of every page)
```python
def page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-header">
      <h1>⚡ {title}</h1>
      <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def neon_divider():
    st.markdown('<hr class="neon-divider">', unsafe_allow_html=True)

def badge(text: str, color: str = "blue"):
    return f'<span class="badge badge-{color}">{text}</span>'
```

### Libraries to install
```
streamlit-agraph>=0.0.45
plotly>=5.18.0
streamlit-extras>=0.3.6
```
Add to `requirements.txt`.

---

## Screen 1 — Ward Overview (`01_🏙_Ward_Map.py`)

### Purpose
First screen the judge sees. Must immediately show the scale and health of Ward 45.

### API calls
- `GET /wards/REG_W45/score` → delivery score + counts
- `GET /wards/REG_W45/assets` → asset list

### Layout

```
┌─────────────────────────────────────────────────────┐
│  PRAMAAN   Ward 45 – Shahdara South, Delhi          │
│  "Governance Delivery Intelligence"                  │
├──────────────┬──────────────┬───────────────────────┤
│  Delivery    │  Total       │  Proven    │  Gaps     │
│  Score Gauge │  Assets: 51  │  Assets:10 │  41       │
│  19.6%       │              │            │           │
├──────────────┴──────────────┴────────────────────────┤
│  Asset Breakdown (donut chart by type)               │
│  + Asset list table with status color coding         │
│  [Click any asset row → opens Proof Chain screen]    │
└─────────────────────────────────────────────────────┘
```

### Components

**1. Delivery Score Gauge (Plotly)**
```python
import plotly.graph_objects as go

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=score,
    title={"text": "Delivery Score", "font": {"color": "white"}},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#4C8EDA"},
        "steps": [
            {"range": [0, 40],  "color": "#E74C3C"},
            {"range": [40, 70], "color": "#F39C12"},
            {"range": [70, 100],"color": "#2ECC71"},
        ],
    },
    number={"suffix": "%", "font": {"color": "white"}},
))
fig.update_layout(paper_bgcolor="#1A1F2E", font_color="white", height=250)
st.plotly_chart(fig, use_container_width=True)
```

**2. Top metric cards (4 columns)**
```python
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ward", "Ward 45 – Shahdara")
col2.metric("Total Assets", total_assets)
col3.metric("Proven", proven_assets, delta=f"{score}%")
col4.metric("Gaps", total_assets - proven_assets, delta_color="inverse")
```

**3. Asset type donut chart (Plotly)**
- Group assets by `type` (drain, road, toilet, housing, streetlight, water_body)
- Show count per type in a donut

**4. Asset table with status colors**
```python
for asset in assets:
    color = {"completed": "🟢", "in_progress": "🟡", "planned": "🔴"}.get(asset["status"], "⚪")
    st.markdown(f"{color} **{asset['name']}** — {asset['type']} — ₹{asset['cost']:,}")
    # Make clickable — store selected asset in st.session_state
```

---

## Screen 2 — Proof Chain Viewer (`02_🧷_Proof_Chain.py`)

### Purpose
Show the full delivery chain for a selected asset as a visual flow. The "wow" screen.

### API calls
- `GET /wards/REG_W45/assets` → asset selector
- `GET /assets/{asset_id}/chain` → full chain

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Select Asset: [dropdown]                            │
├──────────────────────────────────────────────────────┤
│  Delivery Chain Flow                                  │
│                                                       │
│  [Scheme] ──FUNDS──► [Asset] ──BUILT_BY──► [Actor]  │
│      │                   │                            │
│   TARGETS             LOCATED_IN                      │
│      ▼                   ▼                            │
│  [Beneficiary]       [Region]                        │
│                          │                            │
│                       PROVED_BY                       │
│                          ▼                            │
│                      [Evidence]                       │
│                    Before │ After                     │
│                   [image] │ [image]                   │
├──────────────────────────────────────────────────────┤
│  Chain Completeness: ████████░░ 80%                  │
│  Missing: ward-level LOCATED_IN link                 │
└──────────────────────────────────────────────────────┘
```

### Components

**1. Asset selector**
```python
asset_id = st.selectbox("Select Asset", options=[a["asset_id"] for a in assets],
                         format_func=lambda x: asset_map[x])
```

**2. Visual chain steps (custom HTML cards)**
```python
steps = [
    ("🏛 Scheme", chain["scheme"]["name"] if chain["scheme"] else "❌ Missing"),
    ("🏗 Asset",  chain["asset"]["name"]),
    ("👷 Built by", chain["built_by"]["name"] if chain["built_by"] else "❌ Missing"),
    ("📍 Region", chain["region"]["name"] if chain["region"] else "❌ Missing"),
    ("📋 Evidence", f"{len(chain['evidence'])} piece(s)"),
    ("👥 Beneficiaries", f"{sum(b['count'] for b in chain['beneficiaries'])} people"),
]

for icon_label, value in steps:
    status = "🟢" if "❌" not in value else "🔴"
    st.markdown(f"""
    <div class="chain-step">
      {status} <strong>{icon_label}</strong>: {value}
    </div>
    """, unsafe_allow_html=True)
```

**3. Before / After evidence images (side by side)**
```python
before = [e for e in chain["evidence"] if e["before_or_after"] == "before"]
after  = [e for e in chain["evidence"] if e["before_or_after"] == "after"]

col1, col2 = st.columns(2)
with col1:
    st.caption("📷 Before")
    st.image(before[0]["url"]) if before else st.info("No before image")
with col2:
    st.caption("📷 After")
    st.image(after[0]["url"]) if after else st.info("No after image")
```

**4. Chain completeness progress bar**
```python
total_steps = 6  # scheme, asset, actor, region, evidence, beneficiaries
filled = sum([
    bool(chain["scheme"]), bool(chain["asset"]), bool(chain["built_by"]),
    bool(chain["region"]), bool(chain["evidence"]), bool(chain["beneficiaries"])
])
st.progress(filled / total_steps, text=f"Chain completeness: {filled}/{total_steps} steps")
```

---

## Screen 3 — Gap Analysis (`03_📊_Gap_Analysis.py`)

### Purpose
Show judges exactly where governance delivery breaks down. Traffic light system.

### API calls
- `GET /wards/REG_W45/gaps` → scheme gaps + proven_assets count
- `GET /wards/REG_W45/score` → delivery score

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Gap Analysis — Ward 45                              │
├───────────────────┬──────────────────────────────────┤
│  Delivery Score   │  Gap Summary                     │
│  Gauge (19.6%)    │  🔴 no_evidence: X schemes       │
│                   │  🟡 partial: Y schemes            │
│                   │  🟢 complete: Z schemes           │
├───────────────────┴──────────────────────────────────┤
│  Scheme-by-scheme breakdown                          │
│                                                       │
│  SCH_SFC  Local Dev Grants   ████████░░  🟡 partial  │
│           51 assets | 10 proven | 41 missing         │
│                                                       │
│  SCH_SWACHH  Swachh Bharat   ██████████  🟢 complete │
│           1 asset  | 1 proven  | 0 missing           │
└──────────────────────────────────────────────────────┘
```

### Components

**1. Gap status cards**
```python
status_map = {
    "complete":    ("🟢", "Complete",    "#2ECC71"),
    "partial":     ("🟡", "Partial",     "#F39C12"),
    "no_evidence": ("🔴", "No Evidence", "#E74C3C"),
    "no_assets":   ("⚫", "No Assets",   "#7F8C8D"),
}

for gap in gaps:
    icon, label, color = status_map.get(gap["gap_type"], ("⚪", "Unknown", "grey"))
    pct = gap["proven_assets"] / gap["linked_assets"] * 100 if gap["linked_assets"] else 0
    st.markdown(f"### {icon} {gap['scheme_name']}")
    st.progress(pct / 100, text=f"{gap['proven_assets']} / {gap['linked_assets']} assets proven")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", gap["linked_assets"])
    col2.metric("Proven", gap["proven_assets"])
    col3.metric("Gap", gap["linked_assets"] - gap["proven_assets"], delta_color="inverse")
```

**2. Bar chart (Plotly) — assets vs proven per scheme**
```python
fig = go.Figure(data=[
    go.Bar(name="Total Assets", x=scheme_names, y=total_list, marker_color="#4C8EDA"),
    go.Bar(name="Proven",       x=scheme_names, y=proven_list, marker_color="#2ECC71"),
])
fig.update_layout(barmode="group", paper_bgcolor="#1A1F2E",
                  plot_bgcolor="#1A1F2E", font_color="white")
st.plotly_chart(fig, use_container_width=True)
```

---

## Screen 4 — Delivery Graph (`04_🔗_Graph_View.py`)

### Purpose
The "intelligence platform" screen. Interactive graph showing the full delivery network. Most visually impressive.

### API calls
- `GET /wards/REG_W45/assets` → all assets
- `GET /assets/{asset_id}/chain` → per-asset chain (loop for demo assets)

### Library
```python
from streamlit_agraph import agraph, Node, Edge, Config
```

### Layout

```
┌─────────────────────────────────────────────────────┐
│  Filter: [All] [Schemes] [Assets] [Evidence]        │
│  Ward: REG_W45                                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│         [SCH_SFC]────FUNDS────►[ASSET_DRAIN_GALI7]  │
│              │                        │              │
│           TARGETS               LOCATED_IN          │
│              ▼                        ▼              │
│         [BEN_GALI7]           [REG_W45_GALI7]       │
│                                       │              │
│                                    PROVED_BY         │
│                                       ▼              │
│                               [EVD_DRAIN_AFTER]      │
│                                                      │
├─────────────────────────────────────────────────────┤
│  Click a node to see its properties in the sidebar  │
└─────────────────────────────────────────────────────┘
```

### Components

**1. Build graph nodes and edges**
```python
NODE_COLORS = {
    "Scheme":      "#A23B72",
    "Asset":       "#C73E1D",
    "Region":      "#2E86AB",
    "Actor":       "#F18F01",
    "Evidence":    "#44BBA4",
    "Beneficiary": "#3B1F2B",
    "Event":       "#E94F37",
}

nodes, edges = [], []

# Add ward node
nodes.append(Node(id="REG_W45", label="Ward 45", color="#2E86AB", size=30))

for asset in assets:
    nodes.append(Node(id=asset["asset_id"], label=asset["name"][:20],
                      color=NODE_COLORS["Asset"], size=20))
    edges.append(Edge(source=asset["asset_id"], target="REG_W45",
                      label="LOCATED_IN"))

# Add chain nodes for key assets (ASSET_DRAIN_GALI7, ASSET_ROAD_GALI7, etc.)
for chain in chains:
    if chain["scheme"]:
        nodes.append(Node(id=chain["scheme"]["scheme_id"],
                          label=chain["scheme"]["name"][:20],
                          color=NODE_COLORS["Scheme"], size=25))
        edges.append(Edge(source=chain["scheme"]["scheme_id"],
                          target=chain["asset_id"], label="FUNDS"))
    for ev in chain["evidence"]:
        nodes.append(Node(id=ev["evidence_id"], label=ev["before_or_after"],
                          color=NODE_COLORS["Evidence"], size=15))
        edges.append(Edge(source=ev["evidence_id"],
                          target=chain["asset_id"], label="PROVES"))
```

**2. Render graph**
```python
config = Config(
    width=900, height=600,
    directed=True,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#4C8EDA",
    collapsible=False,
    node={"labelProperty": "label"},
    link={"labelProperty": "label", "renderLabel": True},
)

selected = agraph(nodes=nodes, edges=edges, config=config)

if selected:
    st.sidebar.markdown(f"**Selected:** `{selected}`")
```

---

## Screen 5 — Live Ingestion (`05_⚡_Live_Ingestion.py`)

### Purpose
Demo the AI capability. Paste raw text → watch it become graph data.

### API calls
- `POST /ingest/entities` → write extracted entities to Neo4j

### Layout

```
┌──────────────────────┬───────────────────────────────┐
│  Paste Text          │  Extracted Entities            │
│                      │                                │
│  [text area]         │  Regions:  REG_W45, ...       │
│                      │  Schemes:  SCH_SFC             │
│  [Extract →]         │  Assets:   ASSET_DRAIN_GALI7  │
│                      │  Evidence: EVD_...             │
│                      │  Events:   EVT_...             │
├──────────────────────┴───────────────────────────────┤
│  [Ingest into Graph]   ← only enabled after extract  │
│                                                       │
│  ✅ 3 entities ingested | ✅ 2 relations created      │
└──────────────────────────────────────────────────────┘
```

### Components

**1. Split-screen extract flow**
```python
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Raw Text")
    text = st.text_area("Paste PIB/news text here", height=300,
                         placeholder="e.g. MCD completed drain in Gali No. 7...")
    extract_btn = st.button("⚡ Extract Entities", type="primary")

with col2:
    st.subheader("🧠 Extracted Entities")
    if "extracted" in st.session_state:
        result = st.session_state["extracted"]
        for key in ["regions", "schemes", "actors", "assets", "beneficiaries", "evidence", "events"]:
            items = result.get(key, [])
            if items:
                st.markdown(f"**{key.title()}** ({len(items)})")
                st.json(items, expanded=False)
    else:
        st.info("Extraction results will appear here")
```

**2. Extract button action**
```python
if extract_btn and text:
    with st.spinner("🤖 AI extracting entities..."):
        result = extract_entities_and_relations(text, api_key=groq_key)
        st.session_state["extracted"] = result
        st.session_state["source"] = result.get("_source", "llm")
    st.success(f"Extracted from {'cache ⚡' if result.get('_source') == 'cache' else 'LLM 🤖'}")
    st.rerun()
```

**3. Ingest button (only enabled after extraction)**
```python
if "extracted" in st.session_state:
    if st.button("📥 Ingest into Graph", type="primary"):
        with st.spinner("Writing to Neo4j..."):
            payload = build_ingest_payload(st.session_state["extracted"])
            resp = requests.post(f"{BASE_URL}/ingest/entities", json=payload)
            data = resp.json()
        st.success(f"✅ {data['entities_created']} entities | {data['relations_created']} relations added")
        st.balloons()
```

---

## Screen 6 — NL Questions (`06_❓_Questions.py`)

### Purpose
Show AI-powered Q&A over the graph. Chat-style, not a dropdown.

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Ask Pramaan                                         │
│                                                      │
│  Quick questions:                                    │
│  [What was built in Ward 45?]                        │
│  [For Gali 7, show delivery chain]                   │
│  [Which schemes have low scores?]                    │
│                                                      │
│  Or type your own:  [_________________________] [Ask]│
├──────────────────────────────────────────────────────┤
│  Answer                                              │
│                                                      │
│  Q: What was built in Ward 45?                       │
│  → 51 assets found. Types: water_body (46),          │
│    drain (1), road (1), toilet (1), housing (1),     │
│    streetlight (1)                                   │
│                                                      │
│  [View as table]  [View as chart]                    │
└──────────────────────────────────────────────────────┘
```

### Components

**1. Quick question chips**
```python
st.markdown("**Quick Questions:**")
col1, col2, col3 = st.columns(3)
q1 = col1.button("🏗 What was built in Ward 45?")
q2 = col2.button("🔗 Gali 7 delivery chain")
q3 = col3.button("📊 Low delivery scores?")

question = st.text_input("Or ask your own question")
ask = st.button("Ask →", type="primary")

if q1: question = "What was built in Ward 45?"
if q2: question = "For Gali 7, show delivery chain"
if q3: question = "Which schemes have low delivery scores?"
```

**2. Answer renderer based on answer_type**
```python
if question and (ask or q1 or q2 or q3):
    with st.spinner("Querying graph..."):
        result = generate_query(question)

    st.markdown(f"**Q:** {question}")

    if result["answer_type"] == "asset_list":
        st.markdown(f"→ **{result['total']} assets** found in Ward 45")
        st.dataframe(result["assets"])

    elif result["answer_type"] == "proof_chain":
        st.markdown(f"→ Full chain for **{result['asset']['name']}**")
        # Reuse chain step cards from Screen 2

    elif result["answer_type"] == "gap_analysis":
        score = result["delivery_score"]["delivery_score"]
        st.markdown(f"→ Delivery Score: **{score}%**")
        st.dataframe(result["gaps"])

    elif result["answer_type"] == "unrecognised":
        st.warning(result["error"])
        st.markdown("**Try:** " + " | ".join(result["supported_questions"]))
```

---

## Implementation order for Sreenu

1. `app.py` — global CSS + page config
2. `01_🏙_Ward_Map.py` — ward overview (gauge + metric cards + asset table)
3. `02_🧷_Proof_Chain.py` — chain flow + before/after images
4. `05_⚡_Live_Ingestion.py` — split screen extract + ingest
5. `06_❓_Questions.py` — chat-style NL questions
6. `03_📊_Gap_Analysis.py` — traffic light gap view
7. `04_🔗_Graph_View.py` — interactive agraph (most complex, last)

---

## Environment variable Sreenu needs

In `.env`:
```
API_BASE_URL=http://localhost:8000
GROQ_API_KEY=...
```

Read in each page:
```python
import os
from dotenv import load_dotenv
load_dotenv()
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
```

---

## Additional libraries to add to requirements.txt

```
streamlit-agraph>=0.0.45
plotly>=5.18.0
streamlit-extras>=0.3.6
```

---

## Aesthetics Guide

### Design Philosophy
Pramaan should feel like a **real government intelligence platform** — not a student project dashboard.
Reference: Palantir Gotham, Grafana dark theme, military command UIs.
Every screen should communicate: *"This is serious, data-backed, production-grade."*

---

### Visual Identity

**Logo / Brand mark** (top of sidebar)
```python
st.sidebar.markdown("""
<div style="padding: 16px 0 24px 0; border-bottom: 1px solid rgba(76,142,218,0.2); margin-bottom: 16px;">
  <div style="font-size: 1.4rem; font-weight: 700; color: #4C8EDA; letter-spacing: 0.05em;">
    ⚡ PRAMAAN
  </div>
  <div style="font-size: 0.7rem; color: #A0AEB4; letter-spacing: 0.12em; text-transform: uppercase;">
    Governance Intelligence
  </div>
</div>
""", unsafe_allow_html=True)
```

**Page header pattern** (consistent across all screens)
```python
page_header(
    title="Ward Overview",
    subtitle="Ward 45 · Shahdara South · Delhi · Live data from Neo4j"
)
```

---

### Per-Screen Aesthetic Notes

#### Screen 1 — Ward Overview
- Hero element: the **Plotly gauge** centered at the top — big, bold, colored by score range
- Below gauge: 4 glassmorphism metric cards in a row
- Asset table rows: left-colored border by status (green/amber/red)
- Add a thin **"last updated"** timestamp line at the bottom right in grey

#### Screen 2 — Proof Chain
- Chain steps should feel like a **timeline**, not a list
- Use a vertical connector line between steps (CSS `::before` pseudo-element)
- Before/after images: frame them with `evidence-frame` class, add a VS divider between them
- At the top: a horizontal **breadcrumb**: `Scheme → Asset → Region → Evidence → Beneficiaries`
- Completeness bar: use a glowing blue progress bar, not default grey

```python
# Glowing progress bar override
st.markdown("""
<style>
  .stProgress > div > div {
    background: linear-gradient(90deg, #1A56DB, #4C8EDA);
    box-shadow: 0 0 8px rgba(76, 142, 218, 0.6);
    border-radius: 4px;
  }
</style>
""", unsafe_allow_html=True)
```

#### Screen 3 — Gap Analysis
- Each scheme card: full-width glass card with left border colored by status
- Left border = 4px solid green/amber/red
- Inside: scheme name bold, progress bar, 3 mini metrics (total/proven/gap) inline
- Bottom: a **"What would it take to reach 100%?"** box — list missing evidence types

```python
status_border = {"complete": "#2ECC71", "partial": "#F39C12",
                 "no_evidence": "#E74C3C", "no_assets": "#7F8C8D"}

for gap in gaps:
    color = status_border.get(gap["gap_type"], "#7F8C8D")
    st.markdown(f"""
    <div style="
      border-left: 4px solid {color};
      background: rgba(255,255,255,0.03);
      border-radius: 0 12px 12px 0;
      padding: 16px 20px;
      margin: 10px 0;
    ">
      <strong style="color: white; font-size: 1rem;">{gap['scheme_name']}</strong>
      <span style="float:right; color:{color}; font-weight:600;">{gap['gap_type'].upper()}</span>
    </div>
    """, unsafe_allow_html=True)
```

#### Screen 4 — Delivery Graph
- Background of the graph area: `#0A0F1E` (matches app bg — graph floats in space)
- Node sizes: scheme=30, asset=20, evidence=12, beneficiary=12, region=15
- Edge labels: small, grey, only show on hover if possible
- Add a **legend** below the graph (color swatch per node type)
- Add **filter buttons** at the top: `[All] [Schemes] [Assets] [Evidence]`
  - Filter updates which nodes are shown in the graph

```python
# Legend
st.markdown("""
<div style="display:flex; gap:16px; flex-wrap:wrap; margin-top:12px;">
  <span><span style="color:#A23B72">●</span> Scheme</span>
  <span><span style="color:#C73E1D">●</span> Asset</span>
  <span><span style="color:#2E86AB">●</span> Region</span>
  <span><span style="color:#F18F01">●</span> Actor</span>
  <span><span style="color:#44BBA4">●</span> Evidence</span>
  <span><span style="color:#3B1F2B">●</span> Beneficiary</span>
</div>
""", unsafe_allow_html=True)
```

#### Screen 5 — Live Ingestion
- Left panel: dark textarea with blue border glow on focus
- Right panel: entities appear as **colored badge pills** grouped by type
- "Extract" button: gradient blue, full width, glows when clicked
- After extraction: show `_source` tag — `⚡ From cache` or `🤖 From LLM`
- After ingest: `st.balloons()` + green success banner
- Add a **"Demo Text"** button that pre-fills a sample PIB paragraph — so the demo never fails

```python
DEMO_TEXT = """
The MCD Shahdara South Works Department has completed the construction of a storm-water
drain in Gali No. 7, Ward 45, Shahdara under the SFC Local Development Grants scheme
at a cost of Rs 12 lakh. The work was completed in March 2024 and benefits approximately
100 households previously affected by waterlogging.
"""

if st.button("📋 Load Demo Text"):
    st.session_state["demo_text"] = DEMO_TEXT
```

#### Screen 6 — NL Questions
- 3 quick-question buttons styled as **pill chips** with icon + label
- Question chip active state: blue background + glow
- Answer area: `answer-bubble` CSS class — blue-tinted, rounded, with a small robot icon prefix
- For asset_list answers: show a **Plotly bar chart** of assets by type instead of a raw table
- For gap_analysis answers: show the gauge inline (reuse Screen 1 gauge component)
- Source citation line at the bottom: `Source: Neo4j · Ward 45 · REG_W45`

---

### Micro-interactions

| Element | Interaction |
|---|---|
| Asset table row | Hover → slight blue background, cursor pointer |
| Chain step card | Hover → border brightens |
| Graph node | Click → sidebar shows node properties |
| Extract button | Click → pulsing animation while loading |
| Ingest button | Disabled until extraction is complete |
| Progress bars | Glowing blue fill |
| Metric cards | Hover → subtle glow border |

---

### Fonts & Icons
- Font: **Inter** (Google Fonts, loaded via CSS import)
- Icons: use Unicode emoji for simplicity (⚡ 🏙 🔗 📊 ❓ 🟢 🔴 🟡)
- No additional icon libraries needed

---

### What NOT to do
- No white backgrounds on any element
- No default Streamlit light theme
- No plain `st.table()` — always `st.dataframe()` with custom styling or HTML cards
- No uncolored plain text status — always use badge/glow/color
- No lorem ipsum placeholder text — every stub should show "Coming soon" with a styled card
- No horizontal scrollbars — keep all content within `layout="wide"` bounds
