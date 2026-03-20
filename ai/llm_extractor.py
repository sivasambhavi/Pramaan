"""
llm_extractor.py — PRAMAAN Evidence Extractor (Frontend delegate)

Fix 4 applied: This module no longer maintains its own Groq client.
All LLM calls are delegated to the backend's unified AIService via
  POST http://127.0.0.1:8000/scrape/analyze-evidence

This gives the project ONE LLM code path:
  frontend (02_Proof_Chain.py)
      → llm_extractor.DeepDataExtractor.process_document()
          → POST /scrape/analyze-evidence
              → ai_service.AIService.analyze_evidence()
                  → Groq API

Benefits:
  - Single prompt to maintain
  - Single API key / client
  - Backend can be updated without touching frontend code
  - Works even if GROQ_API_KEY is not set on the frontend side
"""

import os
import json
import logging
import requests
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Allow override via env var for non-standard deployments
_BACKEND_URL = os.environ.get("PRAMAAN_BACKEND_URL", "http://127.0.0.1:8000")
_ENDPOINT    = f"{_BACKEND_URL}/scrape/analyze-evidence"
_TIMEOUT     = 15   # seconds


class DeepDataExtractor:
    """
    Thin wrapper around the backend /scrape/analyze-evidence endpoint.
    Preserves the existing interface so 02_Proof_Chain.py needs no changes:

        extractor = DeepDataExtractor()
        result    = extractor.process_document(text, asset_name, ward_name)
        # result = {"key_fact": "...", "relevance": "...", "confidence": 0.9}
    """

    def process_document(
        self,
        text: str,
        asset_name: str,
        ward_name: str,
    ) -> Dict[str, Any]:
        """
        Delegate evidence analysis to the backend AI service.

        Returns:
            dict with keys: key_fact (str), relevance (str), confidence (float)
        """
        try:
            resp = requests.post(
                _ENDPOINT,
                json={
                    "text":       text,
                    "asset_name": asset_name,
                    "ward_name":  ward_name,
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.ConnectionError:
            # Backend not running — provide a graceful mock so Proof Chain
            # still renders without crashing.
            logger.warning(
                "Backend not reachable at %s — returning mock evidence result.",
                _BACKEND_URL,
            )
            return {
                "key_fact":   f"[Offline] Reference to {asset_name} found in news.",
                "relevance":  "Context Match",
                "confidence": 0.5,
            }

        except requests.exceptions.Timeout:
            logger.warning("analyze-evidence request timed out after %ds", _TIMEOUT)
            return {
                "key_fact":   f"[Timeout] Analysis took too long for {asset_name}.",
                "relevance":  "Unknown",
                "confidence": 0.4,
            }

        except Exception as e:
            logger.error("DeepDataExtractor.process_document failed: %s", e)
            return {
                "key_fact":   f"[Error] Could not analyse snippet for {asset_name}.",
                "relevance":  "Unknown",
                "confidence": 0.0,
            }
