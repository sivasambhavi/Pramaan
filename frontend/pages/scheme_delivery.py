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
import plotly.graph_objects as go
from utils.api import safe_get
from utils.events import EVENTS as _EVENTS_FULL, N_EVENTS as _N_EVENTS, render_event_dropdown
from components.topnav import render_topnav
from components.ontology_model import render_ontology_model

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="#020b14",
    plot_bgcolor="#060f1e",
    font=dict(family="monospace", color="#94a3b8", size=11),
    margin=dict(l=0, r=10, t=10, b=0),
    hoverlabel=dict(bgcolor="#0a1628", font_size=11, bordercolor="#334155"),
    showlegend=False,
)

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
    """KPI-tile: big value, unit bar, label, description."""
    raw_id  = imp.get("id") or ""
    itype   = imp.get("type") or imp.get("name") or raw_id.replace("IMP_", "").replace("_", " ").title() or "Impact"
    value   = imp.get("value", "")
    unit    = _html.escape(imp.get("unit", "") or "")
    desc    = _html.escape(_sanitise(imp.get("description", "") or "")[:110])
    source  = imp.get("source", "")
    badge   = _provenance_badge(source)
    label   = _html.escape(itype.replace("_", " ").title()) if itype else "Impact"
    try:
        val_str = f"{int(value):,}" if isinstance(value, (int, float)) and float(value) == int(float(value)) else str(value) if value else "—"
    except (TypeError, ValueError):
        val_str = str(value) if value else "—"
    val_str = _html.escape(val_str)
    # accent bar width — cap at 100%
    try:
        bar_pct = min(100, max(4, abs(float(value)) / 1000)) if isinstance(value, (int, float)) else 40
    except (TypeError, ValueError):
        bar_pct = 40
    st.html(f"""
    <div style="background:#060f1e;border:1px solid {color}33;border-radius:8px;
                padding:12px 14px;margin-bottom:8px;border-left:3px solid {color};">
      <div style="font-size:1.6em;font-weight:900;color:{color};line-height:1;letter-spacing:-0.02em;">{val_str}</div>
      <div style="background:#1e293b;border-radius:2px;height:3px;margin:4px 0 6px;">
        <div style="background:{color};width:{bar_pct}%;height:3px;border-radius:2px;opacity:0.7;"></div>
      </div>
      <div style="font-size:10px;color:#64748b;margin-bottom:4px;">{unit}</div>
      <div style="font-size:11.5px;font-weight:700;color:#94a3b8;">{label}{badge}</div>
      <div style="font-size:10px;color:#475569;margin-top:4px;line-height:1.5;">{desc}</div>
    </div>
    """)


def _render_impacts_chart(impacts: list, color: str):
    """Horizontal bar chart for numeric impacts + text cards for non-numeric."""
    numeric, text_only = [], []
    for imp in impacts:
        raw_id = imp.get("id") or ""
        label  = imp.get("type") or imp.get("name") or raw_id.replace("IMP_", "").replace("_", " ").title() or "Impact"
        label  = label[:35]
        val    = imp.get("value")
        unit   = imp.get("unit", "") or ""
        desc   = _sanitise(imp.get("description", "") or "")[:80]
        try:
            fval = float(str(val).replace(",", "").replace("%", "").replace("₹", "").replace("+", "").replace("-", ""))
            numeric.append({"label": label, "value": fval, "raw": str(val), "unit": unit, "desc": desc})
        except (TypeError, ValueError):
            text_only.append({"label": label, "raw": str(val) if val else "—", "unit": unit, "desc": desc})

    if numeric:
        labels = [n["label"] for n in numeric]
        values = [n["value"] for n in numeric]
        units  = [n["unit"] for n in numeric]
        raws   = [n["raw"] for n in numeric]
        descs  = [n["desc"] for n in numeric]
        max_v  = max(abs(v) for v in values) or 1
        bar_colors = [color if v >= 0 else "#ef4444" for v in values]
        hover = [f"<b>{l}</b><br>{r} {u}<br><i>{d}</i>" for l, r, u, d in zip(labels, raws, units, descs)]
        fig = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=bar_colors, opacity=0.85,
                        line=dict(color=[c.replace(")", ",0.5)").replace("rgb", "rgba") for c in bar_colors], width=0)),
            text=raws,
            textposition="outside",
            textfont=dict(size=10, color="#e2e8f0"),
            hovertext=hover,
            hoverinfo="text",
        ))
        h = max(160, len(numeric) * 36)
        fig.update_layout(**_PLOTLY_LAYOUT, height=h,
                          xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
                                     range=[0, max_v * 1.35], showticklabels=False),
                          yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, color="#94a3b8"),
                                     categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # non-numeric as compact KPI chips
    if text_only:
        chips = "".join(
            f'<div style="background:#060f1e;border:1px solid {color}22;border-left:3px solid {color};'
            f'border-radius:6px;padding:7px 12px;margin-bottom:6px;">'
            f'<div style="font-size:13px;font-weight:800;color:{color};">{t["raw"]} <span style="font-size:9.5px;color:#334155;font-weight:400;">{t["unit"]}</span></div>'
            f'<div style="font-size:10.5px;color:#94a3b8;font-weight:600;">{t["label"]}</div>'
            f'<div style="font-size:9.5px;color:#475569;margin-top:2px;">{t["desc"]}</div>'
            f'</div>'
            for t in text_only
        )
        st.html(chips)


