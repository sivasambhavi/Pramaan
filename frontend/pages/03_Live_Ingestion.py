"""
Live Ingestion — PRAMAAN v5.0
Premium UI: branded header · AI scraper · manual ingestion · delivery chain viewer
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import requests
import json
from utils.icons import icon, icon_box
from utils.session import init_session, get_breadcrumb
from utils.voice_input import voice_text_input
from components.topnav import render_topnav

BASE_URL = "http://127.0.0.1:8000"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "last_autosearch.json")

PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #020b14 !important;
    color: #e2e8f0 !important;
}
.block-container { padding-top: 0.5rem !important; }

.top-bar {
    background: linear-gradient(135deg, #0d1a2e 0%, #0c2461 60%, #0d1a2e 100%);
    border-bottom: 1px solid rgba(249,115,22,0.28);
    border-radius: 14px;
    padding: 18px 28px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.5rem;
}
.top-bar-left { display:flex; align-items:center; gap:14px; }
.top-bar-logo {
    font-size:2em; width:52px; height:52px;
    display:flex; align-items:center; justify-content:center;
    background:rgba(249,115,22,0.12); border-radius:12px; flex-shrink:0;
}
.top-bar-title {
    font-family:'Outfit',sans-serif; font-size:1.6em; font-weight:800;
    background:linear-gradient(90deg,#f97316,#38bdf8);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin:0; line-height:1.1;
}
.top-bar-sub { font-size:0.75em; color:#475569; margin:2px 0 0 0; }
.top-bar-badge {
    background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.35);
    border-radius:20px; padding:5px 16px; font-size:0.75em;
    color:#4ade80; font-weight:600; letter-spacing:0.04em;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity:1; }
    50% { opacity:0.6; }
}

.chain-node {
    border-radius:10px; padding:14px 18px; margin-bottom:4px;
    border-left:4px solid; position:relative;
}
.chain-node-label {
    font-size:0.7em; font-weight:700; text-transform:uppercase;
    letter-spacing:0.08em; margin:0 0 4px 0;
}
.chain-node-value {
    font-size:1.05em; font-weight:600; color:#f1f5f9; margin:0;
}
.chain-node-meta { font-size:0.75em; color:#64748b; margin-top:3px; }
.chain-arrow {
    text-align:center; font-size:1.4em;
    color:rgba(249,115,22,0.4); margin:2px 0; line-height:1;
}

.sec-label {
    font-family:'Outfit',sans-serif; font-size:1.05em; font-weight:700;
    color:#cbd5e1; margin:0 0 14px 0; letter-spacing:0.02em;
    display:flex; align-items:center; gap:8px;
}
.sec-label::after {
    content:''; flex:1; height:1px;
    background:rgba(71,85,105,0.5); margin-left:8px;
}

button[data-baseweb="tab"] {
    font-size:15px !important; font-weight:600 !important;
    padding:10px 22px !important; color:#475569 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color:#f97316 !important;
    border-bottom:2px solid #f97316 !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1a2e 0%, #020b14 100%);
    border-right: 1px solid rgba(71,85,105,0.4);
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: rgba(15,23,42,0.8) !important;
    border: 1px solid rgba(71,85,105,0.5) !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
hr { border-color: rgba(71,85,105,0.4) !important; }
[data-testid="stToolbar"] { display:none !important; }
[data-testid="stDeployButton"] { display:none !important; }
#MainMenu { visibility:hidden !important; }
* { scrollbar-width:thin; scrollbar-color:#f97316 #1a1f2e; }
*::-webkit-scrollbar { width:6px; height:6px; }
*::-webkit-scrollbar-track { background:#1a1f2e; }
*::-webkit-scrollbar-thumb { background:#f97316; border-radius:3px; }

[data-testid="stSidebarNav"] a span { color:#94a3b8 !important; font-size:0.9em !important; font-weight:500 !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] span { color:#f97316 !important; font-weight:700 !important; }
[data-testid="stSidebarNav"] a svg { color:#64748b !important; fill:#64748b !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] svg { color:#f97316 !important; fill:#f97316 !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:rgba(249,115,22,0.08) !important; border-radius:8px !important; border-left:3px solid #f97316 !important; }
</style>
"""

