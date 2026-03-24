"""
03_Delivery_Monitor.py — PRAMAAN v5
Delivery Monitor: per-event impacts, actors, evidence, cross-domain connections.
Delhi pilot — AMRUT drainage + PMAY housing with real government data.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from utils.api import safe_get
from utils.events import EVENTS as _EVENTS_FULL, N_EVENTS as _N_EVENTS, render_event_dropdown
from components.topnav import render_topnav

# Strip lat/lon — Live Feed only needs first 6 fields
EVENTS = [e[:6] for e in _EVENTS_FULL]

DOMAIN_COLORS = {
    "Climate":     "#22c55e",
    "Defense":     "#f97316",
    "Economics":   "#38bdf8",
    "Society":     "#fb7185",
    "Governance":  "#06b6d4",
    "Geopolitics": "#a78bfa",
    "Technology":  "#facc15",
}
SOURCE_ICONS = {
    "PIB":    "🏛️",
    "NDMA":   "🚨",
    "ISRO":   "🛰️",
    "IMD":    "🌩️",
    "MHA":    "🔒",
    "MoE":    "💻",
    "Govt":   "🏛️",
    "Press":  "📰",
    "MoHFW":  "🏥",
    "G20":    "🌐",
    "MEA":    "🤝",
    "Sansad": "🏛️",
}

SEV_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}


def _source_icon(source: str) -> str:
    for key, icon in SOURCE_ICONS.items():
        if key.lower() in (source or "").lower():
            return icon
    return "📄"


def _provenance_badge(source: str) -> str:
    """Return an HTML badge based on data source."""
    if "data.gov.in" in (source or "").lower():
        return '<span style="background:#0ea5e922;color:#0ea5e9;font-size:9px;font-weight:700;padding:1px 6px;border-radius:3px;border:1px solid #0ea5e944;margin-left:6px;letter-spacing:0.05em;">LIVE · data.gov.in</span>'
    return ""


def _evidence_card(ev: dict, color: str):
    icon   = _source_icon(ev.get("source", ""))
    title  = ev.get("title") or ev.get("id", "Evidence")
    source = ev.get("source", "")
    date   = ev.get("date", "")
    url    = ev.get("url", "")
    etype  = ev.get("type", "")
    badge  = _provenance_badge(source)
    link_html = (
        f'<a href="{url}" target="_blank" style="font-size:10px;color:{color};'
        f'text-decoration:none;margin-top:4px;display:inline-block;">View source →</a>'
        if url else ""
    )
    st.markdown(f"""
    <div style="background:#0a1628;border:1px solid {color}33;border-left:3px solid {color};
                border-radius:8px;padding:10px 14px;margin-bottom:8px;">
      <div style="display:flex;align-items:flex-start;gap:8px;">
        <span style="font-size:18px;line-height:1;">{icon}</span>
        <div style="flex:1;">
          <div style="font-size:12.5px;font-weight:700;color:#e2e8f0;line-height:1.3;">
            {title}{badge}
          </div>
          <div style="font-size:10.5px;color:#475569;margin-top:3px;">
            {source}{' · ' + date if date else ''}{' · ' + etype if etype else ''}
          </div>
          {link_html}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _impact_card(imp: dict, color: str):
    itype   = imp.get("type", "")
    value   = imp.get("value", "")
    unit    = imp.get("unit", "")
    desc    = imp.get("description", "")[:100]
    source  = imp.get("source", "")
    val_str = f"{value:,}" if isinstance(value, (int, float)) and value == int(value) else str(value) if value else "—"
    badge   = _provenance_badge(source)
    st.markdown(f"""
    <div style="background:#060f1e;border:1px solid {color}22;border-radius:8px;
                padding:8px 12px;margin-bottom:6px;display:flex;align-items:center;gap:12px;">
      <div style="min-width:60px;text-align:center;">
        <div style="font-size:1.3em;font-weight:800;color:{color};line-height:1;">{val_str}</div>
        <div style="font-size:9.5px;color:#334155;margin-top:1px;">{unit}</div>
      </div>
      <div style="flex:1;">
        <div style="font-size:11.5px;font-weight:600;color:#94a3b8;">
          {itype.replace('_',' ').title()}{badge}
        </div>
        <div style="font-size:10.5px;color:#475569;margin-top:2px;">{desc}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def page():
    st.set_page_config(page_title="Delivery Monitor – PRAMAAN", layout="wide")
    render_topnav(active_page="Delivery Monitor")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(34,197,94,0.7), 0 0 30px rgba(34,197,94,0.4), 0 0 50px rgba(34,197,94,0.2); }
        50%       { text-shadow: 0 0 25px rgba(34,197,94,1), 0 0 60px rgba(34,197,94,0.8), 0 0 100px rgba(34,197,94,0.5); }
    }
    /* Compact buttons in left panel */
    div[data-testid="stButton"] button { font-size: 11px !important; padding: 4px 8px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state ──────────────────────────────────────────────────────────
    if "deep_link_feed" in st.session_state:
        raw = st.session_state.pop("deep_link_feed")
        valid_ids = {e[0] for e in EVENTS}
        if raw in valid_ids:
            st.session_state.feed_sel = raw

    # ── Title ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:8px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#22c55e;font-family:'Cinzel',serif;
                   letter-spacing:0.08em;white-space:nowrap;
                   animation:glowPulse 2.5s ease-in-out infinite;">DELIVERY MONITOR</span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        {_N_EVENTS} Events &nbsp;·&nbsp; Verified Government Sources &nbsp;·&nbsp;
        <span style="color:#475569;">PIB · NDMA · ISRO · IMD</span> &nbsp;·&nbsp;
        <span style="color:#334155;">Real Impact Data</span>
      </span>
    </div>
    <div style="font-size:12px;color:#475569;margin-bottom:8px;">
      Select any event to see its measured impacts, key actors, funding schemes,
      and cross-domain links — all sourced from verified government data.
    </div>
    """, unsafe_allow_html=True)

    # ── Event selector row ─────────────────────────────────────────────────────
    if "feed_sel" not in st.session_state:
        st.session_state.feed_sel = EVENTS[0][0]

    dcol, ncol = st.columns([3, 1], gap="small")
    with dcol:
        render_event_dropdown("feed_sel", "feed_event_drop")

    sel_evt = next((e for e in EVENTS if e[0] == st.session_state.feed_sel), EVENTS[0])
    event_id, name, color, domain, date, sev = sel_evt
    sev_badge_color = SEV_COLOR.get(sev, "#64748b")

    with ncol:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("View AI Summary →", key=f"goto_brief_{event_id}", type="primary",
                     use_container_width=True):
            st.session_state["deep_link_brief"] = event_id
            st.switch_page("pages/04_Proof_and_Evidence.py")

    # ── Event banner ───────────────────────────────────────────────────────────
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

    # ── Fetch data ─────────────────────────────────────────────────────────────
    with st.spinner(f"Loading data for {name}..."):
        data = safe_get(f"/ontology/events/{event_id}", silent=False)

    if not data:
        st.error("Could not load event data. Is the backend running?")
        return

    # ── Content columns ────────────────────────────────────────────────────────
    col_imp, col_ev = st.columns([1, 1], gap="large")

    with col_imp:
        impacts = data.get("impacts", [])
        st.markdown(
            f'<div style="font-size:0.7em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.1em;font-weight:700;margin-bottom:10px;">'
            f'MEASURED IMPACTS ({len(impacts)})</div>',
            unsafe_allow_html=True,
        )
        if impacts:
            for imp in impacts:
                _impact_card(imp, color)
        else:
            st.markdown('<div style="font-size:12px;color:#334155;">No impact data loaded.</div>',
                        unsafe_allow_html=True)

        actors = data.get("actors", [])
        if actors:
            st.markdown(
                '<div style="font-size:0.7em;color:#475569;text-transform:uppercase;'
                'letter-spacing:0.1em;font-weight:700;margin-top:14px;margin-bottom:8px;">KEY ACTORS</div>',
                unsafe_allow_html=True,
            )
            for a in actors:
                aname = a.get("name", a.get("actor_id", ""))
                atype = a.get("type", "")
                st.markdown(f"""
                <div style="background:#060f1e;border:1px solid #38bdf844;border-radius:6px;
                            padding:6px 10px;margin-bottom:5px;font-size:11.5px;">
                  <span style="color:#38bdf8;font-weight:600;">{aname}</span>
                  <span style="color:#334155;margin-left:6px;">{atype}</span>
                </div>
                """, unsafe_allow_html=True)

    with col_ev:
        evidence = data.get("evidence", [])
        st.markdown(
            f'<div style="font-size:0.7em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.1em;font-weight:700;margin-bottom:10px;">'
            f'EVIDENCE SOURCES ({len(evidence)})</div>',
            unsafe_allow_html=True,
        )
        if evidence:
            for ev in evidence:
                _evidence_card(ev, color)
        else:
            st.markdown('<div style="font-size:12px;color:#334155;">No evidence nodes found.</div>',
                        unsafe_allow_html=True)

        connections = data.get("connections", [])
        if connections:
            st.markdown(
                '<div style="font-size:0.7em;color:#f97316;text-transform:uppercase;'
                'letter-spacing:0.1em;font-weight:700;margin-top:14px;margin-bottom:8px;">CROSS-DOMAIN LINKS</div>',
                unsafe_allow_html=True,
            )
            for conn in connections:
                cd_raw = conn.get("domain", "")
                cd     = cd_raw.replace("DOM_", "").title() if cd_raw else ""
                cc     = DOMAIN_COLORS.get(cd, "#f97316")
                st.markdown(f"""
                <div style="background:#0a1628;border:1px solid {cc}44;border-left:3px solid {cc};
                            border-radius:8px;padding:8px 12px;margin-bottom:6px;">
                  <div style="font-size:12px;font-weight:700;color:{cc};">{conn.get('name','')}</div>
                  <div style="font-size:10.5px;color:#475569;margin-top:2px;">{cd}</div>
                  <div style="font-size:10.5px;color:#64748b;margin-top:3px;font-style:italic;">
                    "{conn.get('reason','')}"
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Event description ───────────────────────────────────────────────────────
    event_data = data.get("event", {})
    if event_data.get("description"):
        st.markdown("---")
        st.markdown(
            f'<div style="font-size:0.7em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.1em;font-weight:700;margin-bottom:8px;">EVENT DESCRIPTION</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="background:#0a1628;border:1px solid {color}33;border-radius:8px;'
            f'padding:12px 16px;font-size:13px;color:#94a3b8;line-height:1.6;">'
            f'{event_data["description"]}</div>',
            unsafe_allow_html=True,
        )
        if event_data.get("source_url"):
            st.markdown(
                f'<a href="{event_data["source_url"]}" target="_blank" '
                f'style="font-size:11px;color:{color};text-decoration:none;">Primary source →</a>',
                unsafe_allow_html=True,
            )


page()
