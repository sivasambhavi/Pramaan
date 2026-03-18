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

LOGO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Pramaan_logo.png")
)


def home() -> None:
    # Sidebar-only CSS (cannot go inside the iframe)
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #020b14 !important;
        color: #e2e8f0 !important;
    }
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    /* hide top padding gap */
    header[data-testid="stHeader"] { display:none !important; }

    /* sidebar */
    [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#0d1a2e 0%,#020b14 100%);
        border-right:1px solid rgba(71,85,105,0.35);
    }
    [data-testid="stSidebarNav"] a span { color:#94a3b8 !important; font-size:0.88em !important; font-weight:500 !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] span { color:#f97316 !important; font-weight:700 !important; }
    [data-testid="stSidebarNav"] a svg { color:#64748b !important; fill:#64748b !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] svg { color:#f97316 !important; fill:#f97316 !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background:rgba(249,115,22,0.08) !important;
        border-radius:8px !important; border-left:3px solid #f97316 !important;
    }
    [data-testid="stSidebarNav"] a { transition:background 0.15s ease !important; border-radius:6px !important; }
    [data-testid="stSidebarNav"] a:hover { background:rgba(71,85,105,0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

    # Encode logo as base64
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as _f:
            logo_b64 = base64.b64encode(_f.read()).decode()
    logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""

    # Everything in one iframe — flex column fills viewport, nothing scrolls
    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@700;800&family=Cinzel:wght@700;900&display=swap" rel="stylesheet">
    <style>
      *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
      html, body {{
        width: 100%; height: 100%;
        background: transparent;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
        overflow: hidden;
      }}

      .page {{
        width: 100%; height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-evenly;
        padding: 16px 24px 10px;
      }}

      /* ── Logo ── */
      .logo-img {{
        width: 180px; height: 180px;
        object-fit: contain;
        animation: glowPulse 3s ease-in-out infinite;
        image-rendering: -webkit-optimize-contrast;
      }}
      @keyframes glowPulse {{
        0%,100% {{ filter: drop-shadow(0 0 16px rgba(249,115,22,0.4)); }}
        50%      {{ filter: drop-shadow(0 0 32px rgba(249,115,22,0.7)); }}
      }}

      /* ── Title block ── */
      .title-block {{ text-align: center; }}
      .hero-title {{
        font-family: 'Cinzel', serif;
        font-size: 4.4em; font-weight: 900;
        background: linear-gradient(
          105deg,
          #f97316 0%,
          #fb923c 28%,
          #fff4e6 46%,
          #ffe9b0 52%,
          #fb923c 68%,
          #38bdf8 100%
        );
        background-size: 250% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1; margin-bottom: 8px;
        letter-spacing: 0.18em;
        animation: fadeDown 0.5s ease both, titleShine 3.5s linear 0.8s infinite;
      }}
      @keyframes titleShine {{
        0%   {{ background-position: 200% center; }}
        100% {{ background-position: -50% center; }}
      }}
      .hero-tagline {{
        font-size: 1.05em; color: #64748b; letter-spacing: 0.04em;
        animation: fadeDown 0.5s 0.1s ease both;
      }}
      @keyframes fadeDown {{
        from {{ opacity:0; transform:translateY(-10px); }}
        to   {{ opacity:1; transform:translateY(0); }}
      }}

      /* ── Explainer ── */
      .explainer {{
        font-size: 0.82em; color: #475569; text-align: center;
        line-height: 1.65; max-width: 500px;
        padding: 12px 18px;
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(71,85,105,0.3);
        border-radius: 10px;
        animation: fadeDown 0.5s 0.18s ease both;
      }}

      /* ── Stats bar ── */
      .stats-wrap {{
        width: 100%;
        background: rgba(13,20,35,0.85);
        border: 1px solid rgba(249,115,22,0.22);
        border-radius: 14px;
        padding: 18px 12px;
        display: flex; justify-content: center; gap: 0;
        animation: fadeUp 0.5s 0.25s ease both;
      }}
      @keyframes fadeUp {{
        from {{ opacity:0; transform:translateY(10px); }}
        to   {{ opacity:1; transform:translateY(0); }}
      }}
      .stat {{
        flex: 1; text-align: center;
        padding: 0 12px;
        border-right: 1px solid rgba(71,85,105,0.3);
      }}
      .stat:last-child {{ border-right: none; }}
      .stat-val {{
        font-family: 'Outfit', sans-serif;
        font-size: 2.2em; font-weight: 800;
        color: #f97316; line-height: 1; letter-spacing: -0.02em;
      }}
      .stat-lbl {{
        font-size: 0.62em; color: #475569;
        text-transform: uppercase; letter-spacing: 0.08em;
        font-weight: 600; margin-top: 4px;
      }}
      .stat-sub {{ font-size: 0.64em; color: #334155; margin-top: 2px; }}

      /* ── CTA ── */
      .cta-wrap {{ text-align: center; animation: fadeUp 0.5s 0.35s ease both; }}
      .cta-btn {{
        display: inline-block;
        background: linear-gradient(135deg,#f97316,#ea580c);
        color: #fff; text-decoration: none;
        border-radius: 12px; padding: 13px 52px;
        font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1em;
        letter-spacing: 0.02em;
        box-shadow: 0 4px 20px rgba(249,115,22,0.4);
        transition: box-shadow 0.2s ease, transform 0.15s ease;
      }}
      .cta-btn:hover {{
        box-shadow: 0 8px 32px rgba(249,115,22,0.6);
        transform: translateY(-2px);
      }}

      /* ── Badges ── */
      .badge-row {{
        display: flex; justify-content: center; gap: 8px; flex-wrap: wrap;
        animation: fadeUp 0.5s 0.42s ease both;
      }}
      .badge {{
        background: rgba(15,23,42,0.9); border: 1px solid rgba(71,85,105,0.5);
        border-radius: 20px; padding: 4px 12px; font-size: 0.7em;
        color: #94a3b8; font-weight: 600; letter-spacing: 0.04em;
        display: inline-flex; align-items: center; gap: 5px;
        transition: border-color 0.2s ease, color 0.2s ease;
        cursor: default;
      }}
      .badge:hover {{ border-color: rgba(249,115,22,0.4); color: #f97316; }}
      .dot {{ width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }}

      /* ── Footer ── */
      .footer {{
        font-size: 0.68em; color: #334155; text-align: center;
        border-top: 1px solid rgba(71,85,105,0.2);
        padding-top: 8px; width: 100%;
        animation: fadeUp 0.5s 0.5s ease both;
      }}
    </style>
    </head>
    <body>
    <div class="page">

      <!-- logo -->
      {"<img class='logo-img' src='" + logo_src + "' />" if logo_src else ""}

      <!-- title -->
      <div class="title-block">
        <div class="hero-title">PRAMAAN</div>
        <div class="hero-tagline">One Graph That Proves What India Built</div>
      </div>

      <!-- explainer -->
      <div class="explainer">
        Public money funds roads, drains, and housing across India —
        but citizens rarely know if the work was done.
        PRAMAAN links every scheme, contractor, and asset to verifiable
        field evidence so any official or citizen can trace delivery in seconds.
      </div>

      <!-- stats -->
      <div class="stats-wrap">
        <div class="stat"><div class="stat-val" id="s1">0</div><div class="stat-lbl">Assets Tracked</div><div class="stat-sub">across Delhi wards</div></div>
        <div class="stat"><div class="stat-val" id="s2">0</div><div class="stat-lbl">Schemes Mapped</div><div class="stat-sub">AMRUT · PMAY · SBM</div></div>
        <div class="stat"><div class="stat-val" id="s3">0</div><div class="stat-lbl">Evidence Nodes</div><div class="stat-sub">photos + reports</div></div>
        <div class="stat"><div class="stat-val" id="s4">0</div><div class="stat-lbl">Graph Nodes</div><div class="stat-sub">live Neo4j knowledge graph</div></div>
      </div>

      <!-- CTA -->
      <div class="cta-wrap">
        <a class="cta-btn" href="/Ward_Map" target="_self">Enter Dashboard</a>
      </div>

      <!-- badges -->
      <div class="badge-row">
        <span class="badge"><span class="dot" style="background:#22c55e"></span>Neo4j Knowledge Graph</span>
        <span class="badge"><span class="dot" style="background:#38bdf8"></span>FastAPI Backend</span>
        <span class="badge"><span class="dot" style="background:#f97316"></span>Streamlit Frontend</span>
        <span class="badge"><span class="dot" style="background:#a78bfa"></span>Groq · LLaMA 3.3 70B</span>
        <span class="badge"><span class="dot" style="background:#fb923c"></span>data.gov.in Live Data</span>
      </div>

      <!-- footer -->
      <div class="footer">
        Built for <strong style="color:#475569">India Innovates 2026</strong>
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
        countUp(document.getElementById('s1'), 56,  1200);
        countUp(document.getElementById('s2'), 4,   800);
        countUp(document.getElementById('s3'), 14,  1000);
        countUp(document.getElementById('s4'), 223, 1400);
      }}, 400);
    </script>
    </body>
    </html>
    """, height=720, scrolling=False)


def main() -> None:
    pg = st.navigation(
        {
            "Home": [
                st.Page(home, title="Pramaan", icon=":material/verified_user:", default=True),
            ],
            "Delivery Intelligence": [
                st.Page("pages/01_Ward_Map.py",            title="Ward Map",             icon=":material/map:"),
                st.Page("pages/02_Proof_Chain.py",          title="Proof Chain",          icon=":material/link:"),
                st.Page("pages/03_Live_Ingestion.py",       title="Live Ingestion",       icon=":material/electric_bolt:"),
                st.Page("pages/04_Micro_Accountability.py", title="Micro Accountability", icon=":material/mark_chat_read:"),
            ],
        },
        expanded=True,
    )

    # Each page manages its own sidebar — no global sidebar injection here

    pg.run()


if __name__ == "__main__":
    main()
