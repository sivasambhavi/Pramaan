"""
NewsService — PRAMAAN v3.1
Guaranteed-working RSS scraper using Google News RSS + feedparser.
No API key required. Uses multi-query fallback strategy.
"""
import feedparser
import urllib.parse
from datetime import datetime
from typing import List, Dict


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
        Legacy method — wraps scrape_news_for_asset with a single query.
        Called by /scrape/news endpoint.
        """
        results = NewsService.scrape_news_for_asset(
            asset_name=query,
            ward_name="",
            scheme_name=""
        )
        # Normalize to legacy field names for backward compat
        return [
            {
                "title":      r.get("title", ""),
                "link":       r.get("url", ""),
                "published":  r.get("date", ""),
                "summary":    r.get("snippet", ""),
                "relevance":  r.get("relevance", 0),
                "query_used": r.get("query_used", ""),
            }
            for r in results
        ]

    @staticmethod
    def scrape_news_for_asset(
        asset_name: str,
        ward_name: str,
        scheme_name: str = ""
    ) -> List[Dict]:
        """
        Scrape Google News RSS for governance evidence.
        Tries 3 queries from specific → broad. Returns first batch that works.
        Includes keyword-based relevance filtering to avoid 'Property Tax' pollution.
        """
        # ── 1. Clean Inputs ──────────────────────────────────────────────────
        # Remove "DMC Ward No - " or "Ward " prefixes for cleaner search
        clean_ward = ward_name.replace("DMC Ward No - ", "").replace("Ward ", "").strip()
        asset_clean = asset_name.split("(")[0].strip() # Remove (type) suffix if any

        # ── 2. Build 3 query tiers ──────────────────────────────────────────
        q1 = f'"{asset_clean}" {clean_ward} MCD Delhi'
        q2 = f'{asset_clean} {clean_ward} MCD Delhi'
        q3 = f"MCD Delhi {scheme_name or 'infrastructure'} {clean_ward} 2025"

        queries = [q1, q2, q3]
        print(f"[NewsService] Scrape for: {asset_clean} | Ward: {clean_ward}")

        # ── 3. Define Must-Have Relevance Keywords ──────────────────────────
        # We want the result to at least mention the asset type or name
        check_words = set()
        if asset_clean:
            check_words.update(asset_clean.lower().split())
        if clean_ward:
            check_words.update(clean_ward.lower().split())
        
        # Add broad category words if specific asset name is complex
        if "drain" in asset_name.lower(): check_words.add("drain")
        if "water" in asset_name.lower(): check_words.add("water")
        if "road" in asset_name.lower():  check_words.add("road")

        # Remove very common words
        stop_words = {"mcd", "delhi", "the", "and", "for", "ward", "no", "-"}
        check_words = {w for w in check_words if w not in stop_words and len(w) > 2}

        print(f"[NewsService] Relevance keywords: {check_words}")

        for query in queries:
            encoded = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
            
            try:
                feed = feedparser.parse(rss_url)
                entries = feed.entries or []
                
                valid_results = []
                for entry in entries:
                    title = entry.get("title", "").lower()
                    snip  = entry.get("summary", "").lower()
                    
                    # Score relevance: how many check_words appear?
                    match_count = sum(1 for word in check_words if word in title or word in snip)
                    
                    # RELEVANCE CRITERIA: 
                    # If it's a specific query (q1/q2), we need at least 1 match.
                    # If it's q3, we need at least 2 matches to be sure.
                    required = 1 if query != q3 else 2
                    
                    if match_count >= required:
                        valid_results.append({
                            "title":       entry.get("title", ""),
                            "url":         entry.get("link", ""),
                            "snippet":     entry.get("summary", "")[:300],
                            "source":      (entry.get("source") or {}).get("title", "News"),
                            "date":        entry.get("published", datetime.now().strftime("%d %b %Y")),
                            "relevance":   match_count,
                            "query_used":  query
                        })
                    
                    if len(valid_results) >= 3: break
                
                if valid_results:
                    print(f"[NewsService] ✅ Found {len(valid_results)} relevant items for query: '{query}'")
                    return valid_results
                    
            except Exception as e:
                print(f"[NewsService] Query Error: {e}")
                continue

        print("[NewsService] No highly relevant evidence found.")
        return []


news_service = NewsService()
