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
from components.ontology_model import render_ontology_model

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


INDIA_CENTER = [22.5, 82.0]
INDIA_ZOOM   = 5
WORLD_CENTER = [30.0, 55.0]
WORLD_ZOOM   = 3

DEFAULT_CENTER = INDIA_CENTER
DEFAULT_ZOOM   = INDIA_ZOOM

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
        {n_events} Events &nbsp;·&nbsp; {n_domains} Active Domains
        &nbsp;·&nbsp; <span style="color:#22c55e;font-weight:600;">● Streaming</span>
        &nbsp;·&nbsp; <span style="color:#475569;">PIB · NDMA · ISRO · IMD · UN · World Bank</span>
        &nbsp;·&nbsp; <span style="color:#334155;">Global Neo4j Knowledge Graph</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    import datetime as _dt
    _ts = _dt.datetime.now().strftime("%H:%M IST")
    st.markdown(
        f'<div style="font-size:12px;color:#475569;margin-bottom:2px;">'
        f'Global knowledge graph · India lens active · AI-powered event extraction, entity linking &amp; risk scoring · '
        f'Tracks {N_EVENTS} high-impact events across climate, defense, economics and geopolitics.'
        f'</div>'
        f'<div style="font-size:10px;color:#334155;margin-bottom:4px;">'
        f'Last updated: {_ts} &nbsp;·&nbsp; Streaming from PIB · NDMA · ISRO · IMD · UN · IMF · World Bank'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Event dropdown + Cross-links toggle ──────────────────────────────────
    tcol1, tcol2 = st.columns([2.5, 1], gap="medium")
    with tcol1:
        render_event_dropdown("sel_event", "map_event_dropdown", include_all=True)
    with tcol2:
        show_cross = st.checkbox("Cross-links", value=False, key="cross_cb")
        if show_cross:
            st.markdown(
                "<div style='font-size:9px;color:#FFD700;margin-top:-8px;'>🌐 Global cross-links active</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='font-size:9px;color:#94a3b8;margin-top:-8px;'>🇮🇳 India lens · global graph beneath</div>",
                unsafe_allow_html=True
            )

    # ── Chip filter bar — HTML anchors with target="_self" (same-page navigation) ──
    dcounts = {d: sum(1 for m in EVENT_META.values() if m[3] == d) for d in DOMAIN_ORDER}
    sev_str = ",".join(sorted(s.lower() for s in st.session_state.get("sev_filter", ["Critical","High","Medium"])))

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
            f'<a href="{_chip_href(domain)}" target="_self" '
            f'style="display:inline-flex;align-items:center;'
            f'border-radius:20px;padding:2px 9px;font-size:10px;font-weight:600;'
            f'line-height:18px;white-space:nowrap;border:{border};color:{text_c};'
            f'background:transparent;text-decoration:none;flex-shrink:0;">'
            f'{emoji} {domain} ({cnt})</a>'
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

    # ── Map center: fit all visible markers when no selection ──────────────────
    if sel and sel in filtered_events:
        lat0, lon0   = filtered_events[sel][0], filtered_events[sel][1]
        # Auto-zoom based on location (further out for Europe/Canada)
        zoom_in      = 5 if abs(lon0) < 35 else 6
        map_center   = [lat0, lon0]
        map_zoom     = zoom_in
        use_fitbounds = False
    else:
        # Two-state zoom tied to Cross-links toggle
        if show_cross:
            map_center = WORLD_CENTER
            map_zoom   = WORLD_ZOOM
        else:
            map_center = INDIA_CENTER
            map_zoom   = INDIA_ZOOM
        use_fitbounds = True  # Fit map to all visible markers when no event selected

    # ── Build Folium map ───────────────────────────────────────────────────────
    m = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles="CartoDB positron",
        scrollWheelZoom=True,
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

        # Halo ring added FIRST so it sits below the clickable marker in the layer stack
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius + 8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.15 if is_selected else 0.08,
            weight=1,
            interactive=False,
        ).add_to(m)

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.9 if is_selected else 0.85,
            weight=3 if is_selected else 2,
            popup=folium.Popup(popup_html, max_width=250, show=is_selected),
            tooltip=folium.Tooltip(f"<b style='color:{color}'>{name}</b><br>{domain} · {date}"),
        ).add_to(m)

    # Fit map to show all visible markers when no event is selected
    if use_fitbounds and filtered_events:
        all_lats = [v[0] for v in filtered_events.values()]
        all_lons = [v[1] for v in filtered_events.values()]
        pad = 3   # degrees padding
        m.fit_bounds(
            [[min(all_lats) - pad, min(all_lons) - pad],
             [max(all_lats) + pad, max(all_lons) + pad]]
        )

    # ── Cross-domain gold polylines (PRD v6 "WOW MOMENT") ──────────────────
    CROSS_PAIRS = [
        # Pahalgam → Operation Sindoor escalation chain
        ("EVT_PAHALGAM_2025",            "EVT_OPERATION_SINDOOR_2025",    "Terror attack triggered cross-border military strike"),
        ("EVT_OPERATION_SINDOOR_2025",   "EVT_LOC_SKIRMISHES_2025",       "Post-strike LoC tensions escalated to sustained skirmishes"),
        ("EVT_OPERATION_SINDOOR_2025",   "EVT_INDIA_PAK_CEASEFIRE_2025",  "Military action led to US-brokered ceasefire"),
        ("EVT_INDIA_PAK_CEASEFIRE_2025", "EVT_INDIA_PAK_DIPLO_CRISIS_2025","Post-ceasefire diplomatic breakdown and expulsions"),
        ("EVT_PAHALGAM_2025",            "EVT_INDUS_WATERS_CRISIS_2025",  "India suspended Indus Waters Treaty after Pahalgam attack"),
        # Iran war chain → India economic impact
        ("EVT_IRAN_WAR_2026",            "EVT_HORMUZ_BLOCKADE_2026",      "Iran war triggered Strait of Hormuz closure"),
        ("EVT_HORMUZ_BLOCKADE_2026",     "EVT_IRAN_CEASEFIRE_TALKS_2026", "Blockade economic pressure accelerated ceasefire talks"),
        ("EVT_IMEC_2023",                "EVT_HORMUZ_BLOCKADE_2026",      "IMEC corridor further disrupted by Hormuz crisis"),
        # India strategic / technology
        ("EVT_G20_INDIA_2023",           "EVT_INDIA_CANADA_2023",         "G20 diplomacy vs bilateral breakdown"),
        ("EVT_CHANDRAYAAN3_2023",        "EVT_SHUKLA_ISS_2025",           "ISRO space programme milestone progression"),
        ("EVT_TATA_SEMI_2024",           "EVT_INDIA_US_DEFENSE_2025",     "Semiconductor + defense pact: India-US strategic depth"),
        # Climate chain
        ("EVT_DELHI_FLOODS_2023",        "EVT_JOSHIMATH_2023",            "Urban load on fragile river floodplain"),
        ("EVT_WAYANAD_2024",             "EVT_INDIA_EXTREME_WEATHER_2025","Back-to-back extreme climate events stress NDMA capacity"),
    ]
    if show_cross:
        for e1_id, e2_id, reason in CROSS_PAIRS:
            if e1_id in filtered_events and e2_id in filtered_events:
                lat1, lon1 = filtered_events[e1_id][0], filtered_events[e1_id][1]
                lat2, lon2 = filtered_events[e2_id][0], filtered_events[e2_id][1]
                folium.PolyLine(
                    locations=[[lat1, lon1], [lat2, lon2]],
                    color="#FFD700",
                    weight=2.5,
                    opacity=0.75,
                    dash_array="6 4",
                    tooltip=f"🔗 Cross-domain: {reason}",
                ).add_to(m)

    # ── Map + right panel ───────────────────────────────────────────────────────
    col_map, col_right = st.columns([2.5, 1.5], gap="medium")

    with col_map:
        map_result = st_folium(m, key="pramaan_map", width="100%", height=520,
                               returned_objects=["last_object_clicked"])

        # ── Sync map marker click → session state (no rerun — update in-place) ─────
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
                    st.session_state.sel_event = best_eid


    # Re-read sel AFTER click detection so first click shows the panel immediately
    sel = st.session_state.sel_event

    # ── Right — event detail panel ─────────────────────────────────────────────
    with col_right:
        if sel and sel in EVENT_META:
            lat0, lon0, sname, sdomain, scolor, sdate, ssev = EVENT_META[sel]
            sev_label, _ = SEVERITY_BADGE.get(ssev, SEVERITY_BADGE["high"])
            detail   = safe_get(f"/ontology/events/{sel}", silent=True) or {}
            evt_data = detail.get("event", {})
            impacts  = detail.get("impacts", [])
            schemes  = detail.get("schemes", [])
            actors   = detail.get("actors", [])
            evidence = detail.get("evidence", [])
            policies = detail.get("policies", [])
            sdesc    = evt_data.get("description", "") or api_events.get(sel, {}).get("description", "")

            # ── Event header card — always visible above tabs ───────────────────────
            _risk_score = {"critical": "9.1", "high": "7.4", "medium": "5.2"}.get(ssev, "6.0")
            _risk_color = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}.get(ssev, "#94a3b8")
            st.markdown(f"""
            <div style="border-left:3px solid {scolor};padding:10px 12px;
                        background:#0a1628;border-radius:6px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;">
                <div style="font-size:12px;font-weight:700;color:{scolor};line-height:1.3;">{sname}</div>
                {sev_label}
              </div>
              <div style="font-size:10px;color:#64748b;">{sdomain} · {sdate}</div>
              <div style="display:flex;align-items:center;gap:8px;margin-top:5px;">
                <span style="font-size:8px;color:#475569;">Model risk score:</span>
                <span style="font-size:11px;font-weight:700;color:{_risk_color};">{_risk_score}/10</span>
                <span style="font-size:8px;color:#334155;cursor:default;" title="Derived from event severity, impact count, cross-domain links, and source confidence via PRAMAAN ontology engine">[ how derived ]</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── All data maps (defined before tabs so available in all tab blocks) ────
            NEEDS_MAP = {
                # 2026
                "EVT_IRAN_CEASEFIRE_TALKS_2026":  ("Strategic Petroleum Reserve Need",  "India's SPR covers only 9 days — minimum 30-day reserve needed to buffer Hormuz-class shocks.", "#38bdf8"),
                "EVT_HORMUZ_BLOCKADE_2026":        ("Energy Route Diversification Need", "No operational alternative to Gulf oil routing — pipeline via Central Asia or expanded SPR urgently required.", "#f97316"),
                "EVT_IRAN_WAR_2026":               ("Energy Security Policy Need",       "India lacks a formal energy-shock response protocol; ad-hoc oil procurement from spot markets is costly.", "#a78bfa"),
                # 2025
                "EVT_PAHALGAM_2025":               ("Counter-Terror Early-Warning Need", "IB-RAW-state intelligence fusion gaps allowed a 20-man team to operate in Pahalgam for 4+ hours undetected.", "#f97316"),
                "EVT_OPERATION_SINDOOR_2025":       ("Border Civilian Evacuation Need",  "No permanent evacuation protocol for 1.2M border-belt civilians — ad-hoc relocations during Sindoor exposed gap.", "#f97316"),
                "EVT_LOC_SKIRMISHES_2025":          ("Bunker Modernisation Need",        "Only 34% of LoC border villages have blast-proof shelters — Ministry of Home Affairs audit flagged in 2023.", "#f97316"),
                "EVT_INDIA_PAK_CEASEFIRE_2025":     ("Diplomatic Back-Channel Need",     "Absence of formal India-Pakistan back-channel forced reliance on US mediation — Track-2 framework needed.", "#a78bfa"),
                "EVT_INDIA_PAK_DIPLO_CRISIS_2025":  ("Diaspora Protection Need",         "No bilateral consular agreement covers 800K Pakistan-origin Indians — emergency repatriation protocol absent.", "#a78bfa"),
                "EVT_INDUS_WATERS_CRISIS_2025":     ("Water Treaty Modernisation Need",  "1960 Indus Waters Treaty has no dispute mechanism for non-military suspension — legal framework overdue.", "#06b6d4"),
                "EVT_LABOUR_CODES_2025":            ("Gig Worker Coverage Need",         "4 Labour Codes still exclude 15Cr platform/gig workers from social security — ESIC extension pending.", "#06b6d4"),
                "EVT_INDIA_US_DEFENSE_2025":        ("MRO Ecosystem Need",               "India has only 3 certified MRO facilities for advanced platforms — target 12 by 2030 to service pact obligations.", "#f97316"),
                "EVT_SP_UPGRADE_2025":              ("Sovereign Bond Market Need",       "India still has no local-currency sovereign bond issuance in global indices — Euroclear integration pending.", "#38bdf8"),
                "EVT_INDIA_UK_CETA_2025":           ("Pharma Export Standards Need",     "UK MHRA recognition of Indian CDSCO not yet formalised — delays ₹28,000 Cr pharma export pipeline.", "#38bdf8"),
                "EVT_TWELVE_DAY_WAR_2025":          ("Trade Route Resilience Need",      "India's IMEC corridor not operationalised — sole alternative remains Cape of Good Hope rerouting.", "#a78bfa"),
                "EVT_INDIA_EXTREME_WEATHER_2025":   ("NDRF Pre-positioning Need",        "NDRF battalions stationed in 16 fixed depots — dynamic pre-positioning algorithm needed for climate-risk zones.", "#22c55e"),
                # 2024
                "EVT_CYCLONE_DANA_2024":            ("Coastal Resilience Need",          "Cyclone-resilient housing and early-warning last-mile gaps in Odisha.", "#38bdf8"),
                "EVT_WAYANAD_2024":                 ("Land-Use Governance Need",         "Deforestation on eco-sensitive slopes without oversight.", "#f97316"),
                "EVT_TATA_SEMI_2024":               ("Semiconductor Sovereignty Need",   "Domestic chip manufacturing capacity near-zero before PLI.", "#facc15"),
                # 2023
                "EVT_DELHI_FLOODS_2023":            ("Drainage Capacity Need",           "Ward-level storm water drain capacity insufficient; Ward 46 incomplete.", "#22c55e"),
                "EVT_JOSHIMATH_2023":               ("Urban Subsidence Need",            "Heavy construction on fragile hill terrain without geological load assessment.", "#fb7185"),
                "EVT_MANIPUR_2023":                 ("Conflict Early-Warning Need",      "Ethnic tension signals went unaddressed 6+ months before escalation.", "#f97316"),
                "EVT_IMEC_2023":                    ("Trade Route Resilience Need",      "IMEC corridor not operationalized — compounded by Hormuz blockade in 2026.", "#fb7185"),
            }
            GAP_LABEL = {
                "Defense":     ("⚔ SECURITY GAP EXPOSED",    "#f97316"),
                "Climate":     ("🌊 RESILIENCE GAP EXPOSED",  "#22c55e"),
                "Economics":   ("📉 MARKET GAP EXPOSED",      "#38bdf8"),
                "Technology":  ("🔬 CAPABILITY GAP EXPOSED",  "#facc15"),
                "Geopolitics": ("🌐 DIPLOMATIC GAP EXPOSED",  "#a78bfa"),
                "Governance":  ("⚖ GOVERNANCE GAP EXPOSED",  "#06b6d4"),
                "Society":     ("👥 SOCIAL GAP EXPOSED",      "#fb7185"),
            }
            TYPE1_MAP = {
                "EVT_DELHI_FLOODS_2023":        [("SDRF Delhi", "₹350 Cr", "Delhi Govt / MHA"), ("NDRF Teams", "12 units", "MHA")],
                "EVT_WAYANAD_2024":             [("SDRF Kerala", "₹200 Cr", "Kerala Govt"), ("NDRF Deploy", "₹90 Cr", "MHA")],
                "EVT_CYCLONE_DANA_2024":        [("SDRF Odisha", "₹800 Cr", "Odisha Govt"), ("NDRF Deploy", "₹350 Cr", "MHA")],
                "EVT_JOSHIMATH_2023":           [("SDRF Uttarakhand", "₹250 Cr", "Uttarakhand"), ("NDRF Deploy", "₹80 Cr", "MHA")],
                "EVT_INDIA_EXTREME_WEATHER_2025":[("SDRF Multi-state", "₹3,200 Cr", "MHA"), ("NDRF Deploy", "48 units", "MHA")],
                "EVT_MANIPUR_2023":             [("SDRF Manipur", "₹175 Cr", "Manipur Govt"), ("CRPF Deploy", "5 Bn", "MHA")],
                "EVT_PAHALGAM_2025":            [("PM Relief Fund", "₹50 Cr", "PMO"), ("CRPF Surge", "8 Bn", "MHA"), ("NIA Investigation", "Activated", "MHA")],
                "EVT_OPERATION_SINDOOR_2025":   [("IAF Strike Op", "9 targets", "MoD"), ("Army LoC Posture", "High-readiness", "MoD")],
                "EVT_LOC_SKIRMISHES_2025":      [("Army Artillery Reserve", "Activated", "MoD"), ("Border Civilian Evac", "14 villages", "MHA")],
            }

            # ── Watch Points — forward-looking intelligence (all domains) ──────────────
            WATCH_POINTS = {
                # 2026
                "EVT_IRAN_CEASEFIRE_TALKS_2026":  ["Will ceasefire hold past 90-day review? Iran parliament hardliners pushing back.", "India-Iran bilateral oil deal window opens if Hormuz reopens — track MEA signals.", "IMEC Phase 1 restart conditional on Hormuz status — Jul 2026 deadline."],
                "EVT_HORMUZ_BLOCKADE_2026":        ["SPR drawdown rate — India crosses critical 5-day buffer around Day 18 of blockade.", "Spot LNG procurement surge expected; watch GAIL tender prices.", "US 5th Fleet posture change in Bahrain is the key de-escalation signal."],
                "EVT_IRAN_WAR_2026":               ["Brent above $130 triggers automatic fuel subsidy review under MoPNG protocol.", "India's vote if UNSC emergency session called — non-aligned vs US pressure.", "Pakistan opportunism risk: cross-border provocation while India is economically stressed."],
                # 2025
                "EVT_PAHALGAM_2025":               ["Indus Waters Treaty legal challenge at Hague by Pakistan — ICJ jurisdiction question pending.", "J&K election calendar: security situation determines polling feasibility.", "LeT-proxy reconstitution attempts in Neelum Valley — IB tracking."],
                "EVT_OPERATION_SINDOOR_2025":       ["Pakistan Army's internal accountability review — Rawalpindi Corps response.", "India's next doctrine test: will 'right to pursue' be codified in MoD white paper?", "Satellite imagery of struck sites — BrahMos accuracy assessment ongoing at DRDO."],
                "EVT_LOC_SKIRMISHES_2025":          ["Ceasefire violation count — next escalation trigger if >50 incidents in 30 days.", "Bunker construction tender under MHA — awarded or stalled?", "Winter posture change in Siachen sector — Army forward deployment levels."],
                "EVT_INDIA_PAK_CEASEFIRE_2025":     ["90-day ceasefire review: will India restore diplomatic missions?", "Pakistan's IMF tranche conditional on regional stability — economic leverage.", "Attari-Wagah reopening timeline — trade lobby pressure on both sides."],
                "EVT_INDIA_PAK_DIPLO_CRISIS_2025":  ["Visa backlog for 800K+ Pakistani nationals in India — MHA processing status.", "High Commission downgrade: chargé d'affaires vs ambassador — signals intent.", "Third-country mediation offer from UAE — India's response is the watch signal."],
                "EVT_INDUS_WATERS_CRISIS_2025":     ["Pakistan's Rabi wheat crop — harvest shortfall estimate by Apr 2026.", "World Bank arbitration panel — India's non-participation precedent at stake.", "Kishanganga / Ratle dam construction restart — Pakistan's legal counter."],
                "EVT_LABOUR_CODES_2025":            ["Gig worker social security rules — draft regulations due Q1 2026, delayed.", "State-level implementation: UP, Bihar, MP are laggards — compliance deadline.", "Contract labour threshold change: industry challenging 50-worker cutoff in court."],
                "EVT_INDIA_US_DEFENSE_2025":        ["GE F414 engine ToT for Tejas MkII — IPR clause still unresolved.", "MRO facility land acquisition in Chennai — TIDCO approval pending.", "DTTI next review: AI and space domain additions expected by Sep 2026."],
                "EVT_SP_UPGRADE_2025":              ["Moody's and Fitch reviews due H2 2026 — fiscal deficit trajectory is key.", "India's inclusion in JPMorgan EM bond index — ₹40,000 Cr passive inflow expected.", "Rupee appreciation pressure post-upgrade — RBI intervention policy watch."],
                "EVT_INDIA_UK_CETA_2025":           ["Scotch whisky tariff phase-down schedule — 150%→75%→0% over 10 years.", "UK financial services access for GIFT City — FSB equivalence decision pending.", "NHS-India nurse recruitment agreement — MoHFW and UK Home Office MoU."],
                "EVT_SHUKLA_ISS_2025":              ["Gaganyaan crewed mission window: Nov 2026 target — ISRO readiness review Q3.", "AXIOM Space commercial module — India's seat reservation for 2027.", "Shukla's microgravity experiments: pharma and materials results due Q4 2026."],
                "EVT_TWELVE_DAY_WAR_2025":          ["IMEC corridor restart talks — India-Saudi-UAE trilateral track.", "Israel-Iran next flashpoint: Natanz enrichment restart monitoring.", "India's insurance premium for Middle East cargo routes — shipping index tracker."],
                "EVT_ISRO_SPADEX_2025":             ["Gaganyaan docking simulation using SpaDeX heritage — schedule update.", "Commercial docking service offer to ESA smallsat operators — NSIL tender.", "DRDO interest in SpaDeX-derived ASAT refuelling platform — classified review."],
                "EVT_INDIA_EXTREME_WEATHER_2025":   ["2026 monsoon forecast — IMD extended range prediction due March.", "NDRF 16th battalion raise — budget approved but recruitment delayed.", "NDMA's national risk index update — 5 new districts added to extreme-risk tier."],
                # 2024
                "EVT_CYCLONE_DANA_2024":            ["Cyclone season 2025 Bay of Bengal forecast — IMD pre-season bulletin due April.", "Odisha coastal housing scheme post-Dana: ₹800 Cr released, 60% utilized.", "Early warning last-mile gap: 12 Odisha blocks still without NDMA alert infrastructure."],
                "EVT_WAYANAD_2024":                 ["Wayanad rehabilitation township — land acquisition stalled, 800 families still in camps.", "Kerala's eco-sensitive zone notification: Gadgil report implementation — SC hearing.", "Landslide early-warning sensor network: NRSC deployment in 200 high-risk sites."],
                "EVT_TATA_SEMI_2024":               ["Tata fab Phase 2 expansion: 28nm → 16nm node timeline — 2027 target.", "ISMC (SoftBank JV) Mysuru fab ground-breaking — delayed by land clearance.", "India's chip design talent gap: 85,000 engineers needed — IIT curriculum update."],
                # 2023
                "EVT_INDIA_CANADA_2023":            ["Nijjar case trial in Canada: Indian diplomats named — next hearing date.", "Indian student visa rejection rate — still elevated at 32% vs 18% pre-crisis.", "Canada election outcome: Conservative govt likely warmer on India relations."],
                "EVT_G20_INDIA_2023":               ["G20 South Africa 2025 presidency — India's PGII infrastructure commitments.", "Global debt restructuring: Zambia/Ghana outcomes shape India's MDB leverage.", "India-Africa trade target ₹5 Lakh Cr by 2030 — annual progress review."],
                "EVT_IMEC_2023":                    ["IMEC Phase 1 MoU to binding agreement: legal framework still unsigned.", "Saudi Arabia port expansion at Haifa link — ground-breaking timeline.", "Hormuz reopening is the prerequisite — all IMEC signals conditioned on this."],
                "EVT_ADITYAL1_2023":                ["Aditya-L1 first solar flare alert issued to ISRO grid ops — response protocol test.", "Space weather data sharing MoU with ESA — signed Q4 2025.", "VELC coronagraph data: first peer-reviewed paper due Nature Astronomy."],
                "EVT_CHANDRAYAAN3_2023":            ["Chandrayaan-4 sample-return mission: launch window 2028 — module integration.", "Lunar Gateway India participation — NASA-ISRO MoU scope expansion.", "Pragyan rover data: water-ice confirmation paper — ISRO embargo lifting timeline."],
                "EVT_DELHI_FLOODS_2023":            ["Yamuna floodplain encroachment: 48,000 structures still in flood zone — NGT order.", "AMRUT 2.0 Ward 46 drain upgrade: ₹1,200 Cr, 41% complete as of Jan 2026.", "Hathnikund Barrage real-time telemetry: DJB sensor uptime below 60%."],
                "EVT_MANIPUR_2023":                 ["Manipur peace talks: MHA interlocutor meetings — stalled since Aug 2025.", "Kuki-Zo demand for separate administration — Home Ministry response pending.", "NHRC inquiry report on Manipur: submission deadline extended to Mar 2026."],
                "EVT_JOSHIMATH_2023":               ["NTPC Tapovan boring restart: MoEF clearance under challenge at NGT.", "Joshimath subsidence rate: NRSC satellite monitoring — Jan 2026 update.", "Char Dham highway expansion: Supreme Court order on width cap compliance."],
            }

            # ── Defense-specific panels ─────────────────────────────────────────────────
            ESCALATION_CHAIN = {
                "EVT_PAHALGAM_2025": [
                    ("22 Apr 2025", "Attack",      "Pahalgam Baisaran massacre — 26 civilians killed by LeT proxies"),
                    ("23 Apr 2025", "Attribution", "RAW/IB brief to NSA — Pakistan-based handlers confirmed"),
                    ("24 Apr 2025", "Diplomatic",  "India suspends Indus Waters Treaty, expels Pakistani diplomats"),
                    ("26 Apr 2025", "Military",    "Army LoC posture shifted to high-readiness; CRPF surge to J&K"),
                    ("07 May 2025", "Strike",      "Operation Sindoor — IAF/Army strike 9 terrorist sites in PoK & Pakistan"),
                    ("10 May 2025", "Ceasefire",   "US-brokered ceasefire announced; LoC skirmishes continue 4 days"),
                    ("14 May 2025", "Diplomatic",  "Pakistan expels 6 Indian diplomats; Attari-Wagah border closed"),
                ],
                "EVT_OPERATION_SINDOOR_2025": [
                    ("07 May 2025", "Launch",      "IAF Rafale and Mirage 2000 strike packages airborne from multiple bases"),
                    ("07 May 2025", "Strikes",     "9 targets hit in 23 minutes: Muridke, Bahawalpur, Muzaffarabad, Kotli, Chakothi"),
                    ("07 May 2025", "Result",      "All 9 targets destroyed; no IAF aircraft lost; BrahMos used on 2 hardened sites"),
                    ("08 May 2025", "LoC",         "Pakistan Army artillery response — 14 Indian border villages evacuated"),
                    ("10 May 2025", "Ceasefire",   "DGMO-level hotline activated; US SecState mediates ceasefire terms"),
                ],
                "EVT_LOC_SKIRMISHES_2025": [
                    ("07 May 2025", "Trigger",     "Post-Sindoor Pakistan Army artillery — 14 villages evacuated"),
                    ("08 May 2025", "Escalation",  "Indian Army counter-battery fire — Pakistani posts at 3 locations silenced"),
                    ("09 May 2025", "Peak",        "Heaviest exchange since Kargil — BSF and Army in joint posture"),
                    ("10 May 2025", "Ceasefire",   "DGMO hotline ceasefire — violations continue for 4 days after"),
                    ("14 May 2025", "Stabilise",   "Ceasefire holding; forward deployment maintained at high-readiness"),
                ],
                "EVT_IRAN_WAR_2026": [
                    ("Jan 2026",  "Trigger",      "US strikes on Iranian nuclear facilities after IAEA red-line crossed"),
                    ("Feb 2026",  "Iran Response","Iran launches ballistic missiles at US bases in Qatar and UAE"),
                    ("Feb 2026",  "Israel",       "Israel joins with strikes on Iranian IRGC command nodes"),
                    ("Mar 2026",  "Hormuz",       "Iran closes Strait of Hormuz — IRGC mines and corvette deployment"),
                    ("Mar 2026",  "Talks",        "Oman back-channel: ceasefire framework negotiations begin"),
                ],
            }

            FORCES_DEPLOYED = {
                "EVT_OPERATION_SINDOOR_2025": [
                    ("IAF", "Rafale EH", "Strike package — SCALP/Hammer munitions"),
                    ("IAF", "Mirage 2000H", "SEAD suppression of air defences"),
                    ("Army", "BrahMos Battery", "2 hardened targets — supersonic cruise strike"),
                    ("Army", "Special Forces", "Ground-truth verification post-strike"),
                    ("Navy", "INS Vikrant CBG", "Arabian Sea deterrence — surge posture"),
                ],
                "EVT_LOC_SKIRMISHES_2025": [
                    ("Army", "Artillery Brigade", "Counter-battery fire — Bofors + M777 howitzers"),
                    ("BSF", "5 Battalions", "Forward LoC posts — active engagement"),
                    ("IAF", "Su-30MKI CAP", "Combat air patrol over J&K — deterrence"),
                    ("MHA/CRPF", "8 Battalions", "Civilian evacuation and rear-area security"),
                ],
                "EVT_PAHALGAM_2025": [
                    ("CRPF", "8 Battalions", "Surge deployment to J&K within 48 hours"),
                    ("Army RR", "2 Battalions", "Cordon-and-search in Baisaran / Pahalgam belt"),
                    ("NIA", "Special Investigation Team", "Evidence collection and handler tracing"),
                    ("IB/RAW", "Technical Teams", "Signal intelligence on LeT network activation"),
                ],
                "EVT_INDIA_US_DEFENSE_2025": [
                    ("IAF", "GE F414 Engine ToT", "126 engines for Tejas MkII — IP transfer pending"),
                    ("Navy", "MQ-9B SeaGuardian", "30 drones — ISR over Indian Ocean"),
                    ("Army", "Stryker IFV evaluation", "Joint production feasibility — DRDO lead"),
                    ("MoD", "Chennai MRO Facility", "Joint venture — ₹8,000 Cr investment"),
                ],
            }

            DIPLOMATIC_RESPONSE = {
                "EVT_PAHALGAM_2025": [
                    ("India → Pakistan", "Suspended Indus Waters Treaty; expelled 6 diplomats; closed Attari-Wagah"),
                    ("Pakistan → India", "Expelled 6 Indian diplomats; denied involvement; sought UN intervention"),
                    ("USA",              "Called for restraint; SecState mediated ceasefire; condemned attack"),
                    ("Russia",           "Condemned terror attack; supported India's right to self-defence"),
                    ("China",            "Called for dialogue; abstained from condemning Pakistan at UNSC"),
                    ("UN Security Council", "Emergency session called; no resolution — China veto threat"),
                ],
                "EVT_OPERATION_SINDOOR_2025": [
                    ("India → World",    "MEA briefed 60 ambassadors; framed as targeted counter-terror, not war"),
                    ("Pakistan",         "Declared national emergency; activated nuclear command authority (NCA)"),
                    ("USA",              "Urged immediate de-escalation; both sides hotline activated"),
                    ("UK / France",      "Condemned Pahalgam; noted India's right to respond proportionately"),
                    ("China",            "Condemned Indian strikes; called for UN Security Council meeting"),
                    ("Gulf States",      "UAE and Saudi Arabia offered mediation — India accepted back-channel"),
                ],
                "EVT_INDIA_PAK_DIPLO_CRISIS_2025": [
                    ("India",            "Downgraded mission to Chargé d'Affaires; closed Kartarpur corridor"),
                    ("Pakistan",         "Expelled Indian HC staff; suspended all bilateral trade formally"),
                    ("USA",              "Offered consular assistance to both diaspora communities"),
                    ("UAE",              "Facilitated third-country communication channel"),
                ],
                "EVT_IRAN_WAR_2026": [
                    ("India",            "Called for restraint; abstained at UNSC; protected 18,000 nationals in Iran"),
                    ("India → Iran",     "Emergency consular operations — 6 flights to evacuate nationals"),
                    ("India → USA",      "Sought oil waiver exemption — similar to 2019 sanctions precedent"),
                    ("China",            "Condemned US strikes; continued Iran oil purchases"),
                    ("Russia",           "Supplied Iran with S-400 air defence components pre-war"),
                ],
                "EVT_TWELVE_DAY_WAR_2025": [
                    ("India",            "Abstained at UNSC; called for ceasefire; protected nationals in Israel and Iran"),
                    ("USA",              "Backed Israel; positioned carrier groups in Eastern Mediterranean"),
                    ("Russia / China",   "Backed Iran at UNSC; opposed military action"),
                    ("Gulf States",      "Closed airspace; UAE and Qatar offered mediation"),
                ],
                "EVT_INDIA_CANADA_2023": [
                    ("India",            "Expelled Canadian diplomat; called allegations 'absurd and motivated'"),
                    ("Canada",           "Expelled Indian diplomat; named RAW in Nijjar killing"),
                    ("USA / UK",         "Expressed concern; called for accountability — stopped short of India criticism"),
                    ("Five Eyes",        "Shared intelligence with Canada — India's Five Eyes concerns noted"),
                ],
                "EVT_G20_INDIA_2023": [
                    ("India",            "Achieved consensus Delhi Declaration — 83-point document, no Ukraine paragraph"),
                    ("Russia / China",   "Agreed to Delhi Declaration; Ukraine war language softened"),
                    ("Africa Union",     "Admitted as permanent G20 member — India's key diplomatic win"),
                    ("USA",              "Praised India's leadership; PGII infrastructure MoU signed"),
                ],
            }

            # ── Climate-specific panels ─────────────────────────────────────────────────
            IMD_ALERT_AUDIT = {
                "EVT_WAYANAD_2024":             ("Orange", "Red", "48 hrs before", "No evacuation ordered", "gap"),
                "EVT_CYCLONE_DANA_2024":        ("Red",    "Red", "72 hrs before", "800,000 evacuated",     "adequate"),
                "EVT_DELHI_FLOODS_2023":        ("Orange", "Red", "24 hrs before", "Partial — low-lying only","partial"),
                "EVT_INDIA_EXTREME_WEATHER_2025":("Red",   "Red", "Varies",        "6 states — mixed response","partial"),
                "EVT_JOSHIMATH_2023":           ("None",   "High","Weeks (slow)",  "600 families — reactive", "gap"),
            }
            # format: (alert_issued, actual_level, warning_lead_time, response_taken, assessment)

            NDRF_RESPONSE = {
                "EVT_WAYANAD_2024":              ("10 teams", "6 hours after disaster", "231 rescued", "No pre-positioning"),
                "EVT_CYCLONE_DANA_2024":         ("28 teams", "36 hours before landfall","800K evacuated","Pre-positioned"),
                "EVT_DELHI_FLOODS_2023":         ("12 teams", "8 hours after breach",   "27K displaced rescued","Delayed deployment"),
                "EVT_INDIA_EXTREME_WEATHER_2025":("48 teams", "Varies by state",        "6 states simultaneous","Stretched capacity"),
                "EVT_JOSHIMATH_2023":            ("4 teams",  "3 days after subsidence report","600 families","Adequate for scale"),
            }

            RECONSTRUCTION_STATUS = {
                "EVT_WAYANAD_2024":              ("18 months on", "Rehabilitation township: land acquired, construction 15%", "800 families in relief camps", "#f97316"),
                "EVT_CYCLONE_DANA_2024":         ("15 months on", "Housing reconstruction: 68% complete", "PMGSY roads: 82% restored", "#22c55e"),
                "EVT_DELHI_FLOODS_2023":         ("30 months on", "AMRUT storm drain: 41% complete", "Floodplain encroachments: still present", "#facc15"),
                "EVT_JOSHIMATH_2023":            ("36 months on", "Subsidence monitoring: active", "Rehabilitation: 420/600 families resettled", "#facc15"),
            }

            # ── Economics-specific panels ──────────────────────────────────────────────
            MARKET_REACTION = {
                "EVT_SP_UPGRADE_2025":      ("+1.8%", "+0.9%", "INR 83.1→81.4", "Positive — FII inflow ₹22,000 Cr in 30 days"),
                "EVT_INDIA_UK_CETA_2025":   ("+0.6%", "+0.3%", "Stable",        "Moderate positive — pharma/textile sectors led"),
                "EVT_HORMUZ_BLOCKADE_2026": ("-3.2%", "+18bp", "INR 84.2→87.6", "Negative — OMC stocks fell 8%; GAIL down 11%"),
                "EVT_IRAN_WAR_2026":        ("-4.1%", "+24bp", "INR 83.8→88.2", "Severe — Brent $120; fuel subsidy bill +₹40,000 Cr"),
                "EVT_TATA_SEMI_2024":       ("+2.1%", "-5bp",  "Stable",        "Positive — semiconductor index up 14% on day"),
                "EVT_IMEC_2023":            ("+0.4%", "-3bp",  "Stable",        "Modest — logistics sector up 3%"),
            }
            # format: (sensex_move, bond_yield_change, inr_move, summary)

            SECTOR_IMPACT = {
                "EVT_SP_UPGRADE_2025":      [("Banking / NBFC", "↑ Strong", "Lower borrowing costs; FII flows"), ("Infrastructure", "↑ Strong", "Increased bond financing capacity"), ("IT / Exports", "↑ Moderate", "Rupee appreciation risk to margins")],
                "EVT_INDIA_UK_CETA_2025":   [("Pharma", "↑ Strong", "₹28,000 Cr export pipeline — MHRA recognition pending"), ("Textiles", "↑ Moderate", "Tariff elimination on yarn and fabric"), ("Scotch / Spirits", "↓ Risk", "Domestic industry faces cheaper UK imports")],
                "EVT_HORMUZ_BLOCKADE_2026": [("OMCs / Oil", "↓ Severe", "HPCL / BPCL / IOC margin squeeze — crude cost +40%"), ("Aviation", "↓ Severe", "ATF price surge — SpiceJet, IndiGo loss-making"), ("Fertilizers", "↓ High", "Urea feedstock gas shortage — Rabi sowing at risk")],
                "EVT_IRAN_WAR_2026":        [("Energy", "↓ Severe", "India's 18% oil from Gulf — full supply disruption"), ("Defence PSUs", "↑ Strong", "HAL, BEL, MDL order book surge on security concerns"), ("Renewables", "↑ Moderate", "Crisis accelerates solar/wind capex approvals")],
                "EVT_TATA_SEMI_2024":       [("Electronics", "↑ Strong", "Import substitution — ₹2.4 Lakh Cr domestic chip market"), ("Auto / EV", "↑ Moderate", "Domestic chip supply reduces semiconductor import cost"), ("IT Services", "↑ Moderate", "Chip design services — new export category opens")],
            }

            # ── Technology-specific panels ──────────────────────────────────────────────
            MISSION_PARAMS = {
                "EVT_CHANDRAYAAN3_2023": [("Landing site", "Shiv Shakti Point — 69.37°S, 32.35°E", "South Polar region"), ("Lander", "Vikram — 1,752 kg", "Soft landing 23 Aug 2023"), ("Rover", "Pragyan — 26 kg", "500m traverse, 14 Earth-day mission"), ("Key finding", "Sulphur, Fe, O, Ti confirmed", "LIBS spectrometer data")],
                "EVT_ADITYAL1_2023":     [("Orbit", "L1 Halo orbit — 1.5M km from Earth", "Reached Jan 2024"), ("Payload", "VELC coronagraph", "Continuous solar observation"), ("Key data", "Solar wind speed real-time", "ISRO SEOC alert integration"), ("Duration", "5-year mission life", "Fuel sufficient to 2028")],
                "EVT_ISRO_SPADEX_2025":  [("Mission", "Space Docking Experiment", "2 spacecraft — SDX01 chaser, SDX02 target"), ("Docking", "Autonomous rendezvous at 470km LEO", "Completed Jan 2025"), ("Significance", "4th nation with autonomous docking", "After USA, Russia, China"), ("Next use", "Gaganyaan module transfer", "2026 crewed mission")],
                "EVT_SHUKLA_ISS_2025":   [("Mission", "Axiom Mission 4 — ISS", "Jun 2025, 14-day mission"), ("Crew", "Shubhanshu Shukla — pilot", "IAF Group Captain"), ("Experiments", "Muscle atrophy, food crops in space", "ISRO payload"), ("Significance", "First Indian in space since Rakesh Sharma 1984", "41-year gap closed")],
            }

            INDIA_RANKING = {
                "EVT_CHANDRAYAAN3_2023": ("Space", "4th nation to soft-land on Moon", "1st on lunar south pole", "USA / Russia / China / India"),
                "EVT_ISRO_SPADEX_2025":  ("Space", "4th nation with autonomous orbital docking", "India joins ISS-capable nations", "USA / Russia / China / India"),
                "EVT_SHUKLA_ISS_2025":   ("Space", "7th nation to send astronaut to ISS", "2nd Indian in space overall", "Gaganyaan 2026 crewed mission next"),
                "EVT_ADITYAL1_2023":     ("Space", "4th nation with dedicated solar observatory", "L1 orbit — only India + USA/ESA/Japan", "VELC: world's largest coronagraph in space"),
                "EVT_TATA_SEMI_2024":    ("Technology", "6th nation with domestic semiconductor fab", "1st in South Asia", "28nm node — 3 generations behind TSMC frontier"),
            }

            # ── Governance-specific panels ──────────────────────────────────────────────
            POLICY_STATUS = {
                "EVT_LABOUR_CODES_2025":     ("Gazette notified — Nov 2025", "Effective: Jan 2026", "28/28 states rules drafted", "Enforcement: partial — 14 states active"),
                "EVT_INDUS_WATERS_CRISIS_2025":("Treaty suspended — Apr 2025", "No expiry date", "World Bank mediation: India declined", "ICJ jurisdiction: disputed"),
                "EVT_INDIA_US_DEFENSE_2025": ("MoU signed — Oct 2025", "DTTI operative", "ITAR waivers: 14 of 22 cleared", "ToT on F414: pending IPR resolution"),
                "EVT_INDIA_UK_CETA_2025":    ("Agreement signed — Jul 2025", "Ratification: UK Parliament pending", "India GST notifications: due Q2 2026", "Tariff phase-down: 0→10 year schedule"),
                "EVT_SP_UPGRADE_2025":       ("Upgrade announced — Aug 2025", "Outlook: Stable", "Next review: Aug 2026", "Triggers: fiscal deficit <4.5% of GDP"),
            }

            # ── Tabs ────────────────────────────────────────────────────────
            DOMAIN_TAB = {
                "Defense":     "⚔ Operations",
                "Climate":     "🌊 Response",
                "Economics":   "📊 Markets",
                "Technology":  "🛰 Mission",
                "Geopolitics": "🌐 Diplomacy",
                "Governance":  "⚖ Policy",
                "Society":     "👥 Response",
            }
            domain_tab_name = DOMAIN_TAB.get(sdomain, "📋 Detail")
            tab_overview, tab_domain, tab_watch = st.tabs(["Overview", domain_tab_name, "👁 Watch"])

            # ── Tab 1 — Overview ─────────────────────────────────────────────
            with tab_overview:
                if sdesc:
                    st.markdown(
                        '<div style="font-size:7.5px;font-weight:700;color:#14b8a6;'
                        'letter-spacing:.08em;margin:4px 0 3px;">AI-EXTRACTED EVENT SUMMARY</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div style="font-size:10.5px;color:#94a3b8;line-height:1.55;'
                        f'background:#060f1e;border-radius:6px;padding:8px 10px;margin-bottom:8px;">'
                        f'{sdesc[:260]}{"…" if len(sdesc) > 260 else ""}</div>',
                        unsafe_allow_html=True,
                    )
                need_data = NEEDS_MAP.get(sel)
                if need_data:
                    need_title, need_desc, need_color = need_data
                    gap_header, gap_color = GAP_LABEL.get(sdomain, ("⚠ GAP EXPOSED", "#94a3b8"))
                    st.markdown(
                        f'<div style="background:#0d1f12;border-left:3px solid {need_color};'
                        f'border-radius:8px;padding:8px 10px;margin:6px 0 8px 0;">'
                        f'<div style="font-size:7.5px;font-weight:700;color:#14b8a6;'
                        f'letter-spacing:.08em;margin-bottom:2px;">AI-DETECTED RESILIENCE GAP</div>'
                        f'<div style="font-size:8px;font-weight:700;color:{gap_color};'
                        f'letter-spacing:.08em;margin-bottom:3px;">{gap_header}</div>'
                        f'<div style="font-size:11px;font-weight:600;color:#e2e8f0;">{need_title}</div>'
                        f'<div style="font-size:9px;color:#94a3b8;margin-top:2px;">{need_desc}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                if impacts:
                    st.markdown(
                        '<div style="font-size:8px;font-weight:700;color:#94a3b8;'
                        'letter-spacing:.08em;margin:8px 0 4px;">IMPACTS</div>',
                        unsafe_allow_html=True,
                    )
                    for imp in impacts[:4]:
                        itype = imp.get("type", "").replace("_", " ").title()
                        ival  = imp.get("value", "")
                        iunit = imp.get("unit", "")
                        st.markdown(
                            f'<div style="font-size:9.5px;color:#94a3b8;padding:2px 0;">'
                            f'<span style="color:#e2e8f0;font-weight:600;">{ival} {iunit}</span>'
                            f' — {itype}</div>',
                            unsafe_allow_html=True,
                        )
                if schemes and sdomain not in ("Defense", "Technology", "Economics"):
                    st.markdown(
                        '<div style="font-size:8px;font-weight:700;color:#38bdf8;'
                        'letter-spacing:.08em;margin:8px 0 4px;">LINKED SCHEMES</div>',
                        unsafe_allow_html=True,
                    )
                    for s in schemes[:3]:
                        sname_s = s.get("name", s.get("scheme_id", ""))[:32]
                        sbudget = s.get("budget_crore")
                        bstr    = f" · ₹{sbudget:,.0f} Cr" if sbudget else ""
                        st.markdown(
                            f'<div style="font-size:10px;color:#94a3b8;padding:2px 0;">• {sname_s}{bstr}</div>',
                            unsafe_allow_html=True,
                        )

            # ── Tab 2 — Domain tab ───────────────────────────────────────────
            with tab_domain:
                # ── Domain-specific panels ──────────────────────────────────────────────────
                if sdomain == "Defense":
                    # Escalation Chain
                    chain = ESCALATION_CHAIN.get(sel)
                    if chain:
                        st.markdown('<div style="font-size:8px;font-weight:700;color:#f97316;letter-spacing:.08em;margin:4px 0 6px;">ESCALATION CHAIN</div>', unsafe_allow_html=True)
                        for dt, stage, desc in chain:
                            st.markdown(
                                f'<div style="display:flex;gap:6px;margin-bottom:5px;">'
                                f'<div style="min-width:58px;font-size:8px;color:#475569;padding-top:1px;">{dt}</div>'
                                f'<div style="min-width:52px;font-size:8px;font-weight:700;color:#f97316;padding-top:1px;">{stage}</div>'
                                f'<div style="font-size:9px;color:#94a3b8;line-height:1.4;">{desc}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    # Forces Deployed
                    forces = FORCES_DEPLOYED.get(sel)
                    if forces:
                        st.markdown('<div style="font-size:8px;font-weight:700;color:#ef4444;letter-spacing:.08em;margin:8px 0 4px;">FORCES DEPLOYED</div>', unsafe_allow_html=True)
                        for service, asset, role in forces:
                            st.markdown(
                                f'<div style="background:#1a0a0a;border:1px solid #ef444430;border-radius:5px;'
                                f'padding:4px 8px;margin-bottom:3px;">'
                                f'<span style="font-size:9px;font-weight:700;color:#fca5a5;">{service}</span>'
                                f'<span style="font-size:9px;color:#94a3b8;"> · {asset}</span>'
                                f'<div style="font-size:8.5px;color:#475569;">{role}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    # Diplomatic Response
                    diplo = DIPLOMATIC_RESPONSE.get(sel)
                    if diplo:
                        st.markdown('<div style="font-size:8px;font-weight:700;color:#a78bfa;letter-spacing:.08em;margin:8px 0 4px;">DIPLOMATIC RESPONSE</div>', unsafe_allow_html=True)
                        for actor, action in diplo:
                            st.markdown(
                                f'<div style="border-left:2px solid #a78bfa44;padding:3px 0 3px 8px;margin-bottom:3px;">'
                                f'<span style="font-size:9px;font-weight:700;color:#c4b5fd;">{actor}</span>'
                                f'<div style="font-size:9px;color:#94a3b8;">{action}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    # TYPE1 — Operational Response
                    t1_schemes = TYPE1_MAP.get(sel)
                    if t1_schemes:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#f97316;'
                            'letter-spacing:.08em;margin:8px 0 4px;">OPERATIONAL RESPONSE</div>',
                            unsafe_allow_html=True,
                        )
                        for sname_t, sbudget_t, sministry_t in t1_schemes:
                            st.markdown(
                                f'<div style="background:#1a1200;border:1px solid #f9731640;'
                                f'border-radius:6px;padding:5px 8px;margin:2px 0;">'
                                f'<span style="font-size:10px;font-weight:700;color:#fdba74;">{sname_t}</span>'
                                f'<span style="font-size:9px;color:#94a3b8;"> · {sbudget_t} · {sministry_t}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                elif sdomain == "Climate":
                    # IMD Alert Audit
                    imd = IMD_ALERT_AUDIT.get(sel)
                    if imd:
                        alert_issued, actual_level, lead_time, response, assessment = imd
                        assess_color = "#22c55e" if assessment == "adequate" else ("#facc15" if assessment == "partial" else "#ef4444")
                        assess_label = {"adequate": "✓ ADEQUATE", "partial": "⚠ PARTIAL", "gap": "✗ FAILED"}.get(assessment, assessment)
                        st.markdown(
                            f'<div style="background:#0a1a0a;border:1px solid #22c55e33;border-radius:8px;padding:8px 10px;margin:6px 0;">'
                            f'<div style="font-size:8px;font-weight:700;color:#22c55e;letter-spacing:.08em;margin-bottom:5px;">IMD ALERT AUDIT</div>'
                            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:9px;">'
                            f'<div><span style="color:#475569;">Alert issued:</span> <span style="color:#e2e8f0;">{alert_issued}</span></div>'
                            f'<div><span style="color:#475569;">Actual level:</span> <span style="color:#e2e8f0;">{actual_level}</span></div>'
                            f'<div><span style="color:#475569;">Warning lead:</span> <span style="color:#e2e8f0;">{lead_time}</span></div>'
                            f'<div><span style="color:#475569;">Assessment:</span> <span style="color:{assess_color};font-weight:700;">{assess_label}</span></div>'
                            f'</div>'
                            f'<div style="font-size:9px;color:#64748b;margin-top:4px;">{response}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    # NDRF Response
                    ndrf = NDRF_RESPONSE.get(sel)
                    if ndrf:
                        teams, timing, outcome, note = ndrf
                        st.markdown(
                            f'<div style="background:#0a1628;border:1px solid #38bdf833;border-radius:8px;padding:8px 10px;margin:6px 0;">'
                            f'<div style="font-size:8px;font-weight:700;color:#38bdf8;letter-spacing:.08em;margin-bottom:5px;">NDRF RESPONSE</div>'
                            f'<div style="font-size:9px;color:#94a3b8;display:flex;flex-direction:column;gap:2px;">'
                            f'<div><span style="color:#475569;">Teams:</span> {teams}</div>'
                            f'<div><span style="color:#475569;">Deployed:</span> {timing}</div>'
                            f'<div><span style="color:#475569;">Outcome:</span> {outcome}</div>'
                            f'<div style="color:#475569;font-style:italic;">{note}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )
                    # Reconstruction Status
                    recon = RECONSTRUCTION_STATUS.get(sel)
                    if recon:
                        elapsed, status1, status2, rcolor = recon
                        st.markdown(
                            f'<div style="background:#0a1628;border-left:3px solid {rcolor};border-radius:6px;padding:7px 10px;margin:6px 0;">'
                            f'<div style="font-size:8px;font-weight:700;color:{rcolor};letter-spacing:.08em;margin-bottom:4px;">RECONSTRUCTION STATUS ({elapsed})</div>'
                            f'<div style="font-size:9px;color:#94a3b8;">• {status1}</div>'
                            f'<div style="font-size:9px;color:#94a3b8;margin-top:2px;">• {status2}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    # TYPE1 — Disaster Response
                    t1_schemes = TYPE1_MAP.get(sel)
                    if t1_schemes:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#f97316;'
                            'letter-spacing:.08em;margin:8px 0 4px;">DISASTER RESPONSE</div>',
                            unsafe_allow_html=True,
                        )
                        for sname_t, sbudget_t, sministry_t in t1_schemes:
                            st.markdown(
                                f'<div style="background:#1a1200;border:1px solid #f9731640;'
                                f'border-radius:6px;padding:5px 8px;margin:2px 0;">'
                                f'<span style="font-size:10px;font-weight:700;color:#fdba74;">{sname_t}</span>'
                                f'<span style="font-size:9px;color:#94a3b8;"> · {sbudget_t} · {sministry_t}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                elif sdomain == "Economics":
                    # Market Reaction
                    mkt = MARKET_REACTION.get(sel)
                    if mkt:
                        sensex, bond, inr, summary = mkt
                        s_color = "#22c55e" if "+" in sensex else "#ef4444"
                        b_color = "#ef4444" if "+" in bond else "#22c55e"
                        st.markdown(
                            f'<div style="background:#0a1628;border:1px solid #38bdf833;border-radius:8px;padding:8px 10px;margin:6px 0;">'
                            f'<div style="font-size:8px;font-weight:700;color:#38bdf8;letter-spacing:.08em;margin-bottom:6px;">MARKET REACTION (EVENT DAY)</div>'
                            f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:5px;">'
                            f'<div style="text-align:center;"><div style="font-size:14px;font-weight:800;color:{s_color};">{sensex}</div><div style="font-size:8px;color:#475569;">SENSEX</div></div>'
                            f'<div style="text-align:center;"><div style="font-size:14px;font-weight:800;color:{b_color};">{bond}</div><div style="font-size:8px;color:#475569;">10Y BOND</div></div>'
                            f'<div style="text-align:center;"><div style="font-size:13px;font-weight:700;color:#94a3b8;">{inr}</div><div style="font-size:8px;color:#475569;">INR/USD</div></div>'
                            f'</div>'
                            f'<div style="font-size:9.5px;color:#64748b;">{summary}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    # Sector Impact
                    sectors = SECTOR_IMPACT.get(sel)
                    if sectors:
                        st.markdown('<div style="font-size:8px;font-weight:700;color:#38bdf8;letter-spacing:.08em;margin:8px 0 4px;">SECTOR IMPACT</div>', unsafe_allow_html=True)
                        for sector, direction, detail in sectors:
                            dir_color = "#22c55e" if "↑" in direction else "#ef4444"
                            st.markdown(
                                f'<div style="background:#060f1e;border:1px solid #1e293b;border-radius:5px;'
                                f'padding:5px 8px;margin-bottom:3px;display:flex;align-items:flex-start;gap:8px;">'
                                f'<span style="font-size:12px;color:{dir_color};min-width:16px;">{direction.split()[0]}</span>'
                                f'<div><div style="font-size:9.5px;font-weight:600;color:#e2e8f0;">{sector}</div>'
                                f'<div style="font-size:9px;color:#64748b;">{detail}</div></div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                elif sdomain == "Technology":
                    # Mission Parameters
                    params = MISSION_PARAMS.get(sel)
                    if params:
                        st.markdown('<div style="font-size:8px;font-weight:700;color:#facc15;letter-spacing:.08em;margin:8px 0 4px;">MISSION PARAMETERS</div>', unsafe_allow_html=True)
                        for param, value, note in params:
                            st.markdown(
                                f'<div style="border-left:2px solid #facc1544;padding:3px 0 3px 8px;margin-bottom:3px;">'
                                f'<span style="font-size:9px;color:#fef08a;font-weight:600;">{param}:</span>'
                                f'<span style="font-size:9px;color:#e2e8f0;"> {value}</span>'
                                f'<div style="font-size:8.5px;color:#475569;">{note}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    # India Ranking
                    ranking = INDIA_RANKING.get(sel)
                    if ranking:
                        domain_r, position, milestone, context = ranking
                        st.markdown(
                            f'<div style="background:#0f1a0a;border:1px solid #facc1544;border-radius:8px;padding:8px 10px;margin:6px 0;">'
                            f'<div style="font-size:8px;font-weight:700;color:#facc15;letter-spacing:.08em;margin-bottom:4px;">INDIA GLOBAL STANDING</div>'
                            f'<div style="font-size:12px;font-weight:800;color:#fef08a;">{position}</div>'
                            f'<div style="font-size:9.5px;color:#94a3b8;margin-top:2px;">{milestone}</div>'
                            f'<div style="font-size:8.5px;color:#475569;margin-top:3px;">{context}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                elif sdomain == "Geopolitics":
                    # Diplomatic Response
                    diplo = DIPLOMATIC_RESPONSE.get(sel)
                    if diplo:
                        st.markdown('<div style="font-size:8px;font-weight:700;color:#a78bfa;letter-spacing:.08em;margin:8px 0 4px;">DIPLOMATIC RESPONSE</div>', unsafe_allow_html=True)
                        for actor, action in diplo:
                            st.markdown(
                                f'<div style="border-left:2px solid #a78bfa44;padding:3px 0 3px 8px;margin-bottom:3px;">'
                                f'<span style="font-size:9px;font-weight:700;color:#c4b5fd;">{actor}</span>'
                                f'<div style="font-size:9px;color:#94a3b8;">{action}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                elif sdomain == "Governance":
                    # Policy Status
                    pol = POLICY_STATUS.get(sel)
                    if pol:
                        status, effective, adoption, enforcement = pol
                        st.markdown(
                            f'<div style="background:#0a1628;border:1px solid #06b6d433;border-radius:8px;padding:8px 10px;margin:6px 0;">'
                            f'<div style="font-size:8px;font-weight:700;color:#06b6d4;letter-spacing:.08em;margin-bottom:5px;">POLICY STATUS</div>'
                            f'<div style="font-size:9px;color:#94a3b8;display:flex;flex-direction:column;gap:3px;">'
                            f'<div><span style="color:#475569;">Status:</span> <span style="color:#22c55e;font-weight:600;">{status}</span></div>'
                            f'<div><span style="color:#475569;">Effective:</span> {effective}</div>'
                            f'<div><span style="color:#475569;">State adoption:</span> {adoption}</div>'
                            f'<div><span style="color:#475569;">Enforcement:</span> {enforcement}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )
                    # Linked Schemes
                    if schemes:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#38bdf8;'
                            'letter-spacing:.08em;margin:8px 0 4px;">LINKED SCHEMES</div>',
                            unsafe_allow_html=True,
                        )
                        for s in schemes[:3]:
                            sname_s = s.get("name", s.get("scheme_id", ""))[:32]
                            sbudget  = s.get("budget_crore")
                            bstr     = f" · ₹{sbudget:,.0f} Cr" if sbudget else ""
                            st.markdown(
                                f'<div style="font-size:10px;color:#94a3b8;padding:2px 0;">• {sname_s}{bstr}</div>',
                                unsafe_allow_html=True,
                            )

                elif sdomain == "Society":
                    # TYPE1 — Emergency Response
                    t1_schemes = TYPE1_MAP.get(sel)
                    if t1_schemes:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#f97316;'
                            'letter-spacing:.08em;margin:8px 0 4px;">EMERGENCY RESPONSE</div>',
                            unsafe_allow_html=True,
                        )
                        for sname_t, sbudget_t, sministry_t in t1_schemes:
                            st.markdown(
                                f'<div style="background:#1a1200;border:1px solid #f9731640;'
                                f'border-radius:6px;padding:5px 8px;margin:2px 0;">'
                                f'<span style="font-size:10px;font-weight:700;color:#fdba74;">{sname_t}</span>'
                                f'<span style="font-size:9px;color:#94a3b8;"> · {sbudget_t} · {sministry_t}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    # Schemes
                    if schemes:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#38bdf8;'
                            'letter-spacing:.08em;margin:8px 0 4px;">LINKED SCHEMES</div>',
                            unsafe_allow_html=True,
                        )
                        for s in schemes[:3]:
                            sname_s = s.get("name", s.get("scheme_id", ""))[:32]
                            sbudget  = s.get("budget_crore")
                            bstr     = f" · ₹{sbudget:,.0f} Cr" if sbudget else ""
                            st.markdown(
                                f'<div style="font-size:10px;color:#94a3b8;padding:2px 0;">• {sname_s}{bstr}</div>',
                                unsafe_allow_html=True,
                            )

                # ── Dynamic fallback for live-ingested events not in curated dicts ──
                # Checks if anything was rendered above; if not, shows Neo4j data
                _has_curated = any([
                    ESCALATION_CHAIN.get(sel), FORCES_DEPLOYED.get(sel),
                    DIPLOMATIC_RESPONSE.get(sel), TYPE1_MAP.get(sel),
                    IMD_ALERT_AUDIT.get(sel), NDRF_RESPONSE.get(sel),
                    RECONSTRUCTION_STATUS.get(sel), MARKET_REACTION.get(sel),
                    SECTOR_IMPACT.get(sel), MISSION_PARAMS.get(sel),
                    INDIA_RANKING.get(sel), POLICY_STATUS.get(sel),
                ])
                if not _has_curated:
                    if actors:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#38bdf8;'
                            'letter-spacing:.08em;margin:4px 0 6px;">KEY ACTORS</div>',
                            unsafe_allow_html=True,
                        )
                        for a in actors[:5]:
                            aname = a.get("name", a.get("actor_id", ""))
                            atype = a.get("type", "")
                            st.markdown(
                                f'<div style="font-size:9.5px;color:#94a3b8;padding:2px 0;">'
                                f'<span style="color:#e2e8f0;font-weight:600;">{aname}</span>'
                                f'{" · " + atype if atype else ""}</div>',
                                unsafe_allow_html=True,
                            )
                    if policies:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#06b6d4;'
                            'letter-spacing:.08em;margin:8px 0 4px;">LINKED POLICIES</div>',
                            unsafe_allow_html=True,
                        )
                        for p in policies[:3]:
                            pname = p.get("name", p.get("policy_id", ""))
                            st.markdown(
                                f'<div style="font-size:9.5px;color:#94a3b8;padding:2px 0;">• {pname}</div>',
                                unsafe_allow_html=True,
                            )
                    if schemes:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#facc15;'
                            'letter-spacing:.08em;margin:8px 0 4px;">LINKED SCHEMES</div>',
                            unsafe_allow_html=True,
                        )
                        for s in schemes[:3]:
                            sname_s = s.get("name", s.get("scheme_id", ""))
                            st.markdown(
                                f'<div style="font-size:9.5px;color:#94a3b8;padding:2px 0;">• {sname_s}</div>',
                                unsafe_allow_html=True,
                            )
                    if evidence:
                        st.markdown(
                            '<div style="font-size:8px;font-weight:700;color:#e2e8f0;'
                            'letter-spacing:.08em;margin:8px 0 4px;">EVIDENCE SOURCES</div>',
                            unsafe_allow_html=True,
                        )
                        for ev in evidence[:3]:
                            etitle = ev.get("title", ev.get("evidence_id", ""))
                            eurl   = ev.get("url", "")
                            link   = f' <a href="{eurl}" target="_blank" style="color:{scolor};font-size:8px;">→</a>' if eurl else ""
                            st.markdown(
                                f'<div style="font-size:9.5px;color:#94a3b8;padding:2px 0;">• {etitle}{link}</div>',
                                unsafe_allow_html=True,
                            )
                    if not any([actors, policies, schemes, evidence]):
                        st.markdown(
                            '<div style="font-size:10px;color:#334155;padding:12px 0;">'
                            'Intelligence brief not yet available for this event.<br>'
                            '<span style="font-size:9px;">Data will populate as evidence is verified and added to the graph.</span></div>',
                            unsafe_allow_html=True,
                        )

            # ── Tab 3 — Watch ───────────────────────────────────────────────────────
            # ── Tab 3 — Watch ────────────────────────────────────────────────
            with tab_watch:
                watch = WATCH_POINTS.get(sel)
                if watch:
                    st.markdown(
                        '<div style="font-size:8px;font-weight:700;color:#f59e0b;'
                        'letter-spacing:.08em;margin-bottom:6px;">WATCH POINTS</div>',
                        unsafe_allow_html=True,
                    )
                    for wp in watch:
                        st.markdown(
                            f'<div style="font-size:9.5px;color:#94a3b8;padding:3px 0 3px 8px;'
                            f'border-left:2px solid #f59e0b44;margin-bottom:4px;">• {wp}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        '<div style="font-size:10px;color:#334155;padding:12px 0;">No watch points available for this event.</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            if st.button("Decision Engine →", key=f"goto_graph_{sel}",
                         use_container_width=True, type="primary"):
                st.session_state["deep_link_event"] = sel
                st.switch_page("pages/02_Decision_Engine.py")
        else:
            _featured = "EVT_PAHALGAM_2025"
            if _featured in EVENT_META:
                lat0, lon0, sname, sdomain, scolor, sdate, ssev = EVENT_META[_featured]
                _featured_data = safe_get(f"/ontology/events/{_featured}") or {}
                _fdesc = (_featured_data.get("event") or {}).get("description", "")
                st.markdown(f"""
                <div style='padding:10px;border-radius:8px;background:#0f1f2e;border:1px solid {scolor}44'>
                  <div style='color:{scolor};font-size:10px;font-weight:700;letter-spacing:0.08em;'>FEATURED EVENT</div>
                  <div style='font-size:13px;font-weight:700;color:#e2e8f0;margin-top:4px;'>{sname}</div>
                  <div style='font-size:10px;color:#94a3b8;'>{sdomain} · {sdate}</div>
                  <div style='font-size:11px;color:#cbd5e1;margin-top:6px;line-height:1.5;'>
                    {_fdesc}
                  </div>
                </div>
                """, unsafe_allow_html=True)



page()
render_ontology_model()
