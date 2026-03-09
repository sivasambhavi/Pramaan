from app.services.news_service import news_service
import json

def test():
    query = "AMRUT 2.0 Delhi"
    print(f"Testing Scraper with query: {query}")
    results = news_service.fetch_google_news(query)
    print(f"Total results: {len(results)}")
    for r in results:
        print(f"- {r['title']}")

if __name__ == "__main__":
    test()
