import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    resp = httpx.get(f"{BASE_URL}/health")
    print(f"Health: {resp.status_code} - {resp.json()}")

def test_list_wards():
    resp = httpx.get(f"{BASE_URL}/wards/")
    print(f"Wards: {resp.status_code} - Found {len(resp.json())} wards")

def test_ward_score():
    ward_id = "REG_W45"
    resp = httpx.get(f"{BASE_URL}/wards/{ward_id}/score")
    print(f"Score {ward_id}: {resp.status_code} - {json.dumps(resp.json(), indent=2)}")

def test_asset_chain():
    asset_id = "ASSET_WB_272027"
    resp = httpx.get(f"{BASE_URL}/assets/{asset_id}/chain")
    print(f"Chain {asset_id}: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Asset: {data['asset']['name']}")
        print(f"  Scheme: {data['scheme']['name'] if data['scheme'] else 'None'}")
        print(f"  Evidence count: {len(data['evidence'])}")

if __name__ == "__main__":
    try:
        test_health()
        test_list_wards()
        test_ward_score()
        test_asset_chain()
    except Exception as e:
        print(f"Error: {e}")
