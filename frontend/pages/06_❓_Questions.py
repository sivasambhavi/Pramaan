"""
Questions — PRAMAAN v3.0
Governance Audit Console: 5 preset Cypher questions + free-text LLM mode
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests
import pandas as pd
from utils.geo_selector import render_geo_selector, geo_breadcrumb
from utils.constants import SCHEME_DISPLAY_NAMES

BASE_URL = "http://127.0.0.1:8000"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

# ─── NLP Keyword Matching ──────────────────────────────────────────────
INTENT_KEYWORDS = {
    "amrut": "What was built in this ward under AMRUT 2.0?",
    "amrut 2.0": "What was built in this ward under AMRUT 2.0?",
    "built": "What was built in this ward under AMRUT 2.0?",
    "constructed": "What was built in this ward under AMRUT 2.0?",
    "infrastructure": "What was built in this ward under AMRUT 2.0?",
    "no evidence": "Which assets have NO evidence linked?",
    "unverified": "Which assets have NO evidence linked?",
    "no proof": "Which assets have NO evidence linked?",
    "missing": "Which assets have NO evidence linked?",
    "water bod": "Which assets have NO evidence linked?",
    "water body": "Show all water body assets",
    "water bodies": "Show all water body assets",
    "jheel": "Show all water body assets",
    "lake": "Show all water body assets",
    "pond": "Show all water body assets",
    "funding": "How much funding was allocated per scheme?",
    "budget": "How much funding was allocated per scheme?",
    "allocated": "How much funding was allocated per scheme?",
    "cost": "How much funding was allocated per scheme?",
    "scheme": "How much funding was allocated per scheme?",
    "agency": "Which agency implemented the most projects?",
    "implemented": "Which agency implemented the most projects?",
    "mcd": "Which agency implemented the most projects?",
    "drain": "Show all completed drain projects",
    "nallah": "Show all completed drain projects",
    "desilting": "Show all completed drain projects",
    "toilet": "Show all completed drain projects",
    "road": "Show all completed drain projects",
    "delhi": "📊 AMRUT national drainage progress — where does Delhi stand?",
    "national": "📊 AMRUT national drainage progress — where does Delhi stand?",
    "pmay": "How much funding was allocated per scheme?",
    "housing": "How much funding was allocated per scheme?",
    "sbm": "How much funding was allocated per scheme?",
    "swachh": "How much funding was allocated per scheme?",
}

def match_intent(user_question: str) -> str | None:
    q_lower = user_question.lower()
    for keyword, mapped_question in INTENT_KEYWORDS.items():
        if keyword in q_lower:
            return mapped_question
    return None

# ──────────────────────────────────────────────────────────────
# Preset questions — each has a label and a backend endpoint call
# ──────────────────────────────────────────────────────────────
PRESET_QUESTIONS = [
    {
        "label": "What was built in this ward under AMRUT 2.0?",
        "endpoint": "q_amrut",
        "mock": [
            {"Asset": "Main Shahdara Drain", "Type": "drain", "Status": "completed", "Cost (₹)": "12,00,000"},
            {"Asset": "Gali No.7 Drain", "Type": "drain", "Status": "completed", "Cost (₹)": "9,00,000"},
        ]
    },
    {
        "label": "Which assets have NO evidence linked?",
        "endpoint": "q_no_evidence",
        "mock": [
            {"Asset": "Water Body - BURARI", "Type": "water_body", "Status": "completed"},
            {"Asset": "Water Body - TIMARPUR", "Type": "water_body", "Status": "completed"},
            {"Asset": "LED Streetlights Block A", "Type": "streetlight", "Status": "completed"},
        ]
    },
    {
        "label": "How much funding was allocated per scheme?",
        "endpoint": "q_scheme_funding",
        "mock": [
            {"Scheme": "SFC", "Assets": 28, "Total Allocated (₹)": "2,40,00,000"},
            {"Scheme": "PMAY", "Assets": 5, "Total Allocated (₹)": "1,50,00,000"},
            {"Scheme": "Swachh Bharat", "Assets": 8, "Total Allocated (₹)": "64,00,000"},
        ]
    },
    {
        "label": "Which agency implemented the most projects?",
        "endpoint": "q_top_agency",
        "mock": [
            {"Agency": "MCD Shahdara Works Dept", "Projects": 32},
            {"Agency": "Contractor Infra 1", "Projects": 8},
            {"Agency": "MCD Shahdara Sanitation", "Projects": 5},
        ]
    },
    {
        "label": "Show all completed drain projects",
        "endpoint": "q_drains",
        "mock": [
            {"Asset": "Main Shahdara Drain", "Cost (₹)": "12,00,000", "Status": "completed"},
            {"Asset": "Gali No.7 Drain", "Cost (₹)": "9,00,000", "Status": "completed"},
        ]
    },
    {
        "label": "📊 AMRUT national drainage progress — where does Delhi stand?",
        "endpoint": "amrut_national",   # handled specially below
        "mock": []
    },
]





def run_preset_question(endpoint: str, ward_id: str) -> dict | None:
    """Call the backend question endpoint. Returns {rows: [...], is_mock: bool} or None on error."""
    try:
        r = requests.get(f"{BASE_URL}/questions/{endpoint}", params={"ward_id": ward_id}, timeout=8)
        if r.status_code == 200:
            return {"rows": r.json().get("data", []), "is_mock": False}
    except Exception:
        pass
    return None


def nl_to_cypher_and_run(question: str, ward_id: str) -> dict | None:
    """LLM converts NL → Cypher → run on Neo4j via /questions/custom."""
    if not GROQ_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        schema = """Nodes: Asset(asset_id,name,type,status,cost), Region(region_id,name,type), 
        Actor(actor_id,name,type), Scheme(scheme_id,name,ministry,category), Evidence(evidence_id,url,type)
        Rels: (Scheme)-[:FUNDS]->(Asset), (Asset)-[:BUILT_BY]->(Actor), 
               (Asset)-[:LOCATED_IN]->(Region), (Evidence)-[:PROVES]->(Asset)"""
        prompt = f"""Convert the following natural language question to a Neo4j Cypher query.
