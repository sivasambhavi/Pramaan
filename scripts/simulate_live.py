# simulate_live.py — demo-safe version
import time
import requests
import random

BACKEND = "http://localhost:8000"

# Pre-bake a set of realistic entity payloads that look like they came from scraping
PREBUILT_PAYLOADS = [
    {
        "entities": [
            {"id": "EVD_IMD_YAMUNA_LIVE", "label": "Evidence",
             "properties": {"name": "IMD Yamuna Level Alert — 208.66m (CRITICAL)", 
                           "source": "IMD", "confidence": 0.95}}
        ],
        "relations": [],
        "source_type": "live_simulation"
    },
    {
        "entities": [
            {"id": "EVD_DATAGOV_AMRUT_UPDATE", "label": "Evidence",
             "properties": {"name": "data.gov.in — AMRUT Ward 45 drainage completion ✅",
                           "source": "data.gov.in", "confidence": 0.98}}
        ],
        "relations": [],
        "source_type": "live_simulation"
    },
    {
        "entities": [
            {"id": "EVD_PIB_SDRF_KERALA", "label": "Evidence",
             "properties": {"name": "PIB: Relief disbursed to 150 families in Wayanad",
                           "source": "PIB", "confidence": 0.94}}
        ],
        "relations": [],
        "source_type": "live_simulation"
    },
    {
        "entities": [
            {"id": "EVD_NDMA_ODISHA_LIVE", "label": "Evidence",
             "properties": {"name": "NDMA: Cyclone Dana evacuation data - 8L persons",
                           "source": "NDMA", "confidence": 0.97}}
        ],
        "relations": [],
        "source_type": "live_simulation"
    },
    {
        "entities": [
            {"id": "EVD_NTPC_INSIDE_CHAMOLI", "label": "Evidence",
             "properties": {"name": "NTPC: Tapovan tunnel desilting progress report",
                           "source": "NTPC", "confidence": 0.92}}
        ],
        "relations": [],
        "source_type": "live_simulation"
    },
    {
        "entities": [
            {"id": "EVD_ISRO_DANA_RADAR", "label": "Evidence",
             "properties": {"name": "ISRO: EOS-04 satellite imagery of Odisha coast",
                           "source": "ISRO", "confidence": 0.99}}
        ],
        "relations": [],
        "source_type": "live_simulation"
    }
]

def main():
    print(f"🚀 Starting PRAMAAN Live Simulation Loop... (Targeting {BACKEND})")
    print("Ingesting realistic payloads every 45s for demo safety.")
    
    while True:
        payload = random.choice(PREBUILT_PAYLOADS)
        
        # Update timestamp to now so it shows as "just ingested" in the UI
        current_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        for ent in payload["entities"]:
            ent["properties"]["ingested_at"] = current_ts
            print(f"Ingesting: {ent['properties']['name']} at {current_ts}")
        
        try:
            r = requests.post(f"{BACKEND}/ingest/entities", json=payload, timeout=5)
            if r.status_code == 200:
                print(f"✅ Success: 200 OK")
            else:
                print(f"❌ Failed: {r.status_code} - {r.text[:100]}")
        except Exception as e:
            print(f"⚠️ Ingest skipped (Backend likely down): {e}")
        
        time.sleep(45)

if __name__ == "__main__":
    main()
