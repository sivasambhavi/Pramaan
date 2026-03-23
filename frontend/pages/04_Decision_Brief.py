"""
04_Decision_Brief.py — PRAMAAN Global Ontology Engine
AI-powered decision brief using Groq LLaMA 3.3 70B.
Synthesizes event subgraph data into a structured intelligence brief.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from collections import defaultdict
from groq import Groq
from utils.api import safe_get
from components.topnav import render_topnav

EVENTS = [
    ("EVT_WAYANAD_2024",       "Wayanad Landslide",           "#22c55e", "Climate",     "Jul 2024", "critical"),
    ("EVT_CYCLONE_DANA_2024",  "Cyclone Dana – Puri",         "#22c55e", "Climate",     "Oct 2024", "critical"),
    ("EVT_CHAMOLI_2021",       "Chamoli Glacier Burst",       "#22c55e", "Climate",     "Feb 2021", "critical"),
    ("EVT_JOSHIMATH_2023",     "Joshimath Subsidence",        "#06b6d4", "Governance",  "Jan 2023", "high"),
    ("EVT_ART370_2019",        "Article 370 Abrogation",      "#06b6d4", "Governance",  "Aug 2019", "high"),
    ("EVT_DELHI_FLOODS_2023",  "Delhi Yamuna Floods",         "#fb7185", "Society",     "Jul 2023", "critical"),
    ("EVT_COVID_WAVE2_2021",   "COVID Second Wave",           "#fb7185", "Society",     "Apr 2021", "critical"),
    ("EVT_MANIPUR_2023",       "Manipur Conflict",            "#f97316", "Defense",     "May 2023", "critical"),
    ("EVT_BALAKOT_2019",       "Balakot Airstrikes",          "#f97316", "Defense",     "Feb 2019", "critical"),
    ("EVT_TATA_SEMI_2024",     "Tata Semiconductor Fab",      "#38bdf8", "Economics",   "Feb 2024", "high"),
    ("EVT_IMEC_2023",          "IMEC Corridor Signing",       "#38bdf8", "Economics",   "Sep 2023", "high"),
    ("EVT_G20_INDIA_2023",     "G20 New Delhi Summit",        "#a78bfa", "Geopolitics", "Sep 2023", "high"),
    ("EVT_INDIA_CANADA_2023",  "India-Canada Diplomatic Row", "#a78bfa", "Geopolitics", "Sep 2023", "high"),
    ("EVT_CHANDRAYAAN3_2023",  "Chandrayaan-3 Landing",       "#facc15", "Technology",  "Aug 2023", "high"),
    ("EVT_ADITYAL1_2023",      "Aditya-L1 Solar Mission",     "#facc15", "Technology",  "Sep 2023", "high"),
]

DOMAIN_BULLET = {
    "Climate":     "🟢",
    "Defense":     "🟠",
    "Economics":   "🔵",
    "Society":     "🔴",
    "Governance":  "🟤",
    "Geopolitics": "🟣",
    "Technology":  "🟡",
}

SEV_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}
MONTH_MAP = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
             "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def _build_context(event_id: str, name: str, data: dict | None = None) -> str:
    """Fetch event subgraph and format as structured context for the LLM."""
    if data is None:
        data = safe_get(f"/ontology/events/{event_id}", silent=True) or {}
    event = data.get("event", {})
    impacts = data.get("impacts", [])
    actors = data.get("actors", [])
    schemes = data.get("schemes", [])
    evidence = data.get("evidence", [])
    connections = data.get("connections", [])
    regions = data.get("regions", [])

    lines = [f"EVENT: {name}", f"Date: {event.get('date', 'unknown')}", f"Severity: {event.get('severity', 'high')}"]

    if event.get("description"):
        lines.append(f"Description: {event['description']}")

    if regions:
        lines.append(f"Location: {', '.join(r.get('name','') for r in regions)}")

    if impacts:
        govdata_count = sum(1 for i in impacts if "data.gov.in" in (i.get("source") or ""))
        src_note = f"  [{govdata_count} from data.gov.in API]" if govdata_count else ""
        lines.append(f"\nMEASURED IMPACTS:{src_note}")
        for imp in impacts:
            val = imp.get('value', '')
            unit = imp.get('unit', '')
            itype = imp.get('type', '').replace('_', ' ').title()
            desc = imp.get('description', '')
            src = " [data.gov.in]" if "data.gov.in" in (imp.get("source") or "") else ""
            lines.append(f"  - {itype}: {val} {unit} — {desc}{src}")

    if actors:
        lines.append("\nKEY ACTORS:")
        for a in actors:
            lines.append(f"  - {a.get('name','')} ({a.get('type','')}): {a.get('role','')}")

    if schemes:
        lines.append("\nSCHEMES / FUNDING:")
        for s in schemes:
            amt = f"₹{s.get('budget_inr_cr', '')} Cr" if s.get('budget_inr_cr') else ""
            lines.append(f"  - {s.get('name', '')}: {amt} — {s.get('description','')[:80]}")

    if evidence:
        lines.append("\nEVIDENCE SOURCES:")
        for ev in evidence:
            lines.append(f"  - {ev.get('source','')} ({ev.get('type','')}: {ev.get('title','')[:60]})")

    if connections:
        lines.append("\nCROSS-DOMAIN LINKS:")
        for c in connections:
            lines.append(f"  - Connected to {c.get('name','')} ({c.get('domain','')}): {c.get('reason','')}")

    return "\n".join(lines)


def _generate_brief(context: str, name: str, query: str) -> str:
    """Call Groq LLaMA 3.3 70B to generate a decision brief."""
    client = Groq(api_key=GROQ_API_KEY)

    system_prompt = (
        "You are PRAMAAN — an AI-powered Global Ontology Engine that synthesizes verified government data "
        "into intelligence briefs for senior officials, policymakers, and researchers. "
        "Your output is precise, structured, evidence-driven, and free of speculation. "
        "Always cite specific numbers, actors, schemes, and sources from the context provided. "
        "When an impact is tagged [data.gov.in], explicitly note it is drawn from the official data.gov.in API. "
        "Format your response in clear sections using markdown."
    )

    user_prompt = (
        f"Using the verified ontology data below for **{name}**, answer the following:\n\n"
        f"**Query:** {query}\n\n"
        f"**Ontology Context:**\n```\n{context}\n```\n\n"
        "Structure your response with these sections:\n"
        "1. **Situation Summary** (2-3 sentences)\n"
        "2. **Key Impacts** (bullet points with real numbers)\n"
        "3. **Actors & Accountability** (who is responsible, what they did)\n"
        "4. **Cross-Domain Connections** (how this event connects to other domains)\n"
        "5. **Governance Gaps / Recommendations** (what is missing or needs attention)\n"
        "6. **Evidence Quality** (confidence assessment based on sources)\n\n"
        "Use only data from the context. Do not hallucinate facts."
    )

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1200,
        stream=True,
    )

    return completion


def page():
    st.set_page_config(page_title="Decision Brief – PRAMAAN", layout="wide")
    render_topnav(active_page="Decision Brief", show_sidebar=True)

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; }
    .stMarkdown p { font-size: 13.5px !important; color: #cbd5e1 !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #f97316 !important; }
    .stMarkdown ul li { color: #94a3b8 !important; font-size: 13px !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(56,189,248,0.7), 0 0 30px rgba(56,189,248,0.4), 0 0 50px rgba(56,189,248,0.2); }
        50%       { text-shadow: 0 0 25px rgba(56,189,248,1), 0 0 60px rgba(56,189,248,0.8), 0 0 100px rgba(56,189,248,0.5); }
    }
    div[data-testid="stExpander"] summary p { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state ──────────────────────────────────────────────────────────
    if "deep_link_brief" in st.session_state:
        raw = st.session_state.pop("deep_link_brief")
        valid_ids = {e[0] for e in EVENTS}
        if raw in valid_ids:
            st.session_state.brief_sel = raw

    if "brief_sel" not in st.session_state:
        st.session_state.brief_sel = EVENTS[0][0]

    # ── Sidebar — event navigator ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="font-size:13px;font-weight:700;color:#38bdf8;font-family:'Cinzel',serif;
                    letter-spacing:0.06em;margin-bottom:12px;padding-bottom:8px;
                    border-bottom:1px solid #1e293b;">
            EVENT NAVIGATOR
        </div>
        """, unsafe_allow_html=True)

        sort_by = st.selectbox(
            "Sort",
            ["Newest", "Oldest", "Severity"],
            label_visibility="collapsed",
            key="brief_sort",
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        SEV_ORDER = {"critical": 0, "high": 1, "medium": 2}

        def sort_key(e):
            month, year = e[4].split()
            ts = int(year) * 100 + MONTH_MAP.get(month, 0)
            return (SEV_ORDER.get(e[5], 9), -ts) if sort_by == "Severity" else (
                -ts if sort_by == "Newest" else ts
            )

        sorted_events = sorted(EVENTS, key=sort_key)
        domain_groups = defaultdict(list)
        for evt in sorted_events:
            domain_groups[evt[3]].append(evt)

        for domain, evts in domain_groups.items():
            bullet = DOMAIN_BULLET.get(domain, "●")
            expanded = any(e[0] == st.session_state.brief_sel for e in evts)
            with st.expander(f"{bullet} {domain}  ({len(evts)})", expanded=expanded):
                for (eid, ename, ecolor, edom, edate, esev) in evts:
                    is_sel = (eid == st.session_state.brief_sel)
                    sev_dot = SEV_COLOR.get(esev, "#64748b")
                    if st.button(
                        f"{'▶ ' if is_sel else ''}{ename}",
                        key=f"brief_btn_{eid}",
                        use_container_width=True,
                    ):
                        st.session_state.brief_sel = eid
                        st.rerun()
                    st.markdown(
                        f'<div style="font-size:9.5px;color:#475569;padding:0 4px 6px;'
                        f'margin-top:-8px;display:flex;align-items:center;gap:5px;">'
                        f'<span style="width:5px;height:5px;border-radius:50%;background:{sev_dot};'
                        f'flex-shrink:0;"></span>{edate} · {esev}</div>',
                        unsafe_allow_html=True,
                    )

    # ── Resolve selected event ─────────────────────────────────────────────────
    sel_evt = next((e for e in EVENTS if e[0] == st.session_state.brief_sel), EVENTS[0])
    event_id, name, color, domain, date, sev = sel_evt

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:8px;display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#38bdf8;font-family:'Cinzel',serif;letter-spacing:0.08em;white-space:nowrap;animation:glowPulse 2.5s ease-in-out infinite;">
        DECISION BRIEF
      </span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        AI-Powered Intelligence Brief &nbsp;·&nbsp; <span style="color:#475569;">Groq LLaMA 3.3 70B</span> &nbsp;·&nbsp; <span style="color:#334155;">Verified Ontology Data</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:12px;color:#475569;margin-bottom:8px;">'
        'Select an event and a query — PRAMAAN synthesises verified ontology data into a structured '
        'intelligence brief using Groq LLaMA 3.3 70B. Every fact is drawn from real government sources.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Event banner ───────────────────────────────────────────────────────────
    sev_badge_color = SEV_COLOR.get(sev, "#64748b")
    st.markdown(
        f'<div style="background:#0a1628;border:1px solid {color}44;border-left:4px solid {color};'
        f'border-radius:10px;padding:10px 16px;margin-bottom:12px;'
        f'display:flex;align-items:center;gap:12px;">'
        f'<div style="flex:1;">'
        f'<span style="font-size:14px;font-weight:700;color:{color};">{name}</span>'
        f'<span style="font-size:11px;color:#64748b;margin-left:12px;">{domain} · {date}</span>'
        f'</div>'
        f'<span style="background:{sev_badge_color}22;color:{sev_badge_color};font-weight:700;'
        f'font-size:10px;padding:2px 8px;border-radius:4px;border:1px solid {sev_badge_color}66;'
        f'text-transform:uppercase;letter-spacing:0.05em;">{sev}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Query selector ─────────────────────────────────────────────────────────
    default_queries = [
        "What are the key governance failures and accountability gaps?",
        "What is the total financial impact and fund utilization status?",
        "How effectively did government actors respond, and what is still pending?",
        "What cross-domain risks does this event expose for India?",
        "Summarize all verified evidence and assess data quality.",
        "Provide a quantitative impact assessment using official government data.",
        "What does this event reveal about India's strategic vulnerabilities?",
    ]

    col_q, col_btn = st.columns([3, 1], gap="medium")
    with col_q:
        query = st.selectbox("Intelligence Query", default_queries, index=0)
        custom_query = st.text_input("Or type a custom query", placeholder="e.g. What is the rehabilitation status?")
        final_query = custom_query.strip() if custom_query.strip() else query

    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        generate = st.button(
            "Generate Brief →",
            type="primary",
            use_container_width=True,
        )

    if generate:
        st.markdown("---")
        st.markdown(f"""
        <div style="background:#0a1628;border:1px solid {color}44;border-left:4px solid {color};
                    border-radius:10px;padding:12px 18px;margin-bottom:16px;">
          <div style="font-size:14px;font-weight:700;color:{color};">INTELLIGENCE BRIEF: {name.upper()}</div>
          <div style="font-size:11.5px;color:#475569;margin-top:4px;">
            Query: <span style="color:#94a3b8;font-style:italic;">{final_query}</span>
          </div>
          <div style="font-size:10.5px;color:#334155;margin-top:3px;">
            Model: LLaMA 3.3 70B · Source: PRAMAAN Neo4j Ontology · Groq AI
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("Fetching ontology data..."):
            data = safe_get(f"/ontology/events/{event_id}", silent=True) or {}
            context = _build_context(event_id, name, data=data)
            impacts_count  = len(data.get("impacts", []))
            evidence_count = len(data.get("evidence", []))
            govdata_impacts = sum(1 for i in data.get("impacts", []) if "data.gov.in" in (i.get("source") or ""))
            connections_count = len(data.get("connections", []))

        # Data provenance mini-bar
        st.markdown(
            f'<div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap;">'
            f'<span style="font-size:10.5px;color:#475569;">📊 <b style="color:#94a3b8;">{impacts_count}</b> impacts</span>'
            + (f'<span style="background:#0ea5e922;color:#0ea5e9;font-size:10px;font-weight:700;'
               f'padding:1px 7px;border-radius:3px;border:1px solid #0ea5e944;">'
               f'LIVE · {govdata_impacts} from data.gov.in</span>' if govdata_impacts else '')
            + f'<span style="font-size:10.5px;color:#475569;">📎 <b style="color:#94a3b8;">{evidence_count}</b> evidence nodes</span>'
            f'<span style="font-size:10.5px;color:#475569;">🔗 <b style="color:#94a3b8;">{connections_count}</b> cross-domain links</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        brief_placeholder = st.empty()
        full_text = ""

        with st.spinner("Generating brief with Groq LLaMA 3.3 70B..."):
            try:
                stream = _generate_brief(context, name, final_query)
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    full_text += delta
                    brief_placeholder.markdown(full_text)
            except Exception as e:
                st.error(f"Groq API error: {e}")
                return

        with st.expander("View raw ontology context used", expanded=False):
            st.code(context, language="text")

    else:
        st.markdown(f"""
        <div style="background:#0a1628;border:1px dashed #1e293b;border-radius:12px;
                    padding:40px;text-align:center;margin-top:20px;">
          <div style="font-size:2em;margin-bottom:12px;">🧠</div>
          <div style="font-size:14px;color:#475569;margin-bottom:6px;">Select an event and query above, then click Generate Brief</div>
          <div style="font-size:12px;color:#334155;">
            PRAMAAN will synthesize verified ontology data into a structured intelligence brief<br>
            using Groq LLaMA 3.3 70B · All facts drawn from real government sources
          </div>
        </div>
        """, unsafe_allow_html=True)


page()
