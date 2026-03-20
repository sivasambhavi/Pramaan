"""
run_agent.py — PRAMAAN Ingestion Agent Trigger
Uses APScheduler to run the daily classification pipeline, or
can be run manually via CLI for a specific drop-zone or URL.
"""

import os
import time
import argparse
import logging
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
    base_name = os.path.basename(source_hint).split('?')[0]
    if not base_name or base_name == source_hint:
        base_name = "ingested_file"
        
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
    # Example sources we monitor daily
    daily_sources = [
        "https://pib.gov.in/PressReleasePage.aspx?PRID=123456", # Example unstructured
    ]
    
    # Also process anything in the inbox
    inbox_dir = os.path.join(os.getcwd(), 'inbox')
    if os.path.exists(inbox_dir):
        for filename in os.listdir(inbox_dir):
            if filename != '.gitkeep':
                process_source(filename)
                
    # Process regular API/Web sources
    for src in daily_sources:
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
