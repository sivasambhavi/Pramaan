"""
PRAMAAN — Unified AI Extraction Service

Two responsibilities:
  1. extract_ontology(text, source_type)  — extracts entities/relations from any text
  2. score_evidence(text, asset_name, ward_name) — scores relevance of a news snippet to an asset

source_type must be one of:
  unstructured_llm   — user-pasted text (POST /scrape/analyze)
  unstructured_rss   — RSS / news headline (GET /scrape/news)

Fix 2 applied: Graph-aware prompt includes known canonical IDs preventing orphan nodes.
Fix 4 applied: Single unified LLM service — llm_extractor.py delegates here.
"""

import os
import json
import logging
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

VALID_SOURCE_TYPES = {"unstructured_llm", "unstructured_rss"}

# ─── Canonical IDs already seeded in Neo4j ───────────────────────────────────
KNOWN_IDS_CONTEXT = """
IMPORTANT — The graph already contains these nodes. When the text mentions any
of them, use the EXACT ID listed. Do NOT invent a new ID for an existing entity.

Schemes:
  SCH_AMRUT        = AMRUT (Atal Mission for Rejuvenation and Urban Transformation)
  SCH_PMAY         = PMAY-Urban (Pradhan Mantri Awas Yojana)
  SCH_SWACHH       = Swachh Bharat Mission - Urban
  SCH_SFC          = Local Development Grants - Roads & Drains (Delhi SFC)
  SCH_LOCAL_LIGHTS = Urban Streetlight Improvement (Delhi)

Regions:
  REG_DELHI           = Delhi (city level)
  REG_SHAHDARA_NORTH  = Shahdara North Zone
  REG_SHAHDARA_SOUTH  = Shahdara South Zone
  REG_W45             = Ward 45 Shahdara
  REG_W45_GALI7       = Gali No. 7 (street inside Ward 45)
  REG_W45_GALI12      = Gali No. 12 (street inside Ward 45)
  REG_W45_GALI3       = Gali No. 3 (street inside Ward 45)
  REG_W45_MARKET_ROAD = Shahdara Market Road
  REG_W45_COLONY_Y    = Colony Y Housing Cluster

Actors:
  ACT_MCD_SHAHDARA_WORKS      = MCD Shahdara North Works Dept
  ACT_MCD_SHAHDARA_SANITATION = MCD Shahdara Sanitation Dept
  ACT_MCD_ELECTRICAL          = MCD Electrical Dept - Shahdara
  ACT_DDA                     = Delhi Development Authority
  ACT_W45_COUNCILLOR          = Ward 45 Councillor
  ACT_CONTRACTOR_INFRA_1      = ABC Infra Pvt Ltd
  ACT_CONTRACTOR_LIGHTS_1     = BrightLights Engineering

Only create a NEW id (e.g. "act_xyz123") if the entity is genuinely not in
this list and is not a synonym/alias for any entry above.
"""

