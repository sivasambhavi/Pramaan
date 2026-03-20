"""
transform_to_7_table_schema.py — PRAMAAN Step 2: Transform

Reads raw data from data/resources/ (API JSONs, KML, CSV, MD files)
and normalizes everything into the 7-table canonical schema:

    schemes.csv, regions.csv, actors.csv, assets.csv,
    beneficiaries.csv, evidence.csv, events.csv

Output lands in: data/resources/final_formalized/

Run after: fetch_govdata.py
Run before: validate.py  →  load_seed_data.py
"""

import pandas as pd
import json
import os
import re
from pathlib import Path

# ── Dynamic cross-platform paths ──────────────────────────────────────────────
# This script lives at: data/scripts/transform_to_7_table_schema.py
# Project root is 2 levels up.
_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]          # Pramaan/
govdata_dir    = str(_PROJECT_ROOT / "data" / "resources" / "structured" / "govdata")
external_dir   = str(_PROJECT_ROOT / "data" / "resources" / "structured" / "external")
semi_dir       = str(_PROJECT_ROOT / "data" / "resources" / "semi_structured")
output_dir     = str(_PROJECT_ROOT / "data" / "resources" / "final_formalized")
os.makedirs(output_dir, exist_ok=True)

def _load_json(filename, source="govdata"):
    """Load a JSON file from the appropriate raw/ subfolder. Returns {} on missing file."""
    base = govdata_dir if source == "govdata" else external_dir
    path = os.path.join(base, filename)
    if not os.path.exists(path):
        fetcher = "fetch_govdata.py" if source == "govdata" else "fetch_external.py"
        print(f"  ⚠️  Missing: {filename} — skipping (run {fetcher} first)")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _records(data):
    """Return records list from a data.gov.in JSON response."""
    return data.get("records", [])

print("=" * 60)
print("  PRAMAAN — Transform to 7-Table Schema")
print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# 1. SCHEMES
#    Sources: hardcoded base list + amrut_funds.json (financial enrichment)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/7] Generating schemes.csv ...")

schemes = [
    {'scheme_id': 'SCH_AMRUT',       'name': 'AMRUT - Atal Mission for Rejuvenation and Urban Transformation', 'ministry': 'MoHUA',     'category': 'infrastructure'},
    {'scheme_id': 'SCH_SFC',         'name': 'Local Development Grants - Roads & Drains (Delhi)',               'ministry': 'GNCTD/MCD', 'category': 'roads_drains'},
    {'scheme_id': 'SCH_SWACHH',      'name': 'Swachh Bharat Mission - Urban',                                  'ministry': 'MoHUA',     'category': 'sanitation'},
    {'scheme_id': 'SCH_PMAY',        'name': 'PMAY-Urban (Pradhan Mantri Awas Yojana)',                        'ministry': 'MoHUA',     'category': 'housing'},
    {'scheme_id': 'SCH_LOCAL_LIGHTS','name': 'Urban Streetlight Improvement (Delhi)',                           'ministry': 'GNCTD/MCD', 'category': 'streetlights'},
]

# Enrich with AMRUT funds data — add Delhi allocation amount
amrut_funds_data = _load_json("amrut_funds.json")
for rec in _records(amrut_funds_data):
    state = str(rec.get("state_ut", "") or rec.get("states_ut", ""))
    if "Delhi" in state or "delhi" in state.lower():
        # Add fund allocation as extra fields
        for s in schemes:
            if s["scheme_id"] == "SCH_AMRUT":
                s["allocated_crore"] = rec.get("_2022_23", rec.get("total", ""))
                break

pd.DataFrame(schemes).to_csv(os.path.join(output_dir, "schemes.csv"), index=False)
print(f"  ✅ {len(schemes)} schemes written")


# ─────────────────────────────────────────────────────────────────────────────
# 2. REGIONS
#    Sources: ward census CSV (272 Delhi wards) + hardcoded gallis for Ward 45
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/7] Generating regions.csv ...")

regions = [
    {'region_id': 'REG_DELHI',          'name': 'Delhi',               'type': 'state', 'parent_region_id': ''},
    {'region_id': 'REG_SHAHDARA_NORTH', 'name': 'Shahdara North Zone', 'type': 'zone',  'parent_region_id': 'REG_DELHI'},
    {'region_id': 'REG_SHAHDARA_SOUTH', 'name': 'Shahdara South Zone', 'type': 'zone',  'parent_region_id': 'REG_DELHI'},
]

ward_pop_json = os.path.join(external_dir, "delhi_ward_population_2011.json")
if os.path.exists(ward_pop_json):
    with open(ward_pop_json, "r", encoding="utf-8") as f:
        ward_pop_data = json.load(f)
    seen_ward_ids = set()
    ward_count = 0
    for row in ward_pop_data.get("records", []):
        ward_name = str(row.get("Ward", "")).strip()
        match = re.search(r'\d+', ward_name)
        w_num = match.group() if match else "UNK"
        region_id = f"REG_W{w_num}"
        if region_id in seen_ward_ids:
            continue   # deduplicate
        seen_ward_ids.add(region_id)
        regions.append({
            'region_id':        region_id,
            'name':             ward_name,
            'type':             'ward',
            'parent_region_id': 'REG_SHAHDARA_NORTH',
            'population':       row.get("Population", ""),
        })
        ward_count += 1
    print(f"  ✅ {ward_count} unique wards loaded from ward population JSON (with population)")
