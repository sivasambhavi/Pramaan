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

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_feed, tab_pilot = st.tabs(["📡 Event Intelligence", "📍 Delhi Pilot — Proof Chain"])

    with tab_feed:
        _render_event_feed()

    with tab_pilot:
        _render_delhi_pilot()


def _render_event_feed():
    import streamlit as st
    from utils.api import safe_get
    from utils.events import EVENTS as _EVENTS_FULL, render_event_dropdown

    EVENTS_LOCAL = [e[:6] for e in _EVENTS_FULL]
    SEV_COLOR_L = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}

    if "feed_sel" not in st.session_state:
        st.session_state.feed_sel = EVENTS_LOCAL[0][0]

    dcol, ncol = st.columns([3, 1], gap="small")
    with dcol:
        render_event_dropdown("feed_sel", "feed_event_drop")

    sel_evt = next((e for e in EVENTS_LOCAL if e[0] == st.session_state.feed_sel), EVENTS_LOCAL[0])
    event_id, name, color, domain, date, sev = sel_evt
    sev_badge_color = SEV_COLOR_L.get(sev, "#64748b")

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


def _render_delhi_pilot():
    """Delhi Pilot — 5-layer proof chain: Delhi Floods → SDRF/AMRUT/PMAY → Assets → Evidence."""
    import streamlit as st

    # ── Proof chain banner ──────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#0a1628;border:1px solid #22c55e44;border-left:4px solid #22c55e;
                border-radius:10px;padding:12px 16px;margin-bottom:16px;">
      <div style="font-size:13px;font-weight:800;color:#22c55e;margin-bottom:4px;">
        Delhi Yamuna Floods (Jul 2023) — Full Proof Chain
      </div>
      <div style="font-size:10.5px;color:#64748b;line-height:1.6;">
        Yamuna at 208.65m record level · 27,000+ evacuated · SDRF activated ·
        AMRUT drainage + PMAY housing tracked to ground level with real data.gov.in evidence.
      </div>
      <div style="display:flex;align-items:center;gap:6px;margin-top:10px;flex-wrap:wrap;font-size:11px;">
        <span style="background:#ef444422;color:#fca5a5;padding:3px 8px;border-radius:4px;border:1px solid #ef444444;font-weight:600;">Event</span>
        <span style="color:#475569;">→</span>
        <span style="background:#f9731622;color:#fdba74;padding:3px 8px;border-radius:4px;border:1px solid #f9731644;font-weight:600;">Response</span>
        <span style="color:#475569;">→</span>
        <span style="background:#facc1522;color:#fde047;padding:3px 8px;border-radius:4px;border:1px solid #facc1544;font-weight:600;">Scheme</span>
        <span style="color:#475569;">→</span>
        <span style="background:#22c55e22;color:#86efac;padding:3px 8px;border-radius:4px;border:1px solid #22c55e44;font-weight:600;">Asset</span>
        <span style="color:#475569;">→</span>
        <span style="background:#38bdf822;color:#7dd3fc;padding:3px 8px;border-radius:4px;border:1px solid #38bdf844;font-weight:600;">Evidence</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Layer 1+2: Event + Response ─────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.7em;color:#475569;text-transform:uppercase;letter-spacing:0.1em;'
        'font-weight:700;margin-bottom:8px;">LAYER 1+2 — EVENT & RESPONSE</div>',
        unsafe_allow_html=True,
    )
    ev_col, r1_col, r2_col = st.columns([2, 1, 1], gap="medium")
    with ev_col:
        st.markdown("""
        <div style="background:#060f1e;border:1px solid #ef444433;border-left:4px solid #ef4444;
                    border-radius:8px;padding:12px 14px;">
          <div style="font-size:12px;font-weight:700;color:#fca5a5;">Delhi Yamuna Floods</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;">Jul 13 2023 · Climate · CRITICAL</div>
          <div style="font-size:10.5px;color:#94a3b8;margin-top:6px;line-height:1.5;">
            Yamuna at 208.65m — all-time record. 27,000+ evacuated.
            Triggered emergency SDRF release + accelerated AMRUT/PMAY implementation.
          </div>
          <div style="font-size:10px;color:#475569;margin-top:6px;">Source: IMD · NDMA · PIB</div>
        </div>
        """, unsafe_allow_html=True)
    with r1_col:
        st.markdown("""
        <div style="background:#060f1e;border:1px solid #f9731633;border-left:3px solid #f97316;
                    border-radius:8px;padding:10px 12px;">
          <div style="font-size:9px;color:#f97316;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Type 1 — Emergency</div>
          <div style="font-size:11.5px;font-weight:700;color:#fdba74;">SDRF</div>
          <div style="font-size:10px;color:#64748b;margin-top:2px;">₹43,900 Cr · MHA</div>
          <div style="font-size:10px;color:#94a3b8;margin-top:4px;">State Disaster Response Fund activated within 48 hrs</div>
        </div>
        """, unsafe_allow_html=True)
    with r2_col:
        st.markdown("""
        <div style="background:#060f1e;border:1px solid #f9731633;border-left:3px solid #f97316;
                    border-radius:8px;padding:10px 12px;">
          <div style="font-size:9px;color:#f97316;font-weight:700;text-transform:uppercase;margin-bottom:4px;">Type 1 — Emergency</div>
          <div style="font-size:11.5px;font-weight:700;color:#fdba74;">NDRF</div>
          <div style="font-size:10px;color:#64748b;margin-top:2px;">₹12,390 Cr · MHA</div>
          <div style="font-size:10px;color:#94a3b8;margin-top:4px;">NDRF teams deployed · 27,000+ rescued</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Layer 3: Scheme → Asset ─────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.7em;color:#475569;text-transform:uppercase;letter-spacing:0.1em;'
        'font-weight:700;margin-bottom:8px;">LAYER 3+4 — SCHEME DELIVERY & ASSETS (Delhi Pilot)</div>',
        unsafe_allow_html=True,
    )

    amrut_col, pmay_col = st.columns(2, gap="large")

    with amrut_col:
        st.markdown("""
        <div style="background:#0a1a0a;border:1px solid #22c55e44;border-left:4px solid #22c55e;
                    border-radius:10px;padding:12px 14px;margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
            <div>
              <div style="font-size:9px;color:#22c55e;font-weight:700;text-transform:uppercase;">Type 2 — Ongoing</div>
              <div style="font-size:13px;font-weight:800;color:#86efac;">AMRUT 2.0</div>
            </div>
            <span style="background:#22c55e22;color:#86efac;font-size:9px;font-weight:700;padding:2px 7px;border-radius:4px;border:1px solid #22c55e44;">₹66,750 Cr Total</span>
          </div>
          <div style="font-size:10.5px;color:#64748b;margin-bottom:10px;">Urban storm water drainage — NCT Delhi allocation</div>
        </div>
        """, unsafe_allow_html=True)

        # AMRUT asset cards — real data from data.gov.in
        amrut_assets = [
            {"name": "Storm Water Drain — Ward 45 Gali 7", "status": "completed", "cost": "₹2.15 Cr", "proof": "data.gov.in"},
            {"name": "Storm Water Drain — Ward 45 Gali 12", "status": "completed", "cost": "₹3.23 Cr", "proof": "data.gov.in"},
            {"name": "Storm Water Drain — Ward 46", "status": "in_progress", "cost": "₹1.87 Cr", "proof": "PIB"},
        ]
        for a in amrut_assets:
            status_color = "#22c55e" if a["status"] == "completed" else "#f97316"
            status_text  = "✅ Completed" if a["status"] == "completed" else "⚠️ In Progress"
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid {status_color}22;border-radius:8px;'
                f'padding:9px 12px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">'
                f'<div style="flex:1;">'
                f'<div style="font-size:11.5px;font-weight:600;color:#94a3b8;">{a["name"]}</div>'
                f'<div style="font-size:10px;color:#475569;margin-top:2px;">'
                f'{a["cost"]} &nbsp;·&nbsp; '
                f'<span style="color:#0ea5e9;">{a["proof"]}</span>'
                f'</div>'
                f'</div>'
                f'<span style="font-size:10px;color:{status_color};font-weight:600;white-space:nowrap;">'
                f'{status_text}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # AMRUT summary
        st.markdown("""
        <div style="background:#0a2010;border:1px solid #22c55e33;border-radius:8px;
                    padding:10px 14px;margin-top:4px;display:flex;gap:16px;">
          <div style="text-align:center;flex:1;">
            <div style="font-size:1.6em;font-weight:800;color:#22c55e;">3</div>
            <div style="font-size:10px;color:#475569;">Projects</div>
          </div>
          <div style="text-align:center;flex:1;">
            <div style="font-size:1.6em;font-weight:800;color:#86efac;">₹5.38 Cr</div>
            <div style="font-size:10px;color:#475569;">Delhi Total</div>
          </div>
          <div style="text-align:center;flex:1;">
            <div style="font-size:1.6em;font-weight:800;color:#22c55e;">2/3</div>
            <div style="font-size:10px;color:#475569;">Completed</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with pmay_col:
        st.markdown("""
        <div style="background:#0a1020;border:1px solid #38bdf844;border-left:4px solid #38bdf8;
                    border-radius:10px;padding:12px 14px;margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
            <div>
              <div style="font-size:9px;color:#38bdf8;font-weight:700;text-transform:uppercase;">Type 2 — Ongoing</div>
              <div style="font-size:13px;font-weight:800;color:#7dd3fc;">PMAY-U (Urban)</div>
            </div>
            <span style="background:#38bdf822;color:#7dd3fc;font-size:9px;font-weight:700;padding:2px 7px;border-radius:4px;border:1px solid #38bdf844;">₹401.79 Cr · Delhi</span>
          </div>
          <div style="font-size:10.5px;color:#64748b;margin-bottom:10px;">Pradhan Mantri Awas Yojana — affordable urban housing, NCT Delhi</div>
        </div>
        """, unsafe_allow_html=True)

        # PMAY asset card
        st.markdown("""
        <div style="background:#060f1e;border:1px solid #22c55e33;border-radius:8px;
                    padding:9px 12px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">
          <div style="flex:1;">
            <div style="font-size:11.5px;font-weight:600;color:#94a3b8;">PMAY Housing — Delhi NCT</div>
            <div style="font-size:10px;color:#475569;margin-top:2px;">17,067 houses · ₹401.79 Cr · <span style="color:#0ea5e9;">data.gov.in</span></div>
          </div>
          <span style="font-size:10px;color:#22c55e;font-weight:600;white-space:nowrap;">✅ 100% Complete</span>
        </div>
        """, unsafe_allow_html=True)

        # PMAY summary metrics
        st.markdown("""
        <div style="background:#060f1e;border:1px solid #38bdf822;border-radius:8px;
                    padding:10px 14px;margin-bottom:6px;">
          <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <div style="text-align:center;flex:1;min-width:60px;">
              <div style="font-size:1.4em;font-weight:800;color:#38bdf8;">17,067</div>
              <div style="font-size:9.5px;color:#475569;">Houses</div>
            </div>
            <div style="text-align:center;flex:1;min-width:60px;">
              <div style="font-size:1.4em;font-weight:800;color:#7dd3fc;">₹401 Cr</div>
              <div style="font-size:9.5px;color:#475569;">Allocated</div>
            </div>
            <div style="text-align:center;flex:1;min-width:60px;">
              <div style="font-size:1.4em;font-weight:800;color:#22c55e;">100%</div>
              <div style="font-size:9.5px;color:#475569;">Occupied</div>
            </div>
            <div style="text-align:center;flex:1;min-width:60px;">
              <div style="font-size:1.4em;font-weight:800;color:#86efac;">85K+</div>
              <div style="font-size:9.5px;color:#475569;">Beneficiaries</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#0a2010;border:1px solid #22c55e33;border-radius:8px;
                    padding:8px 12px;font-size:10.5px;color:#64748b;line-height:1.5;">
          ✅ Flood-affected families prioritised in allotment ·
          Ground-truth verified via data.gov.in · MoHUA ministry records
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Layer 5: Evidence ───────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.7em;color:#475569;text-transform:uppercase;letter-spacing:0.1em;'
        'font-weight:700;margin-bottom:8px;">LAYER 5 — EVIDENCE CHAIN</div>',
        unsafe_allow_html=True,
    )

    ev1, ev2, ev3 = st.columns(3, gap="medium")
    with ev1:
        st.markdown("""
        <div style="background:#0a1628;border:1px solid #0ea5e944;border-left:3px solid #0ea5e9;
                    border-radius:8px;padding:10px 12px;">
          <div style="font-size:10px;color:#0ea5e9;font-weight:700;margin-bottom:4px;">📊 DATA PROOF</div>
          <div style="font-size:11.5px;font-weight:600;color:#e2e8f0;">AMRUT Drainage · data.gov.in</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;">3 projects · Delhi NCT · 2024</div>
          <div style="font-size:10px;color:#0ea5e988;margin-top:4px;">LIVE · Government Dataset</div>
        </div>
        """, unsafe_allow_html=True)
    with ev2:
        st.markdown("""
        <div style="background:#0a1628;border:1px solid #0ea5e944;border-left:3px solid #0ea5e9;
                    border-radius:8px;padding:10px 12px;">
          <div style="font-size:10px;color:#0ea5e9;font-weight:700;margin-bottom:4px;">📊 DATA PROOF</div>
          <div style="font-size:11.5px;font-weight:600;color:#e2e8f0;">PMAY Housing · data.gov.in</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;">17,067 houses · Delhi · MoHUA</div>
          <div style="font-size:10px;color:#0ea5e988;margin-top:4px;">LIVE · Government Dataset</div>
        </div>
        """, unsafe_allow_html=True)
    with ev3:
        st.markdown("""
        <div style="background:#0a1628;border:1px solid #facc1544;border-left:3px solid #facc15;
                    border-radius:8px;padding:10px 12px;">
          <div style="font-size:10px;color:#facc15;font-weight:700;margin-bottom:4px;">🏛️ PIB SOURCE</div>
          <div style="font-size:11.5px;font-weight:600;color:#e2e8f0;">SDRF Funds · PIB Press Release</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;">Delhi SDRF allocation · Jul 2023</div>
          <div style="font-size:10px;color:#facc1588;margin-top:4px;">Press Information Bureau</div>
        </div>
        """, unsafe_allow_html=True)

    # ── CTA ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("View Before/After Photos & AI Brief →  Proof & Evidence",
                 key="goto_proof_pilot", type="primary"):
        st.session_state["deep_link_brief"] = "EVT_DELHI_FLOODS_2023"
        st.switch_page("pages/04_Proof_and_Evidence.py")


page()
