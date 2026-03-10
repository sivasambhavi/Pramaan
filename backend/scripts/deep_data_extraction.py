import json
import pandas as pd
from pathlib import Path
import re

BASE_DIR = Path('E:/INDIA_INNOVATES/Pramaan/data/resources')
OUT_DIR = BASE_DIR / 'data' / 'final_formalized'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. PMAY Data and AMRUT Data into scheme_allocations.csv
allocations = []

pmay_path = BASE_DIR / 'pmay_housing_data.json'
if pmay_path.exists():
    with open(pmay_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for rec in data.get('records', []):
            if rec.get('category') in ['States', 'Union Territories'] and 'total' not in rec.get('state_ut', '').lower():
                state = rec.get('state_ut')
                completed = rec.get('houses_as_on_31_12_2024___completed', 0)
                occupied = rec.get('houses_as_on_31_12_2024___occupied', 0)
                if completed != 'NA':
                    allocations.append({
                        'allocation_id': f"pmay_{state.lower().replace(' ', '_')}",
                        'scheme_id': 'sch_pmay_u',
                        'region_name': state,
                        'total_allocated': float(completed) * 1.5, # mock target
                        'total_completed': float(completed),
                        'unit': 'houses'
                    })

amrut_path = BASE_DIR / 'amrut_storm_water_drainage.json'
if amrut_path.exists():
    with open(amrut_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for rec in data.get('records', []):
            if rec.get('state_ut') != 'Grand Total':
                state = list(rec.values())[1]  # state_ut
                if state == 'NCT of Delhi': state = 'Delhi'
                comp_amt = rec.get('work_completed___amount', 0)
                prog_amt = rec.get('work_in_progress___amount', 0)
                if comp_amt == 'NA': comp_amt = 0
                if prog_amt == 'NA': prog_amt = 0
                allocations.append({
                    'allocation_id': f"amrut_{state.lower().replace(' ', '_')}",
                    'scheme_id': 'sch_amrut_2',
                    'region_name': state,
                    'total_allocated': float(comp_amt) + float(prog_amt),
                    'total_completed': float(comp_amt),
                    'unit': 'crores_inr'
                })

pd.DataFrame(allocations).to_csv(OUT_DIR / 'scheme_allocations.csv', index=False)
print(f"Wrote {len(allocations)} allocations to scheme_allocations.csv")

# 2. Delhi Tenders Data into actors_current.csv
actors = []
md_path = BASE_DIR / 'delhi_tenders_data.md'
if md_path.exists():
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if '|' in line and 'Organisation Name' not in line and '---' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    org = parts[2]
                    tenders = parts[3]
                    val = parts[4].replace(',', '')
                    if org and tenders.isdigit():
                        actor_id_str = re.sub(r'[^a-z0-9]', '', org.lower())
                        actors.append({
                            'actor_id': f"act_{actor_id_str}",
                            'name': org,
                            'type': 'Government Agency',
                            'region_id': 'reg_delhi',
                            'total_tenders': int(tenders),
                            'budget_lakhs': float(val) if val else 0.0
                        })

pd.DataFrame(actors).to_csv(OUT_DIR / 'actors_enriched.csv', index=False)
print(f"Wrote {len(actors)} actors to actors_enriched.csv")
