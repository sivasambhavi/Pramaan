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

    # Keywords that indicate a topic is already India-centric
    _INDIA_KEYWORDS = {
        "india", "indian", "pib", "isro", "ndma", "modi", "jaishankar",
        "delhi", "mumbai", "kashmir", "sindoor", "pahalgam", "rupee", "sensex",
    }

    @staticmethod
    def _is_india_topic(query: str) -> bool:
        words = {w.lower() for w in query.split()}
        return bool(words & NewsService._INDIA_KEYWORDS)

    @staticmethod
    def fetch_google_news(query: str) -> List[Dict]:
        """
        Fetch Google News RSS for a query string.
        Called by agentic agent. Uses open queries (no forced India) so breaking
        international events (e.g. Iran navy chief killed) are also captured.
        """
        return NewsService.scrape_news_for_event(event_name=query, force_india=False)

    @staticmethod
    def scrape_news_for_event(
        event_name: str,
        domain: str = "",
        max_results: int = 5,
        force_india: bool = True,
    ) -> List[Dict]:
        """
        Scrape Google News RSS for a national intelligence event.
        Tries queries from specific → broad. Filters results to allowed source domains.

        Args:
            event_name:   Human-readable event name
            domain:       Optional domain context
            max_results:  Max articles to return
            force_india:  If False, lead with open query (no India bias) so
                          breaking international events are captured first.
        """
        event_clean = event_name.strip()
        india_topic = NewsService._is_india_topic(event_clean)

        if force_india or india_topic:
            # India-centric topic — official sources first
            queries = [
                f'"{event_clean}" India site:pib.gov.in OR site:ndma.gov.in OR site:isro.gov.in OR site:imd.gov.in',
                f'"{event_clean}" India official government',
                f'{event_clean} India {domain}'.strip(),
                event_clean,                          # bare fallback — no India filter
            ]
        else:
            # International / breaking news — raw query first, India angle as fallback
            queries = [
                event_clean,                          # exact raw query — gets breaking news
                f'{event_clean} latest news',
                f'{event_clean} India impact',        # India strategic angle
                f'{event_clean} India {domain}'.strip(),
            ]

        check_words = {w.lower() for w in event_clean.split() if len(w) > 3}
        stop_words  = {
            "india", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
            "the", "and", "for", "news", "latest",
        }
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
