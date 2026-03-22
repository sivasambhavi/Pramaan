"""
loader.py — PRAMAAN Downstream Ingestion Loader

The core deterministic processing engine of the Agentic Ingestion Pipeline.
This acts as Step 2 of the pipeline. It sweeps the Data Lake for freshly minted
"raw" files dropped by the Classifier Agent, and securely REST-calls the
PRAMAAN FastAPI backend to extract AI entities and insert them into Neo4j.
"""

import os
import shutil
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
FASTAPI_ANALYZE_URL = "http://localhost:8000/scrape/analyze"
FASTAPI_INGEST_URL = "http://localhost:8000/ingest/entities"

def sweep_unstructured_raw():
    """
    Scans `/data/unstructured/raw/` for dropped markdown/html files.
    Extracts relations via LLM and commits them to the graph database.
    """
    unstructured_raw = os.path.join(DATA_DIR, "unstructured", "raw")
    unstructured_processed = os.path.join(DATA_DIR, "unstructured", "processed")
    os.makedirs(unstructured_processed, exist_ok=True)
    
    if not os.path.exists(unstructured_raw):
        logger.info("No unstructured raw folder found.")
        return

    files = [f for f in os.listdir(unstructured_raw) if f.endswith(".md") or f.endswith(".html")]
    if not files:
        logger.info("No new unstructured files to process.")
        return
        
    for filename in files:
        filepath = os.path.join(unstructured_raw, filename)
        logger.info(f"Processing newly dropped raw file: {filename}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        try:
            # 1. Ask the backend AI service to extract ontology
            logger.info(f" -> Calling AI Analysis Service for {filename}")
            analyze_resp = requests.post(FASTAPI_ANALYZE_URL, json={"text": content}, timeout=120)
            analyze_resp.raise_for_status()
            ai_data = analyze_resp.json()
            
            if not ai_data.get("success"):
                logger.error(f" -> AI Extraction failed for {filename}: {ai_data.get('error')}")
                continue
                
            # 2. Post structured entities to Neo4j Ingestion Backend
            logger.info(f" -> Uploading entities to Neo4j database...")
            ingest_payload = {
                "source_type": "unstructured_llm",  # Used to mark Live Ingestion nodes
                "entities": ai_data.get("entities", []),
                "relations": ai_data.get("relations", [])
            }
            
            ingest_resp = requests.post(FASTAPI_INGEST_URL, json=ingest_payload, timeout=30)
            ingest_resp.raise_for_status()
            
            logger.info(f" -> Successfully loaded {filename} into Neo4j: {ingest_resp.json()}")
            
            # 3. Move file to the processed staging directory
            dest_filepath = os.path.join(unstructured_processed, filename)
            shutil.move(filepath, dest_filepath)
            logger.info(f" -> File archived to {dest_filepath}")
            
        except requests.exceptions.RequestException as req_err:
            logger.error(f" -> Backend connection failed parsing {filename}. Is the server running? {req_err}")
        except Exception as e:
            logger.error(f" -> Unknown failure processing {filename}: {e}")

if __name__ == "__main__":
    logger.info("Starting PRAMAAN Downstream Sweeper Loader...")
    sweep_unstructured_raw()
    logger.info("Downstream sweep complete.")
