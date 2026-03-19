"""
Shared session-state helpers for PRAMAAN.
Every page calls init_session() at the top of main() to ensure defaults exist.
"""
import streamlit as st
from utils.geo_selector import ZONE_WARDS

DEFAULT_STATE = "Delhi (NCT)"
DEFAULT_CITY  = "MCD (Municipal Corporation of Delhi)"
DEFAULT_ZONE  = "Shahdara North Zone"
DEFAULT_WARD  = "DMC Ward No - 45"


def init_session() -> None:
    """Initialise session state with default ward context (idempotent)."""
    ss = st.session_state
    ss.setdefault("selected_state", DEFAULT_STATE)
    ss.setdefault("selected_city",  DEFAULT_CITY)
    ss.setdefault("selected_zone",  DEFAULT_ZONE)
    ss.setdefault("selected_ward",  DEFAULT_WARD)


def get_ward_id() -> str:
    """Return the backend ward_region_id for the currently selected ward."""
    zone      = st.session_state.get("selected_zone", DEFAULT_ZONE)
    ward_name = st.session_state.get("selected_ward", DEFAULT_WARD)
    ward_map  = ZONE_WARDS.get(zone, {DEFAULT_WARD: "REG_W45"})
    return ward_map.get(ward_name, "REG_W45")


def get_ward_name() -> str:
    return st.session_state.get("selected_ward", DEFAULT_WARD)


def get_breadcrumb() -> str:
    ss = st.session_state
    return (
        f"India \u203a "
        f"{ss.get('selected_state', DEFAULT_STATE)} \u203a "
        f"{ss.get('selected_city',  DEFAULT_CITY)} \u203a "
        f"{ss.get('selected_zone',  DEFAULT_ZONE)} \u203a "
        f"{ss.get('selected_ward',  DEFAULT_WARD)}"
    )
