"""
01_National_Intelligence.py — PRAMAAN v5
National Intelligence: world map with event pins, domain-colored markers, event detail cards.
Horizontal chip filter bar. 17 events across 7 domains.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.api import safe_get
from utils.events import MAP_EVENTS as EVENT_META, EVENTS as _EVENTS_FULL, N_EVENTS, render_event_dropdown
from components.topnav import render_topnav

DOMAIN_ORDER = ["Climate", "Defense", "Economics", "Society", "Governance", "Geopolitics", "Technology"]

ALL_DOMAINS = {
    "Climate":     "#22c55e",
    "Defense":     "#f97316",
    "Economics":   "#38bdf8",
    "Society":     "#fb7185",
    "Governance":  "#06b6d4",
    "Geopolitics": "#a78bfa",
    "Technology":  "#facc15",
}

DOMAIN_EMOJI = {
    "Climate":     "🟢",
    "Defense":     "🟠",
    "Economics":   "🔵",
    "Society":     "🔴",
    "Governance":  "🔵",
    "Geopolitics": "🟣",
    "Technology":  "🟡",
}

SEVERITY_BADGE = {
    "critical": ("<span style='background:#ef444422;color:#fca5a5;font-weight:700;font-size:9px;padding:1px 5px;border-radius:4px;border:1px solid #ef444466;'>CRITICAL</span>", 10),
    "high":     ("<span style='background:#f9731622;color:#fdba74;font-weight:700;font-size:9px;padding:1px 5px;border-radius:4px;border:1px solid #f9731666;'>HIGH</span>",      8),
    "medium":   ("<span style='background:#facc1522;color:#fde047;font-weight:700;font-size:9px;padding:1px 5px;border-radius:4px;border:1px solid #facc1566;'>MEDIUM</span>",    6),
}

DEFAULT_CENTER = [35.0, 57.0]
DEFAULT_ZOOM   = 4

# Per-domain / per-severity chip CSS.
# Uses CSS :has() (Chrome 105+, Safari 15.4+, Firefox 121+) to target
# only the filter chip row — identified by the #pramaan-filter-bar sentinel.
# Active chips = solid colored fill. Inactive chips = colored border + text.


def page():
    st.set_page_config(page_title="National Intelligence – PRAMAAN", layout="wide")
    render_topnav(active_page="National Intelligence")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; }
    .stFoliumMap iframe { border-radius: 12px !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(20,184,166,0.7), 0 0 30px rgba(20,184,166,0.4), 0 0 50px rgba(20,184,166,0.2); }
        50%       { text-shadow: 0 0 25px rgba(20,184,166,1), 0 0 60px rgba(20,184,166,0.8), 0 0 100px rgba(20,184,166,0.5), 0 0 140px rgba(20,184,166,0.2); }
    }
    /* Compact selects */
    div[data-baseweb="select"] * { font-size: 13px !important; }
    div[data-baseweb="select"] > div { min-height: 26px !important; padding-top: 1px !important; padding-bottom: 1px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state + query param sync ──────────────────────────────────────
    sel_param = st.query_params.get("sel", None)
    if sel_param and sel_param in EVENT_META:
        st.session_state.sel_event = sel_param

    # Domain filter — driven by ?d= query param when present
    qp_d = st.query_params.get("d", "")
    if qp_d:
        st.session_state.active_domains = set(qp_d.split(",")) & set(DOMAIN_ORDER)
    elif "active_domains" not in st.session_state:
        st.session_state.active_domains = set(DOMAIN_ORDER)

    if "sel_event" not in st.session_state:
        st.session_state.sel_event = None

    # ── Fetch live data ────────────────────────────────────────────────────────
    api_events = {}
    data = safe_get("/ontology/events", silent=True)
    if data:
        for evt in data.get("events", []):
            api_events[evt["event_id"]] = evt

    # ── Filter events ──────────────────────────────────────────────────────────
    active_domains    = st.session_state.active_domains
    _sev_sel          = st.session_state.get("sev_filter", ["Critical", "High", "Medium"])
    active_severities = {s.lower() for s in _sev_sel} if _sev_sel else {"critical", "high", "medium"}
    filtered_events = {
        eid: meta for eid, meta in EVENT_META.items()
        if meta[3] in active_domains and meta[6] in active_severities
    }

    sel = st.session_state.sel_event
    if sel and sel not in filtered_events:
        st.session_state.sel_event = None
        sel = None

    n_events  = len(filtered_events)
    n_domains = len({m[3] for m in filtered_events.values()}) if filtered_events else 0

    # ── Header ─────────────────────────────────────────────────────────────────
    header_slot = st.empty()
    header_slot.markdown(f"""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:6px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#14b8a6;
                   font-family:'Cinzel',serif;letter-spacing:0.08em;white-space:nowrap;
                   animation:glowPulse 2.5s ease-in-out infinite;">
        NATIONAL INTELLIGENCE
      </span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        {n_events} Events &nbsp;·&nbsp; {n_domains} Active Domains &nbsp;·&nbsp; Verified Data
        &nbsp;·&nbsp; <span style="color:#475569;">PIB · NDMA · ISRO · IMD</span>
        &nbsp;·&nbsp; <span style="color:#334155;">Neo4j Knowledge Graph</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:12px;color:#475569;margin-bottom:6px;">'
        f'Tracks {N_EVENTS} high-impact events — from climate disasters to geopolitical shifts — '
        f'plotted on a live map with verified government evidence and cross-domain connections.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Event dropdown ─────────────────────────────────────────────────────────
    render_event_dropdown("sel_event", "map_event_dropdown", include_all=True)

    # ── Chip filter bar — pure HTML anchors, no Streamlit buttons ────────────
    dcounts = {d: sum(1 for m in EVENT_META.values() if m[3] == d) for d in DOMAIN_ORDER}
    sev_str = ",".join(sorted(active_severities))

    def _chip_href(domain: str) -> str:
        new_d = set(active_domains)
        if domain in new_d:
            new_d.discard(domain)
            if not new_d:
                return "#"
        else:
            new_d.add(domain)
        return f"?d={','.join(sorted(new_d))}&s={sev_str}"

    chips_html = (
        '<div style="display:flex;align-items:center;gap:5px;flex-wrap:nowrap;'
        'padding:5px 0 4px;border-top:1px solid #1e293b;border-bottom:1px solid #1e293b;'
        'margin-bottom:6px;overflow-x:auto;">'
    )
    for domain in DOMAIN_ORDER:
        is_on  = domain in active_domains
        color  = ALL_DOMAINS[domain]
        emoji  = DOMAIN_EMOJI.get(domain, "●")
        cnt    = dcounts.get(domain, 0)
        border = f"1px solid {color}" if is_on else f"1px solid {color}40"
        text_c = color if is_on else f"{color}50"
        chips_html += (
            f'<a href="{_chip_href(domain)}" style="display:inline-flex;align-items:center;'
            f'border-radius:20px;padding:2px 9px;font-size:10px;font-weight:600;'
            f'line-height:18px;white-space:nowrap;border:{border};color:{text_c};'
            f'background:transparent;text-decoration:none;flex-shrink:0;">'
            f'{emoji} {domain} {cnt}</a>'
        )
    chips_html += '</div>'

    sev_col, chips_col = st.columns([1.3, 5], gap="small")
    with chips_col:
        st.markdown(chips_html, unsafe_allow_html=True)
    with sev_col:
        st.multiselect(
            "Severity",
            options=["Critical", "High", "Medium"],
            default=["Critical", "High", "Medium"],
            label_visibility="collapsed",
            placeholder="All severities",
            key="sev_filter",
        )

    # ── Map center ─────────────────────────────────────────────────────────────
    if sel and sel in filtered_events:
        lat0, lon0 = filtered_events[sel][0], filtered_events[sel][1]
        zoom_in    = 6 if abs(lon0) < 45 or abs(lon0) > 85 else 7
        map_center, map_zoom = [lat0, lon0], zoom_in
    else:
        map_center, map_zoom = DEFAULT_CENTER, DEFAULT_ZOOM

    # ── Build Folium map ───────────────────────────────────────────────────────
    m = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles="CartoDB positron",
        scrollWheelZoom=False,
    )
    m.get_root().html.add_child(folium.Element(
        "<style>.leaflet-control-attribution { display: none !important; }</style>"
    ))

    for event_id, (lat, lon, name, domain, color, date, sev) in filtered_events.items():
        api          = api_events.get(event_id, {})
        desc         = (api.get("description") or "")[:140]
        if len(api.get("description") or "") > 140:
            desc += "…"
        impact_count = api.get("impact_count", 0)
        sev_label, radius = SEVERITY_BADGE.get(sev, SEVERITY_BADGE["high"])
        is_selected  = (event_id == sel)

        popup_html = f"""
        <div style="font-family:Inter,sans-serif;width:230px;background:#0d1117;
                    color:#e2e8f0;padding:12px 14px;border-radius:10px;
                    border:1px solid {color}55;box-shadow:0 4px 20px rgba(0,0,0,0.6);">
          <div style="font-size:13px;font-weight:700;color:{color};margin-bottom:3px;">{name}</div>
          <div style="font-size:10.5px;color:#64748b;margin-bottom:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <span>{domain}</span><span>·</span><span>{date}</span><span>·</span>{sev_label}
          </div>
          <div style="font-size:11px;color:#94a3b8;line-height:1.45;margin-bottom:8px;">{desc}</div>
          <div style="font-size:10px;color:#475569;border-top:1px solid #1e293b;padding-top:6px;">
            {impact_count} impact nodes &nbsp;·&nbsp; {event_id}
          </div>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.9 if is_selected else 0.85,
            weight=3 if is_selected else 2,
            popup=folium.Popup(popup_html, max_width=250, show=is_selected),
            tooltip=folium.Tooltip(f"<b style='color:{color}'>{name}</b><br>{domain} · {date}"),
        ).add_to(m)

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius + 8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.15 if is_selected else 0.08,
            weight=1,
            interactive=False,
        ).add_to(m)

    # ── Full-width map ──────────────────────────────────────────────────────────
    map_result = st_folium(m, width="100%", height=520,
                           returned_objects=["last_object_clicked"])

    # ── Sync map marker click → session state ──────────────────────────────────
    clicked = (map_result or {}).get("last_object_clicked")
    if clicked:
        clat, clng = clicked.get("lat"), clicked.get("lng")
        if clat and clng:
            best_eid, best_dist = None, float("inf")
            for eid, (lat, lon, *_) in EVENT_META.items():
                dist = abs(lat - clat) + abs(lon - clng)
                if dist < best_dist:
                    best_dist, best_eid = dist, eid
            if best_eid and best_dist < 1.5:
                if st.session_state.sel_event != best_eid:
                    st.session_state.sel_event = best_eid
                    st.rerun()

    # ── Event detail panel (below map, horizontal) ─────────────────────────────
    if sel and sel in EVENT_META:
        lat0, lon0, sname, sdomain, scolor, sdate, ssev = EVENT_META[sel]
        sev_label, _ = SEVERITY_BADGE.get(ssev, SEVERITY_BADGE["high"])
        detail   = safe_get(f"/ontology/events/{sel}", silent=True) or {}
        evt_data = detail.get("event", {})
        impacts  = detail.get("impacts", [])
        schemes  = detail.get("schemes", [])
        sdesc    = evt_data.get("description", "") or api_events.get(sel, {}).get("description", "")

        detail_col, impact_col, scheme_col, action_col = st.columns([2.2, 1.5, 1.5, 1], gap="medium")

        with detail_col:
            st.markdown(f"""
            <div style="border-left:4px solid {scolor};padding:10px 14px;
                        background:#0a1628;border-radius:6px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:13px;font-weight:800;color:{scolor};">{sname}</span>
                {sev_label}
              </div>
              <div style="font-size:10px;color:#64748b;margin-bottom:6px;">{sdomain} · {sdate}</div>
              <div style="font-size:10.5px;color:#94a3b8;line-height:1.5;">
                {sdesc[:220]}{"…" if len(sdesc) > 220 else ""}
              </div>
            </div>
            """, unsafe_allow_html=True)

        with impact_col:
            st.markdown(
                '<div style="font-size:9px;color:#475569;font-weight:700;text-transform:uppercase;'
                'letter-spacing:0.08em;margin-bottom:6px;">MEASURED IMPACTS</div>',
                unsafe_allow_html=True,
            )
            if impacts:
                for imp in impacts[:5]:
                    itype = imp.get("type", "").replace("_", " ").title()
                    val   = imp.get("value", "")
                    unit  = imp.get("unit", "")
                    st.markdown(
                        f'<div style="font-size:10px;color:#64748b;padding:2px 0 2px 8px;'
                        f'border-left:2px solid {scolor}44;margin-bottom:3px;">• {itype}'
                        f'{f" — {val} {unit}" if val else ""}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown('<div style="font-size:10px;color:#334155;">Loading…</div>',
                            unsafe_allow_html=True)

        with scheme_col:
            st.markdown(
                '<div style="font-size:9px;color:#475569;font-weight:700;text-transform:uppercase;'
                'letter-spacing:0.08em;margin-bottom:6px;">GOVT RESPONSE</div>',
                unsafe_allow_html=True,
            )
            if schemes:
                for s in schemes[:4]:
                    sname_s   = s.get("name", s.get("scheme_id", ""))[:28]
                    sbudget   = s.get("budget_crore")
                    bstr      = f" · ₹{sbudget:,.0f} Cr" if sbudget else ""
                    st.markdown(
                        f'<div style="font-size:10px;color:#facc15;padding:2px 0 2px 8px;'
                        f'border-left:2px solid #facc1544;margin-bottom:3px;">• {sname_s}{bstr}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                actors = detail.get("actors", [])
                for a in actors[:3]:
                    aname = a.get("name", "")[:28]
                    st.markdown(
                        f'<div style="font-size:10px;color:#38bdf8;padding:2px 0 2px 8px;'
                        f'border-left:2px solid #38bdf844;margin-bottom:3px;">• {aname}</div>',
                        unsafe_allow_html=True,
                    )

        with action_col:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Scheme Tracker →", key=f"goto_graph_{sel}",
                         use_container_width=True, type="primary"):
                st.session_state["deep_link_event"] = sel
                st.switch_page("pages/02_Scheme_Tracker.py")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Proof & Evidence →", key=f"goto_proof_{sel}",
                         use_container_width=True):
                st.session_state["deep_link_brief"] = sel
                st.switch_page("pages/04_Proof_and_Evidence.py")

    # ── Live Ingestion Panel ────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.expander("📡 Live Ingestion — Fetch & Ingest Real-Time Governance News", expanded=False):
        _render_live_ingestion()


def _render_live_ingestion():
    """Live ingestion: scrape Google News → extract entities → ingest to Neo4j."""
    import time
    import requests as _req
    import streamlit as st
    from utils.api import safe_get

    BACKEND = "http://localhost:8000"

    PRESET_QUERIES = [
        "NDRF disaster relief India 2024",
        "AMRUT urban infrastructure India",
        "PMAY housing scheme India",
        "India flood cyclone relief fund 2024",
        "Ayushman Bharat health scheme India",
        "India semiconductor PLI scheme 2024",
        "Jal Jeevan Mission water supply India",
        "India defence budget DRDO 2024",
        "India G20 trade geopolitics 2024",
        "India climate disaster NDMA response",
    ]

    # Auto-refresh timer state
    if "ingestion_last_run" not in st.session_state:
        st.session_state.ingestion_last_run   = 0.0
    if "ingestion_results"  not in st.session_state:
        st.session_state.ingestion_results    = None
    if "ingestion_query"    not in st.session_state:
        st.session_state.ingestion_query      = PRESET_QUERIES[0]
    if "auto_ingest_on"     not in st.session_state:
        st.session_state.auto_ingest_on       = False

    # ── Controls row ────────────────────────────────────────────────────────
    ctrl_col, btn_col, auto_col = st.columns([3, 1, 1.2], gap="small")

    with ctrl_col:
        query = st.selectbox(
            "News query",
            PRESET_QUERIES,
            index=PRESET_QUERIES.index(st.session_state.ingestion_query)
                  if st.session_state.ingestion_query in PRESET_QUERIES else 0,
            label_visibility="collapsed",
            key="ingestion_query_sel",
        )
        st.session_state.ingestion_query = query

    with btn_col:
        fetch_clicked = st.button("🔍 Fetch & Extract", use_container_width=True, type="primary",
                                  key="live_fetch_btn")

    with auto_col:
        auto_on = st.toggle("Auto (5 min)", value=st.session_state.auto_ingest_on, key="auto_ingest_tog")
        st.session_state.auto_ingest_on = auto_on

    # Auto-refresh trigger
    now = time.time()
    if auto_on and (now - st.session_state.ingestion_last_run) > 300:
        fetch_clicked = True

    # ── Fetch ────────────────────────────────────────────────────────────────
    if fetch_clicked:
        with st.spinner(f"Scraping news for: {query} …"):
            try:
                resp = _req.get(
                    f"{BACKEND}/scrape/news",
                    params={"q": query},
                    timeout=30,
                )
                if resp.status_code == 200:
                    st.session_state.ingestion_results = resp.json()
                    st.session_state.ingestion_last_run = time.time()
                else:
                    st.error(f"Scrape failed: {resp.status_code}")
                    st.session_state.ingestion_results = None
            except Exception as e:
                st.error(f"Connection error: {e}")
                st.session_state.ingestion_results = None

    # ── Show results ─────────────────────────────────────────────────────────
    results = st.session_state.ingestion_results
    if not results:
        st.markdown(
            '<div style="font-size:11px;color:#334155;padding:12px;text-align:center;">'
            'Click "Fetch & Extract" to scrape live governance news and extract entities.</div>',
            unsafe_allow_html=True,
        )
        return

    articles  = results.get("articles", [])
    entities  = results.get("entities", [])
    relations = results.get("relations", [])
    dropped   = results.get("articles_dropped", 0)
    message   = results.get("message", "")

    # Summary bar
    st.markdown(
        f'<div style="background:#0a1628;border:1px solid #22c55e33;border-radius:8px;'
        f'padding:8px 14px;margin-bottom:10px;display:flex;gap:20px;align-items:center;">'
        f'<span style="font-size:11px;color:#22c55e;font-weight:700;">'
        f'✅ {len(articles)} articles</span>'
        f'<span style="font-size:11px;color:#facc15;">'
        f'🧩 {len(entities)} entities</span>'
        f'<span style="font-size:11px;color:#38bdf8;">'
        f'🔗 {len(relations)} relations</span>'
        f'<span style="font-size:10px;color:#475569;">'
        f'{dropped} dropped (Unrelated)</span>'
        f'{"<span style=\\'font-size:10px;color:#64748b;margin-left:auto;\\'>" + message + "</span>" if message else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if message and not articles:
        return

    res_col, ent_col = st.columns([1.4, 1], gap="large")

    with res_col:
        st.markdown(
            '<div style="font-size:9px;color:#475569;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:6px;">NEWS ARTICLES</div>',
            unsafe_allow_html=True,
        )
        for art in articles[:6]:
            rel       = art.get("relevance", "")
            conf      = art.get("confidence", 0)
            title     = art.get("title", "")[:80]
            published = art.get("published", "")[:16]
            link      = art.get("link", "")
            rel_color = "#22c55e" if rel == "Direct Match" else ("#facc15" if rel == "Zone Context" else "#38bdf8")
            link_html = f'<a href="{link}" target="_blank" style="font-size:9px;color:#38bdf8;text-decoration:none;">→</a>' if link else ""
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid #1e293b;border-left:3px solid {rel_color};'
                f'border-radius:6px;padding:7px 10px;margin-bottom:5px;">'
                f'<div style="font-size:10.5px;font-weight:600;color:#e2e8f0;">{title} {link_html}</div>'
                f'<div style="font-size:9.5px;color:#475569;margin-top:2px;display:flex;gap:8px;">'
                f'<span style="color:{rel_color};">{rel}</span>'
                f'<span>conf: {conf:.2f}</span>'
                f'<span>{published}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with ent_col:
        st.markdown(
            '<div style="font-size:9px;color:#475569;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:6px;">EXTRACTED ENTITIES</div>',
            unsafe_allow_html=True,
        )
        if entities:
            for ent in entities[:8]:
                ename = ent.get("properties", {}).get("name", ent.get("id", ""))[:36]
                elabel = ent.get("label", "")
                econf  = ent.get("properties", {}).get("confidence", 0)
                NODE_COLORS = {
                    "Event": "#f97316", "Region": "#22c55e", "Actor": "#38bdf8",
                    "Scheme": "#facc15", "Policy": "#fb7185", "Impact": "#94a3b8",
                    "Evidence": "#e2e8f0", "Asset": "#a78bfa",
                }
                ec = NODE_COLORS.get(elabel, "#64748b")
                st.markdown(
                    f'<div style="background:#060f1e;border:1px solid {ec}22;border-radius:5px;'
                    f'padding:5px 8px;margin-bottom:4px;display:flex;align-items:center;gap:8px;">'
                    f'<span style="background:{ec}22;color:{ec};font-size:8.5px;font-weight:700;'
                    f'padding:1px 5px;border-radius:3px;border:1px solid {ec}44;">{elabel}</span>'
                    f'<span style="font-size:10.5px;color:#94a3b8;flex:1;">{ename}</span>'
                    f'<span style="font-size:9px;color:#334155;">{econf:.2f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="font-size:10px;color:#334155;">No entities extracted.</div>',
                unsafe_allow_html=True,
            )

    # ── Ingest to Neo4j ──────────────────────────────────────────────────────
    if entities or relations:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        ingest_col, status_col = st.columns([1, 2], gap="medium")
        with ingest_col:
            if st.button(f"⬆️ Ingest {len(entities)} Entities → Neo4j",
                         key="do_ingest_btn", use_container_width=True):
                try:
                    payload = {
                        "entities":    entities,
                        "relations":   relations,
                        "source_type": results.get("source_type", "unstructured_rss"),
                    }
                    resp = _req.post(
                        f"{BACKEND}/ingest/entities",
                        json=payload,
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        r = resp.json()
                        st.session_state["last_ingest_result"] = r
                        st.rerun()
                    else:
                        st.error(f"Ingest failed {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    st.error(f"Ingest error: {e}")

        # Show last ingest result
        last = st.session_state.get("last_ingest_result")
        if last:
            with status_col:
                ec   = last.get("entities_created", 0)
                rc   = last.get("relations_created", 0)
                slc  = last.get("skipped_low_confidence", 0)
                sh   = last.get("skipped_hallucinations", 0)
                vs   = last.get("validation_summary", {}) or {}
                tot  = vs.get("total_submitted", 0)
                acc  = vs.get("accepted", 0)
                st.markdown(
                    f'<div style="background:#0a2010;border:1px solid #22c55e44;border-radius:8px;'
                    f'padding:8px 12px;font-size:11px;">'
                    f'<span style="color:#22c55e;font-weight:700;">✅ Ingested:</span>'
                    f' {ec} entities · {rc} relations'
                    f'<span style="color:#475569;margin-left:12px;">|</span>'
                    f'<span style="color:#475569;margin-left:12px;">'
                    f'{slc} low-conf skipped · {sh} hallucinations rejected</span>'
                    f'<span style="color:#475569;margin-left:12px;">|</span>'
                    f'<span style="color:#64748b;margin-left:12px;">'
                    f'Acceptance rate: {acc}/{tot} ({int(acc/tot*100) if tot else 0}%)</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Auto-rerun for timer
    if auto_on:
        elapsed = time.time() - st.session_state.ingestion_last_run
        remaining = max(0, 300 - int(elapsed))
        st.markdown(
            f'<div style="font-size:10px;color:#334155;margin-top:6px;">'
            f'Auto-refresh in {remaining}s</div>',
            unsafe_allow_html=True,
        )
        if remaining > 0:
            import time as _t
            _t.sleep(min(remaining, 30))
            st.rerun()


page()