else:
    print("  ⚠️  delhi_ward_population_2011.json missing — run fetch_external.py first")

# Ward 216 is absent from the 2011 census JSON (Shahdara North Zone roster includes it).
# Add a placeholder so park assets can link to it.
_census_ward_ids = {r['region_id'] for r in regions}
if 'REG_W216' not in _census_ward_ids:
    regions.append({
        'region_id':        'REG_W216',
        'name':             'Ward 216 (Shahdara North)',
        'type':             'ward',
        'parent_region_id': 'REG_SHAHDARA_NORTH',
        'population':       '',
    })
    print("  ℹ️  REG_W216 added as placeholder (absent from census JSON)")

# Ward 45 street-level regions
regions.extend([
    {'region_id': 'REG_W45_GALI7',       'name': 'Gali No. 7',                  'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_GALI12',      'name': 'Gali No. 12',                 'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_GALI3',       'name': 'Gali No. 3',                  'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_MARKET_ROAD', 'name': 'Shahdara Market Road',         'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_BLOCKA',      'name': 'Block A Residential Pocket',   'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_COLONY_Y',    'name': 'Colony Y Housing Cluster',     'type': 'street', 'parent_region_id': 'REG_W45'},
])

pd.DataFrame(regions).to_csv(os.path.join(output_dir, "regions.csv"), index=False)
print(f"  ✅ {len(regions)} total regions written")


# ─────────────────────────────────────────────────────────────────────────────
# 3. ACTORS
#    Sources: hardcoded government depts + delhi_tenders_data.md (contractors)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/7] Generating actors.csv ...")

actors = [
    {'actor_id': 'ACT_MCD_SHAHDARA_WORKS',      'name': 'MCD Shahdara North Works Dept',   'type': 'government',  'region_id': 'REG_SHAHDARA_NORTH'},
    {'actor_id': 'ACT_MCD_SHAHDARA_SANITATION', 'name': 'MCD Shahdara Sanitation Dept',    'type': 'government',  'region_id': 'REG_SHAHDARA_SOUTH'},
    {'actor_id': 'ACT_MCD_ELECTRICAL',          'name': 'MCD Electrical Dept - Shahdara',  'type': 'government',  'region_id': 'REG_SHAHDARA_SOUTH'},
    {'actor_id': 'ACT_DDA',                     'name': 'Delhi Development Authority',     'type': 'government',  'region_id': 'REG_DELHI'},
    {'actor_id': 'ACT_W45_COUNCILLOR',          'name': 'Ward 45 Councillor',              'type': 'elected_rep', 'region_id': 'REG_W45'},
    {'actor_id': 'ACT_CONTRACTOR_INFRA_1',      'name': 'ABC Infra Pvt Ltd',               'type': 'contractor',  'region_id': 'REG_W45'},
    {'actor_id': 'ACT_CONTRACTOR_LIGHTS_1',     'name': 'BrightLights Engineering',        'type': 'contractor',  'region_id': 'REG_W45'},
]

# ── Load contractors from semi_structured/extracted/tenders.json ──────────
_semi_extracted = _PROJECT_ROOT / "data" / "resources" / "semi_structured" / "extracted"
_tenders_json   = _semi_extracted / "tenders.json"
if _tenders_json.exists():
    _tenders_data = json.loads(_tenders_json.read_text())
    seen_ids = {a["actor_id"] for a in actors}
    added = 0
    for row in _tenders_data.get("rows", []):
        actor_id = row["actor_id"]
        if actor_id in seen_ids:
            continue
        actors.append({'actor_id': actor_id, 'name': row["name"],
                       'type': 'contractor', 'region_id': 'REG_DELHI'})
        seen_ids.add(actor_id)
        added += 1
    print(f"  ✅ {added} contractors from tenders.json")
else:
    print("  ⚠️  tenders.json missing — run fetch_semi_structured.py first")

# ── Load supervisors from semi_structured/extracted/parks_roster.json ─────
_parks_json = _semi_extracted / "parks_roster.json"
_parks_data = None
if _parks_json.exists():
    _parks_data = json.loads(_parks_json.read_text())
    seen_act_ids = {a["actor_id"] for a in actors}
    sup_added = 0
    for sup in _parks_data.get("supervisors", []):
        name     = str(sup["name"]).strip()
        actor_id = "ACT_SUP_" + re.sub(r'[^A-Z0-9]', '_', name.upper())[:25].strip('_')
        if actor_id in seen_act_ids:
            continue
        actors.append({'actor_id': actor_id,
                       'name':     f"{name} (Park Supervisor, Shahdara North)",
                       'type':     'government', 'region_id': 'REG_SHAHDARA_NORTH'})
        seen_act_ids.add(actor_id)
        sup_added += 1
    print(f"  ✅ {sup_added} park supervisors from parks_roster.json")
else:
    print("  ⚠️  parks_roster.json missing — run fetch_semi_structured.py first")

