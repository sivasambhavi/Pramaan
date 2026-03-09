import pandas as pd
import json
import os
import re
import xml.etree.ElementTree as ET

# Output directory for formalized data
output_dir = "e:\\INDIA_INNOVATES\\Pramaan\\data\\resources\\data\\final_formalized"
resources_dir = "e:\\INDIA_INNOVATES\\Pramaan\\data\\resources"
os.makedirs(output_dir, exist_ok=True)

# --- 1. SCHEMES ---
print("Generating schemes.csv...")
schemes = [
    {'scheme_id': 'SCH_SFC', 'name': 'Local Development Grants - Roads & Drains (Delhi)', 'ministry': 'GNCTD/MCD', 'category': 'roads_drains'},
    {'scheme_id': 'SCH_SWACHH', 'name': 'Swachh Bharat Mission - Urban', 'ministry': 'MoHUA', 'category': 'sanitation'},
    {'scheme_id': 'SCH_PMAY', 'name': 'PMAY-Urban (Delhi)', 'ministry': 'MoHUA', 'category': 'housing'},
    {'scheme_id': 'SCH_LOCAL_LIGHTS', 'name': 'Urban Streetlight Improvement (Delhi)', 'ministry': 'GNCTD/MCD', 'category': 'streetlights'}
]
pd.DataFrame(schemes).to_csv(os.path.join(output_dir, "schemes.csv"), index=False)

# --- 2. REGIONS ---
print("Generating regions.csv...")
# Hierarchy: Delhi -> Zone -> Ward -> Street
regions = [
    {'region_id': 'REG_DELHI', 'name': 'Delhi', 'type': 'city', 'parent_region_id': ''},
    {'region_id': 'REG_SHAHDARA_SOUTH', 'name': 'Shahdara South Zone', 'type': 'zone', 'parent_region_id': 'REG_DELHI'}
]

# Load Wards from Census CSV
df_wards = pd.read_csv(os.path.join(resources_dir, "c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv"))
for _, row in df_wards.iterrows():
    w_num = re.search(r'\d+', str(row['Ward'])).group() if re.search(r'\d+', str(row['Ward'])) else "UNK"
    regions.append({
        'region_id': f"REG_W{w_num}",
        'name': row['Ward'],
        'type': 'ward',
        'parent_region_id': 'REG_SHAHDARA_SOUTH' # Simplified for demo
    })

# Add specific streets/gallis from user request for Ward 45
regions.extend([
    {'region_id': 'REG_W45_GALI7', 'name': 'Gali No. 7', 'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_MARKET_ROAD', 'name': 'Shahdara Market Road', 'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_BLOCKA', 'name': 'Block A Residential Pocket', 'type': 'street', 'parent_region_id': 'REG_W45'},
    {'region_id': 'REG_W45_COLONY_Y', 'name': 'Colony Y Housing Cluster', 'type': 'street', 'parent_region_id': 'REG_W45'}
])
pd.DataFrame(regions).to_csv(os.path.join(output_dir, "regions.csv"), index=False)

# --- 3. ACTORS ---
print("Generating actors.csv...")
actors = [
    {'actor_id': 'ACT_MCD_SHAHDARA_WORKS', 'name': 'MCD Shahdara South Works Dept', 'type': 'government', 'region_id': 'REG_SHAHDARA_SOUTH'},
    {'actor_id': 'ACT_MCD_SHAHDARA_SANITATION', 'name': 'MCD Shahdara Sanitation Dept', 'type': 'government', 'region_id': 'REG_SHAHDARA_SOUTH'},
    {'actor_id': 'ACT_MCD_ELECTRICAL', 'name': 'MCD Electrical Dept - Shahdara', 'type': 'government', 'region_id': 'REG_SHAHDARA_SOUTH'},
    {'actor_id': 'ACT_W45_COUNCILLOR', 'name': 'Ward 45 Councillor', 'type': 'elected_rep', 'region_id': 'REG_W45'}
]

# Extracting some contractors from tenders MD (simulated)
actors.extend([
    {'actor_id': 'ACT_CONTRACTOR_INFRA_1', 'name': 'ABC Infra Pvt Ltd', 'type': 'contractor', 'region_id': 'REG_W45'},
    {'actor_id': 'ACT_CONTRACTOR_LIGHTS_1', 'name': 'BrightLights Engineering', 'type': 'contractor', 'region_id': 'REG_W45'}
])
pd.DataFrame(actors).to_csv(os.path.join(output_dir, "actors.csv"), index=False)

# --- 4. ASSETS ---
print("Generating assets.csv...")
assets = []

