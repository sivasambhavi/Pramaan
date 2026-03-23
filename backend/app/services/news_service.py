"""
NewsService — PRAMAAN v4.0
Google News RSS scraper for national intelligence events.
Queries are built around event names + official Indian source domains (v1 whitelist).
No API key required.
"""
import time
import feedparser
import urllib.parse
from datetime import datetime
from typing import List, Dict

from app.config import is_allowed_source

_RSS_RETRIES = 3
_RSS_DELAY   = 2.0   # seconds between retries


class NewsService:

    @staticmethod
    def fetch_rss(url: str) -> List[Dict]:
        """Fetch any RSS feed URL directly. Used by scheduler for config-driven feeds."""
        try:
            feed = feedparser.parse(url)
            return [
                {
                    "title":   e.get("title", ""),
                    "summary": e.get("summary", "")[:400],
                    "url":     e.get("link", ""),
                    "date":    e.get("published", ""),
                    "source":  (e.get("source") or {}).get("title", "RSS"),
                }
                for e in (feed.entries or [])[:10]
            ]
        except Exception as exc:
            print(f"[NewsService] fetch_rss error for {url}: {exc}")
            return []

    @staticmethod
    def fetch_google_news(query: str) -> List[Dict]:
        """
        Fetch Google News RSS for a query string.
        Called by /scrape/news endpoint.
        Results are filtered to allowed source domains (v1 whitelist).
        """
        return NewsService.scrape_news_for_event(event_name=query)

    @staticmethod
    def scrape_news_for_event(
        event_name: str,
        domain: str = "",
        max_results: int = 5,
    ) -> List[Dict]:
        """
        Scrape Google News RSS for a national intelligence event.
        Tries queries from specific → broad. Filters results to allowed source domains.

        Args:
            event_name: Human-readable event name (e.g. "Chandrayaan-3 Moon Landing")
            domain:     Optional domain context (e.g. "Technology", "Climate")
            max_results: Max articles to return
        """
        event_clean = event_name.strip()

        # Build query tiers: specific first, broader fallback
        queries = [
            f'"{event_clean}" India site:pib.gov.in OR site:ndma.gov.in OR site:isro.gov.in OR site:imd.gov.in',
            f'"{event_clean}" India official government',
            f'{event_clean} India {domain}'.strip(),
        ]

        check_words = {w.lower() for w in event_clean.split() if len(w) > 3}
        stop_words  = {"india", "2023", "2024", "2021", "2019", "the", "and", "for"}
        check_words -= stop_words

        print(f"[NewsService] Scraping for event: {event_clean} | domain: {domain}")

        for query in queries:
            encoded = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

            feed = None
            for attempt in range(1, _RSS_RETRIES + 1):
                try:
                    feed = feedparser.parse(rss_url)
                    if feed.bozo and not feed.entries:
                        raise feed.bozo_exception
                    break
                except Exception as e:
                    if attempt < _RSS_RETRIES:
                        time.sleep(_RSS_DELAY)
                    else:
                        feed = None

            if feed is None:
                continue

            valid_results = []
            for entry in (feed.entries or []):
                title = entry.get("title", "").lower()
                snip  = entry.get("summary", "").lower()
                url   = entry.get("link", "")

                # Relevance check
                match_count = sum(1 for w in check_words if w in title or w in snip)
                if match_count == 0:
                    continue

                # Domain whitelist check — prefer whitelisted sources, allow others
                allowed = is_allowed_source(url)

                valid_results.append({
                    "title":        entry.get("title", ""),
                    "url":          url,
                    "snippet":      entry.get("summary", "")[:300],
                    "source":       (entry.get("source") or {}).get("title", "News"),
                    "date":         entry.get("published", datetime.now().strftime("%d %b %Y")),
                    "relevance":    match_count,
                    "whitelisted":  allowed,
                    "query_used":   query,
                })

                if len(valid_results) >= max_results:
                    break

            if valid_results:
                # Sort: whitelisted sources first, then by relevance
                valid_results.sort(key=lambda x: (not x["whitelisted"], -x["relevance"]))
                print(f"[NewsService] ✅ {len(valid_results)} results for: '{query}' "
                      f"({sum(1 for r in valid_results if r['whitelisted'])} whitelisted)")
                return valid_results

        print(f"[NewsService] No results found for: {event_clean}")
        return []


news_service = NewsService()
