"""
PRAMAAN — Unified AI Extraction Service

Two responsibilities:
  1. extract_ontology(text, source_type)  — extracts entities/relations from any text
  2. score_evidence(text, asset_name, ward_name) — scores relevance of a news snippet to an asset

source_type must be one of:
  unstructured_llm   — user-pasted text (POST /scrape/analyze)
  unstructured_rss   — RSS / news headline (GET /scrape/news)
"""

import json
import logging
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

VALID_SOURCE_TYPES = {"unstructured_llm", "unstructured_rss"}


class AIService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    # ── 1. Entity + relation extraction ──────────────────────────────────────
    def extract_ontology(self, text: str, source_type: str = "unstructured_llm") -> dict:
        """
        Extract governance entities and relations from raw text.
        Returns a dict with: entities, relations, source_type, success.
        Every entity's properties include a confidence score set by the LLM.
        """
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type '{source_type}'. Must be one of: {VALID_SOURCE_TYPES}")

        prompt = f"""
You are a governance data extraction assistant for India.
Extract entities from the following governance text and return ONLY valid JSON.
No explanation, no markdown, no code blocks.

Text: {text}

Return this exact JSON structure:
{{
  "entities": [
    {{"id": "scheme_amrut", "label": "Scheme", "properties": {{"name": "scheme name", "ministry": "ministry name", "category": "roads/sanitation/housing/drainage/other", "confidence": 0.9}}}},
    {{"id": "reg_w45", "label": "Region", "properties": {{"name": "location name", "type": "ward/street/city/zone", "parent_region_id": "REG_W45", "confidence": 0.85}}}},
    {{"id": "asset_1", "label": "Asset", "properties": {{"name": "asset description", "type": "drain/road/toilet/housing/park/streetlight/water_body/other", "cost": 1200000, "status": "completed/ongoing/planned", "confidence": 0.8}}}},
    {{"id": "actor_mcd", "label": "Actor", "properties": {{"name": "agency or contractor name", "type": "government/contractor/elected_rep", "confidence": 0.85}}}},
    {{"id": "ben_1", "label": "Beneficiary", "properties": {{"count": 100, "description": "description of who benefits", "confidence": 0.7}}}},
    {{"id": "ev_1", "label": "Evidence", "properties": {{"type": "photo/report/certificate", "description": "what the evidence shows", "confidence": 0.75}}}}
  ],
  "relations": [
    {{"from_id": "scheme_amrut", "from_label": "Scheme", "to_id": "asset_1", "to_label": "Asset", "type": "FUNDS"}},
    {{"from_id": "asset_1", "from_label": "Asset", "to_id": "actor_mcd", "to_label": "Actor", "type": "BUILT_BY"}},
    {{"from_id": "asset_1", "from_label": "Asset", "to_id": "reg_w45", "to_label": "Region", "type": "LOCATED_IN"}}
  ]
}}

Rules:
- If a field is unknown, omit it or use null.
- cost must be a number in rupees (e.g. 1200000 for Rs 12 lakh).
- confidence must be a float 0.0–1.0 reflecting how certain you are about this entity.
- Return ONLY the JSON object. Nothing else.
"""
        try:
            resp = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.0,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            result = json.loads(raw)
            result["source_type"] = source_type
            result["success"]     = True
            result.setdefault("entities",  [])
            result.setdefault("relations", [])
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError in extract_ontology: {e}")
            return {"success": False, "source_type": source_type,
                    "error": f"LLM returned invalid JSON: {e}",
                    "entities": [], "relations": []}
        except Exception as e:
            logger.error(f"extract_ontology failed: {e}")
            return {"success": False, "source_type": source_type,
                    "error": str(e), "entities": [], "relations": []}

    # ── 2. Evidence relevance scoring ─────────────────────────────────────────
    def score_evidence(self, text: str, asset_name: str, ward_name: str) -> dict:
        """
        Score how relevant a news/text snippet is to a specific infrastructure asset.
        Returns: key_fact, relevance, confidence (0.0–1.0).
        """
        prompt = f"""
You are a governance data extraction AI.
Analyze the following news snippet and determine its relevance to a specific infrastructure project.
Asset Name: {asset_name}
Location: {ward_name}

News Snippet:
{text}

Extract the most critical 'key_fact' regarding the completion, budget, or status of this asset.
Determine the 'relevance': "Direct Match", "Zone Context", or "National Context".
Give a confidence score between 0.0 and 1.0.

Respond strictly with valid JSON only:
{{
    "key_fact": "string",
    "relevance": "string",
    "confidence": 0.95
}}
"""
        try:
            resp = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content.strip())
        except Exception as e:
            logger.error(f"score_evidence failed: {e}")
            return {
                "key_fact":   f"Fallback: Found mention of {asset_name}.",
                "relevance":  "Context Match",
                "confidence": 0.5,
            }

    # ── Backward-compat alias (remove once all callers updated) ───────────────
    def extract_governance_ontology(self, text: str) -> dict:
        return self.extract_ontology(text, source_type="unstructured_llm")


ai_service = AIService()
