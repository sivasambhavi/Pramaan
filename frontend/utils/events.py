"""
utils/events.py — PRAMAAN single source of truth for all tracked events.

Each entry:
  event_id, name, color, domain, date, severity, lat, lon

Add a new event here → automatically appears in Intelligence Map,
Live Feed, Decision Brief, and all counters.
"""
from __future__ import annotations

# (event_id, name, color, domain, date, severity, lat, lon)
EVENTS = [
    ("EVT_WAYANAD_2024",       "Wayanad Landslide",           "#22c55e", "Climate",     "Jul 2024", "critical",  11.6854,  76.1320),
    ("EVT_CYCLONE_DANA_2024",  "Cyclone Dana – Puri",         "#22c55e", "Climate",     "Oct 2024", "critical",  19.8135,  85.8312),
    ("EVT_CHAMOLI_2021",       "Chamoli Glacier Burst",       "#22c55e", "Climate",     "Feb 2021", "critical",  30.4278,  79.7965),
    ("EVT_JOSHIMATH_2023",     "Joshimath Subsidence",        "#06b6d4", "Governance",  "Jan 2023", "high",      30.5581,  79.5647),
    ("EVT_DELHI_FLOODS_2023",  "Delhi Yamuna Floods",         "#fb7185", "Society",     "Jul 2023", "critical",  28.6139,  77.2090),
    ("EVT_COVID_WAVE2_2021",   "COVID Second Wave",           "#fb7185", "Society",     "Apr 2021", "critical",  19.0760,  72.8777),
    ("EVT_MANIPUR_2023",       "Manipur Conflict",            "#f97316", "Defense",     "May 2023", "critical",  24.8170,  93.9368),
    ("EVT_BALAKOT_2019",       "Balakot Airstrikes",          "#f97316", "Defense",     "Feb 2019", "critical",  30.3782,  76.8267),
    ("EVT_ART370_2019",        "Article 370 Abrogation",      "#06b6d4", "Governance",  "Aug 2019", "high",      34.0837,  74.7973),
    ("EVT_TATA_SEMI_2024",     "Tata Semiconductor Fab",      "#38bdf8", "Economics",   "Feb 2024", "high",      22.4707,  72.2110),
    ("EVT_IMEC_2023",          "IMEC Corridor Signing",       "#38bdf8", "Economics",   "Sep 2023", "high",      18.9220,  72.8347),
    ("EVT_G20_INDIA_2023",     "G20 New Delhi Summit",        "#a78bfa", "Geopolitics", "Sep 2023", "high",      28.6183,  77.2781),
    ("EVT_INDIA_CANADA_2023",  "India-Canada Diplomatic Row", "#a78bfa", "Geopolitics", "Sep 2023", "high",      28.6292,  77.2208),
    ("EVT_CHANDRAYAAN3_2023",  "Chandrayaan-3 Landing",       "#facc15", "Technology",  "Aug 2023", "high",      13.7199,  80.2304),
    ("EVT_ADITYAL1_2023",      "Aditya-L1 Solar Mission",     "#facc15", "Technology",  "Sep 2023", "high",      12.9716,  77.5946),
    ("EVT_RUSSIA_UKRAINE_2022","Russia–Ukraine War",          "#a78bfa", "Geopolitics", "Feb 2022", "critical",  48.3794,  31.1656),
    ("EVT_GAZA_REDSEA_2023",   "Gaza War & Red Sea Crisis",   "#a78bfa", "Geopolitics", "Oct 2023", "critical",  31.3547,  34.3088),
]

_MONTH = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
          "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def _date_key(e: tuple) -> tuple:
    parts = e[4].split()          # e.g. ["Jul", "2024"]
    return (-int(parts[1]), -_MONTH.get(parts[0], 0))

# Sort newest-first so dropdowns always show latest events at the top
EVENTS = sorted(EVENTS, key=_date_key)

# Derived helpers used across pages
N_EVENTS = len(EVENTS)

# Dict keyed by event_id → full tuple (for O(1) lookup)
EVENTS_BY_ID = {e[0]: e for e in EVENTS}

# Intelligence Map format: {event_id: (lat, lon, name, domain, color, date, severity)}
MAP_EVENTS = {
    e[0]: (e[6], e[7], e[1], e[3], e[2], e[4], e[5])
    for e in EVENTS
}

# Domain emoji bullets — used in consistent dropdown labels
DOMAIN_BULLET: dict[str, str] = {
    "Climate":     "🟢",
    "Defense":     "🟠",
    "Economics":   "🔵",
    "Society":     "🔴",
    "Governance":  "🟤",
    "Geopolitics": "🟣",
    "Technology":  "🟡",
}

_ALL_LABEL = "— All Events —"
_NONE_LABEL = "— Select an event —"


def _evt_label(e: tuple) -> str:
    """Consistent dropdown label for one event tuple."""
    bullet = DOMAIN_BULLET.get(e[3], "●")
    return f"{bullet} {e[1]}  ({e[3]} · {e[4]})"


def render_event_dropdown(
    session_key: str,
    widget_key: str,
    include_all: bool = False,
    label: str = "Event",
) -> str | None:
    """
    Render a consistent event selectbox.

    Args:
        session_key:  st.session_state key that holds the selected event_id (or None).
        widget_key:   unique key for the st.selectbox widget.
        include_all:  prepend an "— All Events —" option (for Ontology Graph).
        label:        selectbox label (hidden).

    Returns:
        Selected event_id, or None when "— All Events —" is chosen.

    Side-effect:
        Updates st.session_state[session_key] and calls st.rerun() on change.
    """
    import streamlit as st

    options: dict[str, str | None] = {}
    if include_all:
        options[_ALL_LABEL] = None
    for e in EVENTS:
        options[_evt_label(e)] = e[0]

    current_id = st.session_state.get(session_key)
    current_label = next(
        (lbl for lbl, eid in options.items() if eid == current_id),
        _ALL_LABEL if include_all else _evt_label(EVENTS[0]),
    )

    # If session_key was changed externally (e.g. map marker click), the widget
    # cache will still hold the old label — clear it so the index param wins.
    shadow_key = f"__{widget_key}_shadow"
    if st.session_state.get(shadow_key) != current_id:
        st.session_state.pop(widget_key, None)

    chosen = st.selectbox(
        label,
        list(options.keys()),
        index=list(options.keys()).index(current_label),
        label_visibility="collapsed",
        key=widget_key,
    )
    chosen_id = options[chosen]
    st.session_state[shadow_key] = chosen_id   # track last value set by this widget
    if chosen_id != current_id:
        st.session_state[session_key] = chosen_id
        st.rerun()
    return chosen_id