pd.DataFrame(actors).to_csv(os.path.join(output_dir, "actors.csv"), index=False)
print(f"  ✅ {len(actors)} total actors written")


# ─────────────────────────────────────────────────────────────────────────────
# 4. ASSETS
#    Sources: hardcoded Ward 45 assets + amrut_storm_water_drainage.json (Delhi)
#             + pmay_housing_data.json (Delhi) + watercensusmap.kml (water bodies)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/7] Generating assets.csv ...")

assets = [
    # ── Drains ────────────────────────────────────────────────────────────
    {'asset_id': 'ASSET_W45_GALI7_DRAIN',        'name': 'Storm-water drain — Gali No. 7',          'type': 'drain',       'region_id': 'REG_W45_GALI7',       'scheme_id': 'SCH_SFC',          'actor_id': 'ACT_MCD_SHAHDARA_WORKS',      'cost': 1200000,  'status': 'completed', 'lat': 28.6692, 'lon': 77.2945},
    {'asset_id': 'ASSET_W45_GALI12_DRAIN',       'name': 'Storm-water drain — Gali No. 12',         'type': 'drain',       'region_id': 'REG_W45_GALI12',      'scheme_id': 'SCH_AMRUT',        'actor_id': 'ACT_MCD_SHAHDARA_WORKS',      'cost': 980000,   'status': 'completed', 'lat': 28.6739, 'lon': 77.2934},
    {'asset_id': 'ASSET_W45_GALI3_DRAIN',        'name': 'Storm-water drain — Gali No. 3',          'type': 'drain',       'region_id': 'REG_W45_GALI3',       'scheme_id': 'SCH_SFC',          'actor_id': 'ACT_MCD_SHAHDARA_WORKS',      'cost': 750000,   'status': 'in_progress', 'lat': 28.6760, 'lon': 77.2912},
    # ── Roads ─────────────────────────────────────────────────────────────
    {'asset_id': 'ASSET_W45_ROAD_GALI7',         'name': 'Road resurfacing — Gali No. 7',           'type': 'road',        'region_id': 'REG_W45_GALI7',       'scheme_id': 'SCH_SFC',          'actor_id': 'ACT_CONTRACTOR_INFRA_1',      'cost': 900000,   'status': 'completed', 'lat': 28.6695, 'lon': 77.2948},
    # ── Sanitation ────────────────────────────────────────────────────────
    {'asset_id': 'ASSET_W45_TOILET',             'name': 'Community toilet block — Shahdara Market', 'type': 'toilet',     'region_id': 'REG_W45_MARKET_ROAD', 'scheme_id': 'SCH_SWACHH',       'actor_id': 'ACT_MCD_SHAHDARA_SANITATION', 'cost': 800000,   'status': 'in_progress', 'lat': 28.6685, 'lon': 77.2955},
    # ── Housing ───────────────────────────────────────────────────────────
    {'asset_id': 'ASSET_W45_PMAY_HOUSING_A',     'name': 'PMAY Housing Block A — Colony Y (30 units)', 'type': 'housing', 'region_id': 'REG_W45_COLONY_Y',    'scheme_id': 'SCH_PMAY',         'actor_id': 'ACT_DDA',                     'cost': 30000000, 'status': 'in_progress', 'lat': 28.6720, 'lon': 77.2910},
    # ── Streetlights ──────────────────────────────────────────────────────
    {'asset_id': 'ASSET_W45_GALI12_STREETLIGHT', 'name': 'LED streetlights — Gali No. 12',          'type': 'streetlight', 'region_id': 'REG_W45_GALI12',     'scheme_id': 'SCH_LOCAL_LIGHTS', 'actor_id': 'ACT_CONTRACTOR_LIGHTS_1',     'cost': 600000,   'status': 'in_progress', 'lat': 28.6739, 'lon': 77.2934},
    # ── Parks ─────────────────────────────────────────────────────────────
    {'asset_id': 'ASSET_W45_PARK',               'name': 'Community park — Ward 45',                'type': 'park',        'region_id': 'REG_W45',             'scheme_id': 'SCH_AMRUT',        'actor_id': 'ACT_MCD_SHAHDARA_WORKS',      'cost': 500000,   'status': 'completed', 'lat': 28.6731, 'lon': 77.2904},
]

# ── Enrich from AMRUT JSON: add Delhi-level drain project ─────────────────
amrut_data = _load_json("amrut_storm_water_drainage.json")
for rec in _records(amrut_data):
    if "Delhi" in str(rec.get("state_ut", "")):
        assets.append({
            'asset_id':  'ASSET_AMRUT_DRAIN_DELHI_STATE',
            'name':      f"AMRUT Storm-Water Drainage — Delhi State ({rec.get('work_completed___number', 0)} works completed)",
            'type':      'drain',
            'region_id': 'REG_DELHI',
            'scheme_id': 'SCH_AMRUT',
            'actor_id':  'ACT_MCD_SHAHDARA_WORKS',
            'cost':      float(rec.get('work_completed___amount', 0) or 0) * 100000,
            'status':    'completed',
            'lat':       28.6139,
            'lon':       77.2090,
        })
        break

