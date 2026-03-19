"""
Ward Map — PRAMAAN v5.0
Premium UI: branded header · score hero · glassmorphism cards · scheme chart · asset table · map
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math
import streamlit as st
import streamlit.components.v1 as components
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

from utils.constants import SCHEME_SHORT_NAMES, ASSET_VERIFICATION_OVERRIDE
from utils.icons import icon, icon_box
from utils.geo_selector import INDIAN_STATES, DELHI_ULBS, DELHI_ZONES, ZONE_WARDS
from utils.session import init_session, get_ward_id, get_ward_name, get_breadcrumb, DEFAULT_STATE, DEFAULT_CITY, DEFAULT_ZONE, DEFAULT_WARD
from components.topnav import render_topnav

BASE_URL = "http://127.0.0.1:8000"

# Approximate ward boundary polygons (lat/lon pairs, clockwise).
# Used to draw the ward outline on the folium map.
# Extend this dict as more wards are added.
WARD_BOUNDARIES: dict[str, list[tuple[float, float]]] = {
    "REG_W45": [
        (28.677, 77.284), (28.677, 77.306),
        (28.672, 77.313), (28.660, 77.309),
        (28.655, 77.291), (28.659, 77.283),
        (28.677, 77.284),  # close polygon
    ],
}

# Ward centroid + max-radius (km) for pin sanity-filter.
# Pins beyond the radius are almost certainly mis-tagged data.
WARD_CENTROID: dict[str, tuple[float, float]] = {
    "REG_W45": (28.666, 77.296),
}
PIN_RADIUS_KM = 18  # generous enough for Burari / Khureji Khas (~10 km away)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate great-circle distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))

STATUS_CONFIG = {
    "fully_verified":     ("✅ Fully Verified",      "green",  "#10b981", "#22c55e"),
    "partially_verified": ("⚠️ Partially Verified",  "orange", "#f59e0b", "#f59e0b"),
    "unverified":         ("❌ Unverified",           "red",    "#ef4444", "#ef4444"),
    "news_only":          ("📰 News Only",            "orange", "#f59e0b", "#f59e0b"),
    "verified":           ("✅ Fully Verified",       "green",  "#10b981", "#22c55e"),
    None:                 ("❌ Unverified",           "red",    "#ef4444", "#ef4444"),
    "":                   ("❌ Unverified",           "red",    "#ef4444", "#ef4444"),
}


def apply_override(breakdown: list) -> list:
    for asset in breakdown:
        aid = asset.get("asset_id", "")
        if aid in ASSET_VERIFICATION_OVERRIDE:
            asset["proof_status"] = ASSET_VERIFICATION_OVERRIDE[aid]
    return breakdown


def compute_score(breakdown: list) -> tuple[float, dict]:
    counts = {"fully_verified": 0, "partially_verified": 0, "news_only": 0, "unverified": 0}
    weighted = 0.0
    for b in breakdown:
        ps = b.get("proof_status", "unverified")
        if ps in ("fully_verified", "verified"):
            weighted += 1.0
            counts["fully_verified"] += 1
        elif ps == "partially_verified":
            weighted += 0.5
            counts["partially_verified"] += 1
        elif ps == "news_only":
            weighted += 0.25
            counts["news_only"] += 1
        else:
            counts["unverified"] += 1
    total = len(breakdown)
    score = round(100 * weighted / total, 1) if total > 0 else 0.0
    return score, counts


def get_status_display(proof_status: str) -> tuple:
    key = proof_status.lower() if proof_status else None
    cfg = STATUS_CONFIG.get(key, ("❓ Unknown", "gray", "#8b949e", "#8b949e"))
    return cfg[0], cfg[1], cfg[2]


def get_map_color(proof_status: str) -> str:
    key = proof_status.lower() if proof_status else None
    return STATUS_CONFIG.get(key, ("", "", "", "#8b949e"))[3]


def badge_html(color_name: str, label: str) -> str:
    cls = {"green": "badge-green", "orange": "badge-orange", "red": "badge-red"}.get(color_name, "badge-gray")
    return f'<span class="badge {cls}">{label}</span>'


def kpi_tile(icon_name: str, bg: str, icon_color: str, value: int, label: str, value_color: str) -> str:
    ico = icon_box(icon_name, bg=bg, color=icon_color, size=22, box=48)
    return f"""
    <div class="kpi-tile">
        {ico}
        <div class="kpi-value" style="color:{value_color}">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """


def main() -> None:
    st.set_page_config(page_title="Ward Map | Pramaan", layout="wide", page_icon="🛡️")
    render_topnav("Ward Map")

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #020b14 !important;
        color: #e2e8f0 !important;
    }

    .block-container { padding-top: 0.5rem !important; }

    /* ── Keyframe animations ── */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.94); }
        to   { opacity: 1; transform: scale(1); }
    }
    @keyframes shimmer {
        0%   { background-position: -400px 0; }
        100% { background-position: 400px 0; }
    }
    @keyframes pulse-ring {
        0%, 100% { box-shadow: 0 0 0 0 rgba(249,115,22,0.3); }
        50%       { box-shadow: 0 0 0 6px rgba(249,115,22,0); }
    }
    @keyframes barFill {
        from { width: 0%; }
    }

    /* ── top bar ── */
    .top-bar {
        background: linear-gradient(135deg, #0d1a2e 0%, #0c2461 60%, #0d1a2e 100%);
        border-bottom: 1px solid rgba(249,115,22,0.28);
        border-radius: 14px;
        padding: 18px 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.2rem;
        animation: fadeInDown 0.4s ease both;
    }
    .top-bar-left  { display:flex; align-items:center; gap:14px; }
    .top-bar-logo  { display:flex; align-items:center; justify-content:center; flex-shrink:0; }
    .top-bar-title {
        font-family:'Outfit',sans-serif; font-size:1.6em; font-weight:800;
        background:linear-gradient(90deg,#f97316,#38bdf8);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        margin:0; line-height:1.1;
    }
    .top-bar-sub   { font-size:0.75em; color:#475569; margin:2px 0 0 0; }
    .top-bar-badge {
        background:rgba(249,115,22,0.12); border:1px solid rgba(249,115,22,0.3);
        border-radius:20px; padding:5px 16px; font-size:0.75em;
        color:#f97316; font-weight:600; letter-spacing:0.04em;
        animation: pulse-ring 2.5s infinite;
    }

    /* ── breadcrumb ── */
    .breadcrumb {
        background:rgba(30,41,59,0.6); border:1px solid rgba(71,85,105,0.4);
        border-radius:8px; padding:6px 14px; font-size:0.78em;
        color:#64748b; display:inline-block; margin-bottom:1rem;
        animation: fadeInDown 0.4s 0.1s ease both;
    }
    .breadcrumb strong { color:#e2e8f0; }

    /* ── section panel ── */
    .section-panel {
        background:rgba(13,26,46,0.6); border:1px solid rgba(71,85,105,0.35);
        border-radius:16px; padding:22px 24px; margin-bottom:1.2rem;
        animation: fadeInUp 0.5s 0.15s ease both;
    }
    .section-panel-header {
        font-family:'Outfit',sans-serif; font-size:0.7em; font-weight:700;
        color:#475569; text-transform:uppercase; letter-spacing:0.1em;
        margin-bottom:16px; padding-bottom:10px;
        border-bottom:1px solid rgba(71,85,105,0.3);
    }

    /* ── glass card ── */
    .glass-card {
        background:rgba(15,23,42,0.85); border:1px solid rgba(71,85,105,0.5);
        border-radius:16px; padding:22px 24px;
        backdrop-filter:blur(12px); margin-bottom:1rem;
        animation: fadeInUp 0.5s ease both;
    }
    .glass-card-green  { border-left:4px solid #22c55e; }
    .glass-card-amber  { border-left:4px solid #f59e0b; }
    .glass-card-red    { border-left:4px solid #ef4444; }
    .glass-card-indigo { border-left:4px solid #f97316; }

    /* ── KPI tiles ── */
    .kpi-tile {
        background:rgba(15,23,42,0.9); border-radius:14px;
        padding:20px 14px;
        border:1px solid rgba(71,85,105,0.45);
        display:flex; flex-direction:column; align-items:center; justify-content:center;
        text-align:center;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        animation: scaleIn 0.4s ease both;
        cursor: default;
    }
    .kpi-tile:hover {
        transform: translateY(-3px);
        border-color: rgba(249,115,22,0.4);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .kpi-icon {
        width:48px; height:48px;
        display:flex; align-items:center; justify-content:center;
        border-radius:12px; margin-bottom:10px;
    }
    .kpi-value {
        font-size:2.2em; font-weight:800; font-family:'Outfit',sans-serif;
        line-height:1; margin-bottom:5px;
    }
    .kpi-label {
        font-size:0.65em; color:#64748b;
        text-transform:uppercase; letter-spacing:0.08em; font-weight:600;
    }

    /* ── section label (H2-level) ── */
    .sec-label {
        font-family:'Outfit',sans-serif; font-size:1em; font-weight:700;
        color:#94a3b8; margin:0 0 14px 0; letter-spacing:0.04em;
        text-transform:uppercase;
        display:flex; align-items:center; gap:8px;
    }
    .sec-label::after {
        content:''; flex:1; height:1px;
        background:rgba(71,85,105,0.4); margin-left:8px;
    }

    /* ── score band ── */
    .band-green { background:rgba(34,197,94,0.07);  border-left:4px solid #22c55e; color:#4ade80; }
    .band-amber { background:rgba(234,179,8,0.07);  border-left:4px solid #eab308; color:#facc15; }
    .band-red   { background:rgba(239,68,68,0.07);  border-left:4px solid #ef4444; color:#f87171; }

    /* ── badge ── */
    .badge { display:inline-block; border-radius:20px; padding:3px 11px;
             font-size:0.75em; font-weight:600; white-space:nowrap; }
    .badge-green  { background:rgba(34,197,94,0.12);  color:#4ade80; border:1px solid rgba(34,197,94,0.35); }
    .badge-orange { background:rgba(234,179,8,0.12);  color:#facc15; border:1px solid rgba(234,179,8,0.35); }
    .badge-red    { background:rgba(239,68,68,0.12);  color:#f87171; border:1px solid rgba(239,68,68,0.35); }
    .badge-gray   { background:rgba(100,116,139,0.12); color:#94a3b8; border:1px solid rgba(100,116,139,0.35); }

    /* ── asset row ── */
    .asset-row {
        background:rgba(15,23,42,0.65); border:1px solid rgba(51,65,85,0.5);
        border-radius:10px; padding:13px 18px; margin-bottom:7px;
        transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
    }
    .asset-row:hover {
        background:rgba(30,41,59,0.85);
        border-color:rgba(249,115,22,0.25);
        transform: translateX(3px);
    }
    .asset-name { font-weight:600; font-size:0.95em; color:#f1f5f9; }
    .asset-meta { font-size:0.74em; color:#64748b; margin-top:3px; }

    /* ── tabs — thicker active indicator ── */
    button[data-baseweb="tab"] {
        font-size:14px !important; font-weight:600 !important;
        padding:10px 20px !important; color:#475569 !important;
        transition: color 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover { color:#94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color:#f97316 !important;
        border-bottom:3px solid #f97316 !important;
    }

    /* ── sidebar ── */
    [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#0d1a2e 0%,#020b14 100%);
        border-right:1px solid rgba(71,85,105,0.35);
    }
    [data-testid="stSidebarNav"] a span { color:#94a3b8 !important; font-size:0.88em !important; font-weight:500 !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] span { color:#f97316 !important; font-weight:700 !important; }
    [data-testid="stSidebarNav"] a svg { color:#64748b !important; fill:#64748b !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] svg { color:#f97316 !important; fill:#f97316 !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] { background:rgba(249,115,22,0.08) !important; border-radius:8px !important; border-left:3px solid #f97316 !important; }
    [data-testid="stSidebarNav"] a { transition: background 0.15s ease !important; border-radius:6px !important; }
    [data-testid="stSidebarNav"] a:hover { background:rgba(71,85,105,0.12) !important; }

    /* ── metric override ── */
    [data-testid="stMetric"] {
        background:rgba(15,23,42,0.9); border-radius:12px;
        padding:16px; border:1px solid rgba(71,85,105,0.45);
        transition: box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.25); }
    [data-testid="stMetricValue"] { font-size:1.8em !important; font-family:'Outfit',sans-serif; }
    [data-testid="stMetricLabel"] { font-size:0.72em !important; font-weight:600 !important;
                                    text-transform:uppercase; letter-spacing:0.06em; color:#64748b !important; }

    /* ── animated progress bar ── */
    .anim-bar {
        transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
        animation: barFill 1.2s cubic-bezier(0.4, 0, 0.2, 1) both;
    }

    /* ── gap card hover ── */
    .gap-card {
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .gap-card:hover {
        box-shadow: 0 8px 28px rgba(0,0,0,0.35);
        transform: translateY(-2px);
    }

    /* ── empty state ── */
    .empty-state {
        text-align:center; padding:52px 24px;
        background:rgba(13,26,46,0.5); border:1px dashed rgba(71,85,105,0.5);
        border-radius:16px; animation: fadeInUp 0.5s ease both;
    }
    .empty-state-icon { margin-bottom:16px; opacity:0.4; }
    .empty-state-title {
        font-family:'Outfit',sans-serif; font-size:1.1em; font-weight:700;
        color:#475569; margin-bottom:8px;
    }
    .empty-state-body { font-size:0.83em; color:#334155; line-height:1.6; }

    hr { border-color:rgba(71,85,105,0.35) !important; }
    [data-testid="stToolbar"] { display:none !important; }
    [data-testid="stDeployButton"] { display:none !important; }
    #MainMenu { visibility:hidden !important; }
    * { scrollbar-width:thin; scrollbar-color:#f97316 #1a1f2e; }
    *::-webkit-scrollbar { width:6px; height:6px; }
    *::-webkit-scrollbar-track { background:#1a1f2e; }
    *::-webkit-scrollbar-thumb { background:#f97316; border-radius:3px; }

    /* ── map legend ── */
    .map-legend {
        display:flex; gap:22px; margin-bottom:12px;
        background:rgba(255,255,255,0.05); border-radius:8px;
        padding:10px 16px; border:1px solid rgba(71,85,105,0.35);
        font-size:0.82em; color:#cbd5e1;
    }

    /* ── geo selector row ── */
    [data-testid="stSelectbox"] label {
        font-size:0.72em !important; font-weight:700 !important;
        text-transform:uppercase !important; letter-spacing:0.06em !important;
        color:#64748b !important;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        # ── Top bar ────────────────────────────────────────────────────────────
        logo_svg = icon_box("map", bg="rgba(249,115,22,0.15)", color="#f97316", size=24, box=52)
        st.markdown(f"""
        <div class="top-bar">
            <div class="top-bar-left">
                <div class="top-bar-logo">{logo_svg}</div>
                <div>
                    <div class="top-bar-title">Ward Delivery Map</div>
                    <div class="top-bar-sub">Track field proof for assets and schemes, ward by ward.</div>
                </div>
            </div>
            <span class="top-bar-badge">{icon("shield-check", "#f97316", 14)} PRAMAAN LIVE</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Inline ward filter (Ward Map only) ────────────────────────────────
        import datetime
        init_session()
        ss = st.session_state

        fc1, fc2, fc3, fc4, fc5 = st.columns([1.5, 1.5, 2.5, 2, 0.5], vertical_alignment="bottom")
        with fc1:
            st.caption("STATE / UT")
            _state_idx = INDIAN_STATES.index(ss.get("selected_state", DEFAULT_STATE)) if ss.get("selected_state", DEFAULT_STATE) in INDIAN_STATES else 0
            state = st.selectbox("w_state", INDIAN_STATES, index=_state_idx, label_visibility="collapsed", key="sel_state")
            ss["selected_state"] = state
        with fc2:
            st.caption("CITY / ULB")
            _city_idx = DELHI_ULBS.index(ss.get("selected_city", DEFAULT_CITY)) if ss.get("selected_city", DEFAULT_CITY) in DELHI_ULBS else 0
            city = st.selectbox("w_city", DELHI_ULBS, index=_city_idx, label_visibility="collapsed", key="sel_city")
            ss["selected_city"] = city
        with fc3:
            st.caption("ZONE")
            _zone_list = DELHI_ZONES.get(city, [DEFAULT_ZONE])
            _cur_zone  = ss.get("selected_zone", DEFAULT_ZONE) if ss.get("selected_zone", DEFAULT_ZONE) in _zone_list else _zone_list[0]
            zone = st.selectbox("w_zone", _zone_list, index=_zone_list.index(_cur_zone), label_visibility="collapsed", key="sel_zone")
            ss["selected_zone"] = zone
        with fc4:
            st.caption("WARD")
            _ward_map   = ZONE_WARDS.get(zone, {DEFAULT_WARD: "REG_W45"})
            _ward_names = list(_ward_map.keys())
            _cur_ward   = ss.get("selected_ward", DEFAULT_WARD) if ss.get("selected_ward", DEFAULT_WARD) in _ward_names else _ward_names[0]
            ward_sel = st.selectbox("w_ward", _ward_names, index=_ward_names.index(_cur_ward), label_visibility="collapsed", key="sel_ward")
            ss["selected_ward"] = ward_sel
        with fc5:
            if st.button("↺", key="filter_refresh", use_container_width=True, help="Reset filters to India level."):
                ss["last_refresh"] = datetime.datetime.now().strftime("%H:%M:%S")
                st.cache_data.clear()
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #1e293b;margin:4px 0 10px 0;'>", unsafe_allow_html=True)

        ward_id   = get_ward_id()
        ward_name = get_ward_name()

        # ── Breadcrumb ─────────────────────────────────────────────────────────
        pin_icon = icon("map-pin", "#64748b", 12)
        st.markdown(
            f'<div class="breadcrumb" style="font-size:0.78em;">{pin_icon} {get_breadcrumb()}</div>',
            unsafe_allow_html=True,
        )

        # ── Load data ──────────────────────────────────────────────────────────
        score_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/score", timeout=10)
        if score_resp.status_code != 200:
            st.error(f"Backend error {score_resp.status_code} — could not load ward score.")
            st.stop()

        sd         = score_resp.json()
        total      = sd.get("total_assets", 0)
        breakdown  = sd.get("asset_breakdown", [])
        scheme_bk  = sd.get("scheme_breakdown", {})

        # Deduplicate by asset_id (keep first occurrence)
        _seen = set()
        breakdown = [a for a in breakdown if not (_seen.add(a["asset_id"]) if a["asset_id"] not in _seen else True)]

        breakdown  = apply_override(breakdown)
        score, counts = compute_score(breakdown)

        # ── Score Hero — unified SVG gauge + KPI panel ─────────────────────────
        needle_color = "#22c55e" if score >= 70 else ("#eab308" if score >= 35 else "#ef4444")
        if score >= 70:
            severity_label  = "Good Standing"
            severity_color  = "#22c55e"
            severity_border = "rgba(34,197,94,0.4)"
            band_text       = "Strong delivery proof — most assets verified."
            cta_text        = ""
        elif score >= 35:
            severity_label  = "Warning"
            severity_color  = "#f59e0b"
            severity_border = "rgba(245,158,11,0.4)"
            band_text       = "Partial coverage — some assets lack evidence."
            cta_text        = "Upload field photos to improve score."
        else:
            severity_label  = "Critical"
            severity_color  = "#ef4444"
            severity_border = "rgba(239,68,68,0.4)"
            band_text       = "Low proof coverage — significant gaps detected."
            cta_text        = "Immediate evidence submission required."

        # ── SVG arc math ──────────────────────────────────────────────────────
        CX, CY, R = 130, 120, 90   # centre, radius of gauge arc
        STROKE = 18                 # track thickness

        def _arc_pt(pct: float) -> tuple[float, float]:
            """Map 0–100 score to angle. Arc goes 210° → 330° (left to right, bottom gap)."""
            angle = math.radians(210 + pct * 1.2)   # 0→210°, 100→330°
            return CX + R * math.cos(angle), CY + R * math.sin(angle)

        # Track zones: 0-35 red, 35-70 amber, 70-100 green
        def _zone_arc(start_pct: float, end_pct: float, color: str, opacity: float) -> str:
            sx, sy = _arc_pt(start_pct)
            ex, ey = _arc_pt(end_pct)
            span_deg = (end_pct - start_pct) * 1.2
            large = 1 if span_deg > 180 else 0
            return (f'<path d="M {sx:.1f} {sy:.1f} A {R} {R} 0 {large} 1 {ex:.1f} {ey:.1f}" '
                    f'fill="none" stroke="{color}" stroke-width="{STROKE}" '
                    f'stroke-opacity="{opacity}" stroke-linecap="round"/>')

        # Filled arc for score value
        def _score_arc(pct: float, color: str) -> str:
            if pct <= 0:
                return ""
            sx, sy = _arc_pt(0)
            ex, ey = _arc_pt(min(pct, 99.9))
            span_deg = pct * 1.2
            large = 1 if span_deg > 180 else 0
            return (f'<path d="M {sx:.1f} {sy:.1f} A {R} {R} 0 {large} 1 {ex:.1f} {ey:.1f}" '
                    f'fill="none" stroke="{color}" stroke-width="{STROKE}" '
                    f'stroke-linecap="round"/>')

        # Tick labels at 0, 25, 50, 75, 100
        def _tick_labels() -> str:
            labels = [(0, "0"), (25, "25"), (50, "50"), (75, "75"), (100, "100")]
            out = []
            for pct, lbl in labels:
                tx, ty = _arc_pt(pct)
                # push label outward from arc centre
                angle = math.radians(210 + pct * 1.2)
                ox = (R + 20) * math.cos(angle)
                oy = (R + 20) * math.sin(angle)
                out.append(
                    f'<text x="{CX + ox:.1f}" y="{CY + oy:.1f}" '
                    f'fill="#64748b" font-size="11" font-family="Inter,sans-serif" text-anchor="middle" dominant-baseline="middle">{lbl}</text>'
                )
            return "\n".join(out)

        track_red   = _zone_arc(0,  35,  "#ef4444", 0.18)
        track_amber = _zone_arc(35, 70,  "#f59e0b", 0.15)
        track_green = _zone_arc(70, 100, "#22c55e", 0.15)
        fill_arc    = _score_arc(score, needle_color)

        # Needle dot at arc tip
        _ndx, _ndy = _arc_pt(min(score, 99.9))
        needle_dot  = (f'<circle cx="{_ndx:.1f}" cy="{_ndy:.1f}" r="11" '
                       f'fill="#ffffff" stroke="{needle_color}" stroke-width="3" '
                       f'filter="drop-shadow(0 0 5px {needle_color})"/>'
                       if score > 0 else "")
        tick_labels = _tick_labels()
        cta_html    = ""
        news_html   = (f'<div style="font-size:0.72em;color:#64748b;margin-top:6px;">'
                       f'{counts["news_only"]} assets: news coverage only</div>'
                       if counts.get("news_only", 0) > 0 else "")

        components.html(f"""
        <!DOCTYPE html><html><head>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800&family=Inter:wght@400;500;600&display=swap');
          * {{ box-sizing:border-box; margin:0; padding:0; text-decoration:none !important; }}
          body {{ background:transparent; font-family:'Inter',sans-serif; }}

          .panel {{
            background: linear-gradient(135deg,rgba(13,26,46,0.97) 0%,rgba(10,18,38,0.97) 100%);
            border: 1px solid rgba(71,85,105,0.4);
            border-radius: 16px;
            padding: 20px 24px;
            display: flex;
            align-items: flex-start;
            gap: 28px;
          }}
          .gauge-side {{
            flex: 0 0 260px;
            text-align: center;
            padding-top: 4px;
          }}
          .score-num {{
            font-family:'Outfit',sans-serif;
            font-size:2.8em; font-weight:800;
            color:{needle_color};
            line-height:1;
          }}
          .score-unit {{ font-size:0.75em; font-weight:800; color:{needle_color}; vertical-align:super; }}
          .score-lbl {{ font-size:0.75em; color:#64748b; margin-top:4px; }}
          .ward-lbl  {{ font-size:0.65em; color:#475569; margin-top:2px; }}
          .severity-badge {{
            display:inline-block;
            background:{severity_color};
            color:#020b14;
            font-size:0.65em; font-weight:800;
            border-radius:20px; padding:3px 12px;
            letter-spacing:0.06em; text-transform:uppercase;
            margin: 10px 0 6px 0;
          }}
          .band-text {{ font-size:0.8em; color:#cbd5e1; }}
          .cta-text  {{ margin-top:5px; font-size:0.73em; color:{severity_color}; opacity:0.9; }}

          /* KPI grid */
          .kpi-side {{
            flex: 1;
            min-width: 0;
          }}
          .kpi-header {{
            font-size:0.62em; color:#64748b; font-weight:700;
            text-transform:uppercase; letter-spacing:0.08em;
            margin-bottom:10px;
          }}
          .kpi-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
          }}
          .kpi-card {{
            background:rgba(15,23,42,0.7);
            border:1px solid rgba(71,85,105,0.3);
            border-radius:10px;
            padding:10px 12px;
            min-width: 0;
            transition: border-color 0.2s ease, transform 0.15s ease;
          }}
          .kpi-card:hover {{ border-color:rgba(249,115,22,0.3); transform:translateY(-2px); }}
          .kpi-val  {{ font-family:'Outfit',sans-serif; font-size:1.7em; font-weight:800; line-height:1; }}
          .kpi-name {{ font-size:0.68em; color:#64748b; margin-top:3px; font-weight:600;
                       white-space:normal; line-height:1.3; }}
          {news_html and ".news-note { font-size:0.72em; color:#64748b; margin-top:12px; }" or ""}
        </style>
        </head><body>
        <div class="panel">

          <!-- gauge side -->
          <div class="gauge-side">
            <svg width="260" height="160" viewBox="0 0 260 160">
              {track_red}
              {track_amber}
              {track_green}
              {fill_arc}
              {needle_dot}
              {tick_labels}
              <text x="{CX}" y="{CY - 10}" fill="{needle_color}"
                    font-family="Outfit,sans-serif" font-size="36" font-weight="800"
                    text-anchor="middle" dominant-baseline="middle">{score:.1f}<tspan font-size="18">%</tspan></text>
              <text x="{CX}" y="{CY + 26}" fill="#64748b"
                    font-family="Inter,sans-serif" font-size="11"
                    text-anchor="middle">Delivery Score</text>
            </svg>
            <div style="display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:4px;">
              <div class="severity-badge">{"⚠ " if severity_label == "Critical" else ""}{severity_label}</div>
              <div class="band-text" style="font-size:0.75em;">{band_text}</div>
            </div>
            {cta_html}
          </div>

          <!-- KPI side -->
          <div class="kpi-side">
            <div class="kpi-header">Delivery Snapshot</div>
            <div class="kpi-grid">
              <div class="kpi-card">
                <div class="kpi-val" style="color:#f97316">{total}</div>
                <div class="kpi-name">Total Assets</div>
              </div>
              <div class="kpi-card" title="Fully Verified — field proof accepted and cleared">
                <div class="kpi-val" style="color:#22c55e">{counts["fully_verified"]}</div>
                <div class="kpi-name">Fully Verified</div>
                <div style="font-size:0.6em;color:#475569;margin-top:2px;line-height:1.3;">field proof accepted &amp; cleared</div>
              </div>
              <div class="kpi-card" title="Partial Proof — some documents uploaded, pending review">
                <div class="kpi-val" style="color:#f59e0b">{counts["partially_verified"]}</div>
                <div class="kpi-name">Partial Proof</div>
                <div style="font-size:0.6em;color:#475569;margin-top:2px;line-height:1.3;">docs uploaded, pending review</div>
              </div>
              <div class="kpi-card" title="Unverified — no accepted proof uploaded yet">
                <div class="kpi-val" style="color:#ef4444">{counts["unverified"]}</div>
                <div class="kpi-name">Unverified</div>
                <div style="font-size:0.6em;color:#475569;margin-top:2px;line-height:1.3;">no accepted proof uploaded yet</div>
              </div>
            </div>
            {news_html}
          </div>

        </div>
        </body></html>
        """, height=280)

        if severity_label == "Critical" and counts["unverified"] > 0:
            st.markdown(
                f"<div style='margin:-6px 0 8px 0;'>"
                f"<span style='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);"
                f"border-radius:8px;padding:6px 14px;font-size:0.82em;color:#ef4444;font-weight:700;"
                f"display:inline-block;'>View {counts['unverified']} unverified assets ↓</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Pre-fetch gaps (needed for accurate tab label) ────────────────────
        try:
            _gaps_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/gaps", timeout=10)
            gaps_data  = _gaps_resp.json().get("gaps", []) if _gaps_resp.status_code == 200 else []
        except Exception:
            gaps_data = []
        n_actual_gaps = sum(1 for g in gaps_data if g.get("gap_type") not in ("complete", "no_assets"))

        # Per-scheme proof breakdown (for stacked bar)
        scheme_proof: dict = {}
        for asset in breakdown:
            sname = asset.get("scheme_name") or "Unknown"
            ps    = asset.get("proof_status", "unverified")
            if sname not in scheme_proof:
                scheme_proof[sname] = {"fully_verified": 0, "partially_verified": 0, "unverified": 0}
            bucket = ps if ps in ("fully_verified", "partially_verified") else "unverified"
            scheme_proof[sname][bucket] += 1

        # ── Tabs ──────────────────────────────────────────────────────────────
        n_schemes = len(scheme_bk)
        tab_map, tab_assets, tab_scheme, tab_gaps = st.tabs([
            "Map View",
            f"Assets & Proof ({len(breakdown)})",
            f"Scheme Breakdown ({n_schemes})",
            f"Delivery Gaps ({n_actual_gaps})",
        ])

        # ── Scheme Breakdown ───────────────────────────────────────────────────
        with tab_scheme:
            st.markdown(f"<p class='sec-label'>{icon('banknote', '#94a3b8', 15)} Scheme-wise Asset Distribution</p>", unsafe_allow_html=True)
            if not scheme_bk:
                empty_ico = icon_box("banknote", bg="rgba(71,85,105,0.1)", color="#475569", size=28, box=56)
                st.markdown(f"""
                <div class="empty-state">
                    <div class="empty-state-icon">{empty_ico}</div>
                    <div class="empty-state-title">No scheme data available</div>
                    <div class="empty-state-body">Scheme-asset linkages have not been mapped for this ward yet.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                sorted_schemes = sorted(scheme_bk.items(), key=lambda x: -x[1])
                n_cols = min(len(sorted_schemes), 4)
                cols = st.columns(n_cols)
                for i, (sname, cnt) in enumerate(sorted_schemes):
                    short = SCHEME_SHORT_NAMES.get(sname, sname)
                    with cols[i % n_cols]:
                        st.metric(label=short, value=cnt, help=sname)

                # Stacked bar — verified / partial / unverified per scheme
                if len(sorted_schemes) >= 1:
                    names = [SCHEME_SHORT_NAMES.get(s, s).replace("\n", " ") for s, _ in sorted_schemes]
                    fv = [scheme_proof.get(s, {}).get("fully_verified",    0) for s, _ in sorted_schemes]
                    pv = [scheme_proof.get(s, {}).get("partially_verified", 0) for s, _ in sorted_schemes]
                    uv = [scheme_proof.get(s, {}).get("unverified",         0) for s, _ in sorted_schemes]
                    bar = go.Figure(data=[
                        go.Bar(name="Fully Verified",    x=names, y=fv, marker_color="#22c55e",
                               text=fv, textposition="inside", insidetextanchor="middle"),
                        go.Bar(name="Partial Proof",     x=names, y=pv, marker_color="#f59e0b",
                               text=pv, textposition="inside", insidetextanchor="middle"),
                        go.Bar(name="Unverified",        x=names, y=uv, marker_color="#ef4444",
                               text=uv, textposition="inside", insidetextanchor="middle"),
                    ])
                    bar.update_layout(
                        barmode="stack",
                        height=300, margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font={"color": "#94a3b8", "size": 12},
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
                        xaxis=dict(showgrid=False, color="#475569"),
                        yaxis=dict(showgrid=True, gridcolor="rgba(71,85,105,0.3)", color="#475569"),
                    )
                    st.plotly_chart(bar, use_container_width=True)

        # ── Assets & Proof ─────────────────────────────────────────────────────
        with tab_assets:
            st.markdown(f"<p class='sec-label'>{icon('layers', '#94a3b8', 15)} Assets and Proof Status</p>", unsafe_allow_html=True)
            if not breakdown:
                empty_ico = icon_box("layers", bg="rgba(71,85,105,0.1)", color="#475569", size=28, box=56)
                st.markdown(f"""
                <div class="empty-state">
                    <div class="empty-state-icon">{empty_ico}</div>
                    <div class="empty-state-title">No assets recorded yet</div>
                    <div class="empty-state-body">
                        This ward has no asset data in the knowledge graph.<br>
                        Use Live Ingestion to add governance data for this location.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Filter controls
                f1, f2 = st.columns([2, 2])
                with f1:
                    filter_status = st.selectbox(
                        "Filter by proof status",
                        ["All", "✅ Fully Verified", "⚠️ Partially Verified", "❌ Unverified", "📰 News Only"],
                        label_visibility="collapsed",
                    )
                with f2:
                    search = st.text_input("Search assets", placeholder="Type asset name...", label_visibility="collapsed")

                status_map = {
                    "✅ Fully Verified": "fully_verified",
                    "⚠️ Partially Verified": "partially_verified",
                    "❌ Unverified": "unverified",
                    "📰 News Only": "news_only",
                }

                filtered = breakdown
                if filter_status != "All":
                    key = status_map.get(filter_status, "")
                    filtered = [a for a in breakdown if a.get("proof_status", "unverified") == key]
                if search:
                    filtered = [a for a in filtered if search.lower() in a.get("name", "").lower()]

                st.caption(f"Showing {len(filtered)} of {len(breakdown)} assets")

                # Pre-compute which asset IDs are geographically outside the ward radius
                _centroid = WARD_CENTROID.get(ward_id, (28.666, 77.296))
                _outside_ids: set = set()
                for _a in breakdown:
                    try:
                        _lat = float(_a.get("lat") or 0)
                        _lng = float(_a.get("lon") or 0)
                        if _lat and _lng and _haversine_km(_centroid[0], _centroid[1], _lat, _lng) > PIN_RADIUS_KM:
                            _outside_ids.add(_a["asset_id"])
                    except (ValueError, TypeError):
                        pass

                # Header row
                h1, h2, h3, h4, h5 = st.columns([4, 2, 2, 2, 2])
                for col, label in zip([h1, h2, h3, h4, h5], ["Asset", "Type", "Scheme", "Status", ""]):
                    col.markdown(f"<span style='font-size:0.75em;color:#475569;text-transform:uppercase;letter-spacing:0.06em;'>{label}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0 8px 0;border-color:rgba(71,85,105,0.3);'/>", unsafe_allow_html=True)

                for asset in filtered:
                    ps = asset.get("proof_status", "unverified")
                    label, color_name, _ = get_status_display(ps)
                    bdg = badge_html(color_name, label)
                    s_name = asset.get("scheme_name") or "—"
                    short = SCHEME_SHORT_NAMES.get(s_name, s_name).replace("\n", " ")
                    _is_outside = asset["asset_id"] in _outside_ids
                    _outside_badge = (
                        " <span style='font-size:0.65em;background:rgba(245,158,11,0.12);"
                        "border:1px solid rgba(245,158,11,0.35);border-radius:4px;"
                        "padding:1px 6px;color:#f59e0b;font-weight:600;'>⚠ Outside boundary</span>"
                        if _is_outside else ""
                    )

                    c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 2])
                    _cost = asset.get('cost') or 0
                    _cost_str = f"₹{_cost:,.0f}" if _cost else "N/A"
                    _status = (asset.get('status') or '—').replace('_', ' ').capitalize()
                    c1.markdown(f"<div class='asset-name'>{asset['name']}{_outside_badge}</div>"
                                f"<div class='asset-meta'>{_status} · {_cost_str} · <span style='color:#334155;font-family:monospace'>{asset['asset_id']}</span></div>",
                                unsafe_allow_html=True)
                    c2.write((asset.get("type") or "—").replace("_", " ").title())
                    c3.write(short)
                    c4.markdown(bdg, unsafe_allow_html=True)
                    if c5.button("View Proof Chain", key=f"chain_{asset['asset_id']}"):
                        st.session_state["selected_asset"] = asset["asset_id"]
                        st.session_state["ward_id"]        = ward_id
                        st.session_state["ward_name"]      = ward_name
                        st.switch_page("pages/02_Proof_Chain.py")

                if _outside_ids:
                    _outside_assets = [a for a in breakdown if a["asset_id"] in _outside_ids]
                    with st.expander(f"🗺 {len(_outside_ids)} asset{'s' if len(_outside_ids)>1 else ''} outside ward boundary — possible mis-tag"):
                        st.caption("These assets have coordinates outside the ward radius. They appear in the table above but are hidden from the map. Verify coordinates in assets.csv.")
                        for _oa in _outside_assets:
                            st.markdown(f"- **{_oa['name']}** `{_oa['asset_id']}` — lat: `{_oa.get('lat','?')}`, lon: `{_oa.get('lon','?')}`")

        # ── Map View ───────────────────────────────────────────────────────────
        with tab_map:
            st.markdown(f"<p class='sec-label'>{icon('map', '#94a3b8', 15)} Asset Locations — Color-coded by Proof Status</p>", unsafe_allow_html=True)
            st.markdown("""
            <div class="map-legend">
                <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#22c55e;margin-right:5px;"></span>Fully Verified</span>
                <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f59e0b;margin-right:5px;"></span>Partially Verified / News Only</span>
                <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ef4444;margin-right:5px;"></span>Unverified</span>
            </div>
            """, unsafe_allow_html=True)

            try:
                default_centroid = WARD_CENTROID.get(ward_id, (28.6692, 77.2789))
                ward_lat, ward_lng = default_centroid

                # Collect ALL assets with valid coordinates.
                # Outside-boundary assets are shown as gray pins (not hidden).
                centroid_lat, centroid_lng = WARD_CENTROID.get(ward_id, (ward_lat, ward_lng))
                points, outside_pins = [], 0
                for asset in breakdown:
                    try:
                        lat = float(asset.get("lat") or 0)
                        lng = float(asset.get("lon") or 0)
                        if not (lat and lng):
                            continue
                        dist = _haversine_km(centroid_lat, centroid_lng, lat, lng)
                        is_outside = dist > PIN_RADIUS_KM
                        if is_outside:
                            outside_pins += 1
                        points.append((lat, lng, asset, is_outside))
                    except (ValueError, TypeError):
                        pass

                if not points:
                    st.info("No coordinate data available for this ward's assets. Reseed the database with updated assets.csv to see pins.")
                elif outside_pins:
                    st.caption(f"⚠ {outside_pins} asset(s) shown as gray pins — coordinates fall outside expected ward boundary (possible data mis-tag).")

                # Center on ward boundary centroid, not asset centroid
                center_lat, center_lng = centroid_lat, centroid_lng

                m = folium.Map(
                    location=[center_lat, center_lng],
                    zoom_start=13,
                    tiles="OpenStreetMap",
                )

                # ── Ward boundary overlay ──────────────────────────────────────
                boundary = WARD_BOUNDARIES.get(ward_id)
                if boundary:
                    folium.Polygon(
                        locations=boundary,
                        color="#f97316",
                        weight=2.5,
                        dash_array="8 4",
                        fill=True,
                        fill_color="#f97316",
                        fill_opacity=0.06,
                        tooltip=f"{ward_name} — Approximate Boundary",
                    ).add_to(m)
                    # Ward label marker at centroid
                    folium.Marker(
                        location=[centroid_lat, centroid_lng],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size:11px;font-weight:700;color:#f97316;'
                                 f'white-space:nowrap;text-shadow:0 0 4px #000;">{ward_name}</div>',
                            icon_size=(200, 20),
                            icon_anchor=(100, 10),
                        ),
                    ).add_to(m)

                # ── Asset pins ─────────────────────────────────────────────────
                for lat, lng, asset, is_outside in points:
                    ps        = asset.get("proof_status", "unverified")
                    hex_color = "#94a3b8" if is_outside else get_map_color(ps)
                    label, _, _ = get_status_display(ps)
                    outside_note = " ⚠ Outside boundary" if is_outside else ""

                    folium.CircleMarker(
                        [lat, lng],
                        radius=7 if is_outside else 10,
                        color="#ffffff",
                        weight=1 if is_outside else 2,
                        fill=True,
                        fill_color=hex_color,
                        fill_opacity=0.55 if is_outside else 0.9,
                        popup=folium.Popup(
                            f"<b>{asset['name']}</b>{outside_note}<br>"
                            f"Type: {(asset.get('type') or '?').replace('_',' ').title()}<br>"
                            f"Status: {(asset.get('status') or '?').replace('_',' ').capitalize()}<br>"
                            f"Scheme: {asset.get('scheme_name','?')}<br>"
                            f"Proof: {label}"
                            + ("<br><i style='color:#f59e0b;'>Coordinates may be mis-tagged</i>" if is_outside else ""),
                            max_width=280,
                        ),
                        tooltip=f"{asset['name']} — {label}{outside_note}",
                    ).add_to(m)

                # Fit to boundary if available, else to pins
                if boundary:
                    blats = [p[0] for p in boundary]
                    blngs = [p[1] for p in boundary]
                    m.fit_bounds([[min(blats), min(blngs)], [max(blats), max(blngs)]])
                elif points:
                    lats = [p[0] for p in points]
                    lngs = [p[1] for p in points]
                    m.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])

                st_folium(m, width=None, height=440, returned_objects=[])

            except Exception as map_err:
                st.warning(f"Map error: {map_err}")

        # ── Delivery Gaps ──────────────────────────────────────────────────────
        with tab_gaps:
            st.markdown(f"<p class='sec-label'>{icon('alert-triangle', '#94a3b8', 15)} Proof Gaps — Assets Missing Evidence</p>", unsafe_allow_html=True)
            st.markdown(
                "<div style='background:rgba(56,189,248,0.06);border:1px solid rgba(56,189,248,0.2);"
                "border-radius:8px;padding:8px 14px;font-size:0.78em;color:#94a3b8;margin-bottom:12px;'>"
                "<b style='color:#38bdf8;'>ℹ Proven</b> here means the asset has at least one valid "
                "evidence URL <em>or</em> a news article mentioning it — it's a broad coverage signal. "
                "The Snapshot's <b>Fully Verified</b> count is stricter: it requires 2+ evidence items "
                "or confirmed news + field photo. Both views are correct — they measure different proof depths."
                "</div>",
                unsafe_allow_html=True,
            )
            # gaps_data already fetched above before tab definition

            if not gaps_data:
                st.success("No delivery gaps detected for this ward.")
            else:
                for gap in gaps_data:
                    if gap.get("gap_type") in ("complete", "no_assets"):
                        continue
                    _raw_name    = gap.get("scheme_name", "Unknown Scheme")
                    scheme_name  = SCHEME_SHORT_NAMES.get(_raw_name, _raw_name)
                    gap_type     = gap.get("gap_type", "unknown")
                    linked       = gap.get("linked_assets", 0)
                    proven       = gap.get("proven_assets", 0)
                    unproven     = linked - proven
                    pct          = round(100 * proven / linked, 1) if linked else 0
                    pct_unproven = round(100 - pct, 1)

                    border_color = "#f59e0b" if gap_type == "partial" else "#ef4444"
                    badge_color  = "#facc15" if gap_type == "partial" else "#f87171"
                    badge_label  = "Partial Coverage" if gap_type == "partial" else "No Evidence"

                    st.markdown(f"""
                    <div class="gap-card" style="background:rgba(15,23,42,0.85);border:1px solid rgba(71,85,105,0.45);
                                border-left:4px solid {border_color};border-radius:12px;
                                padding:18px 22px;margin-bottom:12px;">
                        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                            <div style="font-family:'Outfit',sans-serif;font-size:1em;font-weight:700;color:#f1f5f9;">
                                {scheme_name}
                            </div>
                            <span style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);
                                         border-radius:20px;padding:3px 12px;font-size:0.72em;
                                         color:{badge_color};font-weight:700;letter-spacing:0.04em;">{badge_label}</span>
                        </div>
                        <div style="display:flex;gap:28px;font-size:0.83em;margin-bottom:12px;">
                            <div><span style="color:#64748b;font-size:0.85em;text-transform:uppercase;letter-spacing:0.05em;">Total</span><br>
                                 <strong style="color:#f1f5f9;font-size:1.15em;font-family:'Outfit',sans-serif;">{linked}</strong></div>
                            <div><span style="color:#64748b;font-size:0.85em;text-transform:uppercase;letter-spacing:0.05em;">Proven</span><br>
                                 <strong style="color:#22c55e;font-size:1.15em;font-family:'Outfit',sans-serif;">{proven}</strong></div>
                            <div><span style="color:#64748b;font-size:0.85em;text-transform:uppercase;letter-spacing:0.05em;">Missing</span><br>
                                 <strong style="color:#ef4444;font-size:1.15em;font-family:'Outfit',sans-serif;">{unproven}</strong></div>
                            <div><span style="color:#64748b;font-size:0.85em;text-transform:uppercase;letter-spacing:0.05em;">Coverage</span><br>
                                 <strong style="color:#f97316;font-size:1.15em;font-family:'Outfit',sans-serif;">{pct}%</strong></div>
                        </div>
                        <div style="background:rgba(71,85,105,0.12);border-radius:8px;height:12px;overflow:hidden;display:flex;">
                            <div class="anim-bar" style="background:linear-gradient(90deg,#22c55e,#4ade80);width:{pct}%;height:100%;"></div>
                            <div class="anim-bar" style="background:linear-gradient(90deg,#ef4444,#f87171);width:{pct_unproven}%;height:100%;"></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.68em;margin-top:5px;">
                            <span style="color:#4ade80;font-weight:600;">{proven} proven ({pct}%)</span>
                            <span style="color:#f87171;font-weight:600;">{unproven} missing ({pct_unproven}%)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                action_icon = icon("alert-triangle", "#f59e0b", 15)
                st.markdown(f"""
                <div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.25);
                            border-left:4px solid #f59e0b;border-radius:10px;
                            padding:14px 18px;margin-top:8px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        {action_icon}
                        <strong style="color:#f1f5f9;font-size:0.9em;">Action Required</strong>
                    </div>
                    <div style="font-size:0.83em;color:#94a3b8;line-height:1.5;">
                        Submit geo-tagged field photos via Live Ingestion to upgrade unverified assets.
                        Each photo auto-creates an Evidence node and raises the ward delivery score.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.page_link("pages/03_Live_Ingestion.py", label="Upload Evidence", icon=":material/upload:")

    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend offline — start the FastAPI server on port 8000.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
