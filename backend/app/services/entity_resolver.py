"""
entity_resolver.py — PRAMAAN Dynamic Entity Resolver

Upgrades the static `_CANONICAL_MAP` in `ingest.py` to a two-phase resolver:

Phase 1 — Static Map (fast, zero-DB):
    Check the hardcoded keyword table from ingest.py.  If found, return immediately.

Phase 2 — Dynamic Neo4j Fuzzy Match (slower, but catches unseen IDs):
    Query Neo4j for all nodes of the same label, then use `rapidfuzz.process.extractOne`
    to find the best matching node_id or name.  Only accepted if score ≥ FUZZY_THRESHOLD.

Caching:
    All label-specific node lists are cached in `_label_cache` with a TTL of 5 minutes
    so we do not hammer Neo4j for every entity in a batch.

Usage (called from ingest.py):
    from app.services.entity_resolver import resolve_entity_id

    resolved_id = resolve_entity_id(
        raw_id  = "reg_delhi",
        name    = "NCT of Delhi",
        label   = "Region",
        session = session,
    )
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from rapidfuzz import process, fuzz

log = logging.getLogger("pramaan.entity_resolver")

# ── Config ────────────────────────────────────────────────────────────────────
FUZZY_THRESHOLD = 72   # minimum rapidfuzz score to accept a match (0–100)
CACHE_TTL       = 300  # seconds — 5 minutes

# ── In-memory node cache: label → (timestamp, {id_or_name: canonical_id}) ────
_label_cache: dict[str, tuple[float, dict[str, str]]] = {}


# ── Static canonical map (mirrors ingest.py — single source of truth) ────────

_CANONICAL_MAP: dict[str, str] = {
    # ── Schemes ──────────────────────────────────────────────
    "sch_amrut":                "SCH_AMRUT",
    "amrut":                    "SCH_AMRUT",
    "scheme_amrut":             "SCH_AMRUT",
    "sch_pmay":                 "SCH_PMAY",
    "pmay":                     "SCH_PMAY",
    "scheme_pmay":              "SCH_PMAY",
    "pradhan mantri awas":      "SCH_PMAY",
    "sch_swachh":               "SCH_SWACHH",
    "swachh":                   "SCH_SWACHH",
    "swachhbharat":             "SCH_SWACHH",
    "sch_sfc":                  "SCH_SFC",
    "sfc":                      "SCH_SFC",
    "sch_local_lights":         "SCH_LOCAL_LIGHTS",
    "streetlight":              "SCH_LOCAL_LIGHTS",
    # ── Regions ──────────────────────────────────────────────
    "reg_delhi":                "REG_DELHI",
    "reg_w45":                  "REG_W45",
    "ward_45":                  "REG_W45",
    "ward45":                   "REG_W45",
    "ward 45":                  "REG_W45",
    "shahdara ward 45":         "REG_W45",
    "reg_shahdara_north":       "REG_SHAHDARA_NORTH",
    "shahdara north":           "REG_SHAHDARA_NORTH",
    "reg_shahdara_south":       "REG_SHAHDARA_SOUTH",
    "shahdara south":           "REG_SHAHDARA_SOUTH",
    "reg_w45_gali7":            "REG_W45_GALI7",
    "gali 7":                   "REG_W45_GALI7",
    "gali7":                    "REG_W45_GALI7",
    "reg_w45_gali12":           "REG_W45_GALI12",
    "gali 12":                  "REG_W45_GALI12",
    "gali12":                   "REG_W45_GALI12",
    "reg_w45_gali3":            "REG_W45_GALI3",
    "gali 3":                   "REG_W45_GALI3",
    "reg_w45_market_road":      "REG_W45_MARKET_ROAD",
    "shahdara market":          "REG_W45_MARKET_ROAD",
    "reg_w45_colony_y":         "REG_W45_COLONY_Y",
    "colony y":                 "REG_W45_COLONY_Y",
    # ── Actors ───────────────────────────────────────────────
    "act_mcd_shahdara_works":       "ACT_MCD_SHAHDARA_WORKS",
    "mcd shahdara works":           "ACT_MCD_SHAHDARA_WORKS",
    "mcd_shahdara":                 "ACT_MCD_SHAHDARA_WORKS",
    "act_mcd_shahdara_sanitation":  "ACT_MCD_SHAHDARA_SANITATION",
    "mcd sanitation":               "ACT_MCD_SHAHDARA_SANITATION",
    "act_mcd_electrical":           "ACT_MCD_ELECTRICAL",
    "mcd electrical":               "ACT_MCD_ELECTRICAL",
    "act_dda":                      "ACT_DDA",
    "dda":                          "ACT_DDA",
    "delhi development authority":  "ACT_DDA",
    "act_w45_councillor":           "ACT_W45_COUNCILLOR",
    "councillor":                   "ACT_W45_COUNCILLOR",
    "act_contractor_infra_1":       "ACT_CONTRACTOR_INFRA_1",
    "abc infra":                    "ACT_CONTRACTOR_INFRA_1",
    "act_contractor_lights_1":      "ACT_CONTRACTOR_LIGHTS_1",
    "brightlights":                 "ACT_CONTRACTOR_LIGHTS_1",
    # ── Ward 12 actors ───────────────────────────────────────
    "act_w12_councillor":           "ACT_W12_COUNCILLOR",
    "ward 12 councillor":           "ACT_W12_COUNCILLOR",
    "act_w12_works_dept":           "ACT_W12_WORKS_DEPT",
    "mcd ward 12":                  "ACT_W12_WORKS_DEPT",
    # ── Ward 28 actors ───────────────────────────────────────
    "act_w28_councillor":           "ACT_W28_COUNCILLOR",
    "ward 28 councillor":           "ACT_W28_COUNCILLOR",
    "act_w28_sanitation_dept":      "ACT_W28_SANITATION_DEPT",
    "mcd ward 28":                  "ACT_W28_SANITATION_DEPT",
    # ── Extended regions ─────────────────────────────────────
    "reg_w12":                      "REG_W12",
    "ward 12":                      "REG_W12",
    "ward12":                       "REG_W12",
    "reg_w28":                      "REG_W28",
    "ward 28":                      "REG_W28",
    "ward28":                       "REG_W28",
    # ── New schemes ───────────────────────────────────────────
    "sch_jjby":                     "SCH_JJBY",
    "jjby":                         "SCH_JJBY",
    "jal jeevan":                   "SCH_JJBY",
    "har ghar jal":                 "SCH_JJBY",
    "sch_ayushman":                 "SCH_AYUSHMAN",
    "ayushman":                     "SCH_AYUSHMAN",
    "pmjay":                        "SCH_AYUSHMAN",
    "jan arogya":                   "SCH_AYUSHMAN",
    "sch_ddugjy":                   "SCH_DDUGJY",
    "ddugjy":                       "SCH_DDUGJY",
    "deen dayal":                   "SCH_DDUGJY",
    # ── Iran / Geopolitics schemes ────────────────────────────
    "sch_ndrf_fund":                "SCH_NDRF_FUND",
    "ndrf":                         "SCH_NDRF_FUND",
    "national disaster response":   "SCH_NDRF_FUND",
    "sch_sdrf":                     "SCH_SDRF",
    "sdrf":                         "SCH_SDRF",
    "state disaster response":      "SCH_SDRF",
    "sch_spr":                      "SCH_SPR",
    "spr":                          "SCH_SPR",
    "strategic petroleum":          "SCH_SPR",
    "sch_chabahar":                 "SCH_CHABAHAR",
    "chabahar":                     "SCH_CHABAHAR",
    "sch_ongc_videsh":              "SCH_ONGC_VIDESH",
    "ongc videsh":                  "SCH_ONGC_VIDESH",
    "ongc":                         "SCH_ONGC_VIDESH",
    "sch_instc":                    "SCH_INSTC",
    "instc":                        "SCH_INSTC",
    "international north south":    "SCH_INSTC",
    "sch_isro_budget":              "SCH_ISRO_BUDGET",
    "isro budget":                  "SCH_ISRO_BUDGET",
    "sch_green_h2":                 "SCH_GREEN_H2",
    "green hydrogen":               "SCH_GREEN_H2",
    "sch_pli_solar":                "SCH_PLI_SOLAR",
    "pli solar":                    "SCH_PLI_SOLAR",
    "sch_ism":                      "SCH_ISM",
    # ── Known Events ─────────────────────────────────────────
    "evt_iran_war_2026":                    "EVT_IRAN_WAR_2026",
    "iran_war_2026":                        "EVT_IRAN_WAR_2026",
    "iran war":                             "EVT_IRAN_WAR_2026",
    "iran us israel war":                   "EVT_IRAN_WAR_2026",
    "evt_hormuz_blockade_2026":             "EVT_HORMUZ_BLOCKADE_2026",
    "hormuz_blockade_2026":                 "EVT_HORMUZ_BLOCKADE_2026",
    "hormuz blockade":                      "EVT_HORMUZ_BLOCKADE_2026",
    "strait of hormuz":                     "EVT_HORMUZ_BLOCKADE_2026",
    "evt_iran_ceasefire_talks_2026":        "EVT_IRAN_CEASEFIRE_TALKS_2026",
    "iran ceasefire":                       "EVT_IRAN_CEASEFIRE_TALKS_2026",
    "evt_operation_sindoor_2025":           "EVT_OPERATION_SINDOOR_2025",
    "operation_sindoor":                    "EVT_OPERATION_SINDOOR_2025",
    "operation sindoor":                    "EVT_OPERATION_SINDOOR_2025",
    "sindoor":                              "EVT_OPERATION_SINDOOR_2025",
    "evt_pahalgam_2025":                    "EVT_PAHALGAM_2025",
    "pahalgam":                             "EVT_PAHALGAM_2025",
    "pahalgam attack":                      "EVT_PAHALGAM_2025",
    "evt_india_pak_ceasefire_2025":         "EVT_INDIA_PAK_CEASEFIRE_2025",
    "india pak ceasefire":                  "EVT_INDIA_PAK_CEASEFIRE_2025",
    "evt_india_pak_diplo_crisis_2025":      "EVT_INDIA_PAK_DIPLO_CRISIS_2025",
    "india pakistan diplomatic":            "EVT_INDIA_PAK_DIPLO_CRISIS_2025",
    "evt_loc_skirmishes_2025":              "EVT_LOC_SKIRMISHES_2025",
    "loc skirmishes":                       "EVT_LOC_SKIRMISHES_2025",
    "evt_indus_waters_crisis_2025":         "EVT_INDUS_WATERS_CRISIS_2025",
    "indus waters":                         "EVT_INDUS_WATERS_CRISIS_2025",
    "indus treaty":                         "EVT_INDUS_WATERS_CRISIS_2025",
    "evt_twelve_day_war_2025":              "EVT_TWELVE_DAY_WAR_2025",
    "twelve day war":                       "EVT_TWELVE_DAY_WAR_2025",
    "israel iran war":                      "EVT_TWELVE_DAY_WAR_2025",
    "evt_india_us_defense_2025":            "EVT_INDIA_US_DEFENSE_2025",
    "india us defence":                     "EVT_INDIA_US_DEFENSE_2025",
    "india us defense":                     "EVT_INDIA_US_DEFENSE_2025",
    "evt_sp_upgrade_2025":                  "EVT_SP_UPGRADE_2025",
    "sp upgrade":                           "EVT_SP_UPGRADE_2025",
    "sovereign upgrade":                    "EVT_SP_UPGRADE_2025",
    "evt_india_uk_ceta_2025":               "EVT_INDIA_UK_CETA_2025",
    "india uk trade":                       "EVT_INDIA_UK_CETA_2025",
    "ceta":                                 "EVT_INDIA_UK_CETA_2025",
    "evt_shukla_iss_2025":                  "EVT_SHUKLA_ISS_2025",
    "shukla iss":                           "EVT_SHUKLA_ISS_2025",
    "evt_labour_codes_2025":                "EVT_LABOUR_CODES_2025",
    "labour codes":                         "EVT_LABOUR_CODES_2025",
    "four labour codes":                    "EVT_LABOUR_CODES_2025",
    "evt_india_extreme_weather_2025":       "EVT_INDIA_EXTREME_WEATHER_2025",
    "extreme weather 2025":                 "EVT_INDIA_EXTREME_WEATHER_2025",
    "evt_isro_spadex_2025":                 "EVT_ISRO_SPADEX_2025",
    "spadex":                               "EVT_ISRO_SPADEX_2025",
    "isro docking":                         "EVT_ISRO_SPADEX_2025",
    "evt_cyclone_dana_2024":                "EVT_CYCLONE_DANA_2024",
    "cyclone dana":                         "EVT_CYCLONE_DANA_2024",
    "dana cyclone":                         "EVT_CYCLONE_DANA_2024",
    "evt_wayanad_2024":                     "EVT_WAYANAD_2024",
    "wayanad":                              "EVT_WAYANAD_2024",
    "wayanad landslide":                    "EVT_WAYANAD_2024",
    "evt_tata_semi_2024":                   "EVT_TATA_SEMI_2024",
    "tata semiconductor":                   "EVT_TATA_SEMI_2024",
    "evt_g20_india_2023":                   "EVT_G20_INDIA_2023",
    "g20 india":                            "EVT_G20_INDIA_2023",
    "g20 new delhi":                        "EVT_G20_INDIA_2023",
    "evt_chandrayaan3_2023":                "EVT_CHANDRAYAAN3_2023",
    "chandrayaan":                          "EVT_CHANDRAYAAN3_2023",
    "chandrayaan 3":                        "EVT_CHANDRAYAAN3_2023",
    "evt_delhi_floods_2023":                "EVT_DELHI_FLOODS_2023",
    "delhi floods":                         "EVT_DELHI_FLOODS_2023",
    "yamuna floods":                        "EVT_DELHI_FLOODS_2023",
    "evt_manipur_2023":                     "EVT_MANIPUR_2023",
    "manipur":                              "EVT_MANIPUR_2023",
    "evt_joshimath_2023":                   "EVT_JOSHIMATH_2023",
    "joshimath":                            "EVT_JOSHIMATH_2023",
}

# ── Label → (id_field, name_field) ───────────────────────────────────────────
_LABEL_META: dict[str, tuple[str, str]] = {
    "Asset":       ("asset_id",       "name"),
    "Scheme":      ("scheme_id",      "name"),
    "Actor":       ("actor_id",       "name"),
    "Region":      ("region_id",      "name"),
    "Beneficiary": ("beneficiary_id", "description"),
    "Evidence":    ("evidence_id",    "source"),
    "Event":       ("event_id",       "name"),
}


# ── Phase 1: static lookup ────────────────────────────────────────────────────

def _static_lookup(raw_id: str, name: str) -> Optional[str]:
    id_lower   = raw_id.lower().strip().replace("-", "_").replace(" ", "_")
    name_lower = name.lower().strip()

    if id_lower in _CANONICAL_MAP:
        return _CANONICAL_MAP[id_lower]

    for keyword, canonical in _CANONICAL_MAP.items():
        norm_kw = keyword.replace(" ", "_")
        if norm_kw in id_lower or keyword in id_lower:
            return canonical

    for keyword, canonical in _CANONICAL_MAP.items():
        if keyword in name_lower:
            return canonical

    return None


# ── Phase 2: dynamic Neo4j fuzzy lookup ──────────────────────────────────────

def _get_label_corpus(label: str, session) -> dict[str, str]:
    """
    Return a mapping of {searchable_string: canonical_id} for all nodes of
    `label` in Neo4j.  Results are cached for CACHE_TTL seconds.
    """
    now = time.monotonic()
    if label in _label_cache:
        ts, corpus = _label_cache[label]
        if now - ts < CACHE_TTL:
            return corpus

    id_field, name_field = _LABEL_META.get(label, (f"{label.lower()}_id", "name"))

    try:
        result = session.run(
            f"MATCH (n:{label}) RETURN n.{id_field} AS nid, n.{name_field} AS nm LIMIT 2000"
        )
        corpus: dict[str, str] = {}
        for rec in result:
            nid = rec.get("nid") or ""
            nm  = rec.get("nm")  or ""
            if nid:
                corpus[nid.lower()] = nid         # key = lowercase id  → value = canonical id
            if nm:
                corpus[nm.lower()]  = nid         # key = lowercase name → value = canonical id
    except Exception as e:
        log.warning("[EntityResolver] Could not fetch corpus for %s: %s", label, e)
        corpus = {}

    _label_cache[label] = (now, corpus)
    return corpus


def _fuzzy_lookup(raw_id: str, name: str, label: str, session) -> Optional[str]:
    corpus = _get_label_corpus(label, session)
    if not corpus:
        return None

    candidates = list(corpus.keys())
    # Try matching the raw_id first, then the name
    for query_str in [raw_id.lower(), name.lower()]:
        if not query_str:
            continue
        match = process.extractOne(
            query_str,
            candidates,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=FUZZY_THRESHOLD,
        )
        if match:
            matched_key, score, _ = match
            canonical = corpus[matched_key]
            log.info(
                "[EntityResolver] Fuzzy match: '%s' → '%s' (score=%d, via label=%s)",
                query_str, canonical, score, label
            )
            return canonical

    return None


# ── Public API ────────────────────────────────────────────────────────────────

def resolve_entity_id(
    raw_id:  str,
    name:    str = "",
    label:   str = "",
    session=None,           # optional: if provided, enables Phase 2
) -> str:
    """
    Resolve `raw_id` (and optionally `name`) to a canonical graph ID.

    - Phase 1 is always run (static map).
    - Phase 2 (dynamic fuzzy) is run only if `session` is provided and Phase 1 misses.
    - Falls back to the original `raw_id` if nothing matches.
    """
    # Phase 1
    static = _static_lookup(raw_id, name)
    if static:
        return static

    # Phase 2
    if session and label:
        fuzzy = _fuzzy_lookup(raw_id, name, label, session)
        if fuzzy:
            return fuzzy

    return raw_id


def invalidate_cache(label: str | None = None):
    """Force cache invalidation — call when new nodes are bulk-seeded."""
    if label:
        _label_cache.pop(label, None)
    else:
        _label_cache.clear()