# ── Enrich from PMAY JSON: add Delhi-level housing asset ──────────────────
pmay_data = _load_json("pmay_housing_data.json")
for rec in _records(pmay_data):
    if "Delhi" in str(rec.get("state_ut", "")):
        completed = rec.get("houses_as_on_31_12_2024___completed", 0) or 0
        occupied  = rec.get("houses_as_on_31_12_2024___occupied",  0) or 0
        assets.append({
            'asset_id':  'ASSET_PMAY_HOUSING_DELHI_STATE',
            'name':      f"PMAY-U Delhi State — {int(completed):,} houses completed, {int(occupied):,} occupied",
            'type':      'housing',
            'region_id': 'REG_DELHI',
            'scheme_id': 'SCH_PMAY',
            'actor_id':  'ACT_DDA',
            'cost':      int(completed) * 300000,  # ~3 lakh avg cost per unit
            'status':    'completed',
            'lat':       28.6139,
            'lon':       77.2090,
        })
        break

# ── Water bodies from semi_structured/extracted/water_bodies.json ──────────
_wb_json = _semi_extracted / "water_bodies.json"
kml_added = 0
if _wb_json.exists():
    _wb_data = json.loads(_wb_json.read_text())
    for row in _wb_data.get("rows", []):
        assets.append({
            'asset_id':    f"ASSET_WB_{row['objectid']}",
            'name':        row['name'],
            'type':        'water_body',
            'region_id':   'REG_DELHI',
            'scheme_id':   'SCH_AMRUT',
            'actor_id':    'ACT_DDA',
            'cost':        None,
            'status':      row['status'],
            'lat':         row['lat'],
            'lon':         row['lon'],
            'encroached':  row['encroached'],
            'nature':      row['nature'],
            'ownership':   row['ownership'],
            'image_url':   row['image_url'],
            'source_type': 'semi_structured_kml',
            'confidence':  0.95,
        })
        kml_added += 1
    enc_count = sum(1 for a in assets if a.get('encroached') == 'Yes')
    print(f"  ✅ {kml_added} water body assets from water_bodies.json ({enc_count} encroached)")
else:
    print("  ⚠️  water_bodies.json missing — run fetch_semi_structured.py first")

# ── Park assets from semi_structured/extracted/parks_roster.json ───────────
parks_added = 0
if _parks_data is not None:
    # Build supervisor name → actor_id map for linking
    _sup_map = {
        str(sup["name"]).strip():
            "ACT_SUP_" + re.sub(r'[^A-Z0-9]', '_', str(sup["name"]).upper())[:25].strip('_')
        for sup in _parks_data.get("supervisors", [])
        if sup.get("name")
    }
    _seen_wards = set()
    for park in _parks_data.get("parks", []):
        sno       = park['sno']
        park_name = park['park_name']
        region_id = park['region_id']
        actor_id  = _sup_map.get(park.get('supervisor',''), 'ACT_MCD_SHAHDARA_WORKS')
        area      = park.get('area_acres')
        _seen_wards.add(park['ward_no'])
        assets.append({
            'asset_id':    f"ASSET_PARK_SNZ_{sno}",
            'name':        park_name,
            'type':        'park',
            'region_id':   region_id,
            'scheme_id':   'SCH_AMRUT',
            'actor_id':    actor_id,
            'cost':        None,
            'status':      'completed',
            'lat':         park.get('lat'),
            'lon':         park.get('lon'),
            'encroached':  '',
            'nature':      f"Area: {area} acres" if area else '',
            'ownership':   'MCD',
            'image_url':   '',
            'source_type': 'semi_structured_xlsx',
            'confidence':  0.9,
        })
        parks_added += 1
    print(f"  ✅ {parks_added} park assets from parks_roster.json ({len(_seen_wards)} wards)")
else:
    print("  ⚠️  parks_roster.json missing — run fetch_semi_structured.py first")

pd.DataFrame(assets).to_csv(os.path.join(output_dir, "assets.csv"), index=False)
print(f"  ✅ {len(assets)} total assets written")


# ─────────────────────────────────────────────────────────────────────────────
# 5. BENEFICIARIES
#    Sources: hardcoded (partially mocked for demo)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/7] Generating beneficiaries.csv ...")

# ── Ward 45 population from external fetch (delhi_ward_population_2011.json) ──
_w45_pop = None
for _row in ward_pop_data.get("records", []):
    if "45" in str(_row.get("Ward", "")).strip():
        _w45_pop = int(_row["Population"])
        break
if _w45_pop is None:
    raise RuntimeError("Ward 45 population not found in delhi_ward_population_2011.json — run fetch_external.py first")
_w45_households = _w45_pop // 4  # avg 4 persons/household in Delhi

