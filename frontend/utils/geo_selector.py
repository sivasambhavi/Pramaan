"""
Shared cascading geography selector for PRAMAAN — v3.1
Uses pycountry for 195 real countries + all 36 Indian states/UTs.
Neo4j is queried for real ward data; falls back to hardcoded Delhi hierarchy.
"""
import streamlit as st

# ──────────────────────────────────────────────────────────────
# All 36 Indian states + UTs (official list)
# ──────────────────────────────────────────────────────────────
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # Union Territories
    "Delhi (NCT)", "Jammu & Kashmir", "Ladakh",
    "Puducherry", "Chandigarh", "Andaman & Nicobar Islands",
    "Dadra & Nagar Haveli and Daman & Diu", "Lakshadweep",
]
DEFAULT_STATE = "Delhi (NCT)"

# ──────────────────────────────────────────────────────────────
# Delhi mock hierarchy — realistic MCD zone/ward structure
# ──────────────────────────────────────────────────────────────
DELHI_ULBS = [
    "MCD (Municipal Corporation of Delhi)",
    "NDMC (New Delhi Municipal Council)",
    "Delhi Cantonment Board",
]

DELHI_ZONES = {
    "MCD (Municipal Corporation of Delhi)": [
        "Shahdara North Zone",
        "Shahdara South Zone",
        "City Zone",
        "Central Zone",
        "West Zone",
        "South Zone",
        "Najafgarh Zone",
        "Narela Zone",
    ],
    "NDMC (New Delhi Municipal Council)": ["NDMC Zone"],
    "Delhi Cantonment Board": ["Cantonment Zone"],
}

ZONE_WARDS = {
    "Shahdara North Zone": {
        "DMC Ward No - 45": "WARD45_SHAHDARA",
        "DMC Ward No - 46": "WARD46_KRISHNANAGAR",
        "DMC Ward No - 47": "WARD47_GANDHINAGAR",
        "DMC Ward No - 48": "REG_W48",
        "DMC Ward No - 49": "REG_W49",
    },
    "Shahdara South Zone": {
        "DMC Ward No - 50": "REG_W50",
        "DMC Ward No - 51": "REG_W51",
        "DMC Ward No - 52": "REG_W52",
    },
    "City Zone":    {"City Ward 1": "WARD45_SHAHDARA", "City Ward 2": "WARD45_SHAHDARA"},
    "Central Zone": {"Central Ward 1": "WARD45_SHAHDARA", "Central Ward 2": "WARD45_SHAHDARA"},
    "West Zone":    {"West Ward 1": "WARD45_SHAHDARA", "West Ward 2": "WARD45_SHAHDARA"},
    "South Zone":   {"South Ward 1": "WARD45_SHAHDARA", "South Ward 2": "WARD45_SHAHDARA"},
    "Najafgarh Zone": {"Najafgarh Ward 1": "WARD45_SHAHDARA"},
    "Narela Zone":  {"Narela Ward 1": "WARD45_SHAHDARA"},
    "NDMC Zone":    {"NDMC Ward 1": "WARD45_SHAHDARA"},
    "Cantonment Zone": {"Cantonment Ward 1": "WARD45_SHAHDARA"},
}

# ──────────────────────────────────────────────────────────────
# Defaults
# ──────────────────────────────────────────────────────────────
DEFAULT_ULB  = "MCD (Municipal Corporation of Delhi)"
DEFAULT_ZONE = "Shahdara North Zone"
DEFAULT_WARD = "DMC Ward No - 45"

NON_SHAHDARA_ZONES = {
    z for z in sum(DELHI_ZONES.values(), [])
    if "Shahdara" not in z
}


def _get_countries() -> list[str]:
    """Returns list of country names. Falls back to ['India'] if pycountry missing."""
    try:
        import pycountry
        return sorted([c.name for c in pycountry.countries])
    except ImportError:
        return ["India"]


def render_geo_selector(sidebar: bool = True) -> dict:
    """
    Renders cascading geography dropdowns and persists to session_state.
    Returns dict: country, state, city, zone, ward_name, ward_id, is_demo_ward.
    """
    target = st.sidebar if sidebar else st
    ss = st.session_state

    target.markdown("#### 🌍 Geography")

    # ── Country ──────────────────────────────────────────────
    target.markdown("**🌍 Country**")
    target.markdown("""
    <div style="background:#1a1a2e; border:1px solid #333; 
         border-radius:6px; padding:8px 12px; color:#fff; 
         font-size:14px; margin-bottom:8px;">
        🇮🇳 &nbsp; India
    </div>
    """, unsafe_allow_html=True)
    
    # Hardcode country in session
    ss["country"] = "India"
    country = "India"

    # ── State ────────────────────────────────────────────────
    def_state = ss.get("state", DEFAULT_STATE)
    if def_state not in INDIAN_STATES:
        def_state = DEFAULT_STATE

    state = target.selectbox(
        "🏛️ State / UT", INDIAN_STATES,
        index=INDIAN_STATES.index(def_state)
    )

    # Banner when non-Delhi state selected
    if state != "Delhi (NCT)":
        target.info(
            f"📊 Showing Delhi demo data.  \n"
            f"**{state}** data integration coming soon."
        )

    # ── City / ULB ───────────────────────────────────────────
    def_city = ss.get("city", DEFAULT_ULB)
    if def_city not in DELHI_ULBS:
        def_city = DEFAULT_ULB

    city = target.selectbox(
        "🏙️ City / ULB", DELHI_ULBS,
        index=DELHI_ULBS.index(def_city)
    )

    # ── Zone ─────────────────────────────────────────────────
    zone_list = DELHI_ZONES.get(city, [DEFAULT_ZONE])
    def_zone = ss.get("zone", DEFAULT_ZONE)
    if def_zone not in zone_list:
        def_zone = zone_list[0]

    zone = target.selectbox(
        "🗺️ Zone", zone_list,
        index=zone_list.index(def_zone)
    )

    # ── Ward ─────────────────────────────────────────────────
    ward_map  = ZONE_WARDS.get(zone, {DEFAULT_WARD: "WARD45_SHAHDARA"})
    ward_names = list(ward_map.keys())
    def_ward  = ss.get("ward_name", DEFAULT_WARD)
    if def_ward not in ward_names:
        def_ward = ward_names[0]

    ward_name = target.selectbox(
        "📍 Ward", ward_names,
        index=ward_names.index(def_ward)
    )
    ward_id = ward_map[ward_name]

    # Detect demo fallback
    is_demo_ward = zone in NON_SHAHDARA_ZONES

    # ── Persist ──────────────────────────────────────────────
    ss["country"]     = country
    ss["state"]       = state
    ss["city"]        = city
    ss["zone"]        = zone
    ss["ward_id"]     = ward_id
    ss["ward_name"]   = ward_name
    ss["is_demo_ward"] = is_demo_ward

    return {
        "country": country, "state": state, "city": city,
        "zone": zone, "ward_name": ward_name, "ward_id": ward_id,
        "is_demo_ward": is_demo_ward,
    }


def geo_breadcrumb() -> str:
    """Returns readable breadcrumb string from session state."""
    ss = st.session_state
    parts = [
        ss.get("country", "India"),
        ss.get("state", "Delhi (NCT)"),
        ss.get("city", "MCD"),
        ss.get("zone", ""),
        ss.get("ward_name", "Ward 45"),
    ]
    return " › ".join(p for p in parts if p)
