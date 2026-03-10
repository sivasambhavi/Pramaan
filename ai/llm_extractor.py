import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Fallback AI setup if Groq library isn't available
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    try:
        from openai import OpenAI
        HAS_OPENAI = True
    except ImportError:
        HAS_OPENAI = False

class DeepDataExtractor:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment. AI extractor will use mock fallback.")
            
        self.client = None
        if self.api_key:
            if HAS_GROQ:
                self.client = Groq(api_key=self.api_key)
            elif HAS_OPENAI:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1"
                )

    def process_document(self, text: str, asset_name: str, ward_name: str) -> Dict[str, Any]:
        """
        Use Llama 3 (via Groq) to analyze news text and extract key structural mapping info.
        Returns a dict with 'key_fact', 'relevance', 'confidence'.
        """
        if not self.client:
            return {
                "key_fact": f"AI Mock Extraction: Identified references to {asset_name} in {ward_name}.",
                "relevance": "Direct Match",
                "confidence": 0.85
            }

        prompt = f"""
You are a governance data extraction AI.
Analyze the following news snippet and determine its relevance to a specific infrastructure project.
Asset Name: {asset_name}
Location: {ward_name}

News Snippet:
{text}

Extract the most critical 'key_fact' regarding the completion, budget, or status of this asset.
Determine the 'relevance' (e.g., "Direct Match", "Zone Context", "National Context").
Give a confidence score between 0.0 and 1.0.

Respond strictly with valid JSON. Do not include markdown formatting or explanations.
Format:
{{
    "key_fact": "string",
    "relevance": "string",
    "confidence": 0.95
}}
"""
        try:
            if HAS_GROQ:
                resp = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                content = resp.choices[0].message.content.strip()
            else:
                resp = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                content = resp.choices[0].message.content.strip()

            return json.loads(content)
        except Exception as e:
            logger.error(f"AI Extraction failed: {e}")
            return {
                "key_fact": f"Fallback Parse: Found mention of project {asset_name}.",
                "relevance": "Context Match",
                "confidence": 0.5
            }
