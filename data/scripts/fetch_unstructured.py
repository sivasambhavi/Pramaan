"""
fetch_unstructured.py — PRAMAAN Step 1b: Fetch Unstructured

Scrapes official government URLs from seed_graph.json evidence nodes.
Only fetches URLs on the v1 whitelist (pib.gov.in, isro.gov.in, etc.)
Saves raw page text to data/resources/unstructured/raw/

Usage:
    python3 data/scripts/fetch_unstructured.py
    python3 data/scripts/fetch_unstructured.py --dry-run
"""

import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone

_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[1]
_SEED_FILE    = _PROJECT_ROOT / "data" / "resources" / "ontology" / "seed_graph.json"
_RAW_DIR      = _PROJECT_ROOT / "data" / "resources" / "unstructured" / "raw"
_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Load whitelist from config
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))
try:
    from app.config import ALLOWED_SOURCE_DOMAINS, is_allowed_source
except ImportError:
    # Fallback if backend not importable
    ALLOWED_SOURCE_DOMAINS = {
        "pib.gov.in", "ndma.gov.in", "isro.gov.in",
        "imd.gov.in", "ndrf.gov.in", "nrsc.gov.in", "ndap.niti.gov.in",
    }
    def is_allowed_source(url):
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname or ""
            return any(host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS)
        except Exception:
            return False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (PRAMAAN Intelligence Engine; research@pramaan.gov.in)",
    "Accept":     "text/html,application/xhtml+xml",
}
TIMEOUT     = 15
DELAY_SECS  = 2


def _extract_text(html: str) -> str:
    """Extract visible text from HTML using basic parsing."""
    try:
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts  = []
                self._skip  = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "header", "footer"):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "header", "footer"):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    text = data.strip()
                    if text:
                        self.parts.append(text)

        p = TextExtractor()
        p.feed(html)
        return " ".join(p.parts)
    except Exception:
        return html[:5000]


def collect_urls(seed: dict) -> list[dict]:
    """Pull all whitelisted URLs from evidence + event source_urls."""
    seen = set()
    urls = []

    for ev in seed.get("evidence", []):
        url = (ev.get("url") or "").strip()
        if url and url not in seen and is_allowed_source(url) and url.startswith("http"):
            seen.add(url)
            urls.append({
                "url":     url,
                "id":      ev["evidence_id"],
                "title":   ev.get("title", ""),
                "source":  ev.get("source", ""),
            })

    for evt in seed.get("events", []):
        url = (evt.get("source_url") or "").strip()
        if url and url not in seen and is_allowed_source(url) and url.startswith("http"):
            seen.add(url)
            urls.append({
                "url":    url,
                "id":     evt["event_id"],
                "title":  evt.get("name", ""),
                "source": "event_source",
            })

    return urls


def fetch_url(entry: dict, dry_run: bool) -> dict:
    url   = entry["url"]
    eid   = entry["id"]
    title = entry["title"]
    slug  = eid.lower().replace("_", "-")
    out   = _RAW_DIR / f"{slug}.txt"

    # Skip if already fetched
    if out.exists():
        print(f"  ⏭  SKIP  {eid} — already fetched")
        return {"id": eid, "status": "skipped", "file": str(out)}

    if dry_run:
        print(f"  🔍 DRY   {eid}  →  {url[:70]}")
        return {"id": eid, "status": "dry_run"}

    print(f"  ⬇  FETCH {eid}  …  {url[:70]}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        text = _extract_text(resp.text)

        if len(text.strip()) < 100:
            print(f"  ⚠️  EMPTY {eid} — too little text ({len(text)} chars)")
            return {"id": eid, "status": "empty", "chars": len(text)}

        # Save with metadata header
        content = (
            f"SOURCE_URL: {url}\n"
            f"EVIDENCE_ID: {eid}\n"
            f"TITLE: {title}\n"
            f"FETCHED_AT: {datetime.now(timezone.utc).isoformat()}\n"
            f"CHARS: {len(text)}\n"
            f"{'='*60}\n\n"
            f"{text}"
        )
        out.write_text(content, encoding="utf-8")
        print(f"  ✅ OK    {eid} — {len(text):,} chars  →  {out.name}")
        return {"id": eid, "status": "ok", "chars": len(text), "file": str(out)}

    except requests.exceptions.Timeout:
        print(f"  ❌ TIMEOUT {eid}")
        return {"id": eid, "status": "timeout"}
    except Exception as e:
        print(f"  ❌ ERROR  {eid} — {e}")
        return {"id": eid, "status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Fetch unstructured data from official URLs")
    parser.add_argument("--dry-run", action="store_true", help="Print URLs without fetching")
    args = parser.parse_args()

    if not _SEED_FILE.exists():
        print(f"ERROR: seed_graph.json not found at {_SEED_FILE}")
        sys.exit(1)

    seed = json.loads(_SEED_FILE.read_text())
    urls = collect_urls(seed)

    mode = "DRY RUN" if args.dry_run else "LIVE FETCH"
    print("=" * 60)
    print(f"  PRAMAAN — Unstructured Fetch [{mode}]")
    print(f"  Whitelisted domains: {len(ALLOWED_SOURCE_DOMAINS)}")
    print(f"  URLs to fetch: {len(urls)}")
    print(f"  Output: {_RAW_DIR}")
    print("=" * 60 + "\n")

    results = []
    for entry in urls:
        result = fetch_url(entry, dry_run=args.dry_run)
        results.append(result)
        if result["status"] == "ok":
            time.sleep(DELAY_SECS)   # be polite to gov servers

    ok      = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors  = [r for r in results if r["status"] in ("error", "timeout", "empty")]

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"  ✅ Fetched : {len(ok)}")
    print(f"  ⏭  Skipped : {len(skipped)} (already on disk)")
    print(f"  ❌ Failed  : {len(errors)}")
    print(f"{'='*60}")

    if ok:
        total_chars = sum(r.get("chars", 0) for r in ok)
        print(f"\n  {total_chars:,} total chars of official text saved")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
