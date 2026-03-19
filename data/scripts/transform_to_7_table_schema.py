"""
transform_to_7_table_schema.py — PRAMAAN Step 2: Transform

Reads raw data from data/resources/ (API JSONs, KML, CSV, MD files)
and normalizes everything into the 7-table canonical schema:

    schemes.csv, regions.csv, actors.csv, assets.csv,
    beneficiaries.csv, evidence.csv, events.csv

Output lands in: data/resources/data/final_formalized/

Run after: fetch_govdata.py
Run before: validate.py  →  load_seed_data.py
"""

import pandas as pd
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Dynamic cross-platform paths ──────────────────────────────────────────────
# This script lives at: data/scripts/transform_to_7_table_schema.py
# Project root is 2 levels up.
_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]          # Pramaan/
resources_dir = str(_PROJECT_ROOT / "data" / "resources")
output_dir    = str(_PROJECT_ROOT / "data" / "resources" / "data" / "final_formalized")
os.makedirs(output_dir, exist_ok=True)

def _load_json(filename):
    """Load a JSON file from resources_dir. Returns {} on missing file."""
    path = os.path.join(resources_dir, filename)
    if not os.path.exists(path):
        print(f"  ⚠️  Missing: {filename} — skipping (run fetch_govdata.py first)")
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
    {'region_id': 'REG_DELHI',          'name': 'Delhi',               'type': 'city',  'parent_region_id': ''},
    {'region_id': 'REG_SHAHDARA_NORTH', 'name': 'Shahdara North Zone', 'type': 'zone',  'parent_region_id': 'REG_DELHI'},
    {'region_id': 'REG_SHAHDARA_SOUTH', 'name': 'Shahdara South Zone', 'type': 'zone',  'parent_region_id': 'REG_DELHI'},
]

ward_csv = os.path.join(resources_dir, "c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv")
if os.path.exists(ward_csv):
    df_wards = pd.read_csv(ward_csv)
    seen_ward_ids = set()
    ward_count = 0
    for _, row in df_wards.iterrows():
        match = re.search(r'\d+', str(row['Ward']))
        w_num = match.group() if match else "UNK"
        region_id = f"REG_W{w_num}"
        if region_id in seen_ward_ids:
            continue   # deduplicate — census CSV has multiple rows per ward
        seen_ward_ids.add(region_id)
        regions.append({
            'region_id':        region_id,
            'name':             row['Ward'],
            'type':             'ward',
            'parent_region_id': 'REG_SHAHDARA_SOUTH',  # simplified for demo
        })
        ward_count += 1
    print(f"  ✅ {ward_count} unique wards loaded from census CSV (deduplicated)")
else:
    print("  ⚠️  Ward census CSV missing — only base regions written")

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

