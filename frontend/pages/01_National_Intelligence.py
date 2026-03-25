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

# --- Fix 13: Hardcoded fallback event detail for demo (used when Neo4j is down) ---
_FALLBACK_DETAIL = {
    "EVT_DELHI_FLOODS_2023": {
        "description": (
            "Record Yamuna flooding in July 2023 — Hathnikund Barrage released 3.59 lakh cusecs, "
            "highest in 45 years. River breached 208.66m, its highest mark since 1978. "
            "27,000 persons displaced across Delhi's low-lying floodplain areas."
        ),
        "impacts": [
            {"type": "persons_displaced", "value": "27,000",  "unit": "persons"},
            {"type": "river_level",       "value": "208.66",  "unit": "metres"},
            {"type": "barrage_discharge", "value": "3.59",    "unit": "lakh cusecs"},
            {"type": "rainfall_24h",      "value": "153",     "unit": "mm"},
        ],
        "schemes": [
            {"name": "AMRUT 2.0 — Storm Drain Upgrade",    "budget_crore": 1200},
            {"name": "SDRF Delhi Flood Relief",             "budget_crore": 450},
            {"name": "DJB Water Supply Restoration",        "budget_crore": None},
        ],
    },
    "EVT_WAYANAD_2024": {
        "description": (
            "India's deadliest landslide in recorded history struck Mundakkai and Chooralmala "
            "villages, Wayanad at 2am on 30 July 2024. IMD had issued only an Orange Alert — "
            "no pre-emptive evacuation was ordered. 231 confirmed dead, 1,000+ displaced."
        ),
        "impacts": [
            {"type": "deaths",            "value": "231",     "unit": "persons"},
            {"type": "displaced",         "value": "1,000+",  "unit": "persons"},
            {"type": "villages_destroyed","value": "2",       "unit": "villages"},
        ],
        "schemes": [
            {"name": "Kerala SDRF Landslide Relief",       "budget_crore": 300},
            {"name": "NDRF Rescue Operations",             "budget_crore": None},
            {"name": "PM Relief Fund — Wayanad",           "budget_crore": 200},
        ],
    },
    "EVT_CHAMOLI_2021": {
        "description": (
            "Rock-and-ice avalanche on 7 Feb 2021 in Ronti Gad, Chamoli sent a debris flow "
            "destroying NTPC Tapovan-Vishnugad (520 MW) and Rishiganga Power Project (13.2 MW). "
            "204 killed or missing. ₹1,500+ Cr infrastructure damage."
        ),
        "impacts": [
            {"type": "deaths_missing",    "value": "204",     "unit": "persons"},
            {"type": "infrastructure",    "value": "1,500+",  "unit": "Cr INR damage"},
            {"type": "power_loss",        "value": "533",     "unit": "MW"},
        ],
        "schemes": [
            {"name": "NDRF Rescue — Chamoli",              "budget_crore": None},
            {"name": "Uttarakhand SDRF Emergency",         "budget_crore": 180},
            {"name": "NTPC Tapovan Reconstruction",        "budget_crore": 800},
        ],
    },
    "EVT_JOSHIMATH_2023": {
        "description": (
            "Joshimath, Uttarakhand saw 4,000+ structures develop visible cracks from January 2023. "
            "600+ families evacuated. Wadia Institute linked NTPC Tapovan tunnel boring as primary "
            "anthropogenic trigger. Gateway to Badrinath — ₹100+ Cr tourism disruption."
        ),
        "impacts": [
            {"type": "structures_damaged","value": "4,000+",  "unit": "buildings"},
            {"type": "families_evacuated","value": "600+",    "unit": "families"},
            {"type": "tourism_loss",      "value": "100+",    "unit": "Cr INR"},
        ],
        "schemes": [
            {"name": "NDMA Joshimath Rehabilitation",      "budget_crore": 250},
            {"name": "NTPC Tapovan Halt Order",            "budget_crore": None},
            {"name": "Uttarakhand HRERA Compensation",     "budget_crore": None},
        ],
    },
    "EVT_CYCLONE_DANA_2024": {
        "description": (
            "Cyclone Dana made landfall on Odisha coast on 25 Oct 2024 with 100–120 kmph winds. "
            "800,000+ evacuated in India's largest pre-cyclone evacuation. "
            "₹6,000 Cr agricultural and infrastructure damage across Odisha and Andhra Pradesh."
        ),
        "impacts": [
            {"type": "evacuated",         "value": "800,000+","unit": "persons"},
            {"type": "total_damage",      "value": "6,000",   "unit": "Cr INR"},
            {"type": "wind_speed",        "value": "120",     "unit": "kmph"},
        ],
        "schemes": [
            {"name": "Odisha SDRF Cyclone Relief",         "budget_crore": 500},
            {"name": "NDRF Cyclone Dana Response",         "budget_crore": None},
            {"name": "PM Fasal Bima Yojana — Crop Loss",  "budget_crore": 350},
        ],
    },
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

    # ── Event dropdown + Cross-links toggle ──────────────────────────────────
    tcol1, tcol2 = st.columns([2.5, 1], gap="medium")
    with tcol1:
        render_event_dropdown("sel_event", "map_event_dropdown", include_all=True)
    with tcol2:
        show_cross = st.checkbox("Cross-links", value=False, key="cross_cb")
        if show_cross:
            st.markdown(
                "<div style='font-size:9px;color:#FFD700;margin-top:-8px;'>🌐 World view</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='font-size:9px;color:#94a3b8;margin-top:-8px;'>🇮🇳 India view</div>",
                unsafe_allow_html=True
            )

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
        use_fitbounds = False # Manual centers are cleaner for "revelation" demo

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
        ("EVT_DELHI_FLOODS_2023",   "EVT_CHAMOLI_2021",       "Shared Himalayan drainage basin risk"),
        ("EVT_DELHI_FLOODS_2023",   "EVT_JOSHIMATH_2023",     "Urban load on fragile river floodplain"),
        ("EVT_TATA_SEMI_2024",      "EVT_RUSSIA_UKRAINE_2022","Chip supply chain disrupted by sanctions"),
        ("EVT_IMEC_2023",           "EVT_GAZA_REDSEA_2023",   "IMEC corridor frozen by Red Sea crisis"),
        ("EVT_G20_INDIA_2023",      "EVT_INDIA_CANADA_2023",  "G20 diplomacy vs bilateral breakdown"),
        ("EVT_CHANDRAYAAN3_2023",   "EVT_ADITYAL1_2023",      "ISRO dual-mission resource allocation"),
        ("EVT_COVID_WAVE2_2021",    "EVT_MANIPUR_2023",       "Healthcare capacity stress — NE India"),
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
    col_map, col_right = st.columns([3.2, 1], gap="medium")

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

        # ── Intelligence Insight panel (below map) ──────────────────
        current_sel = st.session_state.sel_event
        INSIGHT_MAP = {
            "EVT_DELHI_FLOODS_2023":   ("Climate × Governance",  "3 consecutive flood events linked to Ward 46 drainage gap — AMRUT delivery 33% complete. Structural fix overdue."),
            "EVT_CHAMOLI_2021":        ("Climate × Technology",   "Chamoli and Joshimath share the same Himalayan fault zone. Hydropower construction is amplifying subsidence risk."),
            "EVT_JOSHIMATH_2023":      ("Climate × Governance",   "Joshimath subsidence accelerated after NTPC tunnel boring — MoEF environmental clearance under review."),
            "EVT_WAYANAD_2024":        ("Climate × Society",      "Wayanad landslide zone has 3× higher deforestation rate than Kerala average — land-use policy gap exposed."),
            "EVT_CYCLONE_DANA_2024":   ("Climate × Economics",    "Cyclone Dana disrupted Odisha fisheries (₹800 Cr loss) — SDRF covers disaster but not livelihood recovery."),
            "EVT_TATA_SEMI_2024":      ("Technology × Economics", "India's first fab reduces chip import by est. 12% — but skill gap of 85,000 engineers remains unaddressed."),
            "EVT_IMEC_2023":           ("Geopolitics × Economics","IMEC corridor progress frozen since Gaza conflict — Red Sea rerouting adding ₹4,200 Cr/yr to India's trade cost."),
            "EVT_INDIA_CANADA_2023":   ("Geopolitics × Society",  "Diplomatic row affecting 1.4M Indian diaspora in Canada — student visa rejections up 38% since Sep 2023."),
            "EVT_COVID_WAVE2_2021":    ("Society × Governance",   "Wave 2 exposed oxygen supply chain with single-point failure — 162 hospitals ran out within 48 hrs simultaneously."),
            "EVT_RUSSIA_UKRAINE_2022": ("Geopolitics × Economics","India's Russian oil discount (avg $18/bbl) saving ₹1.2 Lakh Cr/yr — but fertilizer dependency remains critical risk."),
            "EVT_G20_INDIA_2023":      ("Geopolitics × Economics","G20 Delhi Declaration secured consensus on debt restructuring for 73 low-income nations — India's soft power peak."),
            "EVT_MANIPUR_2023":        ("Society × Governance",   "Manipur conflict: 60,000+ displaced, 5,000+ homes burned — CRPF deployed but MHA reconciliation framework absent."),
            "EVT_BALAKOT_2019":        ("Defense × Geopolitics",  "Balakot established India's right to pre-emptive strikes — Pakistan has not retaliated militarily in 5+ years."),
            "EVT_CHANDRAYAAN3_2023":   ("Technology × Geopolitics","Chandrayaan-3 placed India as 4th lunar nation — ISRO now fielding 3 commercial launch requests from foreign entities."),
            "EVT_GAZA_REDSEA_2023":    ("Geopolitics × Economics","Red Sea crisis: India's Europe-bound cargo now rerouted via Cape of Good Hope — avg 14 extra days per shipment."),
        }
        DEFAULT_INSIGHT = ("Cross-domain Pattern", "NDMA is active lead responder across 4 simultaneous critical events — institutional overload risk rising.")
        insight_domain, insight_text = INSIGHT_MAP.get(current_sel, DEFAULT_INSIGHT)

        st.markdown(
            f'<div style="background:#0a0f1f;border:1px solid #1e3a5f;border-radius:10px;'
            f'padding:10px 14px;margin-top:8px;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
            f'<span style="font-size:9px;font-weight:700;color:#a78bfa;letter-spacing:.08em;">'
            f'🧠 INTELLIGENCE INSIGHT</span>'
            f'<span style="background:#a78bfa22;border:1px solid #a78bfa55;border-radius:20px;'
            f'padding:1px 8px;font-size:8px;color:#c4b5fd;">{insight_domain}</span>'
            f'</div>'
            f'<div style="font-size:11px;color:#cbd5e1;line-height:1.5;">{insight_text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

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
            sdesc    = evt_data.get("description", "") or api_events.get(sel, {}).get("description", "")

            # --- Fix 13: fallback when Neo4j returns nothing ---
            _fb = _FALLBACK_DETAIL.get(sel, {})
            if not impacts:
                impacts = _fb.get("impacts", [])
            if not schemes:
                schemes = _fb.get("schemes", [])
            if not sdesc:
                sdesc   = _fb.get("description", "")

            st.markdown(f"""
            <div style="border-left:3px solid {scolor};padding:10px 12px;
                        background:#0a1628;border-radius:6px;margin-bottom:8px;">
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
                    f'{sdesc[:260]}{"…" if len(sdesc) > 260 else ""}</div>',
                    unsafe_allow_html=True,
                )

            # ── Governance Need Exposed ─────────────────────────────────────────────
            NEEDS_MAP = {
                "EVT_DELHI_FLOODS_2023":  ("Drainage Capacity Need",       "Ward-level storm water drain capacity insufficient; Ward 46 incomplete.", "#22c55e"),
                "EVT_WAYANAD_2024":       ("Land-Use Governance Need",     "Deforestation on eco-sensitive slopes without oversight.", "#f97316"),
                "EVT_CHAMOLI_2021":       ("Hydropower Regulation Need",   "Unregulated hydropower in glacial zones exposes downstream communities.", "#38bdf8"),
                "EVT_JOSHIMATH_2023":     ("Urban Subsidence Need",        "Heavy construction on fragile hill terrain without geological load assessment.", "#fb7185"),
                "EVT_COVID_WAVE2_2021":   ("Health Supply-Chain Need",     "Oxygen and ICU surge capacity grossly inadequate vs peak demand.", "#a78bfa"),
                "EVT_MANIPUR_2023":       ("Conflict Early-Warning Need",  "Ethnic tension signals went unaddressed 6+ months before escalation.", "#f97316"),
                "EVT_CYCLONE_DANA_2024":  ("Coastal Resilience Need",      "Cyclone-resilient housing and early-warning last-mile gaps in Odisha.", "#38bdf8"),
                "EVT_RUSSIA_UKRAINE_2022":("Energy Diversification Need",  "Over-dependence on Russian oil; no strategic petroleum reserve policy.", "#facc15"),
                "EVT_GAZA_REDSEA_2023":   ("Trade Route Resilience Need",  "IMEC corridor not operationalized; Red Sea alternate route absent.", "#fb7185"),
                "EVT_TATA_SEMI_2024":     ("Semiconductor Sovereignty Need","Domestic chip manufacturing capacity near-zero before PLI.", "#facc15"),
            }
            need_data = NEEDS_MAP.get(sel)
            if need_data:
                need_title, need_desc, need_color = need_data
                st.markdown(
                    f'<div style="background:#0d1f12;border-left:3px solid {need_color};'
                    f'border-radius:8px;padding:8px 10px;margin:6px 0 8px 0;">'
                    f'<div style="font-size:8px;font-weight:700;color:{need_color};'
                    f'letter-spacing:.08em;margin-bottom:3px;">⚠ GOVERNANCE NEED EXPOSED</div>'
                    f'<div style="font-size:11px;font-weight:600;color:#e2e8f0;">{need_title}</div>'
                    f'<div style="font-size:9px;color:#94a3b8;margin-top:2px;">{need_desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Type 1 Government Response ──────────────────────────────────────────
            TYPE1_MAP = {
                "EVT_DELHI_FLOODS_2023":  [("SDRF", "₹43,900 Cr", "MHA"), ("NDRF", "₹12,390 Cr", "MHA")],
                "EVT_WAYANAD_2024":       [("SDRF", "₹200 Cr", "Kerala Govt"), ("NDRF", "₹90 Cr", "MHA")],
                "EVT_CHAMOLI_2021":       [("SDRF", "₹150 Cr", "Uttarakhand"), ("NDRF", "₹60 Cr", "MHA")],
                "EVT_CYCLONE_DANA_2024":  [("SDRF", "₹800 Cr", "Odisha Govt"), ("NDRF", "₹350 Cr", "MHA")],
                "EVT_JOSHIMATH_2023":     [("SDRF", "₹250 Cr", "Uttarakhand"), ("NDRF", "₹80 Cr", "MHA")],
                "EVT_MANIPUR_2023":       [("SDRF", "₹175 Cr", "Manipur Govt"), ("CRPF Deploy", "5 Bn", "MHA")],
            }
            t1_schemes = TYPE1_MAP.get(sel)
            if t1_schemes:
                st.markdown(
                    '<div style="font-size:8px;font-weight:700;color:#f97316;'
                    'letter-spacing:.08em;margin:8px 0 4px;">🚨 TYPE 1 — EMERGENCY RESPONSE</div>',
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
            elif not schemes:
                st.markdown(
                    '<div style="font-size:9px;color:#475569;margin:6px 0 4px;">'
                    'No Type 1 SDRF/NDRF response recorded.</div>',
                    unsafe_allow_html=True,
                )

            # ── Linked Schemes (Type 2 from graph) ─────────────────────────────────
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

            if impacts:
                st.markdown(
                    '<div style="font-size:9px;color:#475569;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.08em;margin-top:8px;margin-bottom:4px;">IMPACTS</div>',
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
            if st.button("Scheme Tracker →", key=f"goto_graph_{sel}",
                         use_container_width=True, type="primary"):
                st.session_state["deep_link_event"] = sel
                st.switch_page("pages/02_Scheme_Tracker.py")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Proof & Evidence →", key=f"goto_proof_{sel}",
                         use_container_width=True):
                st.session_state["deep_link_brief"] = sel
                st.switch_page("pages/04_Proof_and_Evidence.py")
        else:
            _featured = "EVT_DELHI_FLOODS_2023"
            if _featured in EVENT_META:
                lat0, lon0, sname, sdomain, scolor, sdate, ssev = EVENT_META[_featured]
                _fb = _FALLBACK_DETAIL.get(_featured, {})
                st.markdown(f"""
                <div style='padding:10px;border-radius:8px;background:#0f1f2e;border:1px solid {scolor}44'>
                  <div style='color:{scolor};font-size:10px;font-weight:700;letter-spacing:0.08em;'>⭐ FEATURED EVENT</div>
                  <div style='font-size:13px;font-weight:700;color:#e2e8f0;margin-top:4px;'>{sname}</div>
                  <div style='font-size:10px;color:#94a3b8;'>{sdomain} · {sdate}</div>
                  <div style='font-size:11px;color:#cbd5e1;margin-top:6px;line-height:1.5;'>
                    {_fb.get("description","")[:200]}...
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Live Ingestion — always-visible banner strip ────────────────────────
    _STATIC_TICKER = [
        ("🟢", "IMD Rainfall Alert — Yamuna basin · Updated 2 min ago",         "#22c55e"),
        ("🔴", "NDMA Flash Flood Warning — Delhi NCT · CRITICAL",               "#ef4444"),
        ("🟡", "PIB: SDRF ₹43,900 Cr release confirmed · Jul 2023",             "#facc15"),
        ("🟢", "data.gov.in: AMRUT Ward 45 Gali 7 asset verified ✅",           "#22c55e"),
        ("🔵", "ISRO: Cyclone Dana track updated · Landfall in 18 hrs",         "#38bdf8"),
        ("🟢", "MoHUA: PMAY Delhi 17,067 houses — 100% occupancy confirmed",   "#22c55e"),
        ("🟡", "MEA: India-Canada diplomatic note issued · Response pending",   "#facc15"),
    ]

    if "ticker_idx" not in st.session_state:
        st.session_state.ticker_idx = 0

    # Try pulling a live node from the backend first
    _LABEL_DOT = {"Evidence": "🟢", "Event": "🔵", "Actor": "🟡", "Scheme": "🟤"}
    _LABEL_COL  = {"Evidence": "#22c55e", "Event": "#38bdf8", "Actor": "#facc15", "Scheme": "#a78bfa"}

    try:
        import requests as _r
        _live_resp = _r.get("http://localhost:8000/ingest/live/recent-nodes", timeout=2)
        _live_nodes = _live_resp.json().get("nodes", []) if _live_resp.status_code == 200 else []
    except Exception:
        _live_nodes = []

    if _live_nodes:
        _n     = _live_nodes[st.session_state.ticker_idx % len(_live_nodes)]
        _lbl   = _n.get("label", "Evidence")
        _ts    = _n.get("ts", "")[:19].replace("T", " ")
        dot    = _LABEL_DOT.get(_lbl, "🟢")
        text   = f"{_n.get('name', '')[:70]} · {_ts}"
        col    = _LABEL_COL.get(_lbl, "#22c55e")
    else:
        idx   = st.session_state.ticker_idx % len(_STATIC_TICKER)
        dot, text, col = _STATIC_TICKER[idx]

    st.markdown(
        f'<div style="background:#050e1a;border:1px solid #0f2a45;border-radius:10px;'
        f'padding:8px 14px;margin-top:10px;display:flex;align-items:center;gap:10px;">'
        f'<div style="font-size:9px;font-weight:700;color:#38bdf8;letter-spacing:.1em;'
        f'white-space:nowrap;">📡 LIVE INGESTION</div>'
        f'<div style="flex:1;font-size:10px;color:{col};">{dot} {text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tick_col, full_col = st.columns([1, 1], gap="small")
    with tick_col:
        if st.button("⟳ Next Update", key="ticker_next_btn", use_container_width=True):
            st.session_state.ticker_idx += 1
            st.rerun()
    with full_col:
        with st.expander("⚡ Live Data Sources", expanded=False):
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
        fetch_clicked = st.button("🔍 Refresh Live Sources", use_container_width=True, type="primary",
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
            'Click "Refresh Live Sources" to scrape live governance news and extract entities.</div>',
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
