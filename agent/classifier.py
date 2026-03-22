"""
classifier.py — PRAMAAN Ingestion Agent (Classifier)
Uses Groq Llama3 to classify an incoming data source and route it
to the correct folder in the Data Lake.
"""

import os
import json
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:
    logger.error("Please install groq.")
    raise

# Ensure API key is set (Re-using your existing backend Groq key)
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    logger.warning("GROQ_API_KEY environment variable not set. Classifier will fail.")

client = Groq(api_key=api_key) if api_key else None

def classify_source(source_hint: str, content_snippet: str = "") -> dict:
    """
    Classifies a data source and determines where it should be routed.
    Returns a dictionary matching the ClassificationResult schema.
    """
    if not api_key or not client:
        return {"error": "GROQ_API_KEY not configured in .env"}

    prompt = f"""
    You are the PRAMAAN data ingestion agent for Delhi urban governance.

    STRICT RULES:
    1. Only classify and route sources. NEVER extract or interpret data.
    2. Only look for data related to: infrastructure, water, sanitation, housing, health, governance in Delhi NCT.
    3. If a source is not from a government portal or trusted news outlet, classify it as requires_auth=true to skip it.
    4. Never query social media, opinion blogs, or Wikipedia.
    5. All unstructured sources must resolve to a domain in the approved whitelist.
    6. If unsure about classification, default to semi_structured.

    Source Hint: {source_hint}
    Snippet: {content_snippet}
    
    Respond STRICTLY with valid JSON matching this schema:
    {{
      "source_type": "structured" | "semi_structured" | "unstructured",
      "fetch_method": "api" | "scrape" | "file_upload" | "web_crawl",
      "destination_folder": "/data/structured/raw/" | "/data/semi_structured/raw/<ext>/" | "/data/unstructured/raw/",
      "api_url": "The url or null",
      "requires_auth": boolean
    }}
    
    CRITICAL RULES:
    1. If the URL contains ".aspx", ".html", "PressRelease", or is a standard website:
       MUST USE source_type = "unstructured"
       MUST USE fetch_method = "web_crawl"
       MUST USE destination_folder = "/data/unstructured/raw/"
    2. ONLY use "structured" and "api" if it is a JSON data feed.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON routing AI. Output only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Quick Test
    test_src = "https://pib.gov.in/PressReleasePage.aspx?PRID=123456"
    print(f"Testing classifier with: {test_src}")
    
    result = classify_source(test_src)
    print(json.dumps(result, indent=2))
