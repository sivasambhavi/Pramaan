import pandas as pd
import json
import os
import re

# Output directory
output_dir = "e:\\Pramaan\\resources\\data\\final"
os.makedirs(output_dir, exist_ok=True)

# 1. REGIONS (Wards & Towns)
print("Creating regions.csv...")
# Ward Population
df_wards = pd.read_csv("e:\\Pramaan\\resources\\c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv")
df_wards['ward_id'] = df_wards['Ward'].apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else x)
df_wards['type'] = 'Ward'

# Town Metadata (Aggregated from CSV)
df_towns = pd.read_csv("e:\\Pramaan\\resources\\f1a46aa8-123b-41f9-b267-31da999081ba.csv")
# For MVP, we map DMC(U) to Ward level data for proof of concept
df_towns['region_id'] = df_towns['Town Code']
df_towns['type'] = 'Town'

# Unified Regions (Wards + Towns)
regions = []
for _, row in df_wards.iterrows():
    regions.append({
        'id': f"WARD_{row['ward_id']}",
        'name': row['Ward'],
        'type': 'Ward',
        'population': row['Population'],
        'parent_id': 'DELHI_NCT'
    })
pd.DataFrame(regions).to_csv(os.path.join(output_dir, "regions.csv"), index=False)

# 2. ACTORS (Agencies & Personnel)
print("Creating actors.csv...")
actors = []

# Organizations from Tenders MD
tenders_path = "e:\\Pramaan\\resources\\delhi_tenders_data.md"
if os.path.exists(tenders_path):
    with open(tenders_path, 'r') as f:
        content = f.read()
    # Extract Organization names from table
    orgs = re.findall(r'\| \d+ \| ([^|]+) \|', content)
    for org in orgs[:10]: # Top 10 for MVP
        name = org.strip()
        actors.append({
            'id': f"ORG_{re.sub(r'[^A-Z]', '', name.upper())}",
            'name': name,
            'type': 'Agency',
            'role': 'Implementation'
        })

# Personnel from Excel Duty Roaster (Malis)
try:
    df_mali = pd.read_excel("e:\\Pramaan\\resources\\sh_north_zone_duty_roaster_of_mali_2512011212291229.xlsx", header=None, skiprows=5)
    # Finding names in the sheet (approximate extraction for demo)
    names = df_mali[1].dropna().unique()
    for name in names[:10]:
        actors.append({
            'id': f"ACTOR_{re.sub(r'[^A-Z]', '', str(name).upper())}",
            'name': name,
            'type': 'Individual',
            'role': 'Mali/Frontline'
        })
except: pass

pd.DataFrame(actors).to_csv(os.path.join(output_dir, "actors.csv"), index=False)

# 3. SCHEMES
print("Creating schemes.csv...")
schemes = [
    {'id': 'S_AMRUT', 'name': 'AMRUT', 'ministry': 'MoHUA', 'focus': 'Infrastructure'},
    {'id': 'S_PMAY', 'name': 'PMAY-U', 'ministry': 'MoHUA', 'focus': 'Housing'},
    {'id': 'S_SBM', 'name': 'Swachh Bharat Mission', 'ministry': 'MoHUA', 'focus': 'Sanitation'}
]
pd.DataFrame(schemes).to_csv(os.path.join(output_dir, "schemes.csv"), index=False)

# 4. ASSETS
print("Creating assets.csv...")
assets = []

# Drainage Assets from AMRUT JSON
with open("e:\\Pramaan\\resources\\amrut_storm_water_drainage.json", "r") as f:
    amrut_data = json.load(f)
for rec in amrut_data['records']:
    if rec['state_ut'] == 'Delhi':
        assets.append({
            'id': 'ASSET_AMRUT_DRAIN_DELHI',
            'name': 'Storm Water Drainage Project',
            'type': 'Drainage',
            'scheme_id': 'S_AMRUT',
            'ward_id': 'WARD_45', # Demo ward
            'status': 'Completed',
            'cost_lakhs': rec['total___amount']
        })

# Housing Assets from PMAY JSON
with open("e:\\Pramaan\\resources\\pmay_housing_data.json", "r") as f:
    pmay_data = json.load(f)
for rec in pmay_data['records']:
    if rec['state_ut'] == 'Delhi':
        assets.append({
            'id': 'ASSET_PMAY_HOUSES_DELHI',
            'name': 'PMAY Housing Cluster',
            'type': 'Housing',
            'scheme_id': 'S_PMAY',
            'ward_id': 'WARD_45',
            'status': 'Occupied',
            'count': rec['houses_as_on_31_12_2024___occupied']
        })

pd.DataFrame(assets).to_csv(os.path.join(output_dir, "assets.csv"), index=False)

# 5. BENEFICIARIES (Aggregated)
print("Creating beneficiaries.csv...")
# For hackathon, we link aggregated population as beneficiaries
ben = [
    {'id': 'BEN_W45_ALL', 'type': 'Aggregated', 'count': 55512, 'ward_id': 'WARD_45'}
]
pd.DataFrame(ben).to_csv(os.path.join(output_dir, "beneficiaries.csv"), index=False)

# 6. EVIDENCE (Empty for now, for next engineer to add manual URLs)
pd.DataFrame(columns=['id', 'asset_id', 'type', 'url']).to_csv(os.path.join(output_dir, "evidence.csv"), index=False)

print("\nSUCCESS: All unified datasets generated in e:\\Pramaan\\data\\final")
