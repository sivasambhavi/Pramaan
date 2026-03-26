"""
05_Live_Ingestion.py — PRAMAAN v5
Live Ingestion — unified prompt + scheduling, auto-refreshing feed.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import datetime as _dt
import requests as _req
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from components.topnav import render_topnav
from components.ontology_model import render_ontology_model
from utils.api import safe_get

BACKEND = "http://localhost:8000"

STEP_COLORS = {"ok": "#22c55e", "warn": "#facc15", "skip": "#475569"}

DOMAIN_COLOR = {
    "Climate":    "#22c55e",
    "Governance": "#06b6d4",
    "Society":    "#fb7185",
    "Defense":    "#f97316",
    "Economics":  "#38bdf8",
    "Technology": "#facc15",
    "Geopolitics":"#a78bfa",
}

LABEL_COLOR = {
    "Event": "#f97316", "Scheme": "#38bdf8", "Actor": "#a78bfa",
    "Region": "#22c55e", "Evidence": "#22c55e", "Impact": "#fb7185",
    "Asset": "#facc15", "Policy": "#06b6d4", "Domain": "#94a3b8",
}

SUGGESTED_TOPICS = [
    {"label": "India crude oil supply shock Hormuz blockade 2026",          "category": "Energy crisis",   "domains": ["Economics", "Geopolitics"]},
    {"label": "MEA India response Iran America war UNSC abstain 2026",      "category": "Diplomacy",       "domains": ["Geopolitics", "Governance"]},
    {"label": "India fuel price hike subsidy MoPNG PPAC 2026",              "category": "Energy policy",   "domains": ["Economics", "Governance"]},
    {"label": "Indian nationals evacuation Iran MEA consular 2026",         "category": "Diaspora",        "domains": ["Geopolitics", "Society"]},
    {"label": "India Sensex OMC stock market crash Iran war 2026",          "category": "Market impact",   "domains": ["Economics", "Geopolitics"]},
    {"label": "India strategic petroleum reserve SPR drawdown 2026",        "category": "Energy security", "domains": ["Economics", "Governance"]},
    {"label": "India IMEC corridor disruption Hormuz Middle East 2026",     "category": "Trade route",     "domains": ["Economics", "Geopolitics"]},
    {"label": "India Pakistan ceasefire Operation Sindoor LOC 2025",        "category": "Defense",         "domains": ["Defense", "Geopolitics"]},
]

FEED_ITEMS = [
    {"label": "Policy",  "source": "MEA",     "object": "India abstains at UNSC on Iran strikes",         "time": "1m ago",  "color": "#06b6d4"},
    {"label": "Impact",  "source": "MoPNG",   "object": "Hormuz closure — India 18% crude exposure",      "time": "3m ago",  "color": "#fb7185"},
    {"label": "Asset",   "source": "GAIL",    "object": "Spot LNG prices +34% on Hormuz blockade",        "time": "5m ago",  "color": "#facc15"},
    {"label": "Impact",  "source": "BSE/NSE", "object": "Sensex -3.2% · OMC stocks -8% (HPCL/BPCL/IOC)", "time": "7m ago",  "color": "#fb7185"},
    {"label": "Actor",   "source": "MEA",     "object": "18,000 Indian nationals in Iran — 6 flights",    "time": "12m ago", "color": "#a78bfa"},
    {"label": "Impact",  "source": "RBI",     "object": "INR/USD 83.8 → 88.2 on energy shock",           "time": "18m ago", "color": "#fb7185"},
    {"label": "Actor",   "source": "PIB",     "object": "Cyclone Dana response team",                     "time": "22m ago", "color": "#a78bfa"},
    {"label": "Scheme",  "source": "NDMA",    "object": "Wayanad relief fund disbursement",               "time": "28m ago", "color": "#38bdf8"},
]

SCHED_OPTIONS = ["Manual only", "Every 15m", "Every 1h", "Every 6h", "Every 24h"]
SCHED_MINUTES = {"Every 15m": 15, "Every 1h": 60, "Every 6h": 360, "Every 24h": 1440}

SECTION_LABEL_STYLE = (
    "font-size:9px;font-weight:700;color:#334155;text-transform:uppercase;"
    "letter-spacing:0.12em;margin-bottom:6px;margin-top:14px;"
    "border-left:2px solid #1e293b;padding-left:8px;"
)


# ── Module-level cached fetchers (persist across reruns) ──────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _get_stats():
    return safe_get("/stats", silent=True) or {}

@st.cache_data(ttl=15, show_spinner=False)
def _get_recent_nodes():
    return safe_get("/ingest/live/recent-nodes", params={"limit": 8}, silent=True) or {}

@st.cache_data(ttl=30, show_spinner=False)
def _get_scheduler_status():
    return safe_get("/scheduler/status", silent=True) or {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _section(label: str) -> None:
    st.markdown(f'<div style="{SECTION_LABEL_STYLE}">{label}</div>', unsafe_allow_html=True)


def _domain_chip(domain: str) -> str:
    c = DOMAIN_COLOR.get(domain, "#94a3b8")
    return (
        f'<span style="background:{c}18;border:1px solid {c}55;color:{c};'
        f'font-size:8px;font-weight:600;padding:1px 6px;border-radius:10px;'
        f'white-space:nowrap;">{domain}</span>'
    )


def _rel_time(ts_str: str) -> str:
    if not ts_str:
        return "—"
    try:
        ts  = _dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = _dt.datetime.now(_dt.timezone.utc)
        d   = int((now - ts).total_seconds())
        if d < 60:    return f"{d}s ago"
        if d < 3600:  return f"{d // 60}m ago"
        if d < 86400: return f"{d // 3600}h ago"
        return f"{d // 86400}d ago"
    except Exception:
        return ts_str[:10]


def _feed_card(label: str, name: str, source: str, rel_ts: str, color: str) -> str:
    return (
        f'<div style="background:#060f1e;border:1px solid #0f172a;'
        f'border-left:3px solid {color};border-radius:6px;'
        f'padding:7px 10px;margin-bottom:4px;'
        f'display:flex;align-items:center;gap:10px;">'
        f'<span style="font-size:8px;font-weight:700;color:{color};'
        f'background:{color}18;border:1px solid {color}44;'
        f'padding:1px 6px;border-radius:10px;white-space:nowrap;flex-shrink:0;">'
        f'{label.upper()}</span>'
        f'<span style="font-size:10px;color:#cbd5e1;flex:1;'
        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
        f'{name}</span>'
        f'<span style="font-size:8.5px;color:#475569;white-space:nowrap;flex-shrink:0;">{source}</span>'
        f'<span style="font-size:8.5px;color:#334155;white-space:nowrap;flex-shrink:0;margin-left:8px;">{rel_ts}</span>'
        f'</div>'
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def page():
    st.set_page_config(page_title="Live Ingestion – PRAMAAN", layout="wide")
    render_topnav(active_page="Live Ingestion")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    div[data-baseweb="select"] * { font-size: 13px !important; }
    /* Hide autorefresh iframe height */
    iframe[title="streamlit_autorefresh.autorefresh"] { display: none !important; height: 0 !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(249,115,22,0.5); }
        50%       { text-shadow: 0 0 28px rgba(249,115,22,0.9); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Auto-refresh every 30s — hidden via CSS above so it adds no vertical space
    st_autorefresh(interval=30_000, key="live_autorefresh")

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:6px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#f97316;
                   font-family:'Cinzel',serif;letter-spacing:0.08em;
                   animation:glowPulse 2.5s ease-in-out infinite;">
        LIVE INGESTION
      </span>
      <span style="font-size:0.75em;color:#64748b;">
        Agentic · Ollama LLaMA3 · Neo4j Knowledge Graph
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── SECTION: Graph Status ───────────────────────────────────────────────────
    _section("Graph Status")

    stats       = _get_stats()
    total_nodes = stats.get("total_nodes", 0)
    total_edges = stats.get("total_edges", 0)
    events      = stats.get("events",      0)
    evidence    = stats.get("evidence",    0)

    prev = st.session_state.get("_prev_stats", {})
    st.session_state["_prev_stats"] = {
        "nodes": total_nodes, "edges": total_edges,
        "events": events, "evidence": evidence,
    }

    def _delta(curr, key):
        p = prev.get(key, curr)
        d = curr - p
        if d > 0:
            return f'<span style="font-size:9px;color:#22c55e;">+{d}</span>'
        return '<span style="font-size:9px;color:#334155;">—</span>'

    _IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
    sync_ts = _dt.datetime.now(_IST).strftime("%H:%M:%S IST")
    view_link = (
        '<a href="/Decision_Engine" target="_self" '
        'style="font-size:9px;color:#38bdf8;text-decoration:none;margin-left:6px;">'
        'View graph</a>'
    )

    # ── Stats bar — full width, compact single row ──────────────────────────────
    st.markdown(
        f'<div style="display:flex;gap:0;background:#060f1e;border:1px solid #1e293b;'
        f'border-radius:8px;padding:6px 12px;margin-bottom:8px;">'
        f'<div style="flex:1;text-align:center;border-right:1px solid #1e293b;padding-right:12px;">'
        f'<div style="font-size:1.4em;font-weight:800;color:#a78bfa;">{total_nodes}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Nodes</div>'
        f'<div style="margin-top:1px;">{_delta(total_nodes,"nodes")}{view_link}</div>'
        f'</div>'
        f'<div style="flex:1;text-align:center;border-right:1px solid #1e293b;padding:0 12px;">'
        f'<div style="font-size:1.4em;font-weight:800;color:#38bdf8;">{total_edges}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Edges</div>'
        f'<div style="margin-top:1px;">{_delta(total_edges,"edges")}</div>'
        f'</div>'
        f'<div style="flex:1;text-align:center;border-right:1px solid #1e293b;padding:0 12px;">'
        f'<div style="font-size:1.4em;font-weight:800;color:#f97316;">{events}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Events</div>'
        f'<div style="margin-top:1px;">{_delta(events,"events")}</div>'
        f'</div>'
        f'<div style="flex:1;text-align:center;padding-left:12px;">'
        f'<div style="font-size:1.4em;font-weight:800;color:#22c55e;">{evidence}</div>'
        f'<div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.07em;">Evidence</div>'
        f'<div style="margin-top:1px;font-size:8px;color:#334155;">synced {sync_ts}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Main layout ─────────────────────────────────────────────────────────────
    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:

        # ── SECTION: Ingestion Prompt + Run Controls (unified) ──────────────────
        _section("Ingestion Prompt")

        st.markdown(
            '<div style="font-size:10px;color:#64748b;margin-bottom:8px;">'
            'Describe an issue, paste a link, or give a data source URL — the agent extracts '
            'events, entities, and evidence and writes them into the ontology.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Auto-reset suggestion dropdown after selection (one-shot UX)
        if st.session_state.get("suggestion_select", "— pick a suggestion —") != "— pick a suggestion —":
            st.session_state["_topic_pending"] = st.session_state["suggestion_select"].split(" ·· ")[1]
            st.session_state["suggestion_select"] = "— pick a suggestion —"

        # Move pending suggestion into widget key BEFORE rendering text input
        if "_topic_pending" in st.session_state:
            st.session_state["agent_topic"] = st.session_state.pop("_topic_pending")

        topic = st.text_input(
            "topic",
            label_visibility="collapsed",
            placeholder="e.g. India crude oil Hormuz blockade 2026  or  paste a PIB / MEA URL",
            key="agent_topic",
        )

        # Suggested prompts — single compact selectbox, tags inline in label
        _PLACEHOLDER = "— pick a suggestion —"
        _suggestion_options = [_PLACEHOLDER] + [
            f"{s['category']} · {s['label'][:45]}{'…' if len(s['label'])>45 else ''} · {' · '.join(s['domains'])} ·· {s['label']}"
            for s in SUGGESTED_TOPICS
        ]
        st.selectbox(
            "Suggested topics",
            _suggestion_options,
            index=0,
            label_visibility="collapsed",
            key="suggestion_select",
        )

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # ── Run controls: button + dry run + schedule in one row ────────────────
        dry_run = st.session_state.get("dry_run_toggle", False)
        run_label = "Dry Run Agent" if dry_run else "Run Agent"

        run_col, dry_col, sched_col = st.columns([1.3, 0.7, 1], gap="small")
        with run_col:
            run_clicked = st.button(
                run_label,
                use_container_width=True,
                type="primary",
                key="run_agent_btn",
            )
        with dry_col:
            dry_run = st.toggle(
                "Dry run", value=False, key="dry_run_toggle",
                help="Preview nodes/edges without writing to graph.",
            )
        with sched_col:
            prev_schedule = st.session_state.get("_prev_schedule", "Every 1h")
            schedule = st.selectbox(
                "Schedule",
                SCHED_OPTIONS,
                index=SCHED_OPTIONS.index("Every 1h"),
                label_visibility="collapsed",
                key="agent_schedule",
            )

        if dry_run:
            st.markdown(
                '<div style="font-size:9px;color:#facc15;margin-top:2px;padding:4px 8px;'
                'background:#1a1500;border:1px solid #facc1544;border-radius:4px;">'
                'Dry run ON — diff preview only, nothing written to graph.'
                '</div>',
                unsafe_allow_html=True,
            )

        # Push interval change to backend when dropdown changes
        if schedule != prev_schedule:
            st.session_state["_prev_schedule"] = schedule
            if schedule != "Manual only":
                try:
                    _req.post(
                        f"{BACKEND}/scheduler/set-interval",
                        params={"minutes": SCHED_MINUTES[schedule]},
                        timeout=2,
                    )
                except Exception:
                    pass

        # Live scheduler next-run from backend
        sched_status  = _get_scheduler_status()
        next_run_iso  = sched_status.get("jobs", {}).get("news_refresh", {}).get("next_run")
        next_run_str  = "—"
        if next_run_iso:
            try:
                _IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
                nrt = _dt.datetime.fromisoformat(next_run_iso).astimezone(_IST)
                next_run_str = nrt.strftime("%H:%M IST")
            except Exception:
                next_run_str = next_run_iso[:16]

        mins_label = f"every {SCHED_MINUTES.get(schedule, 60)} min" if schedule != "Manual only" else "manual"
        st.markdown(
            f'<div style="font-size:9px;color:#334155;margin-top:4px;padding:4px 8px;'
            f'background:#060f1e;border:1px solid #1e293b;border-radius:4px;">'
            f'APScheduler · {mins_label} · next auto-run: {next_run_str}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Agent trace output ──────────────────────────────────────────────────
        if run_clicked:
            t = (topic or "").strip()
            if not t:
                st.warning("Enter a topic or URL to run the agent.")
            else:
                with st.spinner("Agent running…"):
                    try:
                        payload = {"topic": t, "max_articles": 6}
                        if dry_run:
                            payload["dry_run"] = True
                        resp = _req.post(f"{BACKEND}/ingest/agentic", json=payload, timeout=120)
                        if resp.status_code == 200:
                            st.session_state["agent_result"] = resp.json()
                            st.cache_data.clear()   # force feed + stats to refresh
                        else:
                            st.error(f"Agent failed ({resp.status_code}): {resp.text[:300]}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

        result = st.session_state.get("agent_result")
        if result:
            ec       = result.get("entities_created", 0)
            rc       = result.get("relations_created", 0)
            skipped  = result.get("entities_skipped", 0)
            duration = result.get("duration_s", 0)
            llm      = result.get("llm_used", "").upper()
            is_dry   = result.get("dry_run", False)
            steps    = result.get("steps", [])

            dry_label = ' · <span style="color:#facc15;">DRY RUN</span>' if is_dry else ""
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #22c55e44;border-radius:8px;'
                f'padding:10px 16px;margin:10px 0;display:flex;gap:20px;align-items:center;">'
                f'<span style="font-size:11px;color:#22c55e;font-weight:700;">{ec} entities</span>'
                f'<span style="font-size:11px;color:#38bdf8;">{rc} relations</span>'
                f'<span style="font-size:10px;color:#475569;">{skipped} skipped</span>'
                f'<span style="font-size:10px;color:#334155;margin-left:auto;">'
                f'{duration}s · {llm}{dry_label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="font-size:9px;color:#334155;font-weight:700;text-transform:uppercase;'
                'letter-spacing:0.1em;margin-bottom:6px;">Agent Trace</div>',
                unsafe_allow_html=True,
            )
            for s in steps:
                color = STEP_COLORS.get(s.get("status", "ok"), "#22c55e")
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:10px;padding:6px 10px;'
                    f'margin-bottom:3px;border-radius:6px;background:#060f1e;border-left:3px solid {color};">'
                    f'<span style="font-size:9px;color:{color};font-weight:700;white-space:nowrap;">Step {s["step"]}</span>'
                    f'<span style="font-size:10px;color:#64748b;font-weight:600;white-space:nowrap;">{s["label"]}</span>'
                    f'<span style="font-size:10px;color:#94a3b8;flex:1;">{s["detail"]}</span>'
                    f'<span style="font-size:9px;color:#334155;white-space:nowrap;">{s["ts"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div style="margin-top:8px;font-size:9px;color:#334155;">'
            'View ingestion logs in '
            '<a href="/Delivery_Monitor" target="_self" style="color:#38bdf8;text-decoration:none;">Delivery Monitor</a>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Right: Feed + LLM status ───────────────────────────────────────────────
    with right_col:
        _section("Recent Ingestion Feed")
        live_data  = _get_recent_nodes()
        live_nodes = live_data.get("nodes", [])
        st.markdown(
            '<div style="font-size:9px;color:#334155;margin-bottom:6px;">'
            'Ontology nodes written to graph · auto-refreshes every 30s</div>',
            unsafe_allow_html=True,
        )
        if live_nodes:
            for node in live_nodes:
                label = node.get("label", "Node")
                c     = LABEL_COLOR.get(label, "#475569")
                st.markdown(
                    _feed_card(label, node.get("name","—"), node.get("source","—"), _rel_time(node.get("ts","")), c),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="font-size:8.5px;color:#475569;padding:2px 0 4px;">Neo4j offline — showing sample</div>',
                unsafe_allow_html=True,
            )
            for item in FEED_ITEMS:
                st.markdown(
                    _feed_card(item["label"], item["object"], item["source"], item["time"], item["color"]),
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        _section("LLM Chain Status")

        ollama_ok = False
        _ollama_host = os.environ.get("OLLAMA_HOST", "http://172.17.240.1:11434").rstrip("/")
        try:
            r = _req.get(f"{_ollama_host}/api/tags", timeout=0.5)
            ollama_ok = r.status_code == 200
        except Exception:
            pass

        groq_ok = bool(safe_get("/health", silent=True))

        def _dot(ok, warn=False):
            c = "#22c55e" if ok else ("#facc15" if warn else "#ef4444")
            return f'<span style="width:7px;height:7px;border-radius:50%;background:{c};display:inline-block;flex-shrink:0;"></span>'

        def _lbl(ok, on_label, off_label, warn=False):
            c = "#22c55e" if ok else ("#facc15" if warn else "#ef4444")
            return f'<span style="font-size:9px;color:{c};margin-left:auto;">{on_label if ok else off_label}</span>'

        st.markdown(
            f'<div style="background:#060f1e;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;">'
            f'<div style="display:grid;grid-template-columns:16px 1fr auto;gap:8px;align-items:center;'
            f'font-size:8px;color:#334155;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;'
            f'margin-bottom:6px;padding-bottom:5px;border-bottom:1px solid #0f172a;">'
            f'<span></span><span>Model</span><span>Role &amp; Status</span></div>'
            # Ollama
            f'<div style="display:grid;grid-template-columns:16px 1fr auto;gap:8px;align-items:center;margin-bottom:6px;">'
            f'{_dot(ollama_ok)}'
            f'<div><div style="font-size:10px;color:#94a3b8;">Ollama · llama3</div>'
            f'<div style="font-size:8.5px;color:#475569;">Primary · extraction + summarisation</div></div>'
            f'{_lbl(ollama_ok, "Online", "Offline")}</div>'
            # Groq
            f'<div style="display:grid;grid-template-columns:16px 1fr auto;gap:8px;align-items:center;margin-bottom:6px;">'
            f'{_dot(groq_ok, warn=True)}'
            f'<div><div style="font-size:10px;color:#94a3b8;">Groq · LLaMA 3.3 70B</div>'
            f'<div style="font-size:8.5px;color:#475569;">Fallback · used when Ollama is offline</div></div>'
            f'{_lbl(groq_ok, "Ready", "Unreachable", warn=True)}</div>'
            # Gemini
            f'<div style="display:grid;grid-template-columns:16px 1fr auto;gap:8px;align-items:center;">'
            f'{_dot(False, warn=True)}'
            f'<div><div style="font-size:10px;color:#475569;">Gemini · Flash</div>'
            f'<div style="font-size:8.5px;color:#334155;">Tertiary · classification + validation</div></div>'
            f'<span style="font-size:9px;color:#475569;">Standby</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )



    render_ontology_model()

page()
