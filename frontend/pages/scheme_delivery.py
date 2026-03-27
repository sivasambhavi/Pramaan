"""
scheme_delivery.py — PRAMAAN v5
Delivery Monitor: per-event impacts, actors, evidence, cross-domain connections.
Delhi pilot — AMRUT drainage + PMAY housing with real government data.
"""

import sys
import os
import html as _html

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from utils.api import safe_get
from utils.events import EVENTS as _EVENTS_FULL, N_EVENTS as _N_EVENTS, render_event_dropdown
from components.topnav import render_topnav
from components.ontology_model import render_ontology_model

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

DOMAIN_ICONS = {
    "Climate":     "🌊",
    "Defense":     "⚔️",
    "Economics":   "💹",
    "Society":     "👥",
    "Governance":  "🏛️",
    "Geopolitics": "🌐",
    "Technology":  "🛰️",
}

IMPACT_ICONS = {
    "people":         "👥",
    "evacuated":      "🚨",
    "displaced":      "🏠",
    "funds":          "💰",
    "financial":      "💸",
    "oil":            "🛢️",
    "petroleum":      "🛢️",
    "supply":         "📦",
    "infrastructure": "🏗️",
    "security":       "🛡️",
    "satellite":      "🛰️",
    "economic":       "📈",
    "trade":          "🤝",
    "energy":         "⚡",
    "flood":          "🌊",
    "health":         "🏥",
    "food":           "🌾",
    "cost":           "💸",
    "revenue":        "📊",
    "cargo":          "🚢",
    "jobs":           "👷",
    "gdp":            "📈",
    "defense":        "🛡️",
    "missile":        "🚀",
    "relief":         "🏕️",
    "shipping":       "🚢",
    "insurance":      "📋",
    "vessel":         "🚢",
    "price":          "💲",
    "loss":           "📉",
    "damage":         "🏚️",
    "killed":         "⚠️",
    "wounded":        "🏥",
    "disruption":     "⚠️",
    "export":         "📤",
    "import":         "📥",
}

SEV_ICONS   = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
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


def _sanitise(text: str) -> str:
    if not text:
        return ""
    replacements = [
        ("\u00e2\u20ac\u2014", "—"),
        ("\u00e2\u20ac\u201d", "—"),
        ("\u00e2\u20ac\u2013", "–"),
        ("\u00e2\u20ac\u2122", "'"),
        ("\u00e2\u20ac\u0153", "\""),
        ("\u00e2\u20ac\u009d", "\""),
        ("\u00e2\u20ac\u00a6", "..."),
    ]
    for bad, good in replacements:
        text = text.replace(bad, good)
    return text


def _source_icon(source: str) -> str:
    for key, icon in SOURCE_ICONS.items():
        if key.lower() in (source or "").lower():
            return icon
    return "📄"


def _provenance_badge(source: str) -> str:
    if "data.gov.in" in (source or "").lower():
        return '<span style="background:#0ea5e922;color:#0ea5e9;font-size:9px;font-weight:700;padding:1px 6px;border-radius:3px;border:1px solid #0ea5e944;margin-left:6px;letter-spacing:0.05em;">LIVE · data.gov.in</span>'
    return ""


def _impact_icon(itype: str) -> str:
    lower = itype.lower()
    for key, icon in IMPACT_ICONS.items():
        if key in lower:
            return icon
    return "📊"


def _evidence_card(ev: dict, color: str):
    icon      = _source_icon(ev.get("source", ""))
    title     = _sanitise(ev.get("title") or ev.get("id", "Evidence"))
    source    = ev.get("source", "")
    date      = ev.get("date", "")
    url       = ev.get("url", "")
    etype     = ev.get("type", "")
    badge     = _provenance_badge(source)
    link_html = (
        f'<a href="{url}" target="_blank" style="font-size:10px;color:{color};'
        f'text-decoration:none;margin-top:4px;display:inline-block;">View source →</a>'
        if url else ""
    )
    st.html(f"""
    <div style="background:#0a1628;border:1px solid {color}33;border-left:3px solid {color};
                border-radius:8px;padding:10px 14px;margin-bottom:8px;">
      <div style="display:flex;align-items:flex-start;gap:8px;">
        <span style="font-size:20px;line-height:1.2;">{icon}</span>
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
    """)


