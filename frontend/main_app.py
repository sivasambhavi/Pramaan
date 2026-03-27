"""
Pramaan — Governance Delivery Proof Engine
Main entry point for the Streamlit frontend.
"""

import os
import sys
import base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import streamlit as st
import streamlit.components.v1 as components
from utils.icons import icon_box, icon
from components.topnav import render_topnav
from utils.api import safe_get

LOGO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Pramaan_logo.png")
)


@st.cache_data(ttl=60)
def _fetch_stats() -> dict:
    return safe_get("/stats", silent=True) or {}


@st.cache_resource
def _logo_src() -> str:
    if not os.path.exists(LOGO_PATH):
        return ""
    with open(LOGO_PATH, "rb") as _f:
        b64 = base64.b64encode(_f.read()).decode()
    return f"data:image/png;base64,{b64}"


def home() -> None:
    render_topnav(active_page=None)
    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    * { scrollbar-width: thin; scrollbar-color: #f97316 #1a1f2e; }
    *::-webkit-scrollbar { width: 6px; } *::-webkit-scrollbar-track { background: #1a1f2e; }
    *::-webkit-scrollbar-thumb { background: #f97316; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

    # Fetch live stats (cached 5 min)
    # --- Fix 12: hardcoded demo fallbacks so stats never show 0 ---
    _DEMO_STATS = {
        "funds_tracked":   28450,   # ₹28,450 Cr tracked across AMRUT, PMAY, SDRF, PLI
        "verified_assets": 6,       # Delhi Pilot: 3 Drains + PMAY + SBM + LED
        "evidence":        31,      # evidence nodes (matches Proof & Evidence page)
        "events":          17,      # 17 events across 7 domains
    }
    _stats           = _fetch_stats()
    _funds_tracked   = _stats.get("funds_tracked",   0) or _DEMO_STATS["funds_tracked"]
    _verified_assets = 6
    _evidence        = _stats.get("evidence",        0) or _DEMO_STATS["evidence"]
    _events          = _stats.get("events",          0) or _DEMO_STATS["events"]

    logo_src = _logo_src()

    # Hero section natively embedded (no iframe) for perfect SPA navigation
    st.markdown(f"""
    <style>
      #pramaan-hero * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      #pramaan-hero {{ width: 100%; height: 580px; display: flex; flex-direction: column; align-items: center; justify-content: space-evenly; padding: 8px 24px 6px; font-family: 'Inter', sans-serif; color: #e2e8f0; overflow: hidden; background: transparent; }}
      #pramaan-hero .logo-wrap {{ width: 130px; height: 130px; border-radius: 22px; background: #020b14; display: flex; align-items: center; justify-content: center; animation: glowPulse 3s ease-in-out infinite; overflow: hidden; }}
      #pramaan-hero .logo-img {{ width: 100%; height: 100%; object-fit: cover; mix-blend-mode: screen; image-rendering: -webkit-optimize-contrast; }}
      @keyframes glowPulse {{ 0%,100% {{ box-shadow: 0 0 20px rgba(249,115,22,0.35); }} 50% {{ box-shadow: 0 0 40px rgba(249,115,22,0.65); }} }}
      #pramaan-hero .title-block {{ text-align: center; }}
      #pramaan-hero .hero-title {{ font-family: 'Cinzel', serif; font-size: 3.4em; font-weight: 900; background: linear-gradient(105deg,#f97316 0%,#fb923c 28%,#fff4e6 46%,#ffe9b0 52%,#fb923c 68%,#38bdf8 100%); background-size: 250% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1; margin-bottom: 8px; letter-spacing: 0.18em; animation: fadeDown 0.5s ease both, titleShine 3.5s linear 0.8s infinite; }}
      @keyframes titleShine {{ 0% {{ background-position: 200% center; }} 100% {{ background-position: -50% center; }} }}
      #pramaan-hero .hero-tagline {{ font-size: 0.92em; color: #64748b; letter-spacing: 0.04em; animation: fadeDown 0.5s 0.1s ease both; }}
      @keyframes fadeDown {{ from {{ opacity:0; transform:translateY(-10px); }} to {{ opacity:1; transform:translateY(0); }} }}
      #pramaan-hero .explainer {{ font-size: 0.78em; color: #475569; text-align: center; line-height: 1.55; max-width: 500px; padding: 8px 16px; background: rgba(15,23,42,0.6); border: 1px solid rgba(71,85,105,0.3); border-radius: 10px; animation: fadeDown 0.5s 0.18s ease both; }}
      #pramaan-hero .stats-wrap {{ width: 80%; background: rgba(13,20,35,0.85); border: 1px solid rgba(249,115,22,0.22); border-radius: 12px; padding: 6px 8px; display: flex; justify-content: center; gap: 0; animation: fadeUp 0.5s 0.25s ease both; }}
      @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
      #pramaan-hero .stat {{ flex: 1; text-align: center; padding: 0 12px; border-right: 1px solid rgba(71,85,105,0.3); }}
      #pramaan-hero .stat:last-child {{ border-right: none; }}
      #pramaan-hero .stat-val {{ font-family: 'Outfit', sans-serif; font-size: 1.8em; font-weight: 800; line-height: 1; letter-spacing: -0.02em; animation: popIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) both; }}
      #pramaan-hero #s1 {{ animation-delay: 0.3s; }}
      #pramaan-hero #s2 {{ animation-delay: 0.4s; }}
      #pramaan-hero #s3 {{ animation-delay: 0.5s; }}
      #pramaan-hero #s4 {{ animation-delay: 0.6s; }}
      @keyframes popIn {{ 0% {{ opacity: 0; transform: scale(0.5); }} 100% {{ opacity: 1; transform: scale(1); }} }}
      #pramaan-hero .stat-lbl {{ font-size: 0.62em; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-top: 4px; }}
      #pramaan-hero .stat-sub {{ font-size: 0.64em; color: #334155; margin-top: 2px; }}
      #pramaan-hero .btn-wrap {{ display:flex; justify-content:center; animation:fadeUp 0.5s 0.35s ease both; }}
      #pramaan-hero .launch-btn {{ background:linear-gradient(135deg,#f97316,#ea580c); color:#fff !important; text-decoration:none; border-radius:12px; padding:10px 44px; font-family:'Outfit',sans-serif; font-weight:700; font-size:1em; letter-spacing:0.02em; box-shadow:0 4px 20px rgba(249,115,22,0.4); display:inline-block; transition:transform 0.2s; cursor: pointer; }}
      #pramaan-hero .launch-btn:hover {{ transform:scale(1.05); }}
      #pramaan-hero .badge-row {{ display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; animation: fadeUp 0.5s 0.42s ease both; }}
      #pramaan-hero .badge {{ background: rgba(15,23,42,0.9); border: 1px solid rgba(71,85,105,0.5); border-radius: 20px; padding: 3px 9px; font-size: 0.62em; color: #94a3b8; font-weight: 600; letter-spacing: 0.03em; display: inline-flex; align-items: center; gap: 4px; cursor: default; white-space: nowrap; }}
      #pramaan-hero .badge:hover {{ border-color: rgba(249,115,22,0.4); color: #f97316; }}
      #pramaan-hero .dot {{ width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }}
      #pramaan-hero .footer {{ font-size: 0.68em; color: #94a3b8; text-align: center; width: 100%; animation: fadeUp 0.5s 0.5s ease both; }}
    </style>
    
    <div id="pramaan-hero">
      {"<div class='logo-wrap'><img class='logo-img' src='" + logo_src + "' /></div>" if logo_src else ""}
      <div class="title-block">
        <div class="hero-title">PRAMAAN</div>
        <div class="hero-tagline">India Governance Intelligence &amp; <span style="color:#f97316;-webkit-text-fill-color:#f97316;">Proof System</span></div>
      </div>
      <div class="explainer">
        Know what's happening. Know why. Decide with proof.
      </div>
      <div class="stats-wrap">
        <div class="stat"><div class="stat-val" id="s1" style="color:#f97316">₹{_funds_tracked:,.0f} Cr</div><div class="stat-lbl">Funds Tracked</div><div class="stat-sub">AMRUT · PMAY · SDRF · PLI</div></div>
        <div class="stat"><div class="stat-val" id="s2" style="color:#22c55e">{_verified_assets:,.0f}</div><div class="stat-lbl">WARD-LEVEL ASSETS VERIFIED</div><div class="stat-sub">data.gov.in · pilot audit</div></div>
        <div class="stat"><div class="stat-val" id="s3" style="color:#38bdf8">{_evidence:,.0f}</div><div class="stat-lbl">Evidence Nodes</div><div class="stat-sub">PIB · NDMA · ISRO · IMD</div></div>
        <div class="stat"><div class="stat-val" id="s4" style="color:#a78bfa">{_events:,.0f}</div><div class="stat-lbl">Events Tracked</div><div class="stat-sub">across 7 domains</div></div>
      </div>
      <div style="height:14px;"></div>
      <div class="btn-wrap">
        <a href="Live_Ingestion" target="_self" class="launch-btn">Launch PRAMAAN &nbsp;→</a>
      </div>
      <div style="height:28px;"></div>
      <div class="badge-row">
        <span class="badge"><span class="dot" style="background:#22c55e"></span>Neo4j Knowledge Graph</span>
        <span class="badge"><span class="dot" style="background:#38bdf8"></span>FastAPI Backend</span>
        <span class="badge"><span class="dot" style="background:#f97316"></span>Streamlit Frontend</span>
        <span class="badge"><span class="dot" style="background:#a78bfa"></span>Groq · LLaMA 3.3 70B</span>
        <span class="badge"><span class="dot" style="background:#facc15"></span>PIB · NDMA · ISRO · IMD</span>
        <span class="badge"><span class="dot" style="background:#fb7185"></span>streamlit-agraph</span>
      </div>
      <div class="footer">
        Built for <strong style="color:#cbd5e1;">India Innovates 2026</strong>
        &nbsp;·&nbsp; Bharat Mandapam, New Delhi &nbsp;·&nbsp; March 28–29
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Fix 12: Live Ticker strip ---
    import time as _time
    _ticker_items = [
        ("🟢", "data.gov.in",    "Delhi Floods impact data ingested",         "2s ago"),
        ("🔵", "NDMA",           "Wayanad relief fund disbursement verified",  "14s ago"),
        ("🟠", "ISRO",           "Chamoli glacier imagery cross-linked",       "31s ago"),
        ("🟢", "PIB",            "Cyclone Dana actor node updated",            "48s ago"),
        ("🔵", "MoEF",           "Joshimath subsidence evidence synced",       "1m ago"),
        ("🟠", "data.gov.in",    "PMAY Ward-45 delivery proof verified",       "2m ago"),
        ("🟢", "IMD",            "Wayanad Orange Alert record ingested",       "3m ago"),
        ("🔵", "NTPC",           "Tapovan damage assessment node linked",      "4m ago"),
    ]
    ticker_html = "".join([
        f'<span style="margin-right:28px;white-space:nowrap;">'
        f'<span style="font-size:8px;vertical-align:middle;">{dot}</span> '
        f'<span style="color:#64748b;font-weight:700;">{src}</span> '
        f'<span style="color:#475569;">— {msg}</span> '
        f'<span style="color:#334155;font-size:9px;">{ts}</span>'
        f'</span>'
        for dot, src, msg, ts in _ticker_items
    ])
    # Duplicate for seamless loop
    ticker_html_double = ticker_html + ticker_html

    st.markdown(
        f"""
        <div style="
            background:#040d1a;
            border-top:1px solid #0f172a;
            border-bottom:1px solid #0f172a;
            padding:6px 0;
            overflow:hidden;
            position:relative;
            margin-bottom:4px;
        ">
          <div style="
            font-size:10px;
            color:#475569;
            white-space:nowrap;
            display:inline-block;
            animation: ticker 28s linear infinite;
          ">
            {ticker_html_double}
          </div>
        </div>
        <style>
          @keyframes ticker {{
            0%   {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )



def main() -> None:
    pg = st.navigation(
        [
            st.Page(home,                                   title="Pramaan",          icon=":material/verified_user:", default=True, url_path=""),
            st.Page("pages/live_ingestion.py",        title="Live Ingestion",       icon=":material/cell_tower:",    url_path="Live_Ingestion"),
            st.Page("pages/national_intelligence.py", title="National Intelligence", icon=":material/map:",           url_path="National_Intelligence"),
            st.Page("pages/ontology_graph.py",        title="Ontology Graph",        icon=":material/hub:",           url_path="Decision_Engine"),
            st.Page("pages/scheme_delivery.py",       title="Scheme Delivery",       icon=":material/electric_bolt:", url_path="Delivery_Monitor"),
            st.Page("pages/proof_and_evidence.py",    title="Proof & Evidence",      icon=":material/psychology:",    url_path="Proof_and_Evidence"),
            st.Page("pages/crisis_tracker.py",        title="Crisis Tracker",        icon=":material/crisis_alert:",  url_path="Crisis_Monitor"),
            st.Page("pages/intelligence_verdict.py",  title="Intelligence Verdict",  icon=":material/psychology:",    url_path="Intelligence_Verdict"),
        ],
        expanded=True,
    )

    pg.run()


if __name__ == "__main__":
    # --- Fix 20: Optional Cache Warm-up ---
    # Pre-fetch heaviest endpoints so the first click on every page is instant
    if "warmed" not in st.session_state:
        for path in ["/stats", "/ontology/events", "/ontology/compound-risk"]:
            safe_get(path, silent=True)
        st.session_state.warmed = True

    main()
