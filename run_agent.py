"""
run_agent.py — PRAMAAN Ingestion Agent Trigger
Uses APScheduler to run the daily classification pipeline, or
can be run manually via CLI for a specific drop-zone or URL.
"""

import os
import time
import argparse
import logging
from dotenv import load_dotenv

# Load API keys before initializing anything else
load_dotenv()

from apscheduler.schedulers.background import BackgroundScheduler
from agent.classifier import classify_source
from agent.tools import fetch_api, scrape_with_crawl4ai, move_from_inbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_source(source_hint: str):
    """
    Orchestrates the classification and tooling for a single source.
    """
    logger.info(f"--- Processing Source: {source_hint} ---")
    
    # 1. Classify
    classification = classify_source(source_hint)
    if "error" in classification:
        logger.error(f"Classification Error: {classification['error']}")
        return
        
    logger.info(f"Classification Result: {classification}")
    
    # 2. Extract configuration
    source_type = classification.get("source_type")
    fetch_method = classification.get("fetch_method")
    dest_folder = classification.get("destination_folder")
    
    # Ensure destination folder is absolute or relative to repo root
    os.makedirs(dest_folder.strip('/'), exist_ok=True)
    
    import re
    from datetime import datetime
    safe_hint = re.sub(r'[^a-zA-Z0-9]', '_', source_hint.split('://')[-1])[:40].strip('_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{safe_hint}_{timestamp}" if safe_hint else f"ingested_{timestamp}"
        
    # 3. Route to Correct Tool
    if source_type == "structured" and fetch_method == "api":
        save_path = os.path.join(dest_folder.strip('/'), f"{base_name}.json")
        fetch_api(source_hint, save_path)
        
    elif source_type == "semi_structured" and fetch_method == "file_upload":
        # Assume source_hint is just the filename in /inbox/
        move_from_inbox(source_hint, dest_folder.strip('/'))
        
    elif source_type == "unstructured" and fetch_method in ["scrape", "web_crawl"]:
        save_path = os.path.join(dest_folder.strip('/'), f"{base_name}.md")
        scrape_with_crawl4ai(source_hint, save_path)
        
    else:
        logger.warning(f"No specific handler defined for {source_type} using {fetch_method}")

def daily_job():
    logger.info("Running daily PRAMAAN ingestion pipeline...")
    
    # 1. Autonomous Discovery via Tavily
    tavily_key = os.environ.get("TAVILY_API_KEY")
    tavily_results = []
    
    if tavily_key and "tvly_" not in tavily_key.lower(): # Basic check for default placeholder
        try:
            from tavily import TavilyClient
            from agent.tools import search_tavily_guarded
            from agent.search_queries import PRIORITY_QUERIES, generate_query_batch
            from agent.relevance_filter import filter_results
            
            logger.info("Initiating autonomous Tavily Hunt with Guardrails & Relevance Scoring...")
            tv_client = TavilyClient(api_key=tavily_key)
            
            # Combine Pre-baked priority queries heavily with dynamic schemes
            queries_to_run = PRIORITY_QUERIES[:2] + generate_query_batch(3)
            
            for query in queries_to_run:
                # Execution layer
                results = search_tavily_guarded(query, tv_client)
                
                # Validation layer
                high_val_results = filter_results(results, min_score=30)
                
                # Extraction layer
                urls = [r.get('url') for r in high_val_results if r.get('url')]
                tavily_results.extend(urls)
                
            logger.info(f"Tavily finalized {len(tavily_results)} intensely relevant URLs globally.")
        except ImportError:
            logger.error("tavily-python not installed. Run `pip install tavily-python`")
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
    else:
        logger.warning("No TAVILY_API_KEY set. Skipping autonomous search hunt.")

    # 2. Combine targeted searches with hardcoded sources
    daily_sources = tavily_results + [
        # You can keep fallback or static sources here
    ]
    
    # 3. Process anything in the Local Inbox first
    inbox_dir = os.path.join(os.getcwd(), 'inbox')
    if os.path.exists(inbox_dir):
        for filename in os.listdir(inbox_dir):
            if filename != '.gitkeep':
                process_source(filename)
                
    # 4. Process all web sources
    for src in daily_sources:
        if src.startswith("http"):
            process_source(src)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PRAMAAN Ingestion Agent")
    parser.add_argument("--url", type=str, help="Manually run agent for a specific URL")
    parser.add_argument("--file", type=str, help="Manually process a specific file inside /inbox/")
    parser.add_argument("--daemon", action="store_true", help="Start APScheduler daily cron daemon")
    
    args = parser.parse_args()
    
    if args.url:
        process_source(args.url)
    elif args.file:
        process_source(args.file)
    elif args.daemon:
        logger.info("Starting AP Scheduler daemon (Ctrl+C to exit)...")
        scheduler = BackgroundScheduler()
        # Schedule to run every day at 02:00 AM
        scheduler.add_job(daily_job, 'cron', hour=2, minute=0)
        scheduler.start()
        
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
    else:
        # Default behavior if no args: run the daily job once
        daily_job()