# Example assets from user request (with local coordinates)
req_assets = [
    {'asset_id': 'ASSET_DRAIN_GALI7', 'name': 'Construction of storm-water drain in Gali No. 7, Shahdara', 'type': 'drain', 'region_id': 'REG_W45_GALI7', 'scheme_id': 'SCH_SFC', 'actor_id': 'ACT_MCD_SHAHDARA_WORKS', 'cost': 1200000, 'status': 'completed', 'lat': 28.6692, 'lon': 77.2945},
    {'asset_id': 'ASSET_ROAD_GALI7', 'name': 'Resurfacing of internal road in Gali No. 7, Shahdara', 'type': 'road', 'region_id': 'REG_W45_GALI7', 'scheme_id': 'SCH_SFC', 'actor_id': 'ACT_CONTRACTOR_INFRA_1', 'cost': 900000, 'status': 'completed', 'lat': 28.6695, 'lon': 77.2948},
    {'asset_id': 'ASSET_TOILET_MARKET', 'name': 'Renovation of public toilet near Shahdara Market', 'type': 'toilet', 'region_id': 'REG_W45_MARKET_ROAD', 'scheme_id': 'SCH_SWACHH', 'actor_id': 'ACT_MCD_SHAHDARA_SANITATION', 'cost': 800000, 'status': 'completed', 'lat': 28.6685, 'lon': 77.2955},
    {'asset_id': 'ASSET_HOUSING_COLONYY', 'name': 'PMAY-Urban housing cluster in Colony Y (30 units)', 'type': 'housing', 'region_id': 'REG_W45_COLONY_Y', 'scheme_id': 'SCH_PMAY', 'actor_id': 'ACT_MCD_SHAHDARA_WORKS', 'cost': 30000000, 'status': 'completed', 'lat': 28.6670, 'lon': 77.2960},
    {'asset_id': 'ASSET_LIGHTS_BLOCKA', 'name': 'LED streetlight upgrade on Block A internal roads', 'type': 'streetlight', 'region_id': 'REG_W45_BLOCKA', 'scheme_id': 'SCH_LOCAL_LIGHTS', 'actor_id': 'ACT_CONTRACTOR_LIGHTS_1', 'cost': 600000, 'status': 'completed', 'lat': 28.6700, 'lon': 77.2965}
]
assets.extend(req_assets)

# Parse KML Water Bodies into the new schema
try:
    tree = ET.parse(os.path.join(resources_dir, "watercensusmap.kml"))
    root = tree.getroot()
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    for i, placemark in enumerate(root.findall('.//kml:Placemark', namespace)):
        ext_data = placemark.find('.//kml:SchemaData', namespace)
        if ext_data is None: continue
        
        data_dict = {}
        for simple_data in ext_data.findall('kml:SimpleData', namespace):
            data_dict[simple_data.attrib['name']] = simple_data.text
        
        asset_id = f"ASSET_WB_{data_dict.get('objectid', 'UNK')}"
        village = data_dict.get('village', 'Unknown')
        
        # Extract coordinates
        point = placemark.find('.//kml:Point/kml:coordinates', namespace)
        lat, lon = 28.6692, 77.2945 # Default to Shahdara
        if point is not None:
            coords = point.text.strip().split(',')
            if len(coords) >= 2:
                lon = float(coords[0])
                lat = float(coords[1])
        
        assets.append({
            'asset_id': asset_id,
            'name': f"Water Body - {village}",
            'type': 'water_body',
            'region_id': 'REG_W45',
            'scheme_id': 'SCH_SFC',
            'actor_id': 'ACT_MCD_SHAHDARA_WORKS',
            'cost': 500000,
            'status': 'completed',
            'lat': lat,
            'lon': lon
        })
        if i >= 50: break # Only 50 for demo
except Exception as e:
    print(f"KML skip: {e}")

pd.DataFrame(assets).to_csv(os.path.join(output_dir, "assets.csv"), index=False)

