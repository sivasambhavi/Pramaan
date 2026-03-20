"""
classifier.py — PRAMAAN Ingestion Agent (Classifier)
Uses Gemini 1.5 Flash to classify an incoming data source and route it
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
    import google.generativeai as genai
    from pydantic import BaseModel, Field
except ImportError:
    logger.error("Please install google-generativeai and pydantic.")
    raise

# Ensure API key is set
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY environment variable not set. Classifier will fail.")
else:
    genai.configure(api_key=api_key)

class ClassificationResult(BaseModel):
    source_type: str = Field(description="One of: structured, semi_structured, unstructured")
    fetch_method: str = Field(description="One of: api, scrape, file_upload, web_crawl")
    destination_folder: str = Field(description="The matching /data/.../raw folder path")
    api_url: Optional[str] = Field(description="The URL if structured API", default=None)
    requires_auth: bool = Field(description="If the source likely requires authentication", default=False)

def classify_source(source_hint: str, content_snippet: str = "") -> dict:
    """
    Classifies a data source and determines where it should be routed.
    Returns a dictionary matching the ClassificationResult schema.
    """
    if not api_key:
        return {"error": "GEMINI_API_KEY not configured."}

    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    You are the PRAMAAN Ingestion Routing Agent.
    Your job is to classify the incoming data source and route it to the correct folder.
    
    Source Hint (URL, Path, or Description): {source_hint}
    Content Snippet (if available): {content_snippet}
    
    Rules for source_type:
    - structured: JSON or CSV from an API/URL
    - semi_structured: XML, KML, PDF, MD, or Excel file
    - unstructured: HTML webpage, press release, news article
    
    Rules for destination_folder:
    - structured -> /data/structured/raw/
    - semi_structured -> /data/semi_structured/raw/<ext>/
    - unstructured -> /data/unstructured/raw/
    
    Rules for fetch_method:
    - api: clean structured JSON APIs
    - file_upload: local files in the inbox
    - web_crawl: standard web pages requiring Crawl4AI
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ClassificationResult,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Quick Test
    test_src = "https://pib.gov.in/PressReleasePage.aspx?PRID=123456"
    print(f"Testing classifier with: {test_src}")
    
    result = classify_source(test_src)
    print(json.dumps(result, indent=2))
