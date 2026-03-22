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
def _fetch_regions(type: str = None, parent_id: str = None) -> list[dict]:
    """Fetch regions from API with optional type/parent_id filters."""
    try:
        params = {}
        if type:      params["type"]      = type
        if parent_id: params["parent_id"] = parent_id
        resp = requests.get(f"{BASE_URL}/regions/", params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def _build_hierarchy(regions: list[dict]) -> dict:
    """
    Build cascading dicts from flat region list.
    Handles state → city → zone → ward hierarchy.
    Returns:
      states    : list of state names
      districts : {state_name: [city_name, ...]}  (city level)
      wards     : {zone_or_city_name: {ward_name: ward_id}}
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

        elif rtype in ("city", "district", "zone"):
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

    # ── Fetch states ──────────────────────────────────────────
    state_regions = _fetch_regions(type="state")
    if not state_regions:
        target.warning("Could not load regions from API — backend may be offline.")
        return {"state": DEFAULT_STATE, "district": DEFAULT_CITY,
                "ward_name": DEFAULT_WARD, "ward_id": DEFAULT_WARD_ID, "is_demo_ward": False}

    state_map = {r["name"]: r["region_id"] for r in state_regions}
    states    = sorted(state_map.keys())

    def_state = ss.get("state", DEFAULT_STATE)
    if def_state not in states:
        def_state = states[0] if states else DEFAULT_STATE

    state     = target.selectbox("State / UT", states, index=states.index(def_state), key="sel_state_geo")
    state_id  = state_map.get(state, "")

    # ── Fetch cities for selected state ───────────────────────
    city_regions = _fetch_regions(type="city", parent_id=state_id) if state_id else []
    city_map     = {r["name"]: r["region_id"] for r in city_regions}
    city_list    = sorted(city_map.keys())
    if not city_list:
        city_list = [DEFAULT_CITY]
        city_map  = {DEFAULT_CITY: ""}

    def_city = ss.get("city", DEFAULT_CITY)
    if def_city not in city_list:
        def_city = city_list[0]

    city    = target.selectbox("City / ULB", city_list, index=city_list.index(def_city), key="sel_city_geo")
    city_id = city_map.get(city, "")

    # ── Fetch zones for selected city ─────────────────────────
    zone_regions = _fetch_regions(type="zone", parent_id=city_id) if city_id else []
    zone_map     = {r["name"]: r["region_id"] for r in zone_regions}
    zone_list    = sorted(zone_map.keys())
    has_zones    = bool(zone_list)
    if not zone_list:
        zone_list = [DEFAULT_ZONE]
        zone_map  = {DEFAULT_ZONE: city_id}  # fallback: use city as parent for wards

    def_zone = ss.get("zone", DEFAULT_ZONE)
    if def_zone not in zone_list:
        def_zone = zone_list[0]

    zone    = target.selectbox("Zone", zone_list, index=zone_list.index(def_zone), key="sel_zone_geo")
    zone_id = zone_map.get(zone, city_id)

    # ── Fetch wards for selected zone (or city if no zones) ───
    ward_parent_id = zone_id if has_zones else city_id
    ward_regions   = _fetch_regions(type="ward", parent_id=ward_parent_id) if ward_parent_id else []
    ward_map       = {r["name"]: r["region_id"] for r in ward_regions}
    ward_names     = sorted(ward_map.keys())
    if not ward_names:
        ward_names = [DEFAULT_WARD]
        ward_map   = {DEFAULT_WARD: DEFAULT_WARD_ID}

    def_ward = ss.get("ward_name", DEFAULT_WARD)
    if def_ward not in ward_names:
        def_ward = ward_names[0]

    ward_name = target.selectbox("Ward", ward_names, index=ward_names.index(def_ward), key="sel_ward_geo")
    ward_id   = ward_map[ward_name]

    # Update module-level lists for backward compat
    global INDIAN_STATES, DELHI_ULBS, DELHI_ZONES, ZONE_WARDS
    INDIAN_STATES = states
    DELHI_ULBS    = city_list
    DELHI_ZONES   = {city: zone_list}
    ZONE_WARDS    = {zone: ward_map}

    # ── Persist ───────────────────────────────────────────────
    ss["state"]        = state
    ss["city"]         = city
    ss["zone"]         = zone
    ss["ward_id"]      = ward_id
    ss["ward_name"]    = ward_name
    ss["is_demo_ward"] = False
    ss["country"]      = "India"

    return {
        "state": state, "city": city, "zone": zone,
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
