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
    Path 3: Unstructured web scraping to get clean markdown via playright/crawl4ai.
    """
    if not CRAWL4AI_AVAILABLE:
        logger.error("Crawl4AI is not fully installed. Falling back to stub.")
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"# Fallback Scrape Context for {url}\n\n(Install crawl4ai to enable real headless scraping.)")
        return True
        
    logger.info(f"Initiating Crawl4AI asynchronous crawl for {url}")
    try:
        # Launch the playwright async loop to fetch the rendered website
        markdown_text = asyncio.run(_crawl_async(url))
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
            
        logger.info(f"Scraped rendered markdown content saved to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Crawl4AI headless extraction failed for {url}: {e}")
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
    return dest_path
