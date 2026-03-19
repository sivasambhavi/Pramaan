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

LOGO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Pramaan_logo.png")
)


def home() -> None:
    render_topnav(active_page=None)
    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    /* No scrolling on landing page */
    html, body, .main, section[data-testid="stMain"], [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
    }
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@600;700;800&family=Cinzel:wght@700;900&display=swap" rel="stylesheet">
    <style>
      *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
      html, body {{
        width: 100%; height: 100%;
        background: transparent;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
        overflow: hidden;
      }}

      /* ── Page shell ── */
      .page {{
        width: 100%; height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0;
        padding: 0 40px 12px;
        max-width: 860px;
        margin: 0 auto;
      }}
      .page > * {{ flex-shrink: 0; }}
      .spacer {{ flex: 1; }}

      /* ────────────────────────────────
         HERO — logo + title grouped
      ──────────────────────────────── */
      .hero {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
        animation: fadeDown 0.5s ease both;
      }}
      .logo-wrap {{
        width: 120px; height: 120px;
        border-radius: 24px;
        background: #020b14;
        display: flex; align-items: center; justify-content: center;
        animation: glowPulse 3s ease-in-out infinite;
        overflow: hidden;
        flex-shrink: 0;
      }}
      .logo-img {{
        width: 100%; height: 100%;
        object-fit: cover;
        mix-blend-mode: screen;
        image-rendering: -webkit-optimize-contrast;
      }}
      @keyframes glowPulse {{
        0%,100% {{ box-shadow: 0 0 20px rgba(249,115,22,0.3); }}
        50%      {{ box-shadow: 0 0 44px rgba(249,115,22,0.6); }}
      }}
      .title-block {{ text-align: center; }}
      .hero-title {{
        font-family: 'Cinzel', serif;
        font-size: 3.6em; font-weight: 900;
        background: linear-gradient(105deg, #f97316 0%, #fb923c 28%, #fff4e6 46%, #ffe9b0 52%, #fb923c 68%, #38bdf8 100%);
        background-size: 250% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        letter-spacing: 0.18em;
        animation: titleShine 3.5s linear 0.6s infinite;
      }}
      @keyframes titleShine {{
        0%   {{ background-position: 200% center; }}
        100% {{ background-position: -50% center; }}
      }}
      .hero-tagline {{
        margin-top: 10px;
        font-size: 1em; font-weight: 500;
        color: #64748b; letter-spacing: 0.03em;
      }}
      @keyframes fadeDown {{
        from {{ opacity:0; transform:translateY(-12px); }}
        to   {{ opacity:1; transform:translateY(0); }}
      }}

      /* ────────────────────────────────
         MISSION
      ──────────────────────────────── */
      .mission {{
        text-align: center;
        max-width: 560px;
        animation: fadeDown 0.5s 0.12s ease both;
      }}
      .mission-label {{
        font-size: 0.6em; font-weight: 700;
        letter-spacing: 0.14em; text-transform: uppercase;
        color: #334155; margin-bottom: 10px;
      }}
      .explainer {{
        font-size: 0.82em; color: #475569; text-align: center;
        line-height: 1.65;
        padding: 14px 20px;
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(71,85,105,0.3);
        border-radius: 10px;
      }}

      /* ────────────────────────────────
         STATS
      ──────────────────────────────── */
      .stats-wrap {{
        width: 100%;
        background: rgba(13,20,35,0.9);
        border: 1px solid rgba(249,115,22,0.2);
        border-radius: 16px;
        padding: 16px 8px;
        display: flex; justify-content: center; gap: 0;
        animation: fadeUp 0.5s 0.22s ease both;
      }}
      @keyframes fadeUp {{
        from {{ opacity:0; transform:translateY(10px); }}
        to   {{ opacity:1; transform:translateY(0); }}
      }}
      .stat {{
        flex: 1; text-align: center;
        padding: 4px 16px;
        border-right: 1px solid rgba(71,85,105,0.25);
      }}
      .stat:last-child {{ border-right: none; }}
      .stat-val {{
        font-family: 'Outfit', sans-serif;
        font-size: 2em; font-weight: 800;
        line-height: 1; letter-spacing: -0.02em;
      }}
      .stat-lbl {{
        font-size: 0.65em; color: #475569;
        text-transform: uppercase; letter-spacing: 0.09em;
        font-weight: 600; margin-top: 6px;
      }}
      .stat-sub {{ font-size: 0.62em; color: #2d3f52; margin-top: 3px; }}

      /* ────────────────────────────────
         CTA + BADGES grouped
      ──────────────────────────────── */
      .cta-area {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        animation: fadeUp 0.5s 0.32s ease both;
      }}
      .cta-btn {{
        display: inline-block;
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: #fff; text-decoration: none;
        border-radius: 14px; padding: 13px 52px;
        font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.05em;
        letter-spacing: 0.04em;
        box-shadow: 0 4px 24px rgba(249,115,22,0.38);
        transition: box-shadow 0.2s ease, transform 0.15s ease;
      }}
      .cta-btn:hover {{
        box-shadow: 0 8px 36px rgba(249,115,22,0.6);
        transform: translateY(-2px);
      }}
      .badge-row {{
        display: flex; justify-content: center; gap: 8px; flex-wrap: wrap;
      }}
      .badge {{
        background: rgba(15,23,42,0.85); border: 1px solid rgba(71,85,105,0.45);
        border-radius: 20px; padding: 4px 11px; font-size: 0.63em;
        color: #64748b; font-weight: 600; letter-spacing: 0.03em;
        display: inline-flex; align-items: center; gap: 5px;
        transition: border-color 0.2s ease, color 0.2s ease;
        cursor: default; white-space: nowrap;
      }}
      .badge:hover {{ border-color: rgba(249,115,22,0.35); color: #f97316; }}
      .dot {{ width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }}

      /* ────────────────────────────────
         FOOTER
      ──────────────────────────────── */
      .footer {{
        width: 100%;
        font-size: 0.67em; color: #1e2d3d; text-align: center;
        border-top: 1px solid rgba(71,85,105,0.15);
        padding-top: 12px;
        animation: fadeUp 0.5s 0.44s ease both;
      }}
    </style>
    </head>
    <body>
    <div class="page">

      <!-- HERO: logo + title + tagline -->
      <div class="hero">
        {"<div class='logo-wrap'><img class='logo-img' src='" + logo_src + "' /></div>" if logo_src else ""}
        <div class="title-block">
          <div class="hero-title">PRAMAAN</div>
          <div class="hero-tagline">One Graph That <span style="color:#f97316;-webkit-text-fill-color:#f97316;">Proves</span> What India Built</div>
        </div>
      </div>

      <div class="spacer"></div>

      <!-- MISSION -->
      <div class="mission">
        <div class="mission-label">About · Mission</div>
        <div class="explainer">
          Public money funds roads, drains, and housing across India —
          but citizens rarely know if the work was done.
          PRAMAAN links every scheme, contractor, and asset to verifiable
          field evidence so any official or citizen can trace delivery in seconds.
        </div>
      </div>

      <div class="spacer"></div>

      <!-- STATS -->
      <div class="stats-wrap">
        <div class="stat"><div class="stat-val" id="s1" style="color:#f97316">0</div><div class="stat-lbl">Assets Tracked</div><div class="stat-sub">across Delhi wards</div></div>
        <div class="stat"><div class="stat-val" id="s2" style="color:#22c55e">0</div><div class="stat-lbl">Schemes Mapped</div><div class="stat-sub">AMRUT · PMAY · SBM</div></div>
        <div class="stat"><div class="stat-val" id="s3" style="color:#38bdf8">0</div><div class="stat-lbl">Evidence Nodes</div><div class="stat-sub">photos + reports</div></div>
        <div class="stat"><div class="stat-val" id="s4" style="color:#a78bfa">0</div><div class="stat-lbl">Graph Nodes</div><div class="stat-sub">live Neo4j knowledge graph</div></div>
      </div>

      <div class="spacer"></div>

      <!-- CTA + BADGES -->
      <div class="cta-area">
        <a class="cta-btn" href="/Ward_Map" target="_self">Enter Dashboard &nbsp;→</a>
        <div class="badge-row">
          <span class="badge"><span class="dot" style="background:#22c55e"></span>Neo4j Knowledge Graph</span>
          <span class="badge"><span class="dot" style="background:#38bdf8"></span>FastAPI Backend</span>
          <span class="badge"><span class="dot" style="background:#f97316"></span>Streamlit Frontend</span>
          <span class="badge"><span class="dot" style="background:#a78bfa"></span>Groq · LLaMA 3.3 70B</span>
          <span class="badge"><span class="dot" style="background:#fb923c"></span>data.gov.in Live Data</span>
        </div>
      </div>

      <div class="spacer"></div>

      <!-- FOOTER -->
      <div class="footer">
        Built for <strong style="color:#2d3f52">India Innovates 2026</strong>
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

      // Resize this iframe to fill the viewport (minus topnav spacer height)
      (function resizeIframe() {{
        try {{
          var avail = window.parent.innerHeight - 62;
          var frame = window.frameElement;
          if (frame && avail > 200) {{
            frame.style.height = avail + 'px';
            frame.style.minHeight = avail + 'px';
          }}
        }} catch(e) {{}}
      }})();
      window.addEventListener('resize', function() {{
        try {{
          var avail = window.parent.innerHeight - 62;
          var frame = window.frameElement;
          if (frame && avail > 200) {{
            frame.style.height = avail + 'px';
            frame.style.minHeight = avail + 'px';
          }}
        }} catch(e) {{}}
      }});
    </script>
    </body>
    </html>
    """, height=900, scrolling=False)


def main() -> None:
    pg = st.navigation(
        [
            st.Page(home,                                   title="Pramaan",             icon=":material/verified_user:", default=True, url_path=""),
            st.Page("pages/01_Ward_Map.py",                 title="Ward Map",             icon=":material/map:",           url_path="Ward_Map"),
            st.Page("pages/02_Proof_Chain.py",              title="Proof Chain",          icon=":material/link:",          url_path="Proof_Chain"),
            st.Page("pages/03_Live_Ingestion.py",           title="Live Ingestion",       icon=":material/electric_bolt:", url_path="Live_Ingestion"),
            st.Page("pages/04_Micro_Accountability.py",     title="Micro Accountability", icon=":material/mark_chat_read:", url_path="Micro_Accountability"),
        ],
        expanded=True,
    )

    # Each page manages its own sidebar — no global sidebar injection here

    pg.run()


if __name__ == "__main__":
    main()
