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
    # ── 2026 ──────────────────────────────────────────────────────────────────
    ("EVT_IRAN_CEASEFIRE_TALKS_2026",  "Iran War Ceasefire Talks",        "#a78bfa", "Geopolitics", "Mar 2026", "high",      35.6892,  51.3890),
    ("EVT_HORMUZ_BLOCKADE_2026",       "Strait of Hormuz Blockade",       "#38bdf8", "Economics",   "Mar 2026", "critical",  26.5667,  56.2500),
    ("EVT_IRAN_WAR_2026",              "Iran-US-Israel War",              "#a78bfa", "Geopolitics", "Feb 2026", "critical",  35.6892,  51.3890),
    # ── 2025 ──────────────────────────────────────────────────────────────────
    ("EVT_LABOUR_CODES_2025",          "Four Labour Codes Enforcement",   "#06b6d4", "Governance",  "Nov 2025", "high",      28.6139,  77.2090),
    ("EVT_INDIA_US_DEFENSE_2025",      "India-US Defence Pact",           "#f97316", "Defense",     "Oct 2025", "high",      28.6139,  77.2090),
    ("EVT_SP_UPGRADE_2025",            "S&P Sovereign Upgrade (BBB)",     "#38bdf8", "Economics",   "Aug 2025", "high",      28.6139,  77.2090),
    ("EVT_INDIA_UK_CETA_2025",         "India-UK Trade Agreement",        "#38bdf8", "Economics",   "Jul 2025", "high",      51.5074,  -0.1278),
    ("EVT_SHUKLA_ISS_2025",            "First Indian on ISS",             "#facc15", "Technology",  "Jun 2025", "high",      12.9716,  77.5946),
    ("EVT_TWELVE_DAY_WAR_2025",        "Twelve-Day War (Israel-Iran)",    "#a78bfa", "Geopolitics", "Jun 2025", "critical",  32.0853,  34.7818),
    ("EVT_INDIA_PAK_DIPLO_CRISIS_2025","India-Pakistan Diplomatic Crisis","#a78bfa", "Geopolitics", "May 2025", "high",      28.6139,  77.2090),
    ("EVT_INDIA_PAK_CEASEFIRE_2025",   "India-Pakistan Ceasefire",        "#a78bfa", "Geopolitics", "May 2025", "high",      34.0837,  74.7973),
    ("EVT_OPERATION_SINDOOR_2025",     "Operation Sindoor",               "#f97316", "Defense",     "May 2025", "critical",  33.5651,  73.0169),
    ("EVT_LOC_SKIRMISHES_2025",        "India-Pakistan LoC Skirmishes",   "#f97316", "Defense",     "Apr 2025", "high",      33.5000,  74.2000),
    ("EVT_INDUS_WATERS_CRISIS_2025",   "Indus Waters Treaty Suspension",  "#06b6d4", "Governance",  "Apr 2025", "high",      30.3753,  69.3451),
    ("EVT_PAHALGAM_2025",              "Pahalgam Terror Attack",          "#f97316", "Defense",     "Apr 2025", "critical",  34.0161,  75.3197),
    ("EVT_INDIA_EXTREME_WEATHER_2025", "India Extreme Weather 2025",      "#22c55e", "Climate",     "Jan 2025", "critical",  20.5937,  78.9629),
    ("EVT_ISRO_SPADEX_2025",           "ISRO SpaDeX Docking",             "#facc15", "Technology",  "Jan 2025", "high",      13.7199,  80.2304),
    # ── 2024 ──────────────────────────────────────────────────────────────────
    ("EVT_CYCLONE_DANA_2024",          "Cyclone Dana – Puri",             "#22c55e", "Climate",     "Oct 2024", "critical",  19.8135,  85.8312),
    ("EVT_WAYANAD_2024",               "Wayanad Landslide",               "#22c55e", "Climate",     "Jul 2024", "critical",  11.6854,  76.1320),
    ("EVT_TATA_SEMI_2024",             "Tata Semiconductor Fab",          "#38bdf8", "Economics",   "Feb 2024", "high",      22.4707,  72.2110),
    # ── 2023 ──────────────────────────────────────────────────────────────────
    ("EVT_INDIA_CANADA_2023",          "India-Canada Diplomatic Row",     "#a78bfa", "Geopolitics", "Sep 2023", "high",      28.6292,  77.2208),
    ("EVT_G20_INDIA_2023",             "G20 New Delhi Summit",            "#a78bfa", "Geopolitics", "Sep 2023", "high",      28.6183,  77.2781),
    ("EVT_IMEC_2023",                  "IMEC Corridor Signing",           "#38bdf8", "Economics",   "Sep 2023", "high",      18.9220,  72.8347),
    ("EVT_ADITYAL1_2023",              "Aditya-L1 Solar Mission",         "#facc15", "Technology",  "Sep 2023", "high",      12.9716,  77.5946),
    ("EVT_CHANDRAYAAN3_2023",          "Chandrayaan-3 Landing",           "#facc15", "Technology",  "Aug 2023", "high",      13.7199,  80.2304),
    ("EVT_DELHI_FLOODS_2023",          "Delhi Yamuna Floods",             "#fb7185", "Society",     "Jul 2023", "critical",  28.6139,  77.2090),
    ("EVT_MANIPUR_2023",               "Manipur Conflict",                "#f97316", "Defense",     "May 2023", "critical",  24.8170,  93.9368),
    ("EVT_JOSHIMATH_2023",             "Joshimath Subsidence",            "#06b6d4", "Governance",  "Jan 2023", "high",      30.5581,  79.5647),
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