class AIService:
    def __init__(self):
        self.client = None
        key = settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        if key:
            try:
                self.client = Groq(api_key=key)
            except Exception as e:
                logger.warning(f"Could not init Groq client: {e}")
        else:
            logger.warning("GROQ_API_KEY not set — AI service will return mock data.")

    # ── 1. Entity + relation extraction ──────────────────────────────────────
    def extract_ontology(self, text: str, source_type: str = "unstructured_llm") -> dict:
        """
        Extract governance entities and relations from raw text.
        Returns a dict with: entities, relations, source_type, success.
        Every entity's properties include a confidence score set by the LLM.
        """
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type '{source_type}'. Must be one of: {VALID_SOURCE_TYPES}")
        if not self.client:
            return {
                "success": False,
                "error": "Groq API key not configured",
                "source_type": source_type,
                "entities": [],
                "relations": [],
            }

        prompt = f"""
You are a governance data extraction assistant for India.
Extract entities from the following governance text and return ONLY valid JSON.
No explanation, no markdown, no code blocks.

{KNOWN_IDS_CONTEXT}

Text:
{text}

Return this exact JSON structure:
{{
  "entities": [
    {{"id": "SCH_AMRUT", "label": "Scheme", "properties": {{"name": "AMRUT", "ministry": "MoHUA", "category": "infrastructure", "confidence": 0.95}}}},
    {{"id": "REG_W45",   "label": "Region", "properties": {{"name": "Ward 45 Shahdara", "type": "ward", "confidence": 0.9}}}},
    {{"id": "asset_new_1","label": "Asset",  "properties": {{"name": "asset description", "type": "drain/road/toilet/housing/park/streetlight/other", "cost": 1200000, "status": "completed/in_progress/planned", "confidence": 0.8}}}},
    {{"id": "ACT_MCD_SHAHDARA_WORKS","label": "Actor", "properties": {{"name": "MCD Shahdara North Works Dept", "type": "government", "confidence": 0.85}}}},
    {{"id": "ben_new_1", "label": "Beneficiary", "properties": {{"count": 100, "description": "households benefiting", "confidence": 0.7}}}},
    {{"id": "ev_new_1",  "label": "Evidence",    "properties": {{"type": "photo/report/certificate", "description": "what the evidence shows", "confidence": 0.75}}}}
  ],
  "relations": [
    {{"from_id": "SCH_AMRUT", "from_label": "Scheme", "to_id": "asset_new_1", "to_label": "Asset", "type": "FUNDS"}},
    {{"from_id": "asset_new_1", "from_label": "Asset", "to_id": "ACT_MCD_SHAHDARA_WORKS", "to_label": "Actor", "type": "BUILT_BY"}},
    {{"from_id": "asset_new_1", "from_label": "Asset", "to_id": "REG_W45", "to_label": "Region", "type": "LOCATED_IN"}}
  ]
}}

Rules:
- Use existing IDs from the IMPORTANT section whenever they match.
- Only create new IDs (e.g. "asset_new_1") for genuinely new entities.
- cost must be a number in rupees (1200000 = Rs 12 lakh).
- confidence: float 0.0–1.0 reflecting certainty from the text.
- Omit unknown fields rather than guessing.
- Return ONLY the JSON object. Nothing else.
"""
        try:
            resp = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                response_format={"type": "json_object"},
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

    # ── Backward-compat alias (remove once all callers updated) ───────────────
    def extract_governance_ontology(self, text: str) -> dict:
        return self.extract_ontology(text, source_type="unstructured_llm")

    # ── 2. Evidence relevance scoring ─────────────────────────────────────────
    def score_evidence(self, text: str, asset_name: str, ward_name: str) -> dict:
        """
        Score how relevant a news/text snippet is to a specific infrastructure asset.
        Returns: key_fact, relevance, confidence (0.0–1.0).
        """
        if not self.client:
            return {
                "key_fact": f"[Mock] Identified reference to {asset_name} in {ward_name}.",
                "relevance": "Context Match",
                "confidence": 0.5,
            }

        prompt = f"""
You are a governance data extraction AI.
Analyze the following news snippet and determine its relevance to a specific infrastructure project.

Asset Name: {asset_name}
Location: {ward_name}

News Snippet:
{text}

Extract the most critical 'key_fact' regarding the completion, budget, or
status of this asset. Determine the 'relevance' category:
  "Direct Match"   — article is specifically about this asset
  "Zone Context"   — article mentions the ward/zone but not this asset
  "National Context" — article discusses the scheme nationally
  "Unrelated"      — not relevant

Give a 'confidence' score 0.0–1.0.

Return ONLY valid JSON — no markdown, no explanation:
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

    def analyze_evidence(self, text: str, asset_name: str = "", ward_name: str = "") -> dict:
        return self.score_evidence(text, asset_name, ward_name)

ai_service = AIService()
