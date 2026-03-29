"""
transform.py — PRAMAAN ETL Step 2: Transform

Reads raw govdata JSONs from data/resources/structured/govdata/
and maps them to ontology-compatible Impact + Evidence nodes.

Output: data/resources/ontology/govdata_nodes.json
  {
    "meta":     { ... },
    "impacts":  [ Impact nodes ],
    "evidence": [ Evidence nodes ],
    "edges":    [ edges linking nodes to existing events ]
  }

This output is consumed by:
  validate_ontology.py  →  backend/scripts/load_govdata.py

Node IDs use DG_ prefix to distinguish from hand-curated seed_graph nodes.

Usage:
    python3 data/scripts/transform.py
    python3 data/scripts/transform.py --dry-run   # print summary, no file write
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]
_GOVDATA_DIR  = _PROJECT_ROOT / "data" / "resources" / "structured" / "govdata"
_REGISTRY     = _PROJECT_ROOT / "data" / "config" / "govdata_registry.json"
_OUTPUT_FILE  = _PROJECT_ROOT / "data" / "resources" / "ontology" / "govdata_nodes.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(filename: str) -> list:
    path = _GOVDATA_DIR / filename
    if not path.exists():
        print(f"  ⚠️  Missing {filename} — skipping (run fetch_govdata.py first)")
        return []
    data = json.loads(path.read_text())
    return data.get("records", [])


def _registry_entry(name: str) -> dict:
    reg = json.loads(_REGISTRY.read_text())
    for d in reg["datasets"]:
        if d["name"] == name:
            return d
    return {}


def _safe_float(val) -> float | None:
    try:
        return float(val) if val not in (None, "", "N/A") else None
    except (ValueError, TypeError):
        return None


def _evidence(name: str, custom_title: str = "") -> dict:
    reg = _registry_entry(name)
    return {
        "evidence_id": f"EVD_DG_{name.upper()}",
        "type":        "dataset",
        "title":       custom_title or reg.get("title", name),
        "source":      "data.gov.in",
        "url":         reg.get("api_endpoint", ""),
        "date":        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def _edge(from_id: str, edge_type: str, to_id: str, reason: str = "") -> dict:
    return {"type": edge_type, "from": from_id, "to": to_id, "reason": reason}


# ── Dataset transformers ──────────────────────────────────────────────────────

def transform_covid_deaths(impacts, evidence, edges):
    recs = _load("covid_deaths_2021.json")
    if not recs:
        return

    total = sum(_safe_float(r.get("deaths_during_2021__till_14th_july_2021_")) or 0 for r in recs)
    imp_id = "IMP_DG_COVID_DEATHS_2021"
    impacts.append({
        "impact_id":   imp_id,
        "type":        "deaths",
        "value":       int(total),
        "unit":        "persons",
        "description": f"Total COVID-19 deaths across India till July 14, 2021 (data.gov.in)",
    })
    evd = _evidence("covid_deaths_statewise_2021", "State/UT-wise COVID-19 Deaths 2021 — data.gov.in")
    evidence.append(evd)
    edges += [
        _edge("EVT_COVID_WAVE2_2021", "CAUSED",    imp_id,        "State-wise COVID deaths data from data.gov.in"),
        _edge("EVT_COVID_WAVE2_2021", "PROVEN_BY", evd["evidence_id"], "Official MoHFW data via data.gov.in"),
    ]
    print(f"  ✅ COVID deaths: total={int(total):,} persons across {len(recs)} states")


def transform_covid_cases(impacts, evidence, edges):
    recs = _load("covid_cases_deaths.json")
    if not recs:
        return

    total_cases  = sum(_safe_float(r.get("total_cases"))  or 0 for r in recs)
    total_deaths = sum(_safe_float(r.get("total_deaths")) or 0 for r in recs)

    imp_cases = "IMP_DG_COVID_TOTAL_CASES"
    imp_dead  = "IMP_DG_COVID_CUMULATIVE_DEATHS"
    impacts += [
        {
            "impact_id":   imp_cases,
            "type":        "total_cases",
            "value":       int(total_cases),
            "unit":        "persons",
            "description": "Cumulative COVID-19 cases across India (data.gov.in)",
        },
        {
            "impact_id":   imp_dead,
            "type":        "deaths",
            "value":       int(total_deaths),
            "unit":        "persons",
            "description": "Cumulative COVID-19 deaths across India (data.gov.in)",
        },
    ]
    evd = _evidence("covid_cases_deaths_recovered", "COVID-19 Cases, Deaths and Recovered — data.gov.in")
    evidence.append(evd)
    edges += [
        _edge("EVT_COVID_WAVE2_2021", "CAUSED",    imp_cases,         "Total COVID cases from MoHFW data"),
        _edge("EVT_COVID_WAVE2_2021", "CAUSED",    imp_dead,          "Total COVID deaths from MoHFW data"),
        _edge("EVT_COVID_WAVE2_2021", "PROVEN_BY", evd["evidence_id"], "MoHFW via data.gov.in"),
    ]
    print(f"  ✅ COVID cases: {int(total_cases):,} total cases, {int(total_deaths):,} deaths")


def transform_ndrf_lives_saved(impacts, evidence, edges):
    recs = _load("ndrf_lives_saved.json")
    if not recs:
        return

    evd = _evidence("ndrf_lives_saved_2018_2023", "NDRF Lives Saved 2018–2023 — data.gov.in")
    evidence.append(evd)

    # Aggregate totals across all years
    total_rescued  = sum(_safe_float(r.get("persons_rescued"))  or 0 for r in recs)
    total_evacuated = sum(_safe_float(r.get("persons_evacuated")) or 0 for r in recs)

    imp_res = "IMP_DG_NDRF_TOTAL_RESCUED"
    imp_eva = "IMP_DG_NDRF_TOTAL_EVACUATED"
    impacts += [
        {
            "impact_id":   imp_res,
            "type":        "persons_rescued",
            "value":       int(total_rescued),
            "unit":        "persons",
            "description": f"Total persons rescued by NDRF 2018–2023 (data.gov.in)",
        },
        {
            "impact_id":   imp_eva,
            "type":        "persons_evacuated",
            "value":       int(total_evacuated),
            "unit":        "persons",
            "description": f"Total persons evacuated by NDRF 2018–2023 (data.gov.in)",
        },
    ]
    climate_events = [
        "EVT_WAYANAD_2024", "EVT_CHAMOLI_2021",
        "EVT_CYCLONE_DANA_2024", "EVT_DELHI_FLOODS_2023",
    ]
    for evt in climate_events:
        edges += [
            _edge(evt, "PROVEN_BY", evd["evidence_id"], "NDRF response data from data.gov.in"),
        ]
    edges += [
        _edge("EVT_WAYANAD_2024",    "CAUSED", imp_res, "NDRF rescue operations context"),
        _edge("EVT_CYCLONE_DANA_2024","CAUSED", imp_eva, "NDRF evacuation operations context"),
    ]
    print(f"  ✅ NDRF: {int(total_rescued):,} rescued, {int(total_evacuated):,} evacuated (2018–2023)")


def transform_ndrf_sdrf_funds(impacts, evidence, edges):
    recs = _load("ndrf_sdrf_funds.json")
    if not recs:
        return

    # State → event mapping
    STATE_EVENT = {
        "kerala":       "EVT_WAYANAD_2024",
        "uttarakhand":  "EVT_CHAMOLI_2021",
        "delhi":        "EVT_DELHI_FLOODS_2023",
        "odisha":       "EVT_CYCLONE_DANA_2024",
        "manipur":      "EVT_MANIPUR_2023",
        "jammu":        "EVT_ART370_2019",
    }

    evd = _evidence("ndrf_sdrf_allocation_release_2018_2023", "NDRF/SDRF Fund Allocation 2018–2023 — data.gov.in")
    evidence.append(evd)

    added = 0
    for rec in recs:
        state_raw = str(rec.get("state_ut", "")).lower()
        matched_evt = None
        for key, evt in STATE_EVENT.items():
            if key in state_raw:
                matched_evt = evt
                break
        if not matched_evt:
            continue

        # Use latest NDRF release (2022-23)
        ndrf_val = (_safe_float(rec.get("release_from_ndrf__for_all_calamities____2022_23"))
                    or _safe_float(rec.get("release_from_ndrf__for_all_calamities____2021_22"))
                    or _safe_float(rec.get("release_from_ndrf__for_all_calamities____2020_21__")))
        if not ndrf_val:
            continue

        state_label = rec.get("state_ut", "").replace(" ", "_").upper()[:12]
        imp_id = f"IMP_DG_NDRF_{state_label}"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "disaster_relief_funds",
            "value":       ndrf_val,
            "unit":        "crore_inr",
            "description": f"NDRF release to {rec.get('state_ut')} — latest available year (data.gov.in)",
        })
        edges += [
            _edge(matched_evt, "CAUSED",    imp_id,            f"NDRF funds released to {rec.get('state_ut')}"),
            _edge(matched_evt, "PROVEN_BY", evd["evidence_id"], "NDRF/SDRF funds data from data.gov.in"),
        ]
        added += 1

    print(f"  ✅ NDRF/SDRF funds: {added} state-level impact nodes created")


def transform_cyclone_frequency(impacts, evidence, edges):
    recs = _load("cyclone_frequency.json")
    if not recs:
        return

    # Last 10 years average cyclone count
    recent = [r for r in recs if _safe_float(r.get("year")) and _safe_float(r.get("year")) >= 2012]
    if not recent:
        return

    avg_cyclones = sum(_safe_float(r.get("cyclones___total")) or 0 for r in recent) / len(recent)
    avg_severe   = sum(_safe_float(r.get("severe_cyclones___total")) or 0 for r in recent) / len(recent)

    evd = _evidence("cyclone_frequency_1891_2021", "IMD Annual Cyclone Frequency 1891–2021 — data.gov.in")
    evidence.append(evd)

    imp_freq   = "IMP_DG_CYCLONE_ANNUAL_AVG"
    imp_severe = "IMP_DG_SEVERE_CYCLONE_AVG"
    impacts += [
        {
            "impact_id":   imp_freq,
            "type":        "cyclone_annual_average",
            "value":       round(avg_cyclones, 1),
            "unit":        "cyclones_per_year",
            "description": "Average annual cyclone count in India (2012–2021, IMD data.gov.in)",
        },
        {
            "impact_id":   imp_severe,
            "type":        "severe_cyclone_annual_average",
            "value":       round(avg_severe, 1),
            "unit":        "cyclones_per_year",
            "description": "Average annual severe cyclone count in India (2012–2021, IMD data.gov.in)",
        },
    ]
    edges += [
        _edge("EVT_CYCLONE_DANA_2024", "CAUSED",    imp_freq,          "IMD cyclone frequency context"),
        _edge("EVT_CYCLONE_DANA_2024", "CAUSED",    imp_severe,        "IMD severe cyclone context"),
        _edge("EVT_CYCLONE_DANA_2024", "PROVEN_BY", evd["evidence_id"], "IMD historical cyclone data"),
        _edge("EVT_WAYANAD_2024",      "PROVEN_BY", evd["evidence_id"], "IMD climate data context"),
    ]
    print(f"  ✅ Cyclone frequency: avg {round(avg_cyclones,1)}/yr, severe {round(avg_severe,1)}/yr (2012–2021)")


def transform_cyclone_damage(impacts, evidence, edges):
    recs = _load("cyclone_damage_2021.json")
    if not recs:
        return

    total_deaths = sum(_safe_float(r.get("human_lives_lost")) or 0 for r in recs)
    total_houses = sum(_safe_float(r.get("houses_huts_damaged")) or 0 for r in recs)

    evd = _evidence("cyclone_damage_tauktae_yaas_2021", "Cyclone Tauktae & Yaas Damage 2021 — data.gov.in")
    evidence.append(evd)

    imp_d = "IMP_DG_CYCLONE_TAUKTAE_DEATHS"
    imp_h = "IMP_DG_CYCLONE_TAUKTAE_HOUSES"
    impacts += [
        {
            "impact_id":   imp_d,
            "type":        "deaths",
            "value":       int(total_deaths),
            "unit":        "persons",
            "description": "Deaths from Cyclone Tauktae and Yaas 2021 (data.gov.in)",
        },
        {
            "impact_id":   imp_h,
            "type":        "structures_damaged",
            "value":       int(total_houses),
            "unit":        "count",
            "description": "Houses/huts damaged by Cyclone Tauktae and Yaas 2021 (data.gov.in)",
        },
    ]
    edges += [
        _edge("EVT_CYCLONE_DANA_2024", "CAUSED",    imp_d,             "Cyclone damage precedent data 2021"),
        _edge("EVT_CYCLONE_DANA_2024", "CAUSED",    imp_h,             "Cyclone structural damage precedent"),
        _edge("EVT_CYCLONE_DANA_2024", "PROVEN_BY", evd["evidence_id"], "NDMA cyclone damage data"),
    ]
    print(f"  ✅ Cyclone damage (Tauktae/Yaas): {int(total_deaths)} deaths, {int(total_houses):,} houses")


def transform_pli(impacts, evidence, edges):
    recs_apps = _load("pli_applications.json")
    recs_inv  = _load("pli_investments.json")

    evd_apps = _evidence("pli_applications_approved_sectorwise",
                         "PLI Scheme Applications Approved by Sector 2020–2025 — data.gov.in")
    evd_inv  = _evidence("pli_new_investments_yearwise",
                         "PLI New Investments 2020–2025 — data.gov.in")
    evidence += [evd_apps, evd_inv]

    # Find electronics/semiconductor sector
    semi_apps = 0
    for rec in recs_apps:
        sector = str(rec.get("sectors", "")).lower()
        if any(k in sector for k in ["electronic", "semiconductor", "it hardware", "mobile"]):
            semi_apps += _safe_float(rec.get("_total")) or 0

    if semi_apps:
        imp_id = "IMP_DG_PLI_SEMI_APPS"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "pli_applications",
            "value":       int(semi_apps),
            "unit":        "count",
            "description": "PLI applications approved in Electronics/Semiconductor sectors (data.gov.in)",
        })
        edges += [
            _edge("EVT_TATA_SEMI_2024", "CAUSED",    imp_id,               "PLI electronics applications"),
            _edge("EVT_TATA_SEMI_2024", "PROVEN_BY", evd_apps["evidence_id"], "PLI sector data from data.gov.in"),
        ]

    # Latest year total PLI investment
    if recs_inv:
        latest = recs_inv[-1]
        total_inv = _safe_float(latest.get("_total"))
        year_label = latest.get("_year", "")
        if total_inv:
            imp_id2 = "IMP_DG_PLI_INVESTMENT_LATEST"
            impacts.append({
                "impact_id":   imp_id2,
                "type":        "investment_crore",
                "value":       total_inv * 100,   # Lakh Crore → Crore approx
                "unit":        "crore_inr",
                "description": f"Total new PLI investment in India {year_label} (data.gov.in)",
            })
            edges += [
                _edge("EVT_TATA_SEMI_2024", "CAUSED",    imp_id2,              "PLI total investment"),
                _edge("EVT_IMEC_2023",      "CAUSED",    imp_id2,              "PLI investment context for IMEC"),
                _edge("EVT_TATA_SEMI_2024", "PROVEN_BY", evd_inv["evidence_id"], "PLI investment data"),
            ]

    print(f"  ✅ PLI: {int(semi_apps)} electronics/semi apps, latest inv={recs_inv[-1].get('_total') if recs_inv else '?'} lakh cr")


def transform_semiconductor_imports(impacts, evidence, edges):
    recs = _load("semiconductor_imports.json")
    if not recs:
        return

    evd = _evidence("semiconductor_imports_2021_2024", "Semiconductor Chip Imports 2021–2024 — data.gov.in")
    evidence.append(evd)

    for rec in recs:
        year  = str(rec.get("_year", "")).replace("-", "_")
        val   = _safe_float(rec.get("value__usd_bn_"))
        if not val:
            continue
        imp_id = f"IMP_DG_SEMI_IMPORT_{year}"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "semiconductor_import_usd",
            "value":       val,
            "unit":        "billion_usd",
            "description": f"India semiconductor chip imports {rec.get('_year')} (data.gov.in)",
        })
        edges += [
            _edge("EVT_TATA_SEMI_2024", "CAUSED",    imp_id,            "Import dependency context"),
            _edge("EVT_TATA_SEMI_2024", "PROVEN_BY", evd["evidence_id"], "Semiconductor import data"),
        ]

    print(f"  ✅ Semiconductor imports: {len(recs)} years loaded")


def transform_defence_budget(impacts, evidence, edges):
    recs_rd  = _load("defence_budget_rd.json")
    recs_gdp = _load("defence_budget_gdp.json")

    evd_rd  = _evidence("defence_budget_rd_yearwise",  "Defence R&D Budget over Years — data.gov.in")
    evd_gdp = _evidence("defence_budget_gdp_percentage","Defence Budget % of GDP — data.gov.in")
    evidence += [evd_rd, evd_gdp]

    # Select relevant years
    YEAR_EVENT = {
        "2019": "EVT_BALAKOT_2019",
        "2021": "EVT_MANIPUR_2023",
        "2022": "EVT_MANIPUR_2023",
        "2023": "EVT_MANIPUR_2023",
    }
    for rec in recs_rd:
        year_raw = str(rec.get("_year", ""))
        matched_evt = None
        for y, evt in YEAR_EVENT.items():
            if year_raw.startswith(y):
                matched_evt = evt
                break
        if not matched_evt:
            continue

        budget = _safe_float(rec.get("annual_defence_budget_in_cr_"))
        if not budget:
            continue

        y_slug = year_raw.replace("-", "_").replace("/", "_")[:7]
        imp_id = f"IMP_DG_DEFENCE_BUDGET_{y_slug}"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "defence_budget_crore",
            "value":       budget,
            "unit":        "crore_inr",
            "description": f"India annual defence budget {year_raw} (data.gov.in)",
        })
        edges += [
            _edge(matched_evt, "CAUSED",    imp_id,             f"Defence budget context {year_raw}"),
            _edge(matched_evt, "PROVEN_BY", evd_rd["evidence_id"], "DRDO defence budget data"),
        ]

    for rec in recs_gdp:
        year_raw = str(rec.get("_year", ""))
        pct      = _safe_float(rec.get("defence__budget_as_percentage_of_gdp"))
        if not pct:
            continue

        y_slug = year_raw.replace("-", "_").replace("/", "_")[:7]
        imp_id = f"IMP_DG_DEFENCE_GDP_PCT_{y_slug}"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "defence_gdp_percentage",
            "value":       pct,
            "unit":        "percent",
            "description": f"Defence budget as % of GDP {year_raw} (data.gov.in)",
        })
        edges += [
            _edge("EVT_BALAKOT_2019", "CAUSED",    imp_id,              f"Defence spending context"),
            _edge("EVT_BALAKOT_2019", "PROVEN_BY", evd_gdp["evidence_id"], "GDP defence data"),
        ]

    print(f"  ✅ Defence budget: {len(recs_rd)} R&D years + {len(recs_gdp)} GDP% years processed")


def transform_jk_investment(impacts, evidence, edges):
    recs = _load("jk_development_investment.json")
    if not recs:
        return

    evd = _evidence("jk_development_investment_2019_2023",
                    "J&K Development Investment 2019–2023 — data.gov.in")
    evidence.append(evd)

    total = sum(_safe_float(r.get("amount_of_investment__rs_in_crores_")) or 0 for r in recs)
    for rec in recs:
        year  = str(rec.get("_year", "")).replace("-", "_")[:7]
        val   = _safe_float(rec.get("amount_of_investment__rs_in_crores_"))
        if not val:
            continue
        imp_id = f"IMP_DG_JK_INVEST_{year}"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "investment_crore",
            "value":       val,
            "unit":        "crore_inr",
            "description": f"J&K development investment {rec.get('_year')} post-Art.370 (data.gov.in)",
        })
        edges.append(_edge("EVT_ART370_2019", "CAUSED", imp_id,
                           f"J&K investment {rec.get('_year')}"))

    edges.append(_edge("EVT_ART370_2019", "PROVEN_BY", evd["evidence_id"],
                       "GoI J&K investment data post-2019"))
    print(f"  ✅ J&K investment: {len(recs)} years, total ₹{total:.1f} Cr")


def transform_fdi(impacts, evidence, edges):
    recs_live    = _load("fdi_equity_inflows.json")
    recs_country = _load("fdi_countrywise.json")

    evd_live    = _evidence("fdi_equity_inflows_live",    "FDI Equity Inflows Live (DPIIT) — data.gov.in")
    evd_country = _evidence("fdi_countrywise_2017_2021",  "Country-wise FDI Inflows 2017–2021 — data.gov.in")
    evidence += [evd_live, evd_country]

    # Total FDI from live dataset
    total_usd = sum(_safe_float(r.get("AMOUNT_IN_USD")) or 0 for r in recs_live
                    if (r.get("UNIT") or "").upper() == "MILLION")
    if total_usd:
        imp_id = "IMP_DG_FDI_TOTAL_USD"
        impacts.append({
            "impact_id":   imp_id,
            "type":        "fdi_inflow_usd",
            "value":       round(total_usd, 1),
            "unit":        "million_usd",
            "description": "Total FDI equity inflows into India (all sectors, data.gov.in DPIIT)",
        })
        edges += [
            _edge("EVT_G20_INDIA_2023", "CAUSED",    imp_id,              "FDI context for G20 outcomes"),
            _edge("EVT_IMEC_2023",      "CAUSED",    imp_id,              "FDI context for IMEC corridor"),
            _edge("EVT_G20_INDIA_2023", "PROVEN_BY", evd_live["evidence_id"], "DPIIT FDI data"),
        ]

    # Canada FDI — diplomatic context
    canada_total = None
    for rec in recs_country:
        if "canada" in str(rec.get("country", "")).lower():
            canada_total = _safe_float(rec.get("_total"))
            break
    if canada_total:
        imp_id2 = "IMP_DG_FDI_CANADA_TOTAL"
        impacts.append({
            "impact_id":   imp_id2,
            "type":        "fdi_inflow_usd",
            "value":       canada_total,
            "unit":        "million_usd",
            "description": "Total FDI from Canada to India 2017–2021 (data.gov.in) — diplomatic context",
        })
        edges += [
            _edge("EVT_INDIA_CANADA_2023", "CAUSED",    imp_id2,              "Canada FDI — economic stake in row"),
            _edge("EVT_INDIA_CANADA_2023", "PROVEN_BY", evd_country["evidence_id"], "DPIIT country-wise FDI"),
        ]

    print(f"  ✅ FDI: total {round(total_usd,1):.0f} M USD (all sectors), Canada {canada_total} M USD")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAMAAN ETL Transform step")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print summary without writing output file")
    args = parser.parse_args()

    impacts:  list = []
    evidence: list = []
    edges:    list = []

    print("=" * 60)
    print("  PRAMAAN — Transform (govdata → ontology nodes)")
    print("=" * 60)

    print("\n[Society — COVID]")
    transform_covid_deaths(impacts, evidence, edges)
    transform_covid_cases(impacts, evidence, edges)

    print("\n[Climate — Disasters]")
    transform_ndrf_lives_saved(impacts, evidence, edges)
    transform_ndrf_sdrf_funds(impacts, evidence, edges)
    transform_cyclone_frequency(impacts, evidence, edges)
    transform_cyclone_damage(impacts, evidence, edges)

    print("\n[Economics / Technology — PLI & Semiconductors]")
    transform_pli(impacts, evidence, edges)
    transform_semiconductor_imports(impacts, evidence, edges)

    print("\n[Defense]")
    transform_defence_budget(impacts, evidence, edges)

    print("\n[Governance — J&K]")
    transform_jk_investment(impacts, evidence, edges)

    print("\n[Geopolitics / Economics — FDI]")
    transform_fdi(impacts, evidence, edges)

    # Deduplicate edges
    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e["from"], e["type"], e["to"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    output = {
        "meta": {
            "version":      "1.0",
            "description":  "Govdata-derived Impact and Evidence nodes — PRAMAAN",
            "source":       "data.gov.in",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "impacts":  impacts,
        "evidence": evidence,
        "edges":    unique_edges,
    }

    print(f"\n{'='*60}")
    print(f"  TRANSFORM COMPLETE")
    print(f"  Impact nodes  : {len(impacts)}")
    print(f"  Evidence nodes: {len(evidence)}")
    print(f"  Edges         : {len(unique_edges)}")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n[dry-run] No file written.")
        return 0

    _OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n✅ Written → {_OUTPUT_FILE}")
    print("✅ Next: run validate_ontology.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
