import requests
import json
import os
import sys

# Your API Key
API_KEY = "579b464db66ec23bdd0000015e41d90b35664d4d43987bac4557f358"

# The Resource ID for "State/UT-wise details of CS funds released under AMRUT and AMRUT 2.0 (2018-19 to 2022-23)"
RESOURCE_ID = "21a3ceaf-1725-41e9-9be9-a29d5b762cba"

# The standard data.gov.in API endpoint
API_URL = "https://api.data.gov.in/resource/" + RESOURCE_ID

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'amrut_funds.json')

def fetch_and_store_data():
    # For data.gov.in, the API key is passed as a query parameter
    params = {
        'api-key': API_KEY,
        'format': 'json',
        'limit': 100 # Adjust limit as needed
    }
    
    try:
        print(f"Fetching data from {API_URL}...")
        response = requests.get(API_URL, params=params)
        
        # Check if the response was successful
        response.raise_for_status()
        
        data = response.json()
        
        # Check if the API returned a specialized error message like 'Meta not found'
        if data.get('status') == 'error':
             print(f"API Error Response: {data.get('message', 'Unknown Error')}")
             sys.exit(1)
        
        # Store the data in an output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Data successfully retrieved and saved to: {OUTPUT_FILE}")
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        # Print more details if the server returned an error body
        if hasattr(e.response, 'text'):
            print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    fetch_and_store_data()
