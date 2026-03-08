import requests
import json

# We already know the UUID for "Storm Water Drainage Projects (AMRUT)"
# from our previous sessions!
uuid = "6e38d0c0-045e-4dce-81d0-eca39519bb07"
api_key = "579b464db66ec23bdd0000015e41d90b35664d4d43987bac4557f358"

api_url = f"https://api.data.gov.in/resource/{uuid}?api-key={api_key}&format=json&limit=100"
print(f"Trying API: {api_url}")

try:
    res = requests.get(api_url)
    if res.status_code == 200:
        data = res.json()
        if data.get("status") == "ok":
            print(f"SUCCESS! Found data for UUID {uuid}")
            with open("amrut_storm_water_drainage.json", "w") as f:
                json.dump(data, f, indent=4)
            print("Saved to amrut_storm_water_drainage.json")
        else:
            print("API returned JSON, but status is not ok:", data.get("message"))
    else:
        print(f"Failed with status: {res.status_code}")
except Exception as e:
    print(f"Error: {e}")