Schema: {schema}
Ward context: filter by region_id = '{ward_id}' or parent_region_id = '{ward_id}'.
Question: {question}
Return ONLY the Cypher query string, nothing else. No explanation, no backticks."""

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=300
        )
        cypher = resp.choices[0].message.content.strip().strip("`")
        # Run via backend custom query endpoint
        r = requests.post(f"{BASE_URL}/questions/custom",
                          json={"cypher": cypher, "params": {"ward_id": ward_id}}, timeout=10)
        if r.status_code == 200:
            return {"rows": r.json().get("data", []), "cypher": cypher, "is_mock": False}
    except Exception:
        pass
    return None


def display_result(rows: list, is_mock: bool, endpoint: str = None):
    if is_mock:
        st.warning("⚠️ Demo data — live graph query returned empty. Showing representative data.")
    df = pd.DataFrame(rows)
    if df.empty:
        if endpoint in ["q_no_evidence", "Which assets have NO evidence linked?"]:
            st.success("✅ Every asset in this ward has at least one linked evidence article!")
            st.balloons()
        else:
            st.success("✅ All assets in this ward have linked evidence! Or no matching assets found.")
    else:
        if endpoint in ["q_no_evidence", "Which assets have NO evidence linked?"]:
            st.warning(f"⚠️ {len(df)} out of 29 assets have no proof")
            st.dataframe(df, use_container_width=True)
            st.caption("These assets are marked ❌ Unverified. Add news articles or photos to upgrade their proof status.")
        else:
            st.dataframe(df, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Governance Audit | Pramaan", layout="wide")
    st.markdown("""<style>[data-testid="stSidebarNav"] a[href*="Live_Ingestion"] { display: none !important; }</style>""", unsafe_allow_html=True)

    st.title("🔍 PRAMAAN — Governance Audit Console")
    st.caption("Interrogate the knowledge graph. Ask any question about what was built, funded, and proven.")

    # ── Geography ──────────────────────────────────────────────────────────
    geo = render_geo_selector(sidebar=True)
    ward_id   = geo["ward_id"]
    ward_name = geo["ward_name"]

    st.markdown(f"**📍 Context:** `{geo_breadcrumb()}`")
    st.divider()

    # ── Free-text input ───────────────────────────────────────────────────
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_q = st.text_input("Ask a question about this ward...",
                               placeholder="e.g. Which assets cost more than ₹10 lakh?",
                               label_visibility="collapsed")
    with col_btn:
        ask_btn = st.button("🔍 Ask", use_container_width=True)

    if ask_btn and user_q:
        matched = match_intent(user_q)
        if matched:
            st.info(f"💡 Understood intent as: **{matched}**")
            # Find the equivalent preset question endpoint
            matched_endpoint = None
            for pq in PRESET_QUESTIONS:
                if pq["label"] == matched:
                    matched_endpoint = pq["endpoint"]
                    break
                    
            if matched_endpoint:
                if matched_endpoint == "amrut_national":
                    st.warning("National progress stats are available in the suggested questions panel.")
                else:
                    with st.spinner("Querying knowledge graph..."):
                        result = run_preset_question(matched_endpoint, ward_id)
                    if result and result["rows"]:
                        display_result(result["rows"], False, matched_endpoint)
                    else:
                        st.warning("No data found for this intent.")
        else:
            with st.spinner("🧠 Translating to Cypher and querying the graph..."):
                result = nl_to_cypher_and_run(user_q, ward_id)
            if result:
                st.markdown("#### 📋 Answer")
                if result.get("cypher"):
                    with st.expander("🔎 Generated Cypher"):
                        st.code(result["cypher"], language="cypher")
                
                if not result.get("rows"):
                    st.warning(f"No graph data found for: '{user_q}'. Try one of the suggested questions above.")
                else:
                    display_result(result["rows"], result.get("is_mock", False), "custom")
            else:
                st.warning(f"No graph data found for: '{user_q}'. Try one of the suggested questions above.")

    st.markdown("---")

    # ── Suggested questions ───────────────────────────────────────────────
    st.markdown("#### 💡 Suggested Questions — click to ask")

    for pq in PRESET_QUESTIONS:
        if st.button(pq["label"], use_container_width=True, key=f"pq_{pq['endpoint']}"):
            st.markdown(f"#### 📋 Answer: _{pq['label']}_")

            # ── Special: AMRUT national data chart ──────────────────────────
            if pq["endpoint"] == "amrut_national":
                import plotly.graph_objects as go
                try:
                    ar = requests.get(f"{BASE_URL}/data/amrut-drainage", timeout=8)
                    if ar.status_code == 200:
                        amrut     = ar.json()
                        delhi_d   = amrut.get("delhi", {}) or {}
                        nat_total = amrut.get("grand_total", {}) or {}
                        states    = amrut.get("states", [])
                        src       = amrut.get("source", "data.gov.in")
                        src_url   = amrut.get("source_url", "https://data.gov.in")

                        st.caption(f"📄 Source: **{src}** — [Open Dataset]({src_url})")

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("🏙️ Delhi Completed",
                                  f"{delhi_d.get('work_completed___number','N/A')} projects")
                        m2.metric("💰 Delhi Amount",
                                  f"₹{delhi_d.get('work_completed___amount','N/A')} Cr")
                        m3.metric("🔨 Delhi In-Progress",
                                  f"{delhi_d.get('work_in_progress___number','N/A')} projects")
                        m4.metric("🌍 National Grand Total",
                                  f"{nat_total.get('total___number','N/A')} projects")

                        # Full state breakdown table
                        df_st = pd.DataFrame(states)
                        df_st = df_st[["state_ut", "work_completed___number",
                                       "work_in_progress___number", "total___number",
                                       "total___amount"]]
                        df_st.columns = ["State/UT", "Completed (No.)",
                                         "In-Progress (No.)", "Total (No.)",
                                         "Total Amount (₹ Cr)"]
                        st.dataframe(df_st, use_container_width=True)

                        # Bar chart — completed works by state
                        df_chart = df_st[df_st["Completed (No.)"] != "NA"].copy()
                        df_chart["Completed (No.)"] = pd.to_numeric(
                            df_chart["Completed (No.)"], errors="coerce").fillna(0)
                        df_chart = df_chart.nlargest(12, "Completed (No.)")
                        colors = ["#E63946" if "Delhi" in str(s) else "#3b82f6"
                                  for s in df_chart["State/UT"]]
                        fig = go.Figure(go.Bar(
                            x=df_chart["State/UT"],
                            y=df_chart["Completed (No.)"],
                            marker_color=colors,
                            text=df_chart["Completed (No.)"].astype(int),
                            textposition="outside",
                        ))
                        fig.update_layout(
                            title="AMRUT Storm Drainage — Completed Projects by State",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font={"color": "white"},
                            xaxis={"tickfont": {"size": 9}},
                            height=360,
                            margin=dict(l=10, r=10, t=40, b=90),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("🔴 Delhi highlighted in red")
                    else:
                        st.error("Could not load AMRUT data from backend.")
                except Exception as e:
                    st.error(f"Error: {e}")

            # ── Standard preset Cypher questions ─────────────────────────────
            else:
                with st.spinner("Querying knowledge graph..."):
                    result = run_preset_question(pq["endpoint"], ward_id)
                if result and result["rows"]:
                    display_result(result["rows"], False, pq["endpoint"])
                else:
                    display_result(pq["mock"], True, pq["endpoint"])

    st.markdown("---")

    # ── Live ward stats (always visible) ─────────────────────────────────
    st.markdown("#### 📊 Live Ward Statistics")
    try:
        score_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/score", timeout=8)
        if score_resp.status_code == 200:
            sd = score_resp.json()
            counts = sd.get("counts", {})
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("🏗 Total", sd["total_assets"])
            c2.metric("✅ Fully Verified", counts.get("fully_verified", 0))
            c3.metric("📋 Data Only", counts.get("partially_verified", counts.get("data_only", 0)))
            c4.metric("📰 News Only", counts.get("news_only", 0))
            c5.metric("❌ Unverified", counts.get("unverified", 0))

            from backend.utils.stats import get_scheme_breakdown
            from backend.app.neo4j_client import get_session
            try:
                with get_session() as session:
                    sch = get_scheme_breakdown(ward_name, session)
            except Exception:
                sch = sd.get("scheme_breakdown", {})
                
            if sch:
                st.markdown("**Scheme Breakdown:**")
                sch_cols = st.columns(min(len(sch), 6) or 1)
                for i, (sname, cnt) in enumerate(sorted(sch.items(), key=lambda x: -x[1])):
                    display = SCHEME_DISPLAY_NAMES.get(sname, sname[:20] + "...")
                    sch_cols[i % 6].metric(label=display, value=cnt)
    except Exception as e:
        st.warning(f"Could not load live stats: {e}")


if __name__ == "__main__":
    main()
