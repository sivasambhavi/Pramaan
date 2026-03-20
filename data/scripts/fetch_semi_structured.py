"""
PRAMAAN — Step 1b-semi: Parse Semi-Structured Files
Reads all files from data/resources/semi_structured/ (KML, xlsx, md),
parses them deterministically (no AI), and saves normalized rows to
data/resources/semi_structured/extracted/*.json

Currently parses:
  - delhi_jal_dharohar_2023.kml       → water_bodies.json      (893 water body assets)
  - sh_north_zone_duty_roaster_*.xlsx → parks_roster.json       (750 parks + 23 supervisors)
  - delhi_tenders_data.md             → tenders.json            (contractor actors)

Run before: transform_to_7_table_schema.py
Re-run safe: existing extracted files are overwritten with fresh parse.
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]

SEMI_DIR      = _PROJECT_ROOT / "data" / "resources" / "semi_structured"
EXTRACTED_DIR = SEMI_DIR / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("  PRAMAAN — Semi-Structured Extraction (Step 1b-semi)")
print("=" * 60)


# ── 1. KML — Delhi Jal Dharohar 2023 (water bodies) ──────────────────────────

def parse_water_bodies_kml() -> list[dict]:
    kml_path = SEMI_DIR / "delhi_jal_dharohar_2023.kml"
    if not kml_path.exists():
        print("  ⚠️  delhi_jal_dharohar_2023.kml missing — skipping water bodies")
        return []

    WB_TYPE_MAP = {
        '01': 'Lake/Pond', '02': 'Tank', '03': 'Reservoir',
        '05': 'River/Stream', '06': 'Other Water Body',
    }

    tree = ET.parse(kml_path)
    root = tree.getroot()
    ns   = {'kml': 'http://www.opengis.net/kml/2.2'}

    rows = []
    skipped = 0
    for placemark in root.findall('.//kml:Placemark', ns):
        ext = placemark.find('.//kml:SchemaData', ns)
        if ext is None:
            continue
        d = {sd.attrib['name']: (sd.text or '').strip()
             for sd in ext.findall('kml:SimpleData', ns)}

        obj_id = d.get('objectid', '')
        if not obj_id:
            continue

        lat_s, lon_s = d.get('latitude', ''), d.get('longitude', '')
        try:
            lat, lon = float(lat_s), float(lon_s)
        except ValueError:
            skipped += 1
            continue

        district   = d.get('district', 'Unknown').title()
        village    = d.get('village', 'Unknown').title()
        wb_type    = WB_TYPE_MAP.get(d.get('water_body_type', ''), 'Water Body')
        encroached = d.get('waterbody_encroached', 'Unknown')
        nature     = d.get('water_body_nature', '')
        ownership  = d.get('water_body_ownership', '')
        image_url  = d.get('image_path', '')
        status     = 'encroached' if encroached == 'Yes' else 'completed'

        rows.append({
            'objectid':   obj_id,
            'name':       f"{wb_type} — {village}, {district}",
            'type':       'water_body',
            'district':   district,
            'village':    village,
            'wb_type':    wb_type,
            'lat':        lat,
            'lon':        lon,
            'encroached': encroached,
            'nature':     nature,
            'ownership':  ownership,
            'image_url':  image_url,
            'status':     status,
        })

    enc_count = sum(1 for r in rows if r['encroached'] == 'Yes')
    print(f"  ✅ {len(rows)} water bodies parsed ({enc_count} encroached, {skipped} skipped — no coords)")
    return rows


# ── 2. xlsx — Mali Duty Roster (parks + supervisors) ─────────────────────────

def parse_parks_roster() -> dict:
    roster_glob = list(SEMI_DIR.glob("sh_north_zone_duty_roaster_*.xlsx"))
    if not roster_glob:
        print("  ⚠️  mali duty roster xlsx missing — skipping parks")
        return {"parks": [], "supervisors": []}

    roster_path = roster_glob[0]
    df_raw = pd.read_excel(roster_path, header=None)
    df_raw.columns = ['sno', 'zone', 'ward_no', 'park_name', 'area_acres', 'lat', 'lon',
                      'supervisor', 'supervisor_phone', 'mali_names', 'mali_phones']
    df_raw = df_raw.iloc[1:].copy()  # skip title row
    df_raw['ward_no'] = pd.to_numeric(df_raw['ward_no'], errors='coerce')
    df = df_raw.dropna(subset=['park_name', 'ward_no']).copy()

    parks = []
    for _, row in df.iterrows():
        ward_no   = int(row['ward_no'])
        park_name = str(row['park_name']).strip()
        sno       = str(row['sno']).strip()

        try:
            lat = float(row['lat'])
            lon = float(row['lon'])
            if lat > 90:
                lat = lat / 1_000_000
            if lon > 180:
                lon = lon / 1_000_000
            if not (28.4 <= lat <= 28.9 and 76.8 <= lon <= 77.4):
                lat = lon = None
        except (ValueError, TypeError):
            lat = lon = None

        try:
            area = float(row['area_acres']) if pd.notna(row['area_acres']) else None
        except (ValueError, TypeError):
            area = None

        supervisor = str(row['supervisor']).strip() if pd.notna(row['supervisor']) else ''

        parks.append({
            'sno':        sno,
            'ward_no':    ward_no,
            'region_id':  f"REG_W{ward_no}",
            'park_name':  park_name,
            'area_acres': area,
            'lat':        lat,
            'lon':        lon,
            'supervisor': supervisor,
        })

    # Unique supervisors
    seen_supervisors = set()
    supervisors = []
    for p in parks:
        name = p['supervisor']
        if name and name not in seen_supervisors:
            seen_supervisors.add(name)
            supervisors.append({'name': name})

    print(f"  ✅ {len(parks)} parks parsed across {df['ward_no'].nunique()} wards")
    print(f"  ✅ {len(supervisors)} unique supervisors extracted")
    return {"parks": parks, "supervisors": supervisors}


# ── 3. md — Delhi Tenders (contractor actors) ─────────────────────────────────

def parse_tenders_md() -> list[dict]:
    md_path = SEMI_DIR / "delhi_tenders_data.md"
    if not md_path.exists():
        print("  ⚠️  delhi_tenders_data.md missing — skipping tenders")
        return []

    content = md_path.read_text(encoding='utf-8')
    orgs = re.findall(r'\|\s*\d+\s*\|\s*([^|]+)\|', content)

    rows = []
    seen = set()
    for org in orgs[:15]:
        name = org.strip()
        if not name or len(name) < 3:
            continue
        actor_id = "ACT_" + re.sub(r'[^A-Z0-9]', '_', name.upper())[:30].strip('_')
        if actor_id in seen:
            continue
        seen.add(actor_id)
        rows.append({'actor_id': actor_id, 'name': name})

    print(f"  ✅ {len(rows)} contractors extracted from delhi_tenders_data.md")
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n[1/3] Parsing water bodies (KML) ...")
    water_bodies = parse_water_bodies_kml()
    out = EXTRACTED_DIR / "water_bodies.json"
    out.write_text(json.dumps({"rows": water_bodies, "source_file": "delhi_jal_dharohar_2023.kml",
                                "source_type": "semi_structured_kml", "confidence": 0.95},
                              indent=2, ensure_ascii=False))
    print(f"  → saved to {out.name}")

    print("\n[2/3] Parsing parks roster (xlsx) ...")
    roster = parse_parks_roster()
    out = EXTRACTED_DIR / "parks_roster.json"
    out.write_text(json.dumps({"parks": roster["parks"], "supervisors": roster["supervisors"],
                                "source_file": "sh_north_zone_duty_roaster_*.xlsx",
                                "source_type": "semi_structured_xlsx", "confidence": 0.9},
                              indent=2, ensure_ascii=False))
    print(f"  → saved to {out.name}")

    print("\n[3/3] Parsing tenders (md) ...")
    tenders = parse_tenders_md()
    out = EXTRACTED_DIR / "tenders.json"
    out.write_text(json.dumps({"rows": tenders, "source_file": "delhi_tenders_data.md",
                                "source_type": "semi_structured_md", "confidence": 0.85},
                              indent=2, ensure_ascii=False))
    print(f"  → saved to {out.name}")

    print(f"""
{'=' * 60}
  Semi-structured extraction complete
  Water bodies : {len(water_bodies)}
  Parks        : {len(roster['parks'])}
  Supervisors  : {len(roster['supervisors'])}
  Tenders      : {len(tenders)}
  Output       : {EXTRACTED_DIR}
{'=' * 60}
✅ Next: run transform_to_7_table_schema.py
""")


if __name__ == "__main__":
    main()
