# =============================================================================
# frontend/utils/constants.py — PRAMAAN Centralised Constants
# =============================================================================
# SINGLE SOURCE OF TRUTH for every value that was previously scattered across
# pages, utils, and components.  Import from here — never redefine locally.
#
# Sections
# --------
#   1. Backend API config
#   2. HTTP client / retry config
#   3. Geography defaults & ward geo-data
#   4. Proof status config
#   5. Proof-chain node icons & trust tiers
#   6. Scheme display names
#   7. Asset verification overrides  (demo mode)
#   8. Asset evidence photos
# =============================================================================

import os

# ── API ────────────────────────────────────────────────────────────────────────
API_BASE_URL = "http://127.0.0.1:8001"

# Convenience alias used by legacy code
BASE_URL: str = API_BASE_URL

# ── Node Icons for Proof Chain ────────────────────────────────────────────────
NODE_ICONS = {
    "Asset":      "🏗️",
    "Scheme":     "💰",
    "Department": "🏛️",
    "Ward":       "📍",
    "Evidence":   "📷",
    "Entity":     "🔷",
}

# ── Status Colors ──────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "verified":   "#00C853",
    "pending":    "#FFD600",
    "unverified": "#FF1744",
}

# ── Data Lake Paths ────────────────────────────────────────────────────────────
DATA_ROOT        = "e:/INDIA_INNOVATES/Pramaan/data"
INBOX_DIR        = "e:/INDIA_INNOVATES/Pramaan/inbox"
STRUCTURED_RAW   = f"{DATA_ROOT}/structured/raw"
SEMI_RAW         = f"{DATA_ROOT}/semi_structured/raw"
UNSTRUCTURED_RAW = f"{DATA_ROOT}/unstructured/raw"

# ─────────────────────────────────────────────────────────────────────────────
# 1. BACKEND API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
# Override at runtime via the API_BASE_URL environment variable.
# All frontend pages and utils must reference this — never hardcode the URL.



# ─────────────────────────────────────────────────────────────────────────────
# 2. HTTP CLIENT / RETRY CONFIG
# ─────────────────────────────────────────────────────────────────────────────

API_RETRIES: int   = 3     # total attempts (1 original + 2 retries)
API_DELAY:   float = 1.5   # seconds before 2nd attempt
API_BACKOFF: float = 2.0   # multiplier: 1.5s → 3.0s → 6.0s
API_TIMEOUT: int   = 10    # default request timeout in seconds (per attempt)

# ─────────────────────────────────────────────────────────────────────────────
# 3. GEOGRAPHY — OFFLINE FALLBACKS & STATIC GEO DATA
# ─────────────────────────────────────────────────────────────────────────────
#
# ⚠️  OFFLINE FALLBACKS — NOT primary data sources
# ─────────────────────────────────────────────────
# These values are used ONLY when:
#   • the backend is unreachable (Neo4j / FastAPI down), OR
#   • the user has not yet made any ward selection in the current session.
#
# Under normal operation ward names and IDs come from the /regions/ API
# (populated from regions.csv → Neo4j).  The selectors in Ward Map and
# geo_selector.py write the real values into session state; the code in
# session.py reads from session state first.
#
# Name → value mapping must stay in sync with regions.csv:
#   city:  "Delhi"               (REG_DELHI)
#   zone:  "Shahdara South Zone" (REG_SHAHDARA_SOUTH)
#   ward:  "DMC Ward No - 45"    (REG_W45, parent: REG_SHAHDARA_SOUTH)

DEFAULT_COUNTRY:  str = "India"
DEFAULT_STATE:    str = "Delhi"
DEFAULT_CITY:     str = "East Delhi Municipal Corporation"
DEFAULT_ZONE:     str = "Shahdara South Zone"
DEFAULT_WARD:     str = "DMC Ward No - 45"
DEFAULT_WARD_ID:  str = "REG_W45"

# ─────────────────────────────────────────────────────────────────────────────
# STATIC GEO DATA — ward polygons and centroids
# ─────────────────────────────────────────────────────────────────────────────
# TODO: these should come from a /regions/{id}/geo endpoint once lat/lon
#       columns are added to regions.csv.  Until then they live here.

