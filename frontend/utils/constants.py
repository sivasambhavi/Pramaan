# Shared constants for PRAMAAN ui
import os

SCHEME_DISPLAY_NAMES = {
    "Local Development Grants - Roads & Drains (Delhi)": "Local Dev Grants (LDG)",
    "AMRUT 2.0 — Water Body Rejuvenation": "AMRUT 2.0 Water Bodies",
    "AMRUT 2.0 — Storm Water Drainage": "AMRUT 2.0 Drainage",
    "CMDF — Chief Minister's Development Fund": "CMDF Roads",
    "PMAY-U 2.0 — Pradhan Mantri Awas Yojana Urban": "PMAY-U 2.0 Housing",
    "PMAY - Pradhan Mantri Awas Yojana": "PMAY Housing",
    "Swachh Bharat Mission - Urban": "SBM Urban Sanitation",
    "Swachh Bharat Mission Urban (SBM-U) Phase 2": "SBM Urban Sanitation",
    "AMRUT 2.0": "AMRUT 2.0",
    "LDG": "Local Dev Grants (LDG)",
}

SCHEME_SHORT_NAMES = {
    "AMRUT 2.0 — Water Body Rejuvenation": "AMRUT 2.0\nWater Bodies",
    "AMRUT 2.0 — Storm Water Drainage": "AMRUT 2.0\nDrainage",
    "CMDF — Chief Minister's Development Fund": "CMDF\nRoads",
    "PMAY-U 2.0 — Pradhan Mantri Awas Yojana Urban": "PMAY-U 2.0\nHousing",
    "Swachh Bharat Mission Urban (SBM-U) Phase 2": "SBM-U\nSanitation",
    "PMAY - Pradhan Mantri Awas Yojana": "PMAY\nHousing",
    "Local Development Grants - Roads & Drains (Delhi)": "Local Dev\nGrants (LDG)",
    "Swachh Bharat Mission - Urban": "SBM-U\nSanitation",
}

# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC VERIFICATION OVERRIDE — v4.6.3 Demo Mode
# Each asset_id is mapped to its demo-mode verification status.
# This dict is the single source of truth used by Ward Map, Proof Chain,
# Micro-Accountability, and any future pages that need proof_status.
# Score: (2×1.0 + 2×0.5) / 8 × 100 = 37.5% → shown as 37.5% in gauge
# ─────────────────────────────────────────────────────────────────────────────
ASSET_VERIFICATION_OVERRIDE: dict[str, str] = {
    "ASSET_W45_GALI12_DRAIN":   "fully_verified",    # drain: 3 HT/CSR/ET news articles + Completed status
    "ASSET_W45_PARK":           "fully_verified",     # park: AMRUT completion data + photos
    "ASSET_W45_GALI7_DRAIN":    "partially_verified", # drain: news only (no photos in chain yet)
    "ASSET_W45_GALI3_DRAIN":    "partially_verified", # drain: news only
    "ASSET_W45_TOILET":         "unverified",
    "ASSET_W45_PMAY_HOUSING_A": "unverified",
    "ASSET_W45_ROAD_GALI7":     "unverified",
    "ASSET_W45_GALI12_STREETLIGHT": "unverified",
}

# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE PHOTOS — absolute paths to repo evidence images
# Keyed by asset_id → {"before": path, "after": path, "before_caption": ..., ...}
# All paths are relative to the PRAMAAN project root; we resolve at runtime.
# ─────────────────────────────────────────────────────────────────────────────
_EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "evidence"))

def _img(filename: str) -> str:
    """Return absolute path if the file exists in the evidence directory, else empty string."""
    full = os.path.join(_EVIDENCE_DIR, filename)
    return full if os.path.exists(full) else ""