# Extract contractors from delhi_tenders_data.md
tenders_path = os.path.join(resources_dir, "delhi_tenders_data.md")
if os.path.exists(tenders_path):
    with open(tenders_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Pull org names from markdown table rows: "| N | Org Name |"
    orgs = re.findall(r'\|\s*\d+\s*\|\s*([^|]+)\|', content)
    seen_ids = {a["actor_id"] for a in actors}
    added = 0
    for org in orgs[:15]:
        name = org.strip()
        if not name or len(name) < 3:
            continue
        # Canonical ID: ACT_ + uppercase letters only
        actor_id = "ACT_" + re.sub(r'[^A-Z0-9]', '_', name.upper())[:30].strip('_')
        if actor_id in seen_ids:
            continue
        actors.append({'actor_id': actor_id, 'name': name, 'type': 'contractor', 'region_id': 'REG_DELHI'})
        seen_ids.add(actor_id)
        added += 1
    print(f"  ✅ {added} contractors extracted from delhi_tenders_data.md")
else:
    print("  ⚠️  delhi_tenders_data.md missing — only base actors written")

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

# ── Parse KML water bodies ─────────────────────────────────────────────────
kml_path = os.path.join(resources_dir, "watercensusmap.kml")
kml_added = 0
if os.path.exists(kml_path):
    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
        ns   = {'kml': 'http://www.opengis.net/kml/2.2'}
        for i, placemark in enumerate(root.findall('.//kml:Placemark', ns)):
            ext = placemark.find('.//kml:SchemaData', ns)
            if ext is None:
                continue
            data_dict = {sd.attrib['name']: sd.text for sd in ext.findall('kml:SimpleData', ns)}
            obj_id    = data_dict.get('objectid', str(i))
            village   = data_dict.get('village', 'Unknown')
            lat, lon  = 28.6692, 77.2945
            point = placemark.find('.//kml:Point/kml:coordinates', ns)
            if point is not None:
                parts = point.text.strip().split(',')
                if len(parts) >= 2:
                    lon, lat = float(parts[0]), float(parts[1])
            assets.append({
                'asset_id':  f"ASSET_WB_{obj_id}",
                'name':      f"Water Body — {village}",
                'type':      'water_body',
                'region_id': 'REG_W45',
                'scheme_id': 'SCH_AMRUT',
                'actor_id':  'ACT_MCD_SHAHDARA_WORKS',
                'cost':      500000,
                'status':    'completed',
                'lat':       lat,
                'lon':       lon,
            })
            kml_added += 1
            if kml_added >= 50:
                break
        print(f"  ✅ {kml_added} water body assets from KML")
    except Exception as e:
        print(f"  ⚠️  KML parse error: {e}")
else:
    print("  ⚠️  watercensusmap.kml missing")

pd.DataFrame(assets).to_csv(os.path.join(output_dir, "assets.csv"), index=False)
print(f"  ✅ {len(assets)} total assets written")


# ─────────────────────────────────────────────────────────────────────────────
# 5. BENEFICIARIES
#    Sources: hardcoded (partially mocked for demo)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/7] Generating beneficiaries.csv ...")

beneficiaries = [
    {'beneficiary_id': 'BEN_W45_GALI7_DRAIN',   'asset_id': 'ASSET_W45_GALI7_DRAIN',        'scheme_id': 'SCH_SFC',          'region_id': 'REG_W45_GALI7',       'count': 100,  'description': 'Households protected from waterlogging — Gali No. 7'},
    {'beneficiary_id': 'BEN_W45_GALI12_DRAIN',  'asset_id': 'ASSET_W45_GALI12_DRAIN',       'scheme_id': 'SCH_AMRUT',        'region_id': 'REG_W45_GALI12',      'count': 120,  'description': 'Households benefiting from drain — Gali No. 12'},
    {'beneficiary_id': 'BEN_W45_ROAD_GALI7',    'asset_id': 'ASSET_W45_ROAD_GALI7',         'scheme_id': 'SCH_SFC',          'region_id': 'REG_W45_GALI7',       'count': 100,  'description': 'Households benefiting from road resurfacing — Gali No. 7'},
    {'beneficiary_id': 'BEN_W45_TOILET',        'asset_id': 'ASSET_W45_TOILET',             'scheme_id': 'SCH_SWACHH',       'region_id': 'REG_W45_MARKET_ROAD', 'count': 250,  'description': 'Daily users of community toilet — Shahdara Market'},
    {'beneficiary_id': 'BEN_W45_PMAY',         'asset_id': 'ASSET_W45_PMAY_HOUSING_A',     'scheme_id': 'SCH_PMAY',         'region_id': 'REG_W45_COLONY_Y',    'count': 120,  'description': 'Residents in 30 PMAY units — Colony Y'},
    {'beneficiary_id': 'BEN_W45_LIGHTS',       'asset_id': 'ASSET_W45_GALI12_STREETLIGHT', 'scheme_id': 'SCH_LOCAL_LIGHTS', 'region_id': 'REG_W45_GALI12',      'count': 180,  'description': 'Households with improved night lighting — Gali No. 12'},
    {'beneficiary_id': 'BEN_W45_PARK',         'asset_id': 'ASSET_W45_PARK',               'scheme_id': 'SCH_AMRUT',        'region_id': 'REG_W45',             'count': 2000, 'description': 'Ward 45 residents with access to community park'},
]

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
# Done
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  SUCCESS — 7 CSVs written to:")
print(f"  {output_dir}")
print(f"{'='*60}")
print(f"\n✅ Next step: run validate.py to check data quality before loading into Neo4j")