# Approximate polygon for the folium ward boundary overlay (lat/lon pairs).
WARD_BOUNDARIES: dict[str, list[tuple[float, float]]] = {
    "REG_W45": [
        (28.677, 77.284), (28.677, 77.306),
        (28.672, 77.313), (28.660, 77.309),
        (28.655, 77.291), (28.659, 77.283),
        (28.677, 77.284),   # close polygon
    ],
}

# Ward centroid (lat, lon) — used for map centering and pin sanity-check.
WARD_CENTROID: dict[str, tuple[float, float]] = {
    "REG_W45": (28.666, 77.296),
}

# Pins beyond this many km from the centroid are considered mis-tagged.
PIN_RADIUS_KM: int = 18   # generous for Burari / Khureji Khas (~10 km away)

# ─────────────────────────────────────────────────────────────────────────────
# 4. PROOF STATUS CONFIG
# ─────────────────────────────────────────────────────────────────────────────
# Maps a proof_status string → (label, folium-colour, hex-colour, marker-hex)

STATUS_CONFIG: dict[str, tuple] = {
    "fully_verified":     ("✅ Fully Verified",     "green",  "#10b981", "#22c55e"),
    "partially_verified": ("⚠️ Partially Verified", "orange", "#f59e0b", "#f59e0b"),
    "unverified":         ("❌ Unverified",          "red",    "#ef4444", "#ef4444"),
    "news_only":          ("📰 News Only",           "orange", "#f59e0b", "#f59e0b"),
    "verified":           ("✅ Fully Verified",      "green",  "#10b981", "#22c55e"),
    None:                 ("❌ Unverified",          "red",    "#ef4444", "#ef4444"),
    "":                   ("❌ Unverified",          "red",    "#ef4444", "#ef4444"),
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. PROOF-CHAIN NODE ICONS & TRUST TIERS
# ─────────────────────────────────────────────────────────────────────────────



# Maps trust_tier key → (display_label, text_color, bg_color, border_color)
TRUST_TIERS: dict[str, tuple] = {
    "official":     ("Official",     "#22c55e", "rgba(34,197,94,0.12)",  "rgba(34,197,94,0.35)"),
    "verified":     ("Verified",     "#38bdf8", "rgba(56,189,248,0.12)", "rgba(56,189,248,0.35)"),
    "ai_extracted": ("AI Extracted", "#f59e0b", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.35)"),
    "unverified":   ("Unverified",   "#ef4444", "rgba(239,68,68,0.12)",  "rgba(239,68,68,0.35)"),
}

# source_type strings from Neo4j → TRUST_TIERS key
SOURCE_TYPE_MAP: dict[str, str] = {
    "official_csv":      "official",
    "data.gov.in":       "official",
    "government":        "official",
    "csv":               "official",
    "seed":              "official",
    "geo_photo":         "verified",
    "photo_exif":        "verified",
    "cross_validated":   "verified",
    "ai_extract":        "ai_extracted",
    "ai_extracted":      "ai_extracted",
    "llm":               "ai_extracted",
    "news_rss":          "ai_extracted",
    "rss":               "ai_extracted",
    "news":              "ai_extracted",
}

# Default trust tier per node kind when source_type is blank / unrecognised
NODE_KIND_DEFAULT_TRUST: dict[str, str] = {
    "scheme":   "official",
    "actor":    "official",
    "asset":    "official",
    "location": "official",
    "evidence": "unverified",
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. SCHEME DISPLAY NAMES
# ─────────────────────────────────────────────────────────────────────────────

SCHEME_DISPLAY_NAMES: dict[str, str] = {
    "Local Development Grants - Roads & Drains (Delhi)":  "Local Dev Grants (LDG)",
    "AMRUT 2.0 — Water Body Rejuvenation":                "AMRUT 2.0 Water Bodies",
    "AMRUT 2.0 — Storm Water Drainage":                   "AMRUT 2.0 Drainage",
    "CMDF — Chief Minister's Development Fund":            "CMDF Roads",
    "PMAY-U 2.0 — Pradhan Mantri Awas Yojana Urban":     "PMAY-U 2.0 Housing",
    "PMAY - Pradhan Mantri Awas Yojana":                  "PMAY Housing",
    "Swachh Bharat Mission - Urban":                       "SBM Urban Sanitation",
    "Swachh Bharat Mission Urban (SBM-U) Phase 2":        "SBM Urban Sanitation",
    "AMRUT 2.0":                                          "AMRUT 2.0",
    "LDG":                                                "Local Dev Grants (LDG)",
}

SCHEME_SHORT_NAMES: dict[str, str] = {
    "AMRUT 2.0 — Water Body Rejuvenation":                "AMRUT 2.0\nWater Bodies",
    "AMRUT 2.0 — Storm Water Drainage":                   "AMRUT 2.0\nDrainage",
    "CMDF — Chief Minister's Development Fund":            "CMDF\nRoads",
    "PMAY-U 2.0 — Pradhan Mantri Awas Yojana Urban":     "PMAY-U 2.0\nHousing",
    "Swachh Bharat Mission Urban (SBM-U) Phase 2":        "SBM-U\nSanitation",
    "PMAY - Pradhan Mantri Awas Yojana":                  "PMAY\nHousing",
    "Local Development Grants - Roads & Drains (Delhi)":  "Local Dev\nGrants (LDG)",
    "Swachh Bharat Mission - Urban":                       "SBM-U\nSanitation",
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. ASSET VERIFICATION OVERRIDE  — REMOVED
# ─────────────────────────────────────────────────────────────────────────────
# proof_status is now read directly from Neo4j via the /assets/{id}/chain API.
# The asset node carries proof_status set by load_seed_data.py and the
# VerificationAgent (backend/app/services/verification_agent.py).
# Do NOT hardcode status here — it creates a split-brain between the UI and DB.
#
# If you need to override a status for a demo, call:
#   POST /assets/{asset_id}/set-verified
# which writes directly to the graph and is visible everywhere.

ASSET_VERIFICATION_OVERRIDE: dict[str, str] = {}   # intentionally empty — backend is source of truth

# ─────────────────────────────────────────────────────────────────────────────
# 8. ASSET EVIDENCE PHOTOS
# ─────────────────────────────────────────────────────────────────────────────
# Maps asset_id → {"before": abs_path, "after": abs_path, ...}
# Paths are resolved at import time; empty string means file is missing.

_EVIDENCE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "static", "evidence")
)


def _img(filename: str) -> str:
    """Return absolute path if the file exists in the evidence dir, else ''."""
    full = os.path.join(_EVIDENCE_DIR, filename)
    return full if os.path.exists(full) else ""


ASSET_EVIDENCE_PHOTOS: dict[str, dict] = {
    # ── DRAIN: Gali No. 7 ─────────────────────────────────────────────────
    "ASSET_W45_GALI7_DRAIN": {
        "before":         _img("before_w45_gali7_drain.png"),
        "after":          _img("after_w45_gali7_drain.png"),
        "before_caption": "Reported: waterlogging, blocked drain surface, stagnant water — Jan 2024",
        "after_caption":  "Verified: new drain constructed, surface restored, waterlogging resolved — Mar 2025",
        "before_gps":     "📍 28.6748°N, 77.2921°E — Gali No. 7 Shahdara",
        "after_gps":      "📍 28.6748°N, 77.2921°E — Same location confirmed",
        "before_source":  "📋 MCD Complaint Log #2024-SHD-0132",
        "after_source":   "📸 Geo-tagged photo — MCD field inspector",
    },
    # ── DRAIN: Gali No. 12 — uses w46 drain as visual proxy ──────────────
    "ASSET_W45_GALI12_DRAIN": {
        "before":         _img("before_w46_gali3_drain.png"),
        "after":          _img("after_w46_gali3_drain.png"),
        "before_caption": "Reported: broken drain wall, waterlogging, encroachment — Jan 2024",
        "after_caption":  "Verified: drain reconstructed, walls repaired, drainage restored — Mar 2025",
        "before_gps":     "📍 28.6739°N, 77.2934°E — Gali No. 12 Shahdara",
        "after_gps":      "📍 28.6739°N, 77.2934°E — Same location confirmed",
        "before_source":  "📋 MCD Complaint Log #2024-SHD-0147",
        "after_source":   "📸 Geo-tagged photo — MCD field inspector",
    },
    # ── DRAIN: Gali No. 3 ─────────────────────────────────────────────────
    "ASSET_W45_GALI3_DRAIN": {
        "before":         _img("drain_before.png"),
        "after":          _img("drain_after.png"),
        "before_caption": "Reported: blocked drain, overflow onto road — Jan 2024",
        "after_caption":  "Partially verified: drain cleared, surface repair pending",
        "before_gps":     "📍 28.6760°N, 77.2912°E — Gali No. 3 Shahdara",
        "after_gps":      "📍 28.6760°N, 77.2912°E — Same location",
        "before_source":  "📋 MCD Complaint Log #2024-SHD-0138",
        "after_source":   "📸 Geo-tagged photo — field officer",
    },
    # ── PARK: Community Park ───────────────────────────────────────────────
    "ASSET_W45_PARK": {
        "before":         _img("before_w45_park.jpeg"),
        "after":          _img("after_w45_park.jpeg"),
        "before_caption": "Reported: overgrown, waterlogged park, no benches — Nov 2023",
        "after_caption":  "Verified: park rejuvenated, pathways laid, benches installed — Apr 2025",
        "before_gps":     "📍 28.6731°N, 77.2904°E — Community Park Ward 45",
        "after_gps":      "📍 28.6731°N, 77.2904°E — Same location confirmed",
        "before_source":  "📋 MCD Inspection Report #2023-SHD-P04",
        "after_source":   "📸 Geo-tagged photo — AMRUT monitoring team",
    },
    # ── ROAD: Gali No. 7 ──────────────────────────────────────────────────
    "ASSET_W45_ROAD_GALI7": {
        "before":         _img("before_w45_gali7_road.jpeg"),
        "after":          _img("after_w45_gali7_road.jpeg"),
        "before_caption": "Reported: potholed, broken road surface — Feb 2024",
        "after_caption":  "Pending: road repair work yet to be completed",
        "before_gps":     "📍 28.6748°N, 77.2921°E — Road Gali No. 7",
        "after_gps":      "",
        "before_source":  "📋 MCD Complaint Log #2024-SHD-R019",
        "after_source":   "",
    },
    # ── TOILET: Community Toilet Block ────────────────────────────────────
    "ASSET_W45_TOILET": {
        "before":         _img("before_w45_toilet.jpeg"),
        "after":          _img("after_w45_toilet.jpeg"),
        "before_caption": "Reported: broken toilet facility, no water connection — Mar 2024",
        "after_caption":  "Pending: maintenance contract under tendering",
        "before_gps":     "📍 28.6740°N, 77.2915°E — Community Toilet Ward 45",
        "after_gps":      "",
        "before_source":  "📋 MCD Sanitation Report #2024-SHD-T07",
        "after_source":   "",
    },
    # ── PMAY Housing Block A ───────────────────────────────────────────────
    "ASSET_W45_PMAY_HOUSING_A": {
        "before":         _img("before_w45_pmay.jpeg"),
        "after":          _img("after_w45_pmay.jpeg"),
        "before_caption": "Site pre-construction — foundation under survey — Nov 2023",
        "after_caption":  "Pending: interior finishing and possession handover",
        "before_gps":     "📍 28.6720°N, 77.2910°E — PMAY Housing Block A Ward 45",
        "after_gps":      "",
        "before_source":  "📋 DDA PMAY-U Sanction Report #2023-DDA-H45",
        "after_source":   "",
    },
    # ── STREETLIGHT: Gali No. 12 ──────────────────────────────────────────
    "ASSET_W45_GALI12_STREETLIGHT": {
        "before":         _img("before_w45_gali12_streetlight.jpeg"),
        "after":          _img("after_w45_gali12_streetlight.jpeg"),
        "before_caption": "Reported: street dark at night, lights broken/absent — Jan 2024",
        "after_caption":  "Pending: Smart Street Light Mission deployment in progress",
        "before_gps":     "📍 28.6739°N, 77.2934°E — Gali No. 12 Shahdara",
        "after_gps":      "",
        "before_source":  "📋 MCD Complaint Log #2024-SHD-L023",
        "after_source":   "",
    },
}