ASSET_EVIDENCE_PHOTOS: dict[str, dict] = {
    # ── DRAIN: Gali No. 7 ─────────────────────────────────────────────────
    "ASSET_W45_GALI7_DRAIN": {
        "before":          _img("before_w45_gali7_drain.png"),
        "after":           _img("after_w45_gali7_drain.png"),
        "before_caption":  "Reported: waterlogging, blocked drain surface, stagnant water — Jan 2024",
        "after_caption":   "Verified: new drain constructed, surface restored, waterlogging resolved — Mar 2025",
        "before_gps":      "📍 28.6748°N, 77.2921°E — Gali No. 7 Shahdara",
        "after_gps":       "📍 28.6748°N, 77.2921°E — Same location confirmed",
        "before_source":   "📋 MCD Complaint Log #2024-SHD-0132",
        "after_source":    "📸 Geo-tagged photo — MCD field inspector",
    },
    # ── DRAIN: Gali No. 12 — uses w46 drain as visual proxy ──────────────
    "ASSET_W45_GALI12_DRAIN": {
        "before":          _img("before_w46_gali3_drain.png"),
        "after":           _img("after_w46_gali3_drain.png"),
        "before_caption":  "Reported: broken drain wall, waterlogging, encroachment — Jan 2024",
        "after_caption":   "Verified: drain reconstructed, walls repaired, drainage restored — Mar 2025",
        "before_gps":      "📍 28.6739°N, 77.2934°E — Gali No. 12 Shahdara",
        "after_gps":       "📍 28.6739°N, 77.2934°E — Same location confirmed",
        "before_source":   "📋 MCD Complaint Log #2024-SHD-0147",
        "after_source":    "📸 Geo-tagged photo — MCD field inspector",
    },
    # ── DRAIN: Gali No. 3 ─────────────────────────────────────────────────
    "ASSET_W45_GALI3_DRAIN": {
        "before":          _img("drain_before.png"),
        "after":           _img("drain_after.png"),
        "before_caption":  "Reported: blocked drain, overflow onto road — Jan 2024",
        "after_caption":   "Partially verified: drain cleared, surface repair pending",
        "before_gps":      "📍 28.6760°N, 77.2912°E — Gali No. 3 Shahdara",
        "after_gps":       "📍 28.6760°N, 77.2912°E — Same location",
        "before_source":   "📋 MCD Complaint Log #2024-SHD-0138",
        "after_source":    "📸 Geo-tagged photo — field officer",
    },
    # ── PARK: Community Park ───────────────────────────────────────────────
    "ASSET_W45_PARK": {
        "before":          _img("before_w45_park.jpeg"),
        "after":           _img("after_w45_park.jpeg"),
        "before_caption":  "Reported: overgrown, waterlogged park, no benches — Nov 2023",
        "after_caption":   "Verified: park rejuvenated, pathways laid, benches installed — Apr 2025",
        "before_gps":      "📍 28.6731°N, 77.2904°E — Community Park Ward 45",
        "after_gps":       "📍 28.6731°N, 77.2904°E — Same location confirmed",
        "before_source":   "📋 MCD Inspection Report #2023-SHD-P04",
        "after_source":    "📸 Geo-tagged photo — AMRUT monitoring team",
    },
    # ── ROAD: Gali No. 7 ──────────────────────────────────────────────────
    "ASSET_W45_ROAD_GALI7": {
        "before":          _img("before_w45_gali7_road.jpeg"),
        "after":           _img("after_w45_gali7_road.jpeg"),
        "before_caption":  "Reported: potholed, broken road surface — Feb 2024",
        "after_caption":   "Pending: road repair work yet to be completed",
        "before_gps":      "📍 28.6748°N, 77.2921°E — Road Gali No. 7",
        "after_gps":       "",
        "before_source":   "📋 MCD Complaint Log #2024-SHD-R019",
        "after_source":    "",
    },
    # ── TOILET: Community Toilet Block ────────────────────────────────────
    "ASSET_W45_TOILET": {
        "before":          _img("before_w45_toilet.jpeg"),
        "after":           _img("after_w45_toilet.jpeg"),
        "before_caption":  "Reported: broken toilet facility, no water connection — Mar 2024",
        "after_caption":   "Pending: maintenance contract under tendering",
        "before_gps":      "📍 28.6740°N, 77.2915°E — Community Toilet Ward 45",
        "after_gps":       "",
        "before_source":   "📋 MCD Sanitation Report #2024-SHD-T07",
        "after_source":    "",
    },
    # ── PMAY Housing Block A ───────────────────────────────────────────────
    "ASSET_W45_PMAY_HOUSING_A": {
        "before":          _img("before_w45_pmay.jpeg"),
        "after":           _img("after_w45_pmay.jpeg"),
        "before_caption":  "Site pre-construction — foundation under survey — Nov 2023",
        "after_caption":   "Pending: interior finishing and possession handover",
        "before_gps":      "📍 28.6720°N, 77.2910°E — PMAY Housing Block A Ward 45",
        "after_gps":       "",
        "before_source":   "📋 DDA PMAY-U Sanction Report #2023-DDA-H45",
        "after_source":    "",
    },
    # ── STREETLIGHT: Gali No. 12 ──────────────────────────────────────────
    "ASSET_W45_GALI12_STREETLIGHT": {
        "before":          _img("before_w45_gali12_streetlight.jpeg"),
        "after":           _img("after_w45_gali12_streetlight.jpeg"),
        "before_caption":  "Reported: street dark at night, lights broken/absent — Jan 2024",
        "after_caption":   "Pending: Smart Street Light Mission deployment in progress",
        "before_gps":      "📍 28.6739°N, 77.2934°E — Gali No. 12 Shahdara",
        "after_gps":       "",
        "before_source":   "📋 MCD Complaint Log #2024-SHD-L023",
        "after_source":    "",
    },
}

