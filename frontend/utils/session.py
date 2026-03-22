"""
Shared session-state helpers for PRAMAAN.
Every page calls init_session() at the top of main() to ensure keys exist.

Design principle
----------------
ward_id comes from the BACKEND (via Ward Map selectors or geo_selector).
The DEFAULT_* constants are EMERGENCY OFFLINE FALLBACKS only — they are
never the primary data source.  The priority order for get_ward_id() is:

  1. ss["ward_id"]      — set by Ward Map or geo_selector after API call ✅
  2. ZONE_WARDS lookup  — set when render_geo_selector() ran this session ✅
  3. DEFAULT_WARD_ID    — only if backend is offline and no selection ever made ⚠️
"""
import streamlit as st
from utils.geo_selector import ZONE_WARDS
from utils.constants import (
    DEFAULT_STATE,
    DEFAULT_CITY,
    DEFAULT_ZONE,
    DEFAULT_WARD,
    DEFAULT_WARD_ID,
    DEFAULT_STATE_ID,
)


def init_session() -> None:
    """
    Initialise session state keys so pages don't crash before the user
    has made any selection.  Values here are PLACEHOLDERS — they get
    overwritten by real API data as soon as the Ward Map or geo_selector runs.
    """
    ss = st.session_state
    ss.setdefault("selected_state", "—")
    ss.setdefault("selected_city",  "—")
    ss.setdefault("selected_zone",  "—")
    ss.setdefault("selected_ward",  "—")
    ss.setdefault("ward_id",        "")
    # ward_id is intentionally NOT pre-filled here;
    # it is written by Ward Map / geo_selector from live API data.


def get_ward_id() -> str:
    """
    Return the backend region_id for the currently selected ward.

    Priority:
      1. ss["ward_id"] — already resolved from live API by the selector page
      2. ZONE_WARDS lookup — if render_geo_selector() ran during this session
      3. DEFAULT_WARD_ID — last-resort offline fallback only
    """
    ss = st.session_state

    # ── Priority 1: direct session value (written by Ward Map / geo_selector) ──
    if "ward_id" in ss and ss["ward_id"]:
        return ss["ward_id"]

    # ── Priority 2: re-derive from zone + ward_name if ZONE_WARDS is populated ─
    zone      = ss.get("selected_zone", "")
    ward_name = ss.get("selected_ward", "")
    if zone and ward_name and ZONE_WARDS:
        ward_map = ZONE_WARDS.get(zone, {})
        resolved = ward_map.get(ward_name, "")
        if resolved:
            ss["ward_id"] = resolved   # cache it for next call
            return resolved

    # ── Priority 3: offline / pre-selection fallback ───────────────────────────
    return DEFAULT_WARD_ID


def get_ward_name() -> str:
    v = st.session_state.get("sel_ward", "—")
    return v if v != "—" else DEFAULT_WARD


def get_breadcrumb() -> str:
    ss  = st.session_state
    _PH = "—"
    parts = [
        "India",
        ss.get("sel_state",    ""),
        ss.get("sel_city",     ""),
        ss.get("sel_district", ""),
        ss.get("sel_ward",     ""),
    ]
    return " \u203a ".join(p for p in parts if p and p != _PH)
