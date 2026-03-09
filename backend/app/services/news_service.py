import feedparser
import requests
from typing import List, Dict

class NewsService:
    @staticmethod
    def fetch_google_news(query: str) -> List[Dict]:
        """Fetch news from Google News RSS using Requests + Feedparser for better headers."""
        try:
            # RSS URL with query
            rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            print(f"--- SCRAPER DEBUG ---")
            print(f"URL: {rss_url}")
            
            # Use requests to simulate a browser-like fetch
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"HTTP ERROR: {response.status_code}")
                return []
            
            # Parse the content
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"BOZO BIT SET: {feed.bozo_exception}")
            
            print(f"ENTRIES FOUND: {len(feed.entries)}")
            
            results = []
            for entry in feed.entries[:5]:
                results.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": getattr(entry, 'published', 'N/A'),
                    "summary": getattr(entry, 'summary', 'N/A')
                })
                print(f" - Found: {entry.title[:50]}...")
                
            return results
        except Exception as e:
            print(f"EXCEPTION IN SCRAPER: {e}")
            return []

news_service = NewsService()
