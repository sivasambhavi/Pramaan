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
    _stats       = _fetch_stats()
    _events      = _stats.get("events",      0)
    _actors      = _stats.get("actors",      0)
    _evidence    = _stats.get("evidence",    0)
    _total_nodes = _stats.get("total_nodes", 0)

    # Encode logo as base64
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as _f:
            logo_b64 = base64.b64encode(_f.read()).decode()
    logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""

    # Hero in iframe with JS countUp animation
    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@700;800&family=Cinzel:wght@700;900&display=swap" rel="stylesheet">
    <style>
      *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
      html, body {{ width: 100%; height: 100%; background: transparent; font-family: 'Inter', sans-serif; color: #e2e8f0; overflow: hidden; }}
      .page {{ width: 100%; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: space-evenly; padding: 8px 24px 6px; }}
      .logo-wrap {{ width: 130px; height: 130px; border-radius: 22px; background: #020b14; display: flex; align-items: center; justify-content: center; animation: glowPulse 3s ease-in-out infinite; overflow: hidden; }}
      .logo-img {{ width: 100%; height: 100%; object-fit: cover; mix-blend-mode: screen; image-rendering: -webkit-optimize-contrast; }}
      @keyframes glowPulse {{ 0%,100% {{ box-shadow: 0 0 20px rgba(249,115,22,0.35); }} 50% {{ box-shadow: 0 0 40px rgba(249,115,22,0.65); }} }}
      .title-block {{ text-align: center; }}
      .hero-title {{ font-family: 'Cinzel', serif; font-size: 3.4em; font-weight: 900; background: linear-gradient(105deg,#f97316 0%,#fb923c 28%,#fff4e6 46%,#ffe9b0 52%,#fb923c 68%,#38bdf8 100%); background-size: 250% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1; margin-bottom: 8px; letter-spacing: 0.18em; animation: fadeDown 0.5s ease both, titleShine 3.5s linear 0.8s infinite; }}
      @keyframes titleShine {{ 0% {{ background-position: 200% center; }} 100% {{ background-position: -50% center; }} }}
      .hero-tagline {{ font-size: 0.92em; color: #64748b; letter-spacing: 0.04em; animation: fadeDown 0.5s 0.1s ease both; }}
      @keyframes fadeDown {{ from {{ opacity:0; transform:translateY(-10px); }} to {{ opacity:1; transform:translateY(0); }} }}
      .explainer {{ font-size: 0.78em; color: #475569; text-align: center; line-height: 1.55; max-width: 500px; padding: 8px 16px; background: rgba(15,23,42,0.6); border: 1px solid rgba(71,85,105,0.3); border-radius: 10px; animation: fadeDown 0.5s 0.18s ease both; }}
      .stats-wrap {{ width: 80%; background: rgba(13,20,35,0.85); border: 1px solid rgba(249,115,22,0.22); border-radius: 12px; padding: 6px 8px; display: flex; justify-content: center; gap: 0; animation: fadeUp 0.5s 0.25s ease both; }}
      @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
      .stat {{ flex: 1; text-align: center; padding: 0 12px; border-right: 1px solid rgba(71,85,105,0.3); }}
      .stat:last-child {{ border-right: none; }}
      .stat-val {{ font-family: 'Outfit', sans-serif; font-size: 1.8em; font-weight: 800; line-height: 1; letter-spacing: -0.02em; }}
      .stat-lbl {{ font-size: 0.62em; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-top: 4px; }}
      .stat-sub {{ font-size: 0.64em; color: #334155; margin-top: 2px; }}
      .badge-row {{ display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; animation: fadeUp 0.5s 0.42s ease both; }}
      .badge {{ background: rgba(15,23,42,0.9); border: 1px solid rgba(71,85,105,0.5); border-radius: 20px; padding: 3px 9px; font-size: 0.62em; color: #94a3b8; font-weight: 600; letter-spacing: 0.03em; display: inline-flex; align-items: center; gap: 4px; cursor: default; white-space: nowrap; }}
      .badge:hover {{ border-color: rgba(249,115,22,0.4); color: #f97316; }}
      .dot {{ width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }}
      .footer {{ font-size: 0.68em; color: #94a3b8; text-align: center; width: 100%; animation: fadeUp 0.5s 0.5s ease both; }}
    </style>
    </head>
    <body>
    <div class="page">
      {"<div class='logo-wrap'><img class='logo-img' src='" + logo_src + "' /></div>" if logo_src else ""}
      <div class="title-block">
        <div class="hero-title">PRAMAAN</div>
        <div class="hero-tagline">AI-Powered <span style="color:#f97316;-webkit-text-fill-color:#f97316;">Global Ontology Engine</span> &nbsp;·&nbsp; 7 Domains</div>
      </div>
      <div class="explainer">
        PRAMAAN maps {_events} high-impact events — from Wayanad landslides to the Russia–Ukraine War and Gaza Red Sea crisis —
        across 7 domains: Climate, Economics, Geopolitics, Defense, Technology, Society, and Governance.
        Every node is real. Every edge is evidence-backed.
      </div>
      <div class="stats-wrap">
        <div class="stat"><div class="stat-val" id="s1" style="color:#f97316">0</div><div class="stat-lbl">Events Tracked</div><div class="stat-sub">across 7 domains</div></div>
        <div class="stat"><div class="stat-val" id="s2" style="color:#22c55e">0</div><div class="stat-lbl">Key Actors</div><div class="stat-sub">NDMA · Army · ISRO · MHA</div></div>
        <div class="stat"><div class="stat-val" id="s3" style="color:#38bdf8">0</div><div class="stat-lbl">Evidence Nodes</div><div class="stat-sub">PIB · NDMA · ISRO · IMD</div></div>
        <div class="stat"><div class="stat-val" id="s4" style="color:#a78bfa">0</div><div class="stat-lbl">Graph Nodes</div><div class="stat-sub">live Neo4j knowledge graph</div></div>
      </div>
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
    <script>
      function countUp(el, target, dur) {{
        var start = 0, step = target / (dur / 16);
        var t = setInterval(function() {{
          start = Math.min(start + step, target);
          el.textContent = Math.floor(start);
          if (start >= target) clearInterval(t);
        }}, 16);
      }}
      setTimeout(function() {{
        countUp(document.getElementById('s1'), {_events},      400);
        countUp(document.getElementById('s2'), {_actors},      500);
        countUp(document.getElementById('s3'), {_evidence},    500);
        countUp(document.getElementById('s4'), {_total_nodes}, 700);
      }}, 400);
    </script>
    </body>
    </html>
    """, height=580, scrolling=False)

    # Button in main DOM — navigates correctly
    st.html("""
    <div style="display:flex;justify-content:center;margin:6px 0 10px;">
      <a href="/Intelligence_Map" style="background:linear-gradient(135deg,#f97316,#ea580c);color:#fff;text-decoration:none;border-radius:12px;padding:10px 44px;font-family:Outfit,sans-serif;font-weight:700;font-size:1em;letter-spacing:0.02em;box-shadow:0 4px 20px rgba(249,115,22,0.4);display:inline-block;">
        Enter Dashboard &nbsp;→
      </a>
    </div>
    """)


def main() -> None:
    pg = st.navigation(
        [
            st.Page(home,                                   title="Pramaan",          icon=":material/verified_user:", default=True, url_path=""),
            st.Page("pages/01_Intelligence_Map.py",         title="Intelligence Map", icon=":material/map:",           url_path="Intelligence_Map"),
            st.Page("pages/02_Ontology_Graph.py",           title="Ontology Graph",   icon=":material/hub:",           url_path="Ontology_Graph"),
            st.Page("pages/03_Live_Feed.py",                title="Live Feed",        icon=":material/electric_bolt:", url_path="Live_Feed"),
            st.Page("pages/04_Decision_Brief.py",           title="Decision Brief",   icon=":material/psychology:",    url_path="Decision_Brief"),
        ],
        expanded=True,
    )

    pg.run()


if __name__ == "__main__":
    main()
