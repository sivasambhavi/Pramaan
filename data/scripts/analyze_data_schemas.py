import pandas as pd
import json
import os

files = [
    "f1a46aa8-123b-41f9-b267-31da999081ba.csv",
    "c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv",
    "sh_north_zone_duty_roaster_of_mali_2512011212291229.xlsx",
    "beat_list_shn_2511141026251125.xlsx",
    "amrut_storm_water_drainage.json",
    "pmay_housing_data.json",
    "sbm_toilets.json",
    "statewise_allocation.json"
]

results = {}

for f in files:
    ext = os.path.splitext(f)[1]
    path = os.path.join('e:\\Pramaan', f)
    if not os.path.exists(path):
        continue
    file_info = {"filename": f}
    try:
        if ext == '.csv':
            df = pd.read_csv(path, nrows=5)
            file_info["columns"] = list(df.columns)
            file_info["sample"] = df.head(1).to_dict('records')
        elif ext == '.xlsx':
            df = pd.read_excel(path, nrows=5)
            file_info["columns"] = list(df.columns)
            file_info["sample"] = df.head(1).to_dict('records')
        elif ext == '.json':
            with open(path, 'r', encoding='utf-8') as fp:
                d = json.load(fp)
            if 'records' in d and len(d['records']) > 0:
                file_info["columns"] = list(d['records'][0].keys())
                file_info["sample"] = d['records'][0]
            else:
                file_info["json_keys"] = list(d.keys())
        results[f] = file_info
    except Exception as e:
        results[f] = {"error": str(e)}

with open('e:\\Pramaan\\schema_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=4)
print("Analysis saved to schema_analysis.json")
