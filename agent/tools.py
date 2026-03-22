"""
tools.py — PRAMAAN Ingestion Agent Tools
Functions the agent uses to fetch, scrape, and move classified data.
"""

import os
import json
import shutil
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    pass

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False


def fetch_api(url: str, save_path: str) -> bool:
    """
    Path 1: Fetch a structured JSON api and save to disk.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, indent=2)
        
        logger.info(f"API fetched and saved to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to fetch API {url}: {e}")
        return False


async def _crawl_async(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown


def scrape_with_crawl4ai(url: str, save_path: str) -> bool:
    """
    Path 3: Synchronous Web Scraping Fallback using BS4 + Markdownify.
    (Bypasses asyncio/Playwright pipe errors on Windows)
    """
    logger.info(f"Initiating synchronous requests scraper for {url}")
    try:
        import requests
        from bs4 import BeautifulSoup
        import markdownify
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Remove noisy elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "meta", "link"]):
            element.decompose()
            
        # Convert to markdown
        md_text = markdownify.markdownify(str(soup), heading_style="ATX", strip=['img', 'a', 'svg', 'button', 'input'])
        
        # Clean up excessive blank lines
        import re
        md_clean = re.sub(r'\n{3,}', '\n\n', md_text).strip()
        
        # Add metadata header
        final_markdown = f"# Source: {url}\n\n{md_clean}"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
            
        logger.info(f"Successfully scraped and saved markdown to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Synchronous scraper failed for {url}: {e}")
        return False


def extract_pdf_markdown(pdf_path: str, save_path: str) -> bool:
    """ Uses PyMuPDF to convert PDF layouts into clean text/markdown."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text_blocks = []
        for page in doc:
            text_blocks.append(page.get_text())
        
        md_text = f"# PDF Document: {os.path.basename(pdf_path)}\n\n" + "\n\n---\n\n".join(text_blocks)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(md_text)
        return True
    except Exception as e:
        logger.error(f"Failed to parse PDF {pdf_path}: {e}")
        return False

def move_from_inbox(filename: str, dest_folder: str) -> str:
    """
    Path 2: Move a manually uploaded file from /inbox/ to its semi-structured raw folder.
    """
    source_path = os.path.join(os.getcwd(), 'inbox', filename)
    
    if not os.path.exists(source_path):
        logger.error(f"File {filename} not found in inbox.")
        return ""
        
    os.makedirs(dest_folder, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(filename)
    new_filename = f"{base}_{date_str}{ext}"
    dest_path = os.path.join(dest_folder, new_filename)
    
    shutil.move(source_path, dest_path)
    logger.info(f"Moved {filename} from inbox to {dest_path}")
    
    # Trigger AI-readable conversion if it is a PDF
    if dest_path.lower().endswith('.pdf'):
        md_path = f"{dest_path}.md"
        if extract_pdf_markdown(dest_path, md_path):
            logger.info(f"Successfully converted PDF to Markdown: {md_path}")
            
    return dest_path

# ── TAVILY GUARDRAILS ──────────────────────────────────────────────────────────
import hashlib
from pathlib import Path
from datetime import date

TAVILY_CONFIG = {
    "max_calls_per_run": 10,
    "max_calls_per_day": 50,
    "search_depth": "advanced",
    "max_results_per_query": 5,
    "delay_between_calls_sec": 2,
    "include_domains": [
        "smartcities.gov.in", "mcdonline.nic.in", "data.gov.in", "dda.org.in",
        "delhi.gov.in", "ndmc.gov.in", "urbanindia.nic.in", "mohua.gov.in",
        "niti.gov.in", "pib.gov.in", "thehindu.com", "hindustantimes.com", "downtoearth.org.in"
    ],
    "exclude_domains": [
        "quora.com", "reddit.com", "wikipedia.org", "youtube.com", "facebook.com", "twitter.com", "instagram.com"
    ],
}

COUNTER_FILE = Path(os.path.join(os.getcwd(), 'agent', '.tavily_counter'))

def _get_daily_count() -> int:
    if not COUNTER_FILE.exists(): return 0
    try:
        data = COUNTER_FILE.read_text().strip().split(",")
        if data[0] == str(date.today()): return int(data[1])
    except Exception: pass
    return 0

def _increment_daily_count():
    count = _get_daily_count() + 1
    COUNTER_FILE.write_text(f"{date.today()},{count}")
    return count

def search_tavily_guarded(query: str, client) -> list:
    """ Guarded search returning a list of URLs. """
    daily_count = _get_daily_count()
    if daily_count >= TAVILY_CONFIG["max_calls_per_day"]:
        logger.warning(f"Tavily daily budget exhausted ({daily_count} calls today).")
        return []

    logger.info(f"[TAVILY] Searching ({daily_count+1}/{TAVILY_CONFIG['max_calls_per_day']}): {query}")
    try:
        response = client.search(
            query=query,
            search_depth=TAVILY_CONFIG["search_depth"],
            max_results=TAVILY_CONFIG["max_results_per_query"],
            include_domains=TAVILY_CONFIG["include_domains"],
            exclude_domains=TAVILY_CONFIG["exclude_domains"],
            include_raw_content=True,
        )
        _increment_daily_count()
        import time
        time.sleep(TAVILY_CONFIG["delay_between_calls_sec"])
        return response.get("results", [])
    except Exception as e:
        logger.error(f"Tavily search failed for query: {e}")
        return []
