"""
Shared cascading geography selector for PRAMAAN — v4.0
Fetches region hierarchy dynamically from the backend API.
Falls back to empty lists with a warning if API is unavailable.
"""
import requests
import streamlit as st
from utils.constants import (
    API_BASE_URL  as BASE_URL,
    DEFAULT_STATE,
    DEFAULT_CITY,
    DEFAULT_ZONE,
    DEFAULT_WARD,
    DEFAULT_WARD_ID,
)

# Keep INDIAN_STATES for any imports that still reference it — built dynamically below
INDIAN_STATES  = []
DELHI_ULBS     = []
DELHI_ZONES    = {}
ZONE_WARDS     = {}


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_regions() -> list[dict]:
    """Fetch all regions from API. Cached for 5 minutes."""
    try:
        resp = requests.get(f"{BASE_URL}/regions/", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def _build_hierarchy(regions: list[dict]) -> dict:
    """
    Build cascading dicts from flat region list.
    Returns:
      states       : list of state names
      districts    : {state_name: [district_name, ...]}
      wards        : {district_name: {ward_name: ward_id}}
    """
    states, districts, wards = [], {}, {}

    for r in regions:
        rtype       = r.get("type", "")
        name        = r.get("name", "")
        parent_name = r.get("parent_name") or ""
        region_id   = r.get("region_id", "")

        if rtype == "state":
            if name not in states:
                states.append(name)

        elif rtype == "district":
            districts.setdefault(parent_name, [])
            if name not in districts[parent_name]:
                districts[parent_name].append(name)

        elif rtype == "ward":
            wards.setdefault(parent_name, {})
            wards[parent_name][name] = region_id

    states.sort()
    return states, districts, wards


def render_geo_selector(sidebar: bool = True) -> dict:
    """
    Renders cascading State → District → Ward dropdowns.
    Data comes from the backend API (Neo4j).
    Returns dict: state, district, ward_name, ward_id, is_demo_ward.
    """
    target = st.sidebar if sidebar else st
    ss     = st.session_state

    if sidebar:
        target.markdown("""
        <style>
        [data-testid="stSidebar"] { scrollbar-color: rgba(71,85,105,0.3) transparent !important; }
        [data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: rgba(71,85,105,0.3) !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDeployButton"] { display: none !important; }
        #MainMenu { visibility: hidden !important; }
        </style>
        <div style="padding:8px 4px 4px 4px;text-align:center;">
            <div style="font-family:'Outfit',sans-serif;font-size:1.15em;font-weight:800;
                        background:linear-gradient(90deg,#f97316,#38bdf8);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        line-height:1.1;margin-bottom:3px;">PRAMAAN</div>
            <div style="font-size:0.65em;color:#475569;letter-spacing:0.05em;
                        text-transform:uppercase;font-weight:600;">Governance Proof Engine</div>
        </div>
        <hr style="border-color:rgba(71,85,105,0.2);margin:0 0 8px 0;"/>
        """, unsafe_allow_html=True)

    # ── Fetch & build hierarchy ───────────────────────────────
    raw_regions = _fetch_regions()
    if not raw_regions:
        target.warning("Could not load regions from API — backend may be offline.")
        return {"state": DEFAULT_STATE, "district": DEFAULT_CITY,
                "ward_name": DEFAULT_WARD, "ward_id": DEFAULT_WARD_ID, "is_demo_ward": False}

    states, districts, wards = _build_hierarchy(raw_regions)

    # Update module-level lists so any code that imports them still works
    global INDIAN_STATES, DELHI_ULBS, DELHI_ZONES, ZONE_WARDS
    INDIAN_STATES = states
    DELHI_ULBS    = list(districts.keys())
    DELHI_ZONES   = districts
    ZONE_WARDS    = wards

    # ── State ─────────────────────────────────────────────────
    def_state = ss.get("state", DEFAULT_STATE)
    if def_state not in states:
        def_state = states[0] if states else DEFAULT_STATE

    state = target.selectbox("State / UT", states, index=states.index(def_state), key="sel_state_geo")

    # ── District ──────────────────────────────────────────────
    district_list = districts.get(state, [DEFAULT_CITY])
    def_district  = ss.get("city", DEFAULT_CITY)
    if def_district not in district_list:
        def_district = district_list[0] if district_list else DEFAULT_CITY

    district = target.selectbox("District", district_list,
                                index=district_list.index(def_district), key="sel_district_geo")

    # ── Ward ──────────────────────────────────────────────────
    ward_map   = wards.get(district, {DEFAULT_WARD: DEFAULT_WARD_ID})
    ward_names = list(ward_map.keys())
    def_ward   = ss.get("ward_name", DEFAULT_WARD)
    if def_ward not in ward_names:
        def_ward = ward_names[0] if ward_names else DEFAULT_WARD

    ward_name = target.selectbox("Ward", ward_names,
                                 index=ward_names.index(def_ward), key="sel_ward_geo")
    ward_id   = ward_map[ward_name]

    # ── Persist ───────────────────────────────────────────────
    ss["state"]      = state
    ss["city"]       = district
    ss["zone"]       = district   # backward compat
    ss["ward_id"]    = ward_id
    ss["ward_name"]  = ward_name
    ss["is_demo_ward"] = False
    ss["country"]    = "India"

    return {
        "state": state, "district": district,
        "ward_name": ward_name, "ward_id": ward_id,
        "is_demo_ward": False,
    }


def geo_breadcrumb() -> str:
    ss = st.session_state
    parts = [
        "India",
        ss.get("state", DEFAULT_STATE),
        ss.get("city", DEFAULT_CITY),
        ss.get("ward_name", DEFAULT_WARD),
    ]
    return " › ".join(p for p in parts if p)
