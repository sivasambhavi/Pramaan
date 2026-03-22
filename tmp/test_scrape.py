import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.tools import scrape_with_crawl4ai

url = "https://pib.gov.in/PressReleasePage.aspx?PRID=2015096"
save_path = "tmp/pib_test.md"

print(f"Testing scraper for {url}...")
success = scrape_with_crawl4ai(url, save_path)
print(f"Success: {success}")

if success and os.path.exists(save_path):
    with open(save_path, 'r', encoding='utf-8') as f:
        print("\n--- FIRST 500 CHARS OF EXTRACTED MARKDOWN ---")
        print(f.read()[:500])
        print("---------------------------------------------")