def _impact_card(imp: dict, color: str):
    """Metric-tile style card: big icon + big number + label."""
    itype   = imp.get("type") or imp.get("name") or ""
    value   = imp.get("value", "")
    unit    = imp.get("unit", "")
    desc    = _sanitise(imp.get("description", ""))[:90]
    source  = imp.get("source", "")
    val_str = (
        f"{value:,}" if isinstance(value, (int, float)) and value == int(value)
        else str(value) if value else "—"
    )
    badge = _provenance_badge(source)
    icon  = _impact_icon(itype)
    label = itype.replace("_", " ").title()
    st.html(f"""
    <div style="background:#060f1e;border:1px solid {color}33;border-radius:10px;
                padding:12px 14px;margin-bottom:8px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:8px;right:12px;font-size:28px;opacity:0.08;line-height:1;">{icon}</div>
      <div style="font-size:22px;margin-bottom:4px;line-height:1;">{icon}</div>
      <div style="font-size:1.7em;font-weight:900;color:{color};line-height:1;letter-spacing:-0.02em;">{val_str}</div>
      <div style="font-size:9.5px;color:#334155;margin-top:1px;margin-bottom:5px;">{unit}</div>
      <div style="font-size:11px;font-weight:700;color:#94a3b8;">{label}{badge}</div>
      <div style="font-size:10px;color:#475569;margin-top:3px;line-height:1.4;">{desc}</div>
    </div>
    """)


