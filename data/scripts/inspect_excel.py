import pandas as pd
import os

excel_files = [
    "sh_north_zone_duty_roaster_of_mali_2512011212291229.xlsx",
    "beat_list_shn_2511141026251125.xlsx"
]

for f in excel_files:
    print(f"\n{'='*50}\nFILE: {f}")
    path = os.path.join('e:\\Pramaan', f)
    try:
        xl = pd.ExcelFile(path)
        print("Sheet names:", xl.sheet_names)
        for sheet in xl.sheet_names:
            print(f"\n--- SHEET: {sheet} ---")
            df = pd.read_excel(path, sheet_name=sheet, header=None, nrows=20)
            print(df.to_string())
    except Exception as e:
        print(f"Error reading {f}: {e}")