# ── Ward-level beneficiaries derived from ward population ─────────────────────
beneficiaries = [
    # ~5% of households on each gali for drain/road coverage
    {'beneficiary_id': 'BEN_W45_GALI7_DRAIN',   'asset_id': 'ASSET_W45_GALI7_DRAIN',        'scheme_id': 'SCH_SFC',          'region_id': 'REG_W45_GALI7',       'count': max(100, _w45_households // 20), 'description': f'Households protected from waterlogging — Gali No. 7 (~5% of Ward 45 households)'},
    {'beneficiary_id': 'BEN_W45_GALI12_DRAIN',  'asset_id': 'ASSET_W45_GALI12_DRAIN',       'scheme_id': 'SCH_AMRUT',        'region_id': 'REG_W45_GALI12',      'count': max(100, _w45_households // 22), 'description': f'Households benefiting from drain — Gali No. 12'},
    {'beneficiary_id': 'BEN_W45_GALI3_DRAIN',   'asset_id': 'ASSET_W45_GALI3_DRAIN',        'scheme_id': 'SCH_SFC',          'region_id': 'REG_W45_GALI3',       'count': max(80,  _w45_households // 25), 'description': f'Households on Gali No. 3 drain project'},
    {'beneficiary_id': 'BEN_W45_ROAD_GALI7',    'asset_id': 'ASSET_W45_ROAD_GALI7',         'scheme_id': 'SCH_SFC',          'region_id': 'REG_W45_GALI7',       'count': max(150, _w45_households // 18), 'description': f'Households benefiting from road resurfacing — Gali No. 7'},
    # Public toilet serves ~12% of ward population daily
    {'beneficiary_id': 'BEN_W45_TOILET',        'asset_id': 'ASSET_W45_TOILET',             'scheme_id': 'SCH_SWACHH',       'region_id': 'REG_W45_MARKET_ROAD', 'count': max(200, _w45_pop // 8),         'description': f'Daily users of community toilet — Shahdara Market (~12% of ward pop)'},
    # PMAY housing — fixed (actual sanctioned units)
    {'beneficiary_id': 'BEN_W45_PMAY',          'asset_id': 'ASSET_W45_PMAY_HOUSING_A',     'scheme_id': 'SCH_PMAY',         'region_id': 'REG_W45_COLONY_Y',    'count': 120,                             'description': 'Residents in 30 PMAY units — Colony Y (4 persons/unit)'},
    # Streetlights serve ~10% of ward households
    {'beneficiary_id': 'BEN_W45_LIGHTS',        'asset_id': 'ASSET_W45_GALI12_STREETLIGHT', 'scheme_id': 'SCH_LOCAL_LIGHTS', 'region_id': 'REG_W45_GALI12',      'count': max(100, _w45_households // 10), 'description': f'Households with improved night lighting — Gali No. 12'},
    # Park serves entire ward
    {'beneficiary_id': 'BEN_W45_PARK',          'asset_id': 'ASSET_W45_PARK',               'scheme_id': 'SCH_AMRUT',        'region_id': 'REG_W45',             'count': _w45_pop,                        'description': f'Ward 45 residents with access to community park (census pop: {_w45_pop})'},
]

# ── Delhi state-level beneficiaries from govdata API JSONs ────────────────────
# PMAY: extract Delhi houses from pmay_housing_data.json
# Field names use double-underscore: state__ut, physical_progress_of_houses__in_nos____occupied
pmay_data = _load_json("pmay_housing_data.json")
for rec in _records(pmay_data):
    state = str(rec.get("state__ut", "")).strip()
    if state == "Delhi":
        occupied  = int(rec.get("physical_progress_of_houses__in_nos____occupied", 0) or 0)
        completed = int(rec.get("physical_progress_of_houses__in_nos____completed__delivered", 0) or 0)
        count = occupied if occupied > 0 else completed
        if count > 0:
            beneficiaries.append({
                'beneficiary_id': 'BEN_DELHI_PMAY',
                'asset_id':       'ASSET_W45_PMAY_HOUSING_A',
                'scheme_id':      'SCH_PMAY',
                'region_id':      'REG_DELHI',
                'count':          count,
                'description':    f'Houses occupied under PMAY-Urban in Delhi — source: data.gov.in',
            })
        break

# SBM: extract Delhi toilet count from sbm_toilets_comprehensive.json (year-by-year 2017→2022)
# Field names: state_ut, individual_toilets_constructed__in_nos____till_march__22
sbm_data = _load_json("sbm_toilets_comprehensive.json")
for rec in _records(sbm_data):
    state = str(rec.get("state_ut", "")).strip()
    if "Delhi" in state:
        ihhl_total = int(rec.get("individual_toilets_constructed__in_nos____till_march__22", 0) or 0)
        ct_total   = int(rec.get("public___community_toilets_constructed__in_seats____till_march__22", 0) or 0)
        count = ihhl_total + ct_total
        if count > 0:
            beneficiaries.append({
                'beneficiary_id': 'BEN_DELHI_SBM',
                'asset_id':       'ASSET_W45_TOILET',
                'scheme_id':      'SCH_SWACHH',
                'region_id':      'REG_DELHI',
                'count':          count,
                'description':    f'Toilets (IHHL + CT/PT) constructed in Delhi under SBM-Urban till Mar 2022 — source: data.gov.in',
            })
        break

# PM SVANidhi: extract Delhi street vendor loans
# Field names: state_ut, number_of_pm_svanidhi_beneficiaries___total
svanidhi_data = _load_json("pm_svanidhi_beneficiaries.json")
for rec in _records(svanidhi_data):
    state = str(rec.get("state_ut", "")).strip()
    if "Delhi" in state:
        total = int(rec.get("number_of_pm_svanidhi_beneficiaries___total", 0) or 0)
        if total > 0:
            beneficiaries.append({
                'beneficiary_id': 'BEN_DELHI_SVANIDHI',
                'asset_id':       'ASSET_W45_PARK',
                'scheme_id':      'SCH_AMRUT',
                'region_id':      'REG_DELHI',
                'count':          total,
                'description':    f'Street vendors receiving PM SVANidhi loans in Delhi (cumulative 2020-24) — source: data.gov.in',
            })
        break

# Ayushman Bharat: Delhi does not participate in AB-PMJAY (opted out).
# Skip this entry — no Delhi row exists in ayushman_bharat_cards.json.

pd.DataFrame(beneficiaries).to_csv(os.path.join(output_dir, "beneficiaries.csv"), index=False)
print(f"  ✅ {len(beneficiaries)} beneficiaries written")


# ─────────────────────────────────────────────────────────────────────────────
# 6. EVIDENCE
#    Sources: static evidence photos in frontend/static/evidence/ + news articles
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/7] Generating evidence.csv ...")

evidence = [
    {'evidence_id': 'EVD_W45_GALI7_DRAIN_BEFORE',  'asset_id': 'ASSET_W45_GALI7_DRAIN',        'region_id': 'REG_W45_GALI7',  'type': 'image', 'before_or_after': 'before', 'capture_date': '2024-01-05', 'url': 'frontend/static/evidence/before_w45_gali7_drain.png',    'source': 'MCD Complaint Log #2024-SHD-0132'},
    {'evidence_id': 'EVD_W45_GALI7_DRAIN_AFTER',   'asset_id': 'ASSET_W45_GALI7_DRAIN',        'region_id': 'REG_W45_GALI7',  'type': 'image', 'before_or_after': 'after',  'capture_date': '2025-03-22', 'url': 'frontend/static/evidence/after_w45_gali7_drain.png',     'source': 'MCD field inspector geo-tagged photo'},
    {'evidence_id': 'EVD_W45_GALI12_DRAIN_BEFORE', 'asset_id': 'ASSET_W45_GALI12_DRAIN',       'region_id': 'REG_W45_GALI12', 'type': 'image', 'before_or_after': 'before', 'capture_date': '2024-01-10', 'url': 'frontend/static/evidence/before_w46_gali3_drain.png',    'source': 'MCD Complaint Log #2024-SHD-0147'},
    {'evidence_id': 'EVD_W45_GALI12_DRAIN_AFTER',  'asset_id': 'ASSET_W45_GALI12_DRAIN',       'region_id': 'REG_W45_GALI12', 'type': 'image', 'before_or_after': 'after',  'capture_date': '2025-03-22', 'url': 'frontend/static/evidence/after_w46_gali3_drain.png',     'source': 'MCD field inspector geo-tagged photo'},
    {'evidence_id': 'EVD_W45_PARK_BEFORE',         'asset_id': 'ASSET_W45_PARK',               'region_id': 'REG_W45',        'type': 'image', 'before_or_after': 'before', 'capture_date': '2023-11-01', 'url': 'frontend/static/evidence/before_w45_park.jpeg',          'source': 'MCD Inspection Report #2023-SHD-P04'},
    {'evidence_id': 'EVD_W45_PARK_AFTER',          'asset_id': 'ASSET_W45_PARK',               'region_id': 'REG_W45',        'type': 'image', 'before_or_after': 'after',  'capture_date': '2025-04-10', 'url': 'frontend/static/evidence/after_w45_park.jpeg',           'source': 'AMRUT monitoring team photo'},
    {'evidence_id': 'EVD_W45_ROAD_GALI7_BEFORE',   'asset_id': 'ASSET_W45_ROAD_GALI7',         'region_id': 'REG_W45_GALI7',  'type': 'image', 'before_or_after': 'before', 'capture_date': '2024-02-01', 'url': 'frontend/static/evidence/before_w45_gali7_road.jpeg',    'source': 'MCD Complaint Log #2024-SHD-R019'},
    {'evidence_id': 'EVD_W45_TOILET_BEFORE',       'asset_id': 'ASSET_W45_TOILET',             'region_id': 'REG_W45_MARKET_ROAD', 'type': 'image', 'before_or_after': 'before', 'capture_date': '2024-03-01', 'url': 'frontend/static/evidence/before_w45_toilet.jpeg', 'source': 'MCD Sanitation Report #2024-SHD-T07'},
    {'evidence_id': 'EVD_W45_PMAY_BEFORE',         'asset_id': 'ASSET_W45_PMAY_HOUSING_A',     'region_id': 'REG_W45_COLONY_Y', 'type': 'image', 'before_or_after': 'before', 'capture_date': '2023-11-15', 'url': 'frontend/static/evidence/before_w45_pmay.jpeg',        'source': 'DDA PMAY-U Sanction Report #2023-DDA-H45'},
    {'evidence_id': 'EVD_W45_STREETLIGHT_BEFORE',  'asset_id': 'ASSET_W45_GALI12_STREETLIGHT', 'region_id': 'REG_W45_GALI12',  'type': 'image', 'before_or_after': 'before', 'capture_date': '2024-01-20', 'url': 'frontend/static/evidence/before_w45_gali12_streetlight.jpeg', 'source': 'MCD Complaint Log #2024-SHD-L023'},
]

pd.DataFrame(evidence).to_csv(os.path.join(output_dir, "evidence.csv"), index=False)
print(f"  ✅ {len(evidence)} evidence records written")


# ─────────────────────────────────────────────────────────────────────────────
# 7. EVENTS
#    Sources: hardcoded milestones for demo assets
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7/7] Generating events.csv ...")

events = [
    {'event_id': 'EVT_W45_GALI7_DRAIN_COMPLETE',    'name': 'Drain construction completed — Gali No. 7',          'event_type': 'completion',    'date': '2025-03-22', 'asset_id': 'ASSET_W45_GALI7_DRAIN'},
    {'event_id': 'EVT_W45_GALI12_DRAIN_COMPLETE',   'name': 'Drain reconstruction completed — Gali No. 12',       'event_type': 'completion',    'date': '2025-03-22', 'asset_id': 'ASSET_W45_GALI12_DRAIN'},
    {'event_id': 'EVT_W45_PARK_INAUG',              'name': 'Community park inauguration — Ward 45',              'event_type': 'inauguration',  'date': '2025-04-10', 'asset_id': 'ASSET_W45_PARK'},
    {'event_id': 'EVT_W45_ROAD_GALI7_COMPLETE',     'name': 'Road resurfacing completed — Gali No. 7',            'event_type': 'completion',    'date': '2024-04-20', 'asset_id': 'ASSET_W45_ROAD_GALI7'},
    {'event_id': 'EVT_W45_TOILET_TENDER',           'name': 'Maintenance tender issued — Community Toilet',       'event_type': 'tender',        'date': '2024-06-01', 'asset_id': 'ASSET_W45_TOILET'},
    {'event_id': 'EVT_W45_PMAY_SANCTION',           'name': 'PMAY housing sanction — Colony Y Block A',          'event_type': 'sanction',      'date': '2023-11-15', 'asset_id': 'ASSET_W45_PMAY_HOUSING_A'},
    {'event_id': 'EVT_W45_STREETLIGHT_DEPLOY',      'name': 'Smart LED streetlight deployment — Gali No. 12',    'event_type': 'inauguration',  'date': '2025-01-15', 'asset_id': 'ASSET_W45_GALI12_STREETLIGHT'},
]

pd.DataFrame(events).to_csv(os.path.join(output_dir, "events.csv"), index=False)
print(f"  ✅ {len(events)} events written")


# ─────────────────────────────────────────────────────────────────────────────
# 8. UNSTRUCTURED EXTRACTED JSONs
#    Sources: data/resources/unstructured/extracted/*.json
#    Produced by: fetch_unstructured.py (runs AI extraction on PDFs + docs)
#    Each JSON has: entities[], relations[], source_file, source_type
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8/8] Folding in unstructured extracted data ...")

_EXTRACTED_DIR = _PROJECT_ROOT / "data" / "resources" / "unstructured" / "extracted"

# Confidence per source_type for unstructured data
_UNSTRUCTURED_CONFIDENCE = {
    "unstructured_llm": 0.7,
    "unstructured_rss": 0.6,
}

# ID counters for canonical ID generation
_u_counts = {"Asset": 0, "Region": 0, "Actor": 0, "Scheme": 0,
             "Beneficiary": 0, "Evidence": 0, "Event": 0}

# Track IDs already in the pipeline to avoid duplicate merges
_existing_ids = (
    {r["region_id"] for r in pd.read_csv(os.path.join(output_dir, "regions.csv")).to_dict("records")} |
    {s["scheme_id"] for s in pd.read_csv(os.path.join(output_dir, "schemes.csv")).to_dict("records")} |
    {a["actor_id"] for a in pd.read_csv(os.path.join(output_dir, "actors.csv")).to_dict("records")} |
    {a["asset_id"] for a in pd.read_csv(os.path.join(output_dir, "assets.csv")).to_dict("records")}
)

# Label → canonical list mapping
_label_lists = {
    "Scheme":      (schemes,       "scheme_id",      "SCH_U"),
    "Region":      (regions,       "region_id",       "REG_U"),
    "Actor":       (actors,        "actor_id",        "ACT_U"),
    "Asset":       (assets,        "asset_id",        "ASSET_U"),
    "Beneficiary": (beneficiaries, "beneficiary_id",  "BEN_U"),
    "Evidence":    (evidence,      "evidence_id",     "EVD_U"),
    "Event":       (events,        "event_id",        "EVT_U"),
}

# Valid enum values — reject AI hallucinations
_VALID_ASSET_TYPES   = {"drain","road","toilet","housing","park","streetlight","water_body","other"}
_VALID_ACTOR_TYPES   = {"government","contractor","elected_rep"}
_VALID_REGION_TYPES  = {"state","city","zone","ward","street"}

def _canonical_id(prefix, label, raw_id, source_label):
    """Generate a canonical pipeline ID from an AI-assigned raw_id."""
    slug = re.sub(r"[^a-z0-9]", "_", str(raw_id).lower())[:30].strip("_")
    return f"{prefix}{source_label[:8]}_{slug}"

u_files = sorted(_EXTRACTED_DIR.glob("*.json")) if _EXTRACTED_DIR.exists() else []

if not u_files:
    print("  ⚠️  No extracted JSON files found — run fetch_unstructured.py first")
else:
    u_ent_total = u_rel_total = 0
    for jf in u_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠️  Could not read {jf.name}: {e}")
            continue

        source_label = re.sub(r"[^a-z0-9]", "_", jf.stem.lower())[:12]
        source_type  = data.get("source_type", "unstructured_llm")
        base_conf    = _UNSTRUCTURED_CONFIDENCE.get(source_type, 0.7)

        # Build id remap: AI raw_id → canonical pipeline ID
        id_remap = {}
        ent_added = 0

        for ent in data.get("entities", []):
            label = ent.get("label", "")
            if label not in _label_lists:
                continue

            props   = ent.get("properties", {})
            name    = (props.get("name") or "").strip()
            if not name:
                continue

            _u_counts[label] = _u_counts.get(label, 0) + 1
            target_list, pk_field, prefix = _label_lists[label]
            raw_id   = ent.get("id", f"{label}_{_u_counts[label]}")
            canon_id = _canonical_id(prefix, label, raw_id, source_label)
            id_remap[raw_id] = canon_id

            if canon_id in _existing_ids:
                continue

            conf = float(props.get("confidence", base_conf))

            row = {pk_field: canon_id, "name": name,
                   "source_type": source_type, "confidence": conf,
                   "ingested_by": "fetch_unstructured"}

            # Label-specific fields
            if label == "Scheme":
                row.update({"ministry": props.get("ministry",""), "category": props.get("category","")})
            elif label == "Region":
                rtype = props.get("type","ward")
                row["type"] = rtype if rtype in _VALID_REGION_TYPES else "ward"
                row["parent_region_id"] = props.get("parent_region_id","REG_DELHI")
            elif label == "Actor":
                atype = props.get("type","government")
                row["type"] = atype if atype in _VALID_ACTOR_TYPES else "government"
                row["region_id"] = props.get("region_id","REG_DELHI")
            elif label == "Asset":
                atype = props.get("type","other")
                row["type"] = atype if atype in _VALID_ASSET_TYPES else "other"
                row.update({
                    "region_id":  props.get("region_id","REG_DELHI"),
                    "scheme_id":  props.get("scheme_id",""),
                    "actor_id":   props.get("actor_id",""),
                    "cost":       props.get("cost",""),
                    "status":     props.get("status",""),
                    "lat":        props.get("lat",""),
                    "lon":        props.get("lon",""),
                    "encroached": "",
                    "nature":     "",
                    "ownership":  "",
                    "image_url":  "",
                })
            elif label == "Beneficiary":
                row.update({"count": props.get("count",""), "description": props.get("description",""),
                            "scheme_id": props.get("scheme_id",""), "region_id": props.get("region_id","REG_DELHI")})
            elif label == "Evidence":
                row.update({"type": props.get("type","document"), "url": props.get("url",""),
                            "before_or_after": props.get("before_or_after",""), "capture_date": props.get("capture_date",""),
                            "asset_id": props.get("asset_id",""), "region_id": props.get("region_id","")})
            elif label == "Event":
                row.update({"event_type": props.get("event_type",""), "date": props.get("date",""),
                            "asset_id": props.get("asset_id","")})

            target_list.append(row)
            _existing_ids.add(canon_id)
            ent_added += 1

        u_ent_total += ent_added
        u_rel_total += len(data.get("relations", []))  # relations handled by load_seed_data via Neo4j ingest
        print(f"  ✅ {jf.name} — {ent_added} entities added")

    print(f"  ✅ Unstructured total: {u_ent_total} entities folded in from {len(u_files)} file(s)")

    # Re-write CSVs with unstructured entities appended
    pd.DataFrame(regions).to_csv(os.path.join(output_dir, "regions.csv"), index=False)
    pd.DataFrame(schemes).to_csv(os.path.join(output_dir, "schemes.csv"), index=False)
    pd.DataFrame(actors).to_csv(os.path.join(output_dir, "actors.csv"), index=False)
    pd.DataFrame(assets).to_csv(os.path.join(output_dir, "assets.csv"), index=False)
    pd.DataFrame(beneficiaries).to_csv(os.path.join(output_dir, "beneficiaries.csv"), index=False)
    pd.DataFrame(evidence).to_csv(os.path.join(output_dir, "evidence.csv"), index=False)
    pd.DataFrame(events).to_csv(os.path.join(output_dir, "events.csv"), index=False)
    print(f"  ✅ All 7 CSVs updated with unstructured entities")


# ─────────────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  SUCCESS — 7 CSVs written to:")
print(f"  {output_dir}")
print(f"{'='*60}")
print(f"\n✅ Next step: run validate.py to check data quality before loading into Neo4j")
