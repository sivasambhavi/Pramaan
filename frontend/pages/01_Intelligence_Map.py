"""
01_Intelligence_Map.py — PRAMAAN Global Ontology Engine
World map with 6 event pins, domain-colored markers, event detail cards.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.api import safe_get
from components.topnav import render_topnav

EVENT_META = {
    "EVT_WAYANAD_2024":       (11.6854, 76.1320, "Wayanad Landslide",      "Climate",     "#22c55e", "Jul 2024", "critical"),
    "EVT_CYCLONE_DANA_2024":  (19.8135, 85.8312, "Cyclone Dana – Puri",    "Climate",     "#22c55e", "Oct 2024", "critical"),
    "EVT_JOSHIMATH_2023":     (30.5581, 79.5647, "Joshimath Subsidence",   "Governance",  "#06b6d4", "Jan 2023", "high"),
    "EVT_DELHI_FLOODS_2023":  (28.6139, 77.2090, "Delhi Yamuna Floods",    "Society",     "#fb7185", "Jul 2023", "critical"),
    "EVT_MANIPUR_2023":       (24.8170, 93.9368, "Manipur Conflict",       "Defense",     "#f97316", "May 2023", "critical"),
    "EVT_TATA_SEMI_2024":     (22.4707, 72.2110, "Tata Semiconductor Fab", "Economics",   "#38bdf8", "Feb 2024", "high"),
    "EVT_G20_INDIA_2023":     (28.6183, 77.2781, "G20 New Delhi Summit",      "Geopolitics", "#a78bfa", "Sep 2023", "high"),
    "EVT_CHANDRAYAAN3_2023":  (13.7199, 80.2304, "Chandrayaan-3 Landing",    "Technology",  "#facc15", "Aug 2023", "high"),
    "EVT_CHAMOLI_2021":       (30.4278, 79.7965, "Chamoli Glacier Burst",    "Climate",     "#22c55e", "Feb 2021", "critical"),
    "EVT_BALAKOT_2019":       (30.3782, 76.8267, "Balakot Airstrikes",       "Defense",     "#f97316", "Feb 2019", "critical"),
    "EVT_COVID_WAVE2_2021":   (19.0760, 72.8777, "COVID Second Wave",        "Society",     "#fb7185", "Apr 2021", "critical"),
    "EVT_ART370_2019":        (34.0837, 74.7973, "Article 370 Abrogation",   "Governance",  "#06b6d4", "Aug 2019", "high"),
    "EVT_ADITYAL1_2023":      (12.9716, 77.5946, "Aditya-L1 Solar Mission",  "Technology",  "#facc15", "Sep 2023", "high"),
    "EVT_INDIA_CANADA_2023":  (28.6292, 77.2208, "India-Canada Diplomatic Row", "Geopolitics", "#a78bfa", "Sep 2023", "high"),
    "EVT_IMEC_2023":          (18.9220, 72.8347, "IMEC Corridor Signing",    "Economics",   "#38bdf8", "Sep 2023", "high"),
}

# All 7 domains — full system scope
ALL_DOMAINS = {
    "Climate":     "#22c55e",
    "Defense":     "#f97316",
    "Economics":   "#38bdf8",
    "Society":     "#fb7185",
    "Governance":  "#06b6d4",
    "Geopolitics": "#a78bfa",
    "Technology":  "#facc15",
}

# Domains that currently have event data
ACTIVE_DOMAINS = {"Climate", "Defense", "Economics", "Society", "Governance", "Geopolitics", "Technology"}

DOMAIN_COLOR = {
    "Climate":     "#22c55e",
    "Defense":     "#f97316",
    "Economics":   "#38bdf8",
    "Society":     "#fb7185",
    "Governance":  "#06b6d4",
    "Geopolitics": "#a78bfa",
    "Technology":  "#facc15",
}

SEVERITY_BADGE = {
    "critical": ("<span style='background:#ef444422;color:#fca5a5;font-weight:700;font-size:9px;padding:1px 5px;border-radius:4px;border:1px solid #ef444466;'>CRITICAL</span>", 10),
    "high":     ("<span style='background:#f9731622;color:#fdba74;font-weight:700;font-size:9px;padding:1px 5px;border-radius:4px;border:1px solid #f9731666;'>HIGH</span>",      8),
    "medium":   ("<span style='background:#facc1522;color:#fde047;font-weight:700;font-size:9px;padding:1px 5px;border-radius:4px;border:1px solid #facc1566;'>MEDIUM</span>",    6),
}

DEFAULT_CENTER = [21.0, 82.0]
DEFAULT_ZOOM   = 5


def page():
    st.set_page_config(page_title="Intelligence Map – PRAMAAN", layout="wide")
    render_topnav(active_page="Intelligence Map")

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
    /* Shrink domain expander title */
    div[data-testid="stExpander"] summary p { font-size: 12px !important; }
    /* Compact selects */
    div[data-baseweb="select"] * { font-size: 13px !important; }
    div[data-baseweb="select"] > div { min-height: 26px !important; padding-top: 1px !important; padding-bottom: 1px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Selection via URL query param (read once, then clear so refresh starts fresh) ──
    sel_param = st.query_params.get("sel", None)
    if sel_param and sel_param in EVENT_META:
        st.session_state.sel_event = sel_param
        st.query_params.clear()          # clear URL so page reload starts at overview
    if "sel_event" not in st.session_state:
        st.session_state.sel_event = None
    if "active_domains" not in st.session_state:
        st.session_state.active_domains = set(ACTIVE_DOMAINS)

    # ── Fetch live data ────────────────────────────────────────────────────────
    api_events = {}
    data = safe_get("/ontology/events", silent=True)
    if data:
        for evt in data.get("events", []):
            api_events[evt["event_id"]] = evt

    # ── Header placeholder — sits at top, filled with live stats after filter ──
    header_slot = st.empty()

    active_domains = list(st.session_state.active_domains) if st.session_state.active_domains else list(ACTIVE_DOMAINS)

    _sev_sel = st.session_state.get("sev_filter", ["Critical", "High", "Medium"])
    active_severities = {s.lower() for s in _sev_sel} if _sev_sel else {"critical", "high", "medium"}
    filtered_events = {
        eid: meta for eid, meta in EVENT_META.items()
        if meta[3] in active_domains and meta[6] in active_severities
    }

    # If selected event was filtered out, reset
    sel = st.session_state.sel_event
    if sel and sel not in filtered_events:
        st.session_state.sel_event = None
        sel = None

    n_events  = len(filtered_events)
    n_domains = len({m[3] for m in filtered_events.values()}) if filtered_events else 0

    # Fill the header slot with live stats as tagline
    header_slot.markdown(f"""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:6px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#14b8a6;
                   font-family:'Cinzel',serif;letter-spacing:0.08em;white-space:nowrap;
                   animation:glowPulse 2.5s ease-in-out infinite;">
        INTELLIGENCE MAP
      </span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        {n_events} Events &nbsp;·&nbsp; {n_domains} Active Domains &nbsp;·&nbsp; Verified Data
        &nbsp;·&nbsp; <span style="color:#475569;">PIB · NDMA · ISRO · IMD</span>
        &nbsp;·&nbsp; <span style="color:#334155;">Neo4j Knowledge Graph</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:12px;color:#475569;margin-bottom:8px;">'
        'Tracks 15 high-impact events across India — from climate disasters to geopolitical shifts — '
        'plotted on a live map with verified government evidence and cross-domain connections.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Map center: selected event or default India view ──────────────────────
    if sel and sel in filtered_events:
        lat0, lon0 = filtered_events[sel][0], filtered_events[sel][1]
        map_center, map_zoom = [lat0, lon0], 9
    else:
        map_center, map_zoom = DEFAULT_CENTER, DEFAULT_ZOOM

    # ── Build Folium map — dark tile always, scroll wheel zoom disabled ───────
    m = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles="CartoDB positron",
        scrollWheelZoom=False,
        # prefer_canvas intentionally omitted — canvas mode breaks popup clicks
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

        # Main clickable marker first — glow ring added second so it doesn't intercept clicks
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.9 if is_selected else 0.85,
            weight=3 if is_selected else 2,
            popup=folium.Popup(popup_html, max_width=250, show=is_selected),
            tooltip=folium.Tooltip(f"<b style='color:{color}'>{name}</b><br>{domain} · {date}"),
        ).add_to(m)

        # Glow ring — non-interactive, purely visual
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius + 8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.12 if is_selected else 0.08,
            weight=1,
            interactive=False,
        ).add_to(m)

    # ── 3-column layout: event list | map | detail panel ─────────────────────
    col_left, col_map, col_right = st.columns([1.5, 3, 1], gap="medium")

    # ── LEFT — domain filter + event index ───────────────────────────────────
    with col_left:
        # Domain Index — same card+toggle style as Ontology Graph Node Index
        st.markdown(
            "<div style='font-size:0.7em;color:#475569;letter-spacing:0.1em;"
            "font-weight:700;margin-bottom:6px;text-transform:uppercase;'>DOMAIN INDEX</div>",
            unsafe_allow_html=True,
        )

        DOMAIN_ORDER = ["Climate", "Defense", "Economics", "Society", "Governance", "Geopolitics", "Technology"]
        for domain in DOMAIN_ORDER:
            color    = ALL_DOMAINS[domain]
            is_on    = domain in st.session_state.active_domains
            cnt      = sum(1 for m in EVENT_META.values() if m[3] == domain)
            border_c = f"{color}88" if is_on else "#1e293b"
            bg       = "#111827"    if is_on else "#0a0f1a"
            dot_c    = color        if is_on else "#334155"
            name_c   = color        if is_on else "#475569"
            desc_c   = "#475569"    if is_on else "#1e293b"

            card_col, tog_col = st.columns([5, 1], gap="small")
            with card_col:
                st.markdown(
                    f'<div style="border-left:3px solid {border_c};padding:7px 9px;'
                    f'background:{bg};border-radius:4px;margin-bottom:4px;'
                    f'border:1px solid rgba(71,85,105,0.15);border-left:3px solid {border_c};">'
                    f'<div style="display:flex;align-items:center;gap:6px;">'
                    f'<span style="width:8px;height:8px;border-radius:50%;background:{dot_c};'
                    f'flex-shrink:0;box-shadow:0 0 4px {dot_c}88;"></span>'
                    f'<span style="font-size:11px;font-weight:600;color:{name_c};">{domain}</span>'
                    f'<span style="font-size:10px;color:#334155;margin-left:auto;">{cnt}</span>'
                    f'</div>'
                    f'<div style="font-size:10px;color:{desc_c};padding-left:14px;margin-top:2px;">'
                    f'{cnt} events</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with tog_col:
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                val = st.toggle("", value=is_on, key=f"dom_tog_{domain}", label_visibility="collapsed")
                if val != is_on:
                    if val:
                        st.session_state.active_domains.add(domain)
                    else:
                        st.session_state.active_domains.discard(domain)
                    st.rerun()

        st.markdown("<div style='border-top:1px solid #1e293b;margin:8px 0 6px;'></div>", unsafe_allow_html=True)

        st.multiselect(
            "Severity",
            options=["Critical", "High", "Medium"],
            default=["Critical", "High", "Medium"],
            label_visibility="collapsed",
            placeholder="All severities",
            key="sev_filter",
        )

    # ── CENTER — map ──────────────────────────────────────────────────────────
    with col_map:
        map_result = st_folium(m, width="100%", height=540, returned_objects=["last_object_clicked"])

    # ── Sync map marker click → session state ─────────────────────────────────
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

    # ── RIGHT — detail panel ──────────────────────────────────────────────────
    with col_right:
        if sel and sel in EVENT_META:
            lat0, lon0, sname, sdomain, scolor, sdate, ssev = EVENT_META[sel]
            sev_label, _ = SEVERITY_BADGE.get(ssev, SEVERITY_BADGE["high"])
            detail   = safe_get(f"/ontology/events/{sel}", silent=True) or {}
            evt_data = detail.get("event", {})
            impacts  = detail.get("impacts", [])
            sdesc    = evt_data.get("description", "") or api_events.get(sel, {}).get("description", "")

            st.markdown(f"""
            <div style="border-left:3px solid {scolor};padding:10px 12px;
                        background:#111827;border-radius:4px;margin-bottom:10px;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;">
                <div style="font-size:12px;font-weight:700;color:{scolor};line-height:1.3;">{sname}</div>
                {sev_label}
              </div>
              <div style="font-size:10px;color:#64748b;">{sdomain} · {sdate}</div>
            </div>
            """, unsafe_allow_html=True)

            if sdesc:
                st.markdown(
                    f'<div style="font-size:10.5px;color:#94a3b8;line-height:1.55;'
                    f'background:#060f1e;border-radius:6px;padding:8px 10px;margin-bottom:8px;">'
                    f'{sdesc[:280]}{"…" if len(sdesc) > 280 else ""}</div>',
                    unsafe_allow_html=True,
                )

            if impacts:
                st.markdown(
                    '<div style="font-size:9.5px;color:#475569;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.08em;margin-bottom:4px;">Impact Nodes</div>',
                    unsafe_allow_html=True,
                )
                for imp in impacts[:4]:
                    itype = imp.get("type", "").replace("_", " ").title()
                    val   = imp.get("value", "")
                    unit  = imp.get("unit", "")
                    st.markdown(
                        f'<div style="font-size:10px;color:#64748b;padding:2px 0 2px 8px;'
                        f'border-left:2px solid {scolor}44;margin-bottom:2px;">• {itype}'
                        f'{f": {val} {unit}" if val else ""}</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            if st.button("View in Ontology Graph →", key=f"goto_graph_{sel}",
                         use_container_width=True, type="primary"):
                st.session_state["deep_link_event"] = sel
                st.switch_page("pages/02_Ontology_Graph.py")
        else:
            st.markdown(
                '<div style="font-size:10px;color:#1e293b;padding:8px;text-align:center;margin-top:40px;">'
                'Click an event or map marker to see details</div>',
                unsafe_allow_html=True,
            )



page()