def save_cache(data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_cache():
    AMRUT_CACHE = os.path.join(CACHE_DIR, "amrut_delhi_cached.json")
    if os.path.exists(AMRUT_CACHE):
        with open(AMRUT_CACHE, "r") as f:
            return json.load(f)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def main() -> None:
    st.set_page_config(page_title="Live Ingestion | Pramaan", layout="wide", page_icon="🛡️")
    render_topnav("Live Ingestion")
    init_session()
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

    logo_svg = icon_box("zap", bg="rgba(249,115,22,0.15)", color="#f97316", size=24, box=52)
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-left">
            <div class="top-bar-logo">{logo_svg}</div>
            <div>
                <div class="top-bar-title">Live AI Ingestion</div>
                <div class="top-bar-sub">Auto-extract governance entities from news → write to Knowledge Graph</div>
            </div>
        </div>
        <span class="top-bar-badge" title="Status indicator — AI scraper is ready to ingest live news" style="cursor:default;">{icon("activity", "#4ade80", 14)} LIVE FEED</span>
    </div>
    """, unsafe_allow_html=True)

    _pin = icon("map-pin", "#64748b", 13)
    if not st.session_state.get("selected_ward"):
        st.markdown("<p style='color:#64748b;font-size:0.82em;'>📍 No ward selected — <a href='/Ward_Map' target='_self' style='color:#FF6B35;'>go to Ward Map</a> to select a location.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:#64748b;font-size:0.85em;margin-bottom:1rem;'>{_pin} {get_breadcrumb()}</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Strategic Scraper", "Manual Ingestion"])

    # ── TAB 1: Auto-Search ──────────────────────────────────────────────────
    with tab1:
        st.markdown(f"<p class='sec-label'>{icon('globe', '#94a3b8', 15)} Auto-Search from News</p>", unsafe_allow_html=True)

        # voice_text_input: mic embedded inside the search box
        search_query = voice_text_input(
            placeholder="e.g. AMRUT 2.0 Delhi MCD drain desilting 2025",
            key="live_search_query",
            help="Enter a governance topic. The AI will scrape recent news and extract entities into the knowledge graph.",
        )

        # GAP-15: offline fallback — grouped with a subtle container
        with st.container():
            use_cache = st.checkbox("Use cached result", value=False,
                                    help="Load the last successful scrape result instead of running a live search")

        if st.button("🔍 Auto-Search & Map to Graph"):
            if use_cache:
                cached = load_cache()
                if cached:
                    data = cached
                    st.info("📂 Loaded from cache (offline mode)")
                else:
                    st.warning("No cached result found. Please run a live search first.")
                    return
            else:
                with st.status("🔍 Scraping governance news...", expanded=True) as status:
                    try:
                        scrape_resp = requests.get(f"{BASE_URL}/scrape/news", params={"q": search_query}, timeout=30)
                        if scrape_resp.status_code == 200:
                            data = scrape_resp.json()
                            save_cache(data)
                        else:
                            st.error("Scraping service unavailable.")
                            return
                    except Exception:
                        cached = load_cache()
                        if cached:
                            data = cached
                            st.warning("⚠️ Network unavailable — loaded from offline cache.")
                        else:
                            st.error("Network unavailable and no offline cache found. Run a live search with internet first.")
                            return

            articles = data.get('articles', [])
            st.success(f"✅ Found {len(articles)} relevant news items.")

            with st.expander("📄 View Scraped News Sources"):
                for a in articles:
                    st.markdown(f"**{a['title']}**")
                    st.caption(f"Published: {a.get('published', 'N/A')}")
                    st.write(a.get('summary', ''))
                    st.divider()

            # Show extracted knowledge map
            st.markdown(f"<p class='sec-label'>{icon('git-branch', '#94a3b8', 15)} AI Extracted Knowledge Map</p>", unsafe_allow_html=True)
            st.json({"entities": data.get("entities", []), "relations": data.get("relations", [])})

            if data.get("entities"):
                with st.spinner("Writing to Knowledge Graph..."):
                    try:
                        ingest_resp = requests.post(f"{BASE_URL}/ingest/entities", json=data, timeout=15)
                        if ingest_resp.status_code == 200:
                            result = ingest_resp.json()
                            n_ent = result.get('entities_created', len(data['entities']))
                            n_rel = result.get('relations_created', len(data.get('relations', [])))
                            st.success(f"🚀 Successfully mapped **{n_ent} entities** and **{n_rel} relations** to the Knowledge Graph!")

                            # NEW FEATURE: Delivery Chain
                            response_chain = result.get("delivery_chain")
                            if response_chain:
                                st.markdown("---")
                                st.markdown(f"<p class='sec-label'>{icon('link', '#94a3b8', 15)} Governance Delivery Chain</p>", unsafe_allow_html=True)
                                st.caption("This is the complete traceability path for the asset extracted from the article.")
                                
                                if response_chain.get("matched_existing"):
                                    st.success(f"✅ Matched existing asset: **{response_chain['asset_name']}**")
                                else:
                                    st.info(f"🆕 New asset added to graph: **{response_chain['asset_name']}**")
                                
                                col1, col2 = st.columns([3, 2])
                                with col1:
                                    scheme = response_chain.get("scheme", {})
                                    _ico_scheme = icon("banknote", "#60A5FA", 13)
                                    _ico_actor  = icon("building-2", "#A78BFA", 13)
                                    _ico_asset  = icon("building", "#FCD34D", 13)
                                    _ico_loc    = icon("map-pin", "#34D399", 13)
                                    if scheme:
                                        st.markdown(f"""
                                        <div class="chain-node" style="background:rgba(56,130,246,0.08);border-color:#3B82F6;">
                                            <div class="chain-node-label" style="color:#60A5FA;">{_ico_scheme} Scheme / Funding</div>
                                            <div class="chain-node-value">{scheme.get('name','Unknown')}</div>
                                            <div class="chain-node-meta">Ministry: {scheme.get('ministry','—')} · {scheme.get('category','—')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    st.markdown('<div class="chain-arrow">↓</div>', unsafe_allow_html=True)

                                    actor = response_chain.get("actor", {})
                                    if actor:
                                        st.markdown(f"""
                                        <div class="chain-node" style="background:rgba(139,92,246,0.08);border-color:#8B5CF6;">
                                            <div class="chain-node-label" style="color:#A78BFA;">{_ico_actor} Implementing Agency</div>
                                            <div class="chain-node-value">{actor.get('name','Unknown')}</div>
                                            <div class="chain-node-meta">Type: {actor.get('type','—')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    st.markdown('<div class="chain-arrow">↓</div>', unsafe_allow_html=True)

                                    st.markdown(f"""
                                    <div class="chain-node" style="background:rgba(245,158,11,0.08);border-color:#F59E0B;">
                                        <div class="chain-node-label" style="color:#FCD34D;">{_ico_asset} Asset / Infrastructure</div>
                                        <div class="chain-node-value">{response_chain.get('asset_name','Unknown')}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('<div class="chain-arrow">↓</div>', unsafe_allow_html=True)

                                    region = response_chain.get("region", {})
                                    _ward_val = region.get('ward')
                                    if not _ward_val or str(_ward_val).lower() in ('none', 'null', ''):
                                        _ward_val = "Not resolved — ward name not found in article"
                                    loc_str = f"Ward: {_ward_val}"
                                    if region.get('street'):
                                        loc_str += f" · Street: {region.get('street')}"
                                    st.markdown(f"""
                                    <div class="chain-node" style="background:rgba(16,185,129,0.08);border-color:#10B981;">
                                        <div class="chain-node-label" style="color:#34D399;">{_ico_loc} Location</div>
                                        <div class="chain-node-value">{loc_str}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown(f"<p class='sec-label'>{icon('image', '#94a3b8', 14)} Evidence Found</p>", unsafe_allow_html=True)
                                    evidence = response_chain.get("evidence", [])
                                    if evidence:
                                        for ev in evidence:
                                            label = "✅ AFTER" if ev.get("before_or_after") == "after" else "⏳ BEFORE"
                                            st.markdown(f"**{label}** — {ev.get('capture_date', 'N/A')}")
                                            url = ev.get("url", "")
                                            if url.startswith("http"):
                                                st.image(url, use_container_width=True)
                                            else:
                                                st.caption(f"📁 Path: {url}")
                                    else:
                                        st.info("No photo evidence linked yet.")

                                    st.markdown(f"<p class='sec-label'>{icon('users', '#94a3b8', 14)} People Served</p>", unsafe_allow_html=True)
                                    people = response_chain.get("people_served")
                                    if people:
                                        st.metric("Households", f"{int(people):,}")
                                        st.caption(response_chain.get("beneficiary_desc", ""))
                                    else:
                                        st.info("Beneficiary data pending.")
                        else:
                            st.error(f"Ingestion failed: {ingest_resp.text}")
                    except Exception as e:
                        st.error(f"Ingestion error: {e}")
            else:
                st.warning("The AI could not confidently identify specific governance entities in these headlines.")

    # ── TAB 2: Manual Ingestion ─────────────────────────────────────────────
    with tab2:
        st.markdown(f"<p class='sec-label'>{icon('edit-3', '#94a3b8', 15)} Manual Text Ingestion</p>", unsafe_allow_html=True)
        manual_text = st.text_area("Paste news article or governance text here", height=200)
        if st.button("🧠 Extract & Ingest"):
            if manual_text.strip():
                with st.spinner("Extracting governance entities with AI..."):
                    try:
                        resp = requests.post(f"{BASE_URL}/scrape/analyze", json={"text": manual_text}, timeout=30)
                        if resp.status_code == 200:
                            data = resp.json()
                            if not data.get("success", True):
                                st.error(f"❌ Analysis failed: {data.get('error')}")
                                if data.get("raw"):
                                    with st.expander("Raw AI response (for debugging)"):
                                        st.code(data.get("raw"))
                                st.stop()
                                
                            st.json({"entities": data.get("entities", []), "relations": data.get("relations", [])})
                            if data.get("entities"):
                                ingest_resp = requests.post(f"{BASE_URL}/ingest/entities", json=data, timeout=15)
                                if ingest_resp.status_code == 200:
                                    r = ingest_resp.json()
                                    st.success(f"Added {r.get('entities_created',0)} entities and {r.get('relations_created',0)} relations.")
                                    st.page_link("pages/02_Proof_Chain.py", label="→ View in Proof Chain", icon="🔗")
                                else:
                                    st.error(f"Ingestion failed: {ingest_resp.text}")
                            else:
                                st.warning("No entities extracted.")
                        else:
                            st.error("Analysis failed network error.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please paste some text first.")

    st.divider()
    with st.expander("Advanced Settings"):
        st.warning("**Danger zone.** These actions modify or clear the Knowledge Graph.")
        if st.button("🗑 Clear Demo Nodes (AI-ingested only)"):
            st.session_state['confirm_clear'] = True

        if st.session_state.get('confirm_clear'):
            st.error("Are you sure? This will delete all news-ingested nodes (not seeded data).")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirm Clear"):
                    try:
                        resp = requests.delete(f"{BASE_URL}/ingest/demo-nodes")
                        if resp.status_code == 200:
                            st.success("Demo nodes cleared.")
                            st.session_state['confirm_clear'] = False
                        else:
                            st.error("Clear failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state['confirm_clear'] = False
                    st.rerun()

if __name__ == "__main__":
    main()
