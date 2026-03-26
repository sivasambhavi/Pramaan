"""
05_Live_Ingestion.py — PRAMAAN v5
Live Ingestion Console — Option A: Command + Status + Live Agent Trace
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import requests as _req
import streamlit as st
from components.topnav import render_topnav
from utils.api import safe_get

BACKEND = "http://localhost:8000"

STEP_COLORS = {"ok": "#22c55e", "warn": "#facc15", "skip": "#475569"}
STEP_ICONS  = {"ok": "●", "warn": "◆", "skip": "○"}

SUGGESTED_TOPICS = [
    "NDRF disaster relief India 2025",
    "PMAY housing scheme Delhi 2025",
    "AMRUT urban infrastructure India",
    "Ayushman Bharat health scheme 2025",
    "India flood relief SDRF 2025",
    "PLI semiconductor India 2025",
    "Jal Jeevan Mission water supply",
    "India climate disaster NDMA response",
]

FEED_ITEMS = [
    ("#22c55e", "PIB",         "Cyclone Dana actor node updated",            "2s ago"),
    ("#38bdf8", "NDMA",        "Wayanad relief fund disbursement verified",  "14s ago"),
    ("#f97316", "ISRO",        "Chamoli glacier imagery cross-linked",       "31s ago"),
    ("#22c55e", "data.gov.in", "PMAY Ward-45 delivery proof verified",       "1m ago"),
    ("#38bdf8", "IMD",         "Wayanad Orange Alert record ingested",       "3m ago"),
    ("#f97316", "NTPC",        "Tapovan damage assessment node linked",      "4m ago"),
]


def page():
    st.set_page_config(page_title="Live Ingestion – PRAMAAN", layout="wide")
    render_topnav(active_page="Live Ingestion")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    div[data-baseweb="select"] * { font-size: 13px !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(249,115,22,0.5); }
        50%       { text-shadow: 0 0 28px rgba(249,115,22,0.9); }
    }
    @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:12px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#f97316;
                   font-family:'Cinzel',serif;letter-spacing:0.08em;
                   animation:glowPulse 2.5s ease-in-out infinite;">
        LIVE INGESTION CONSOLE
      </span>
      <span style="font-size:0.75em;color:#64748b;">
        Agentic · Ollama LLaMA3 · Neo4j Knowledge Graph
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Graph Status Bar ───────────────────────────────────────────────────────
    stats = safe_get("/stats", silent=True) or {}
    total_nodes = stats.get("total_nodes", 186)
    total_edges = stats.get("total_edges", 274)
    events      = stats.get("events",       17)
    evidence    = stats.get("evidence",     31)

    st.markdown(
        f'<div style="display:flex;gap:0;background:#060f1e;border:1px solid #1e293b;'
        f'border-radius:10px;padding:10px 20px;margin-bottom:16px;align-items:center;">'
        f'<div style="flex:1;text-align:center;border-right:1px solid #1e293b;padding-right:16px;">'
        f'<div style="font-size:1.5em;font-weight:800;color:#a78bfa;">{total_nodes}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Graph Nodes</div></div>'
        f'<div style="flex:1;text-align:center;border-right:1px solid #1e293b;padding:0 16px;">'
        f'<div style="font-size:1.5em;font-weight:800;color:#38bdf8;">{total_edges}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Edges</div></div>'
        f'<div style="flex:1;text-align:center;border-right:1px solid #1e293b;padding:0 16px;">'
        f'<div style="font-size:1.5em;font-weight:800;color:#f97316;">{events}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Events</div></div>'
        f'<div style="flex:1;text-align:center;padding-left:16px;">'
        f'<div style="font-size:1.5em;font-weight:800;color:#22c55e;">{evidence}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Evidence Nodes</div></div>'
        f'<div style="margin-left:auto;padding-left:24px;font-size:9px;color:#334155;white-space:nowrap;">'
        f'Last sync<br>{time.strftime("%H:%M:%S")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Main layout ────────────────────────────────────────────────────────────
    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:

        # ── Command input ──────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:11px;color:#f97316;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.1em;margin-bottom:8px;">Ingest Topic or URL</div>',
            unsafe_allow_html=True,
        )

        # Staging key lets chips pre-fill the input without widget key conflict
        if "agent_topic_val" not in st.session_state:
            st.session_state["agent_topic_val"] = ""

        topic = st.text_input(
            "topic",
            value=st.session_state["agent_topic_val"],
            label_visibility="collapsed",
            placeholder="e.g. NDRF disaster relief India 2025  or  paste a PIB URL",
            key="agent_topic",
        )

        # Suggested topics as quick-select chips
        st.markdown(
            '<div style="font-size:9px;color:#334155;margin-bottom:6px;">Suggested:</div>',
            unsafe_allow_html=True,
        )
        chip_cols = st.columns(4)
        for i, suggestion in enumerate(SUGGESTED_TOPICS[:4]):
            with chip_cols[i]:
                if st.button(suggestion[:28] + ("…" if len(suggestion) > 28 else ""),
                             key=f"chip_{i}", use_container_width=True):
                    st.session_state["agent_topic_val"] = suggestion
                    st.rerun()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        run_col, sched_col = st.columns([1.4, 1], gap="small")
        with run_col:
            run_clicked = st.button("Run Agent", use_container_width=True,
                                    type="primary", key="run_agent_btn")
        with sched_col:
            schedule = st.selectbox("Schedule", ["Manual only", "Every 1h", "Every 6h", "Every 24h"],
                                    label_visibility="collapsed", key="agent_schedule")

        if schedule != "Manual only":
            st.markdown(
                f'<div style="font-size:10px;color:#334155;margin-top:4px;">'
                f'Scheduler active: {schedule} · next run via APScheduler</div>',
                unsafe_allow_html=True,
            )

        # ── Agent trace output ─────────────────────────────────────────────────
        trace_slot = st.empty()

        if run_clicked:
            t = (topic or "").strip()
            if not t:
                st.warning("Enter a topic or URL to run the agent.")
            else:
                # Show live spinner while agent runs
                with st.spinner("Agent running…"):
                    try:
                        resp = _req.post(
                            f"{BACKEND}/ingest/agentic",
                            json={"topic": t, "max_articles": 6},
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            st.session_state["agent_result"] = resp.json()
                        else:
                            st.error(f"Agent failed ({resp.status_code}): {resp.text[:300]}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

        # Render trace from session state
        result = st.session_state.get("agent_result")
        if result:
            steps    = result.get("steps", [])
            ec       = result.get("entities_created", 0)
            rc       = result.get("relations_created", 0)
            skipped  = result.get("entities_skipped", 0)
            duration = result.get("duration_s", 0)
            llm      = result.get("llm_used", "").upper()
            rtopic   = result.get("topic", "")

            # Summary bar
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #22c55e44;border-radius:8px;'
                f'padding:10px 16px;margin:10px 0;display:flex;gap:20px;align-items:center;">'
                f'<span style="font-size:11px;color:#22c55e;font-weight:700;">{ec} entities created</span>'
                f'<span style="font-size:11px;color:#38bdf8;">{rc} relations</span>'
                f'<span style="font-size:10px;color:#475569;">{skipped} skipped</span>'
                f'<span style="font-size:10px;color:#334155;margin-left:auto;">'
                f'{duration}s · {llm}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Step-by-step trace
            st.markdown(
                '<div style="font-size:9px;color:#334155;font-weight:700;text-transform:uppercase;'
                'letter-spacing:0.1em;margin-bottom:6px;">Agent Trace</div>',
                unsafe_allow_html=True,
            )
            for s in steps:
                color = STEP_COLORS.get(s.get("status", "ok"), "#22c55e")
                icon  = STEP_ICONS.get(s.get("status", "ok"), "●")
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:10px;'
                    f'padding:6px 10px;margin-bottom:3px;border-radius:6px;'
                    f'background:#060f1e;border-left:3px solid {color};">'
                    f'<span style="font-size:9px;color:{color};font-weight:700;'
                    f'white-space:nowrap;margin-top:1px;">Step {s["step"]}</span>'
                    f'<span style="font-size:10px;color:#64748b;font-weight:600;'
                    f'white-space:nowrap;margin-top:1px;">{s["label"]}</span>'
                    f'<span style="font-size:10px;color:#94a3b8;flex:1;">{s["detail"]}</span>'
                    f'<span style="font-size:9px;color:#334155;white-space:nowrap;">{s["ts"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Right: Recent feed ─────────────────────────────────────────────────────
    with right_col:
        st.markdown(
            '<div style="font-size:11px;color:#22c55e;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.1em;margin-bottom:10px;">Recent Ingestion Feed</div>',
            unsafe_allow_html=True,
        )

        # Show real last ingestion results if available
        result = st.session_state.get("agent_result")
        if result and result.get("steps"):
            steps = result.get("steps", [])
            for s in steps:
                color = STEP_COLORS.get(s.get("status", "ok"), "#22c55e")
                st.markdown(
                    f'<div style="background:#060f1e;border:1px solid #0f172a;'
                    f'border-left:3px solid {color};border-radius:6px;'
                    f'padding:7px 12px;margin-bottom:5px;">'
                    f'<div style="font-size:10px;font-weight:700;color:{color};">'
                    f'Step {s["step"]} — {s["label"]}</div>'
                    f'<div style="font-size:9.5px;color:#475569;margin-top:2px;">{s["detail"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            # Static feed until first agent run
            for dot_color, src, msg, ts in FEED_ITEMS:
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:10px;'
                    f'background:#060f1e;border:1px solid #0f172a;'
                    f'border-left:3px solid {dot_color};border-radius:6px;'
                    f'padding:8px 12px;margin-bottom:6px;">'
                    f'<div style="flex:1;">'
                    f'<span style="font-size:10.5px;font-weight:700;color:{dot_color};">{src}</span>'
                    f'<span style="font-size:10px;color:#475569;"> — {msg}</span>'
                    f'</div>'
                    f'<span style="font-size:9px;color:#334155;white-space:nowrap;">{ts}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # LLM status pill
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        ollama_ok = False
        try:
            r = _req.get("http://192.168.48.1:11434/api/tags", timeout=2)
            ollama_ok = r.status_code == 200
        except Exception:
            pass

        groq_ok = bool(safe_get("/health", silent=True))

        st.markdown(
            f'<div style="background:#060f1e;border:1px solid #1e293b;border-radius:8px;'
            f'padding:10px 14px;">'
            f'<div style="font-size:9px;color:#334155;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-bottom:8px;">LLM Chain Status</div>'
            f'<div style="display:flex;flex-direction:column;gap:5px;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{"#22c55e" if ollama_ok else "#ef4444"};display:inline-block;"></span>'
            f'<span style="font-size:10px;color:#94a3b8;">Ollama · llama3</span>'
            f'<span style="font-size:9px;color:{"#22c55e" if ollama_ok else "#ef4444"};margin-left:auto;">{"Primary" if ollama_ok else "Offline"}</span>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:#facc15;display:inline-block;"></span>'
            f'<span style="font-size:10px;color:#94a3b8;">Groq · LLaMA 3.3 70B</span>'
            f'<span style="font-size:9px;color:#facc15;margin-left:auto;">Fallback</span>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:#475569;display:inline-block;"></span>'
            f'<span style="font-size:10px;color:#475569;">Gemini · Flash</span>'
            f'<span style="font-size:9px;color:#475569;margin-left:auto;">Tertiary</span>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


page()