# --- 5. BENEFICIARIES ---
print("Generating beneficiaries.csv...")
beneficiaries = [
    {'beneficiary_id': 'BEN_GALI7_DRAIN', 'scheme_id': 'SCH_SFC', 'region_id': 'REG_W45_GALI7', 'count': 100, 'description': 'Households protected from waterlogging in Gali No. 7'},
    {'beneficiary_id': 'BEN_GALI7_ROAD', 'scheme_id': 'SCH_SFC', 'region_id': 'REG_W45_GALI7', 'count': 100, 'description': 'Households benefiting from smoother internal road in Gali No. 7'},
    {'beneficiary_id': 'BEN_MARKET_TOILET', 'scheme_id': 'SCH_SWACHH', 'region_id': 'REG_W45_MARKET_ROAD', 'count': 250, 'description': 'Approximate daily users of renovated public toilet near Shahdara Market'},
    {'beneficiary_id': 'BEN_COLONYY_PMAY', 'scheme_id': 'SCH_PMAY', 'region_id': 'REG_W45_COLONY_Y', 'count': 120, 'description': 'Approximate residents in 30 PMAY housing units in Colony Y'},
    {'beneficiary_id': 'BEN_BLOCKA_LIGHTS', 'scheme_id': 'SCH_LOCAL_LIGHTS', 'region_id': 'REG_W45_BLOCKA', 'count': 180, 'description': 'Households benefiting from improved night-time lighting in Block A'}
]
pd.DataFrame(beneficiaries).to_csv(os.path.join(output_dir, "beneficiaries.csv"), index=False)

# --- 6. EVIDENCE ---
print("Generating evidence.csv...")
evidence = [
    {'evidence_id': 'EVD_DRAIN_GALI7_BEFORE', 'asset_id': 'ASSET_DRAIN_GALI7', 'region_id': 'REG_W45_GALI7', 'type': 'image', 'url': 'evidence/gali7_drain_before.jpg', 'before_or_after': 'before', 'capture_date': '2024-01-05'},
    {'evidence_id': 'EVD_DRAIN_GALI7_AFTER', 'asset_id': 'ASSET_DRAIN_GALI7', 'region_id': 'REG_W45_GALI7', 'type': 'image', 'url': 'evidence/gali7_drain_after.jpg', 'before_or_after': 'after', 'capture_date': '2024-03-22'},
    {'evidence_id': 'EVD_ROAD_GALI7_BEFORE', 'asset_id': 'ASSET_ROAD_GALI7', 'region_id': 'REG_W45_GALI7', 'type': 'image', 'url': 'evidence/gali7_road_before.jpg', 'before_or_after': 'before', 'capture_date': '2024-01-25'},
    {'evidence_id': 'EVD_ROAD_GALI7_AFTER', 'asset_id': 'ASSET_ROAD_GALI7', 'region_id': 'REG_W45_GALI7', 'type': 'image', 'url': 'evidence/gali7_road_after.jpg', 'before_or_after': 'after', 'capture_date': '2024-04-20'}
]

# Map working proxy images to some water bodies (First 10)
if len(assets) > 5:
    for i, asset in enumerate(assets[5:15]):
        evidence.append({
            'evidence_id': f"EVD_WB_{i}_AFTER",
            'asset_id': asset['asset_id'],
            'region_id': asset['region_id'],
            'type': 'image',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/e/e4/Mungeshpur_Drain%2C_Delhi.jpg',
            'before_or_after': 'after',
            'capture_date': '2024-03-01'
        })

pd.DataFrame(evidence).to_csv(os.path.join(output_dir, "evidence.csv"), index=False)

# --- 7. EVENTS ---
print("Generating events.csv...")
events = [
    {'event_id': 'EVT_DRAIN_GALI7_COMPLETION', 'name': 'Completion of drain in Gali No. 7', 'event_type': 'completion', 'date': '2024-03-20', 'asset_id': 'ASSET_DRAIN_GALI7'},
    {'event_id': 'EVT_ROAD_GALI7_COMPLETION', 'name': 'Completion of road resurfacing', 'event_type': 'completion', 'date': '2024-04-15', 'asset_id': 'ASSET_ROAD_GALI7'},
    {'event_id': 'EVT_TOILET_MARKET_INAUG', 'name': 'Inauguration of renovated public toilet', 'event_type': 'inauguration', 'date': '2024-03-18', 'asset_id': 'ASSET_TOILET_MARKET'},
    {'event_id': 'EVT_HOUSING_COLONYY_HANDOVER', 'name': 'Handover of PMAY housing units', 'event_type': 'handover', 'date': '2024-03-10', 'asset_id': 'ASSET_HOUSING_COLONYY'},
    {'event_id': 'EVT_LIGHTS_BLOCKA_SWITCHON', 'name': 'Switch-on ceremony for LED streetlights', 'event_type': 'inauguration', 'date': '2024-04-12', 'asset_id': 'ASSET_LIGHTS_BLOCKA'}
]
pd.DataFrame(events).to_csv(os.path.join(output_dir, "events.csv"), index=False)

print(f"\nSUCCESS: Formalized 7-table datasets generated in {output_dir}")
