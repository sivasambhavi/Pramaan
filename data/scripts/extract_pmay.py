import requests
import json
import re

url = "https://www.data.gov.in/resource/stateut-wise-total-number-completed-and-occupied-houses-under-pradhan-mantri-awas-yojana"
api_key = "579b464db66ec23bdd0000015e41d90b35664d4d43987bac4557f358"

try:
    response = requests.get(url, timeout=10)
    html = response.text
    uuids = list(set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', html)))
    print("ALL UUIDS FOUND:", uuids)
    
    for uuid in uuids:
        api_url = f"https://api.data.gov.in/resource/{uuid}?api-key={api_key}&format=json&limit=100"
        print(f"\nTrying API: {api_url}")
        res = requests.get(api_url)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "ok":
                print(f"SUCCESS! Found data for UUID {uuid}")
                with open("pmay_housing_data.json", "w") as f:
                    json.dump(data, f, indent=4)
                print("Saved to pmay_housing_data.json")
                break
            else:
                print("API returned JSON, but status is not ok:", data.get("message"))
        else:
            print(f"Failed with status: {res.status_code}")
except Exception as e:
    print(f"Error: {e}")