def _render_schemes_chart(schemes: list):
    """Budget comparison bar chart + utilization bars for all schemes."""
    budgets = [(s.get("name") or s.get("scheme_id") or "—",
                s.get("budget_crore") or 0,
                "#ef4444" if (s.get("scheme_type") or "Type 2") == "Type 1" else "#22c55e",
                s.get("scheme_type_label") or s.get("scheme_type") or "Type 2",
                s.get("status") or "active")
               for s in schemes if s.get("budget_crore")]

    if not budgets:
        return

    names, vals, colors, types, statuses = zip(*sorted(budgets, key=lambda x: x[1]))
    hover = [f"<b>{n}</b><br>₹{v:,.0f} Cr<br>{t} · {s}" for n, v, t, s in zip(names, vals, types, statuses)]
    short_names = [n[:28] + "…" if len(n) > 28 else n for n in names]

    fig = go.Figure(go.Bar(
        x=list(vals),
        y=list(short_names),
        orientation="h",
        marker=dict(color=list(colors), opacity=0.8,
                    line=dict(color="rgba(0,0,0,0)", width=0)),
        text=[f"₹{v:,.0f} Cr" for v in vals],
        textposition="outside",
        textfont=dict(size=10, color="#e2e8f0"),
        hovertext=hover,
        hoverinfo="text",
    ))
    h = max(160, len(budgets) * 38)
    max_v = max(vals)
    fig.update_layout(**_PLOTLY_LAYOUT, height=h,
                      xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
                                 range=[0, max_v * 1.4], showticklabels=False),
                      yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, color="#94a3b8"),
                                 categoryorder="total ascending"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _proof_chain_summary(data: dict, color: str):
    """Horizontal stat pill row showing counts from loaded event data."""
    counts = [
        ("IMPACTS",      len(data.get("impacts", [])),      color),
        ("SCHEMES",      len(data.get("schemes", [])),      "#a78bfa"),
        ("ACTORS",       len(data.get("actors", [])),       "#38bdf8"),
        ("EVIDENCE",     len(data.get("evidence", [])),     "#0ea5e9"),
        ("CROSS-LINKS",  len(data.get("connections", [])),  "#f97316"),
    ]
    pills_html = "".join(
        f'<span style="display:inline-flex;align-items:baseline;gap:5px;'
        f'background:{pc}12;border:1px solid {pc}33;'
        f'border-radius:6px;padding:4px 12px;font-size:10px;">'
        f'<span style="font-size:14px;font-weight:900;color:{pc};">{pv}</span>'
        f'<span style="color:#475569;font-weight:600;letter-spacing:0.06em;">{pn}</span>'
        f'</span>'
        for pn, pv, pc in counts if pv > 0
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

    # Mirror ontology graph: pre-init to None so dropdown starts on "— All Events —"
    if "feed_sel" not in st.session_state:
        st.session_state.feed_sel = None

    dcol, ncol = st.columns([3, 1], gap="small")
    with dcol:
        render_event_dropdown("feed_sel", "feed_event_drop", include_all=True)

    sel_evt = next((e for e in EVENTS_LOCAL if e[0] == st.session_state.get("feed_sel")), None)

    if sel_evt is None:
        st.html(
            '<div style="font-size:13px;color:#334155;padding:40px;text-align:center;'
            'border:1px dashed #1e293b;border-radius:10px;margin-top:12px;">'
            'Select an event above to view '
            '<span style="color:#22c55e;font-weight:700;">scheme delivery</span>'
            ' analysis.</div>'
        )
        return

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
        f'<div style="background:#0a1628;border:1px solid {color}44;border-left:4px solid {color};'
        f'border-radius:8px;padding:12px 18px;margin-bottom:6px;display:flex;align-items:center;gap:16px;">'
        f'<div style="width:4px;height:40px;background:{color};border-radius:2px;flex-shrink:0;"></div>'
        f'<div style="flex:1;">'
        f'<div style="font-size:15px;font-weight:800;color:{color};margin-bottom:4px;">{_html.escape(name)}</div>'
        f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">'
        f'<span style="background:{color}18;color:{color};font-size:9.5px;padding:2px 8px;'
        f'border-radius:4px;font-weight:600;">{_html.escape(domain)}</span>'
        f'<span style="color:#334155;font-size:10px;">{_html.escape(date)}</span>'
        f'<span style="background:{sev_badge_color}22;color:{sev_badge_color};font-weight:700;'
        f'font-size:9px;padding:2px 8px;border-radius:4px;border:1px solid {sev_badge_color}44;'
        f'text-transform:uppercase;letter-spacing:0.06em;">{sev.upper()}</span>'
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
            f'MEASURED IMPACTS ({len(impacts)})</div>',
            unsafe_allow_html=True,
        )
        if impacts:
            _render_impacts_chart(impacts, color)
        else:
            st.html('<div style="font-size:12px;color:#334155;padding:16px;text-align:center;'
                    'border:1px dashed #1e293b;border-radius:8px;">No impact data loaded.</div>')

        actors = data.get("actors", [])
        if actors:
            st.markdown(
                '<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
                'letter-spacing:0.12em;font-weight:700;margin-top:16px;margin-bottom:8px;'
                'border-bottom:1px solid #1e293b;padding-bottom:4px;">KEY ACTORS</div>',
                unsafe_allow_html=True,
            )
            for a in actors:
                aname = _html.escape(a.get("name", a.get("actor_id", "")))
                atype = _html.escape(a.get("type", ""))
                st.html(f"""
                <div style="background:#060f1e;border:1px solid #38bdf822;border-left:3px solid #38bdf844;
                            border-radius:6px;padding:7px 12px;margin-bottom:5px;">
                  <div style="font-size:12px;font-weight:700;color:#38bdf8;">{aname}</div>
                  <div style="font-size:10px;color:#334155;margin-top:1px;">{atype}</div>
                </div>
                """)

    with col_ev:
        evidence = data.get("evidence", [])
        st.markdown(
            f'<div style="font-size:0.65em;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.12em;font-weight:700;margin-bottom:10px;'
            f'border-bottom:1px solid #1e293b;padding-bottom:4px;">'
            f'EVIDENCE SOURCES ({len(evidence)})</div>',
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
                'border-bottom:1px solid #1e293b;padding-bottom:4px;">CROSS-DOMAIN LINKS</div>',
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
                            border-radius:8px;padding:8px 12px;margin-bottom:6px;">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
                    <div style="width:8px;height:8px;border-radius:50%;background:{cc};flex-shrink:0;"></div>
                    <div style="font-size:12px;font-weight:700;color:{cc};">{cname}</div>
                    <span style="font-size:9px;color:#334155;background:{cc}15;padding:1px 6px;border-radius:3px;">{cd}</span>
                  </div>
                  <div style="font-size:10px;color:#475569;font-style:italic;">"{reason}"</div>
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
            f'GOVERNMENT SCHEMES ({len(schemes)})'
            f'{"&nbsp;&nbsp;<span style=\'color:#ef4444;\'>" + str(len(type1)) + " Emergency</span>" if type1 else ""}'
            f'{"&nbsp;·&nbsp;<span style=\'color:#22c55e;\'>" + str(len(type2)) + " Structural</span>" if type2 else ""}'
            f'</div>'
        )

        # Budget comparison chart
        _render_schemes_chart(schemes)

        # Render Type 1 first (if any), then Type 2
        for group_label, group_color, group in [
            ("TYPE 1 — EMERGENCY",  "#ef4444", type1),
            ("TYPE 2 — STRUCTURAL", "#22c55e", type2),
        ]:
            if not group:
                continue
            st.html(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                f'<div style="width:3px;height:14px;background:{group_color};border-radius:2px;"></div>'
                f'<span style="font-size:9px;color:{group_color};font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.1em;">{group_label}</span>'
                f'</div>'
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
                    utilization = sch.get("utilization_pct") or 0
                    try:
                        budget_str = f"₹{int(budget):,} Cr" if budget else "—"
                    except (TypeError, ValueError):
                        budget_str = "—"
                    with scol:
                        util_bar = f"""
                          <div style="margin:6px 0 4px;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                              <span style="font-size:9px;color:#334155;">Utilization</span>
                              <span style="font-size:9px;font-weight:700;color:{group_color};">{utilization}%</span>
                            </div>
                            <div style="background:#1e293b;border-radius:2px;height:4px;">
                              <div style="background:{group_color};width:{utilization}%;height:4px;border-radius:2px;opacity:0.8;"></div>
                            </div>
                          </div>
                        """ if utilization else ""
                        st.html(f"""
                        <div style="background:#060f1e;border:1px solid {group_color}33;
                                    border-top:3px solid {group_color};
                                    border-radius:8px;padding:12px 14px;margin-bottom:10px;">
                          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                            <div style="font-size:13px;font-weight:800;color:#e2e8f0;line-height:1.2;flex:1;">{sname}</div>
                            <span style="background:{sc}18;color:{sc};font-size:9px;font-weight:700;
                                         padding:2px 7px;border-radius:4px;border:1px solid {sc}33;
                                         white-space:nowrap;margin-left:8px;">{status_lbl}</span>
                          </div>
                          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">
                            <span style="font-size:12px;font-weight:700;color:{group_color};">{budget_str}</span>
                            <span style="font-size:10px;color:#475569;background:#0a1628;padding:1px 6px;border-radius:4px;">{ministry}</span>
                          </div>
                          {util_bar}
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
