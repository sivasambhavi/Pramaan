"""
PRAMAAN — Unified AI Extraction Service

Two responsibilities:
  1. extract_ontology(text, source_type)  — extracts entities/relations from any text
  2. score_evidence(text, asset_name, ward_name) — scores relevance of a news snippet to an asset

source_type must be one of:
  unstructured_llm   — user-pasted text (POST /scrape/analyze)
  unstructured_rss   — RSS / news headline (GET /scrape/news)

LLM priority chain:
  1. Ollama (local — llama3, mistral, deepseek-coder)
  2. Groq (remote — llama-3.3-70b)
  3. Gemini (remote — gemini-1.5-flash)
"""

import os
import json
import logging
import requests as _requests
from groq import Groq
import google.generativeai as genai
from app.config import settings
from app.utils.retry import retryable

logger = logging.getLogger(__name__)

# ─── Ollama config ────────────────────────────────────────────────────────────
OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://192.168.48.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:latest")

VALID_SOURCE_TYPES = {"unstructured_llm", "unstructured_rss"}

# ─── Canonical IDs already seeded in Neo4j ───────────────────────────────────
KNOWN_IDS_CONTEXT = """
IMPORTANT — The graph already contains these nodes. When the text mentions any
of them, use the EXACT ID listed. Do NOT invent a new ID for an existing entity.

Events (use these IDs when text mentions the same event):
  EVT_IRAN_WAR_2026          = Iran-US-Israel War (2026, ongoing — Hormuz blockade, oil spike)
  EVT_TWELVE_DAY_WAR_2025    = Twelve-Day War Israel-Iran (June 2025)
  EVT_OPERATION_SINDOOR_2025 = Operation Sindoor India strikes Pakistan PoJK (May 7 2025)
  EVT_PAHALGAM_2025          = Pahalgam Terror Attack J&K 26 killed (April 22 2025)
  EVT_INDIA_EXTREME_WEATHER_2025 = India Extreme Weather Year 2025 (331/334 days)
  EVT_INDIA_UK_CETA_2025     = India-UK Trade Agreement CETA (July 2025)
  EVT_SP_UPGRADE_2025        = S&P Sovereign Rating Upgrade BBB (August 2025)
  EVT_LABOUR_CODES_2025      = Four Labour Codes Enforcement (November 2025)
  EVT_ISRO_SPADEX_2025       = ISRO SpaDeX Satellite Docking (January 2025)
  EVT_SHUKLA_ISS_2025        = First Indian on ISS Shubhanshu Shukla (June 2025)
  EVT_INDIA_US_DEFENSE_2025  = India-US 10-Year Defence Partnership Framework (October 2025)
  EVT_CYCLONE_DANA_2024      = Cyclone Dana (2024, Odisha/West Bengal)
  EVT_WAYANAD_2024           = Wayanad Landslide (2024, Kerala)
  EVT_TATA_SEMI_2024         = Tata Semiconductor Fab (2024)
  EVT_GAZA_REDSEA_2023       = Gaza War & Red Sea Crisis (2023)
  EVT_INDIA_CANADA_2023      = India-Canada Diplomatic Row (2023)
  EVT_G20_INDIA_2023         = G20 New Delhi Summit (2023)
  EVT_IMEC_2023              = IMEC Corridor Signing (2023)
  EVT_ADITYAL1_2023          = Aditya-L1 Solar Mission (2023)
  EVT_CHANDRAYAAN3_2023      = Chandrayaan-3 Moon Landing (2023)
  EVT_DELHI_FLOODS_2023      = Delhi Yamuna Floods (2023)
  EVT_MANIPUR_2023           = Manipur Ethnic Violence (2023)
  EVT_JOSHIMATH_2023         = Joshimath Land Subsidence (2023, Uttarakhand)

Schemes:
  SCH_AMRUT        = AMRUT (Atal Mission for Rejuvenation and Urban Transformation)
  SCH_PMAY         = PMAY-Urban (Pradhan Mantri Awas Yojana)
  SCH_SWACHH       = Swachh Bharat Mission - Urban
  SCH_SFC          = Local Development Grants - Roads & Drains (Delhi SFC)
  SCH_LOCAL_LIGHTS = Urban Streetlight Improvement (Delhi)
  SCH_JJBY         = Jal Jeevan Mission (Har Ghar Jal)
  SCH_AYUSHMAN     = Ayushman Bharat PMJAY

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

Only create a NEW id (e.g. "evt_flood_2025") if the entity is genuinely not in
this list and is not a synonym/alias for any entry above.
"""