def _proof_chain_summary(data: dict, color: str):
    """Horizontal pill row showing counts from loaded event data."""
    impacts     = len(data.get("impacts", []))
    actors      = len(data.get("actors", []))
    evidence    = len(data.get("evidence", []))
    connections = len(data.get("connections", []))
    schemes     = len(data.get("schemes", []))
    pills = [
        ("📊", impacts,     "Impacts",      color),
        ("🏛️", schemes,    "Schemes",      "#a78bfa"),
        ("👥", actors,      "Actors",       "#38bdf8"),
        ("🗂️", evidence,   "Evidence",     "#0ea5e9"),
        ("🔗", connections, "Cross-links",  "#f97316"),
    ]
    pills_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{pc}15;color:{pc};border:1px solid {pc}44;'
        f'border-radius:20px;padding:3px 10px;font-size:10.5px;font-weight:700;">'
        f'{pic} {pv} {pn}</span>'
        for pic, pv, pn, pc in pills if pv > 0
    )
    st.html(f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 14px;">{pills_html}</div>')


def page():
    st.set_page_config(page_title="Scheme Delivery – PRAMAAN", layout="wide")
    render_topnav(active_page="Scheme Delivery")

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
    @keyframes sevPulse {
        0%, 100% { opacity: 1; } 50% { opacity: 0.5; }
    }
    div[data-testid="stButton"] button { font-size: 11px !important; padding: 4px 8px !important; }
    </style>
    """, unsafe_allow_html=True)

    if "deep_link_feed" in st.session_state:
        raw = st.session_state.pop("deep_link_feed")
        valid_ids = {e[0] for e in EVENTS}
        if raw in valid_ids:
            st.session_state.feed_sel = raw

    st.markdown(f"""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:8px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#22c55e;font-family:'Cinzel',serif;
                   letter-spacing:0.08em;white-space:nowrap;
                   animation:glowPulse 2.5s ease-in-out infinite;">SCHEME DELIVERY</span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        {_N_EVENTS} Events &nbsp;·&nbsp; Verified Government Sources &nbsp;·&nbsp;
        <span style="color:#475569;">PIB · NDMA · ISRO · IMD</span> &nbsp;·&nbsp;
        <span style="color:#334155;">Real Impact Data</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    _render_event_feed()


def _render_event_feed():
    from utils.api import safe_get
    from utils.events import EVENTS as _EVENTS_FULL, render_event_dropdown

    EVENTS_LOCAL = [e[:6] for e in _EVENTS_FULL]
    SEV_COLOR_L  = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}

    if "feed_sel" not in st.session_state:
        st.session_state.feed_sel = EVENTS_LOCAL[0][0]

    dcol, ncol = st.columns([3, 1], gap="small")
    with dcol:
        render_event_dropdown("feed_sel", "feed_event_drop")

    sel_evt  = next((e for e in EVENTS_LOCAL if e[0] == st.session_state.feed_sel), EVENTS_LOCAL[0])
    event_id, name, color, domain, date, sev = sel_evt
    sev_badge_color = SEV_COLOR_L.get(sev, "#64748b")
    domain_icon     = DOMAIN_ICONS.get(domain, "📡")
    sev_icon        = SEV_ICONS.get(sev, "⚪")

    with ncol:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("View AI Summary →", key=f"goto_brief_{event_id}", type="primary",
                     use_container_width=True):
            st.session_state["deep_link_brief"] = event_id
            st.switch_page("pages/proof_and_evidence.py")

    # ── Visual event card ───────────────────────────────────────────────────────
    st.html(
        f'<div style="background:linear-gradient(135deg,{color}12 0%,#020b14 60%);'
        f'border:1px solid {color}55;border-radius:12px;padding:14px 18px;margin-bottom:6px;">'
        f'<div style="display:flex;align-items:flex-start;gap:14px;">'
        f'<div style="font-size:3em;line-height:1;filter:drop-shadow(0 0 8px {color}88);">{domain_icon}</div>'
        f'<div style="flex:1;">'
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">'
        f'<span style="font-size:15px;font-weight:800;color:{color};">{name}</span>'
        f'<span style="background:{sev_badge_color}22;color:{sev_badge_color};font-weight:700;'
        f'font-size:10px;padding:2px 8px;border-radius:4px;border:1px solid {sev_badge_color}66;'
        f'text-transform:uppercase;letter-spacing:0.08em;animation:sevPulse 1.5s ease-in-out infinite;">'
        f'{sev_icon} {sev}</span>'
        f'</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
        f'<span style="background:{color}15;color:{color};font-size:10px;padding:2px 8px;'
        f'border-radius:12px;border:1px solid {color}33;font-weight:600;">{domain}</span>'
        f'<span style="color:#475569;font-size:10.5px;">🗓️ {date}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

    # ── Fetch data ──────────────────────────────────────────────────────────────
    with st.spinner(f"Loading data for {name}..."):
        data = safe_get(f"/ontology/events/{event_id}", silent=True) or {}
    if not data:
        st.html(
            '<div style="font-size:12px;color:#334155;padding:30px;text-align:center;'
            'border:1px dashed #1e293b;border-radius:8px;margin-top:8px;">'
            '📭 No data available for this event yet.</div>'
        )
        return

    # ── Proof chain summary bar ─────────────────────────────────────────────────
    _proof_chain_summary(data, color)

    # ── Three-panel layout ──────────────────────────────────────────────────────
    col_imp, col_ev = st.columns([1, 1], gap="large")

    with col_imp:
        impacts = data.get("impacts", [])
        st.markdown(
            f'<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.12em;font-weight:700;margin-bottom:10px;'
            f'border-bottom:1px solid #1e293b;padding-bottom:4px;">'
            f'📊 MEASURED IMPACTS ({len(impacts)})</div>',
            unsafe_allow_html=True,
        )
        if impacts:
            # 2-col grid of metric tiles
            pairs = [impacts[i:i+2] for i in range(0, len(impacts), 2)]
            for pair in pairs:
                pcols = st.columns(len(pair), gap="small")
                for pcol, imp in zip(pcols, pair):
                    with pcol:
                        _impact_card(imp, color)
        else:
            st.html('<div style="font-size:12px;color:#334155;padding:16px;text-align:center;'
                    'border:1px dashed #1e293b;border-radius:8px;">No impact data loaded.</div>')

        actors = data.get("actors", [])
        if actors:
            st.markdown(
                '<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
                'letter-spacing:0.12em;font-weight:700;margin-top:16px;margin-bottom:8px;'
                'border-bottom:1px solid #1e293b;padding-bottom:4px;">👥 KEY ACTORS</div>',
                unsafe_allow_html=True,
            )
            for a in actors:
                aname = _html.escape(a.get("name", a.get("actor_id", "")))
                atype = _html.escape(a.get("type", ""))
                aicon = "🏛️" if "government" in atype.lower() else ("🗳️" if "elected" in atype.lower() else "🔧")
                st.html(f"""
                <div style="background:#060f1e;border:1px solid #38bdf822;border-radius:8px;
                            padding:8px 12px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">
                  <span style="font-size:16px;">{aicon}</span>
                  <div>
                    <div style="font-size:12px;font-weight:700;color:#38bdf8;">{aname}</div>
                    <div style="font-size:10px;color:#334155;margin-top:1px;">{atype}</div>
                  </div>
                </div>
                """)

    with col_ev:
        evidence = data.get("evidence", [])
        st.markdown(
            f'<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.12em;font-weight:700;margin-bottom:10px;'
            f'border-bottom:1px solid #1e293b;padding-bottom:4px;">'
            f'🗂️ EVIDENCE SOURCES ({len(evidence)})</div>',
            unsafe_allow_html=True,
        )
        if evidence:
            for ev in evidence:
                _evidence_card(ev, color)
        else:
            st.html('<div style="font-size:12px;color:#334155;padding:16px;text-align:center;'
                    'border:1px dashed #1e293b;border-radius:8px;">No evidence nodes found.</div>')

        connections = data.get("connections", [])
        if connections:
            st.markdown(
                '<div style="font-size:0.65em;color:#f97316;text-transform:uppercase;'
                'letter-spacing:0.12em;font-weight:700;margin-top:16px;margin-bottom:8px;'
                'border-bottom:1px solid #1e293b;padding-bottom:4px;">🔗 CROSS-DOMAIN LINKS</div>',
                unsafe_allow_html=True,
            )
            for conn in connections:
                cd_raw = conn.get("domain", "")
                cd     = cd_raw.replace("DOM_", "").title() if cd_raw else ""
                cc     = DOMAIN_COLORS.get(cd, "#f97316")
                cd_ic  = DOMAIN_ICONS.get(cd, "🔗")
                cname  = _html.escape(conn.get("name", ""))
                reason = _html.escape(_sanitise(conn.get("reason", "")))
                st.html(f"""
                <div style="background:#0a1628;border:1px solid {cc}33;border-left:3px solid {cc};
                            border-radius:8px;padding:8px 12px;margin-bottom:6px;
                            display:flex;align-items:flex-start;gap:10px;">
                  <span style="font-size:18px;line-height:1.2;">{cd_ic}</span>
                  <div>
                    <div style="font-size:12px;font-weight:700;color:{cc};">{cname}</div>
                    <div style="font-size:10px;color:#64748b;margin-top:1px;">{cd}</div>
                    <div style="font-size:10px;color:#475569;margin-top:3px;font-style:italic;">"{reason}"</div>
                  </div>
                </div>
                """)

    # ── Schemes — Type 1 vs Type 2 visual split ─────────────────────────────────
    schemes = data.get("schemes", [])
    if schemes:
        _STATUS_COLOR = {
            "active":                "#22c55e",
            "at_risk":               "#ef4444",
            "partially_operational": "#f97316",
            "inactive":              "#64748b",
        }
        _STATUS_ICONS = {
            "active": "✅", "at_risk": "🚨", "partially_operational": "⚠️", "inactive": "⛔",
        }
        type1 = [s for s in schemes if (s.get("scheme_type") or "Type 2") == "Type 1"]
        type2 = [s for s in schemes if (s.get("scheme_type") or "Type 2") != "Type 1"]

        st.html('<div style="height:8px;"></div>')
        st.html(
            f'<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.12em;font-weight:700;margin-bottom:10px;'
            f'border-bottom:1px solid #1e293b;padding-bottom:4px;">'
            f'🏛️ GOVERNMENT SCHEMES ({len(schemes)})'
            f'{"&nbsp;&nbsp;<span style=\'color:#ef4444;\'>🚨 " + str(len(type1)) + " Emergency</span>" if type1 else ""}'
            f'{"&nbsp;·&nbsp;<span style=\'color:#22c55e;\'>🏗️ " + str(len(type2)) + " Structural</span>" if type2 else ""}'
            f'</div>'
        )

        # Render Type 1 first (if any), then Type 2
        for group_label, group_icon, group_color, group in [
            ("TYPE 1 — EMERGENCY",  "🚨", "#ef4444", type1),
            ("TYPE 2 — STRUCTURAL", "🏗️", "#22c55e", type2),
        ]:
            if not group:
                continue
            st.html(
                f'<div style="font-size:9px;color:{group_color};font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                f'{group_icon} {group_label}</div>'
            )
            chunks = [group[i:i+3] for i in range(0, len(group), 3)]
            for chunk in chunks:
                scols = st.columns(len(chunk), gap="medium")
                for scol, sch in zip(scols, chunk):
                    sid        = sch.get("scheme_id") or ""
                    sname      = _html.escape(sch.get("name") or sid or "—")
                    budget     = sch.get("budget_crore")
                    status_raw = sch.get("status") or "active"
                    status_lbl = _html.escape(status_raw.replace("_", " ").upper())
                    ministry   = _html.escape(sch.get("ministry") or "")
                    desc_raw   = sch.get("description") or ""
                    desc       = _html.escape(_sanitise(desc_raw)[:120] if desc_raw else "")
                    sc         = _STATUS_COLOR.get(status_raw, "#64748b")
                    st_icon    = _STATUS_ICONS.get(status_raw, "⚪")
                    try:
                        budget_str = f"₹{int(budget):,} Cr" if budget else "—"
                    except (TypeError, ValueError):
                        budget_str = "—"
                    with scol:
                        st.html(f"""
                        <div style="background:linear-gradient(160deg,{group_color}0d 0%,#060f1e 50%);
                                    border:1px solid {group_color}44;border-top:3px solid {group_color};
                                    border-radius:10px;padding:12px 14px;margin-bottom:10px;">
                          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                            <span style="font-size:22px;line-height:1;">{group_icon}</span>
                            <span style="background:{sc}18;color:{sc};font-size:9px;font-weight:700;
                                         padding:2px 7px;border-radius:4px;border:1px solid {sc}44;">
                              {st_icon} {status_lbl}
                            </span>
                          </div>
                          <div style="font-size:13px;font-weight:800;color:#e2e8f0;line-height:1.2;margin-bottom:6px;">{sname}</div>
                          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
                            <span style="font-size:12px;font-weight:700;color:{group_color};">{budget_str}</span>
                            <span style="font-size:10px;color:#475569;background:#0a1628;padding:1px 6px;border-radius:4px;">{ministry}</span>
                          </div>
                          <div style="font-size:10px;color:#475569;line-height:1.5;border-top:1px solid #1e293b;padding-top:6px;">{desc}</div>
                        </div>
                        """)

    # ── Event description ───────────────────────────────────────────────────────
    event_data = data.get("event", {})
    if event_data.get("description"):
        st.markdown("---")
        ed_text = _html.escape(_sanitise(event_data["description"]))
        st.html(
            f'<div style="background:#0a1628;border:1px solid {color}22;border-radius:10px;'
            f'padding:14px 18px;">'
            f'<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.12em;font-weight:700;margin-bottom:8px;">📝 EVENT DESCRIPTION</div>'
            f'<div style="font-size:13px;color:#94a3b8;line-height:1.7;">{ed_text}</div>'
            f'</div>'
        )
        if event_data.get("source_url"):
            st.markdown(
                f'<a href="{event_data["source_url"]}" target="_blank" '
                f'style="font-size:11px;color:{color};text-decoration:none;">Primary source →</a>',
                unsafe_allow_html=True,
            )


page()