class AIService:
    def __init__(self):
        # ── Primary: Ollama (local) ───────────────────────────────────────────
        self.ollama_available = False
        try:
            resp = _requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                self.ollama_available = True
                logger.info("AIService: Ollama available at %s — models: %s", OLLAMA_HOST, models)
            else:
                logger.warning("AIService: Ollama responded %d — skipping", resp.status_code)
        except Exception as e:
            logger.warning("AIService: Ollama not reachable at %s: %s", OLLAMA_HOST, e)

        # ── Secondary: Groq ───────────────────────────────────────────────────
        self.client = None
        groq_key = settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                self.client = Groq(api_key=groq_key)
                logger.info("AIService: Groq client initialised (secondary)")
            except Exception as e:
                logger.warning(f"Could not init Groq client: {e}")
        else:
            logger.warning("GROQ_API_KEY not set — will fall back to Gemini if available")

        # ── Tertiary: Gemini ──────────────────────────────────────────────────
        self.gemini = None
        gemini_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("AIService: Gemini client initialised (tertiary)")
            except Exception as e:
                logger.warning(f"Could not init Gemini client: {e}")

    def _call_ollama(self, prompt: str, model: str = None) -> str:
        """Call Ollama local LLM and return raw text response."""
        m = model or OLLAMA_MODEL
        resp = _requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": m, "prompt": prompt, "stream": False, "format": "json"},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()

    def _is_rate_limit_error(self, e: Exception) -> bool:
        err = str(e)
        return "429" in err or "rate_limit_exceeded" in err or "quota" in err.lower()

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini Flash and return raw text response."""
        resp = self.gemini.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        return resp.text.strip()

    # ── 1. Entity + relation extraction ──────────────────────────────────────
    def extract_ontology(self, text: str, source_type: str = "unstructured_llm") -> dict:
        """
        Extract governance entities and relations from raw text.
        Tries Groq first; falls back to Gemini on rate limit.
        Returns a dict with: entities, relations, source_type, success.
        """
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type '{source_type}'. Must be one of: {VALID_SOURCE_TYPES}")
        if not self.client and not self.gemini:
            return {
                "success": False,
                "error": "No AI provider configured (set GROQ_API_KEY or GOOGLE_API_KEY)",
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
    {{"id": "EVT_WAYANAD_2024",  "label": "Event",  "properties": {{"name": "Wayanad Landslide", "date": "2024-07-30", "domain": "DOM_CLIMATE", "severity": "high", "description": "brief event description", "confidence": 0.9}}}},
    {{"id": "evt_new_flood_2025","label": "Event",  "properties": {{"name": "New Event Name", "date": "2025-01-15", "domain": "DOM_CLIMATE/DOM_GEOPOLITICS/DOM_TECHNOLOGY/DOM_ECONOMICS/DOM_GOVERNANCE/DOM_DEFENSE/DOM_SOCIETY", "severity": "high/medium/low", "description": "brief description", "confidence": 0.8}}}},
    {{"id": "SCH_AMRUT", "label": "Scheme", "properties": {{"name": "AMRUT", "ministry": "MoHUA", "category": "infrastructure", "confidence": 0.95}}}},
    {{"id": "REG_W45",   "label": "Region", "properties": {{"name": "Ward 45 Shahdara", "type": "ward", "confidence": 0.9}}}},
    {{"id": "asset_new_1","label": "Asset",  "properties": {{"name": "asset description", "type": "drain/road/toilet/housing/park/streetlight/other", "cost": 1200000, "status": "completed/in_progress/planned", "confidence": 0.8}}}},
    {{"id": "ACT_MCD_SHAHDARA_WORKS","label": "Actor", "properties": {{"name": "MCD Shahdara North Works Dept", "type": "government", "confidence": 0.85}}}},
    {{"id": "ben_new_1", "label": "Beneficiary", "properties": {{"count": 100, "description": "households benefiting", "confidence": 0.7}}}},
    {{"id": "ev_new_1",  "label": "Evidence",    "properties": {{"type": "photo/report/certificate", "description": "what the evidence shows", "confidence": 0.75}}}}
  ],
  "relations": [
    {{"from_id": "evt_new_flood_2025", "from_label": "Event", "to_id": "REG_W45", "to_label": "Region", "type": "OCCURRED_IN"}},
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
        def _parse(raw: str) -> dict:
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            result["source_type"] = source_type
            result["success"]     = True
            result.setdefault("entities",  [])
            result.setdefault("relations", [])
            return result

        # ── Try Ollama first (local) ──────────────────────────────────────────
        if self.ollama_available:
            try:
                raw = self._call_ollama(prompt)
                result = _parse(raw)
                logger.info("[ai] extract_ontology via Ollama — %d entities", len(result.get("entities", [])))
                return result
            except Exception as e:
                logger.warning("[ai] Ollama extract failed, falling back: %s", e)

        # ── Try Groq second ───────────────────────────────────────────────────
        if self.client:
            @retryable(retries=2, delay=2.0, backoff=2.0, label="Groq.extract_governance_ontology")
            def _call_groq():
                return self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
            try:
                chat = _call_groq()
                return _parse(chat.choices[0].message.content)
            except json.JSONDecodeError as e:
                logger.error(f"Groq JSON parse error: {e}")
                return {"success": False, "source_type": source_type,
                        "error": f"LLM returned invalid JSON: {e}",
                        "entities": [], "relations": []}
            except Exception as e:
                if self._is_rate_limit_error(e) and self.gemini:
                    logger.warning("Groq rate-limited — falling back to Gemini")
                else:
                    logger.error(f"Groq extraction failed: {e}")
                    return {"success": False, "source_type": source_type,
                            "error": str(e), "entities": [], "relations": []}

        # ── Fallback: Gemini ──────────────────────────────────────────────────
        if self.gemini:
            try:
                raw = self._call_gemini(prompt)
                logger.info("Gemini fallback used for extract_ontology")
                return _parse(raw)
            except json.JSONDecodeError as e:
                logger.error(f"Gemini JSON parse error: {e}")
                return {"success": False, "source_type": source_type,
                        "error": f"Gemini returned invalid JSON: {e}",
                        "entities": [], "relations": []}
            except Exception as e:
                logger.error(f"Gemini extraction also failed: {e}")
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
        _fallback = {"key_fact": f"Fallback: Found mention of {asset_name}.",
                     "relevance": "Context Match", "confidence": 0.5}

        # ── Try Ollama first ──────────────────────────────────────────────────
        if self.ollama_available:
            try:
                raw = self._call_ollama(prompt, model="mistral:latest")
                result = json.loads(raw)
                logger.info("[ai] score_evidence via Ollama — relevance=%s", result.get("relevance"))
                return result
            except Exception as e:
                logger.warning("[ai] Ollama score_evidence failed, falling back: %s", e)

        # ── Try Groq second ───────────────────────────────────────────────────
        if self.client:
            @retryable(retries=2, delay=2.0, backoff=2.0, label="Groq.analyze_evidence")
            def _call_groq():
                return self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
            try:
                resp = _call_groq()
                return json.loads(resp.choices[0].message.content.strip())
            except Exception as e:
                if self._is_rate_limit_error(e) and self.gemini:
                    logger.warning("Groq rate-limited — falling back to Gemini for score_evidence")
                else:
                    logger.error(f"score_evidence Groq failed: {e}")
                    return _fallback

        # ── Fallback: Gemini ──────────────────────────────────────────────────
        if self.gemini:
            try:
                raw = self._call_gemini(prompt)
                return json.loads(raw)
            except Exception as e:
                logger.error(f"score_evidence Gemini also failed: {e}")

        return _fallback

    def analyze_evidence(self, text: str, asset_name: str = "", ward_name: str = "") -> dict:
        return self.score_evidence(text, asset_name, ward_name)

ai_service = AIService()
