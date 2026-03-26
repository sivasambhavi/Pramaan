"""
PRAMAAN — Unified AI Extraction Service

Global Ontology Engine — collects and understands content across:
  Geopolitics · Economics · Defense · Technology · Climate · Society · Governance

Three responsibilities:
  1. extract_ontology(text, source_type)  — extracts entities/relations into the global graph
  2. classify_content(text, topic)        — domain-aware relevance filter for the 7 domains
  3. score_evidence(text, asset_name, ward_name) — legacy ward-level asset scoring (kept for delivery monitor)

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
OLLAMA_HOST  = settings.ollama_host
OLLAMA_MODEL = settings.ollama_model

VALID_SOURCE_TYPES = {"unstructured_llm", "unstructured_rss"}

# ─── Canonical IDs already seeded in Neo4j ───────────────────────────────────
KNOWN_IDS_CONTEXT = """
IMPORTANT — The graph already contains these nodes. When the text mentions any
of them, use the EXACT ID listed. Do NOT invent a new ID for an existing entity.

Events:
  EVT_IRAN_WAR_2026          = Iran-US-Israel War (2026, ongoing — Hormuz blockade, oil spike)
  EVT_TWELVE_DAY_WAR_2025    = Twelve-Day War Israel-Iran (June 2025)
  EVT_OPERATION_SINDOOR_2025 = Operation Sindoor — India strikes Pakistan PoJK (May 7 2025)
  EVT_PAHALGAM_2025          = Pahalgam Terror Attack J&K, 26 killed (April 22 2025)
  EVT_INDIA_EXTREME_WEATHER_2025 = India Extreme Weather Year 2025 (331/334 days)
  EVT_INDIA_UK_CETA_2025     = India-UK Free Trade Agreement CETA (July 2025)
  EVT_SP_UPGRADE_2025        = S&P India Sovereign Rating Upgrade BBB (August 2025)
  EVT_ISRO_SPADEX_2025       = ISRO SpaDeX Satellite Docking Mission (January 2025)
  EVT_SHUKLA_ISS_2025        = First Indian on ISS — Shubhanshu Shukla (June 2025)
  EVT_INDIA_US_DEFENSE_2025  = India-US 10-Year Defence Partnership Framework (October 2025)
  EVT_CYCLONE_DANA_2024      = Cyclone Dana (Odisha/West Bengal, 2024)
  EVT_WAYANAD_2024           = Wayanad Landslide (Kerala, 2024)
  EVT_TATA_SEMI_2024         = Tata Electronics Semiconductor Fab groundbreaking (2024)
  EVT_GAZA_REDSEA_2023       = Gaza War and Red Sea Shipping Crisis (2023)
  EVT_INDIA_CANADA_2023      = India-Canada Diplomatic Row (2023)
  EVT_G20_INDIA_2023         = G20 New Delhi Summit (September 2023)
  EVT_IMEC_2023              = India-Middle East-Europe Corridor signing (2023)
  EVT_CHANDRAYAAN3_2023      = Chandrayaan-3 Moon Landing (2023)
  EVT_DELHI_FLOODS_2023      = Delhi Yamuna Floods (2023)

Actors — India Government:
  ACT_MEA          = Ministry of External Affairs India (S. Jaishankar)
  ACT_PMO          = Prime Minister's Office India (PM Modi)
  ACT_MOD          = Ministry of Defence India
  ACT_MOF          = Ministry of Finance India
  ACT_RBI          = Reserve Bank of India
  ACT_ISRO         = Indian Space Research Organisation
  ACT_DRDO         = Defence Research and Development Organisation
  ACT_MoPNG        = Ministry of Petroleum and Natural Gas India
  ACT_PPAC         = Petroleum Planning and Analysis Cell
  ACT_NDMA         = National Disaster Management Authority
  ACT_NDRF         = National Disaster Response Force
  ACT_PIB          = Press Information Bureau India

Actors — India PSU / Finance:
  ACT_HPCL         = Hindustan Petroleum Corporation Ltd
  ACT_BPCL         = Bharat Petroleum Corporation Ltd
  ACT_IOC          = Indian Oil Corporation
  ACT_GAIL         = GAIL India Ltd
  ACT_ONGC         = Oil and Natural Gas Corporation
  ACT_SBI          = State Bank of India
  ACT_NSE          = National Stock Exchange
  ACT_BSE          = Bombay Stock Exchange

Actors — Global:
  ACT_OPEC         = OPEC+ (oil cartel)
  ACT_US_STATE     = US State Department
  ACT_US_DOD       = US Department of Defense
  ACT_IAEA         = International Atomic Energy Agency
  ACT_UN           = United Nations
  ACT_UNSC         = UN Security Council
  ACT_IMF          = International Monetary Fund
  ACT_WORLD_BANK   = World Bank
  ACT_WTO          = World Trade Organization
  ACT_WHO          = World Health Organization
  ACT_IRAN_GOVT    = Government of Iran
  ACT_ISRAEL_GOVT  = Government of Israel
  ACT_PAKISTAN_ISI = Pakistan ISI / Military

Regions — Global:
  REG_INDIA        = India (country)
  REG_IRAN         = Iran
  REG_ISRAEL       = Israel
  REG_USA          = United States of America
  REG_CHINA        = China
  REG_PAKISTAN     = Pakistan
  REG_HORMUZ       = Strait of Hormuz (chokepoint)
  REG_PERSIAN_GULF = Persian Gulf
  REG_MIDDLE_EAST  = Middle East region
  REG_RED_SEA      = Red Sea / Bab-el-Mandeb
  REG_INDO_PACIFIC = Indo-Pacific region
  REG_IMEC         = IMEC Corridor (India-Middle East-Europe)

Regions — India:
  REG_DELHI        = Delhi (NCT)
  REG_KERALA       = Kerala
  REG_ODISHA       = Odisha
  REG_JK           = Jammu & Kashmir
  REG_W45          = Ward 45 Shahdara (Delhi, local delivery pilot)

Schemes / Policies — India:
  SCH_AMRUT        = AMRUT Urban Infrastructure Mission
  SCH_PMAY         = PMAY-Urban Housing Scheme
  SCH_SWACHH       = Swachh Bharat Mission Urban
  SCH_PLI          = Production Linked Incentive Scheme
  SCH_AYUSHMAN     = Ayushman Bharat PMJAY Health Insurance
  SCH_SPR          = India Strategic Petroleum Reserve (SPR)
  SCH_JJBY         = Jal Jeevan Mission

Only create a NEW id (e.g. "evt_iran_ceasefire_2026") if the entity is genuinely
not in this list. Use snake_case prefix matching the label type.
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
You are a Global Ontology Engine for India intelligence.
Extract significant entities and relationships from the text across 7 domains:
  Geopolitics · Economics · Defense · Technology · Climate · Society · Governance

{KNOWN_IDS_CONTEXT}

── ENTITY LABEL DEFINITIONS ──────────────────────────────────────────────────

EVENT — A specific, discrete occurrence that:
  ✓ Happened at a point in time or narrow window (has or can have a date)
  ✓ Is nationally or strategically significant for India
  ✓ Is a thing that HAPPENED, not a standing state, law, or ongoing condition
  ✓ Severity must be high or critical to qualify as a standalone Event
  Examples that ARE Events:
    Wayanad Landslide (happened on a date, mass casualties)
    Operation Sindoor (military strike, specific date)
    Chandrayaan-3 Moon Landing (specific mission success date)
    Cyclone Dana making landfall (specific natural disaster)
    India-UK CETA signing (treaty signed on a specific date)
    INR crossing 87/USD threshold (specific market shock event)
  Examples that are NOT Events — use the correct label instead:
    "National Sports Policy" → label as Policy
    "GST rate changes" → label as Policy (ongoing fiscal rule)
    "India's Foreign Policy" → too vague, skip entirely
    "Delhi road construction" → label as Asset or skip
    "National Policy on Senior Citizens" → label as Policy
    "Swachh Bharat Mission" → label as Scheme
    "India inflation" → label as Impact (economic metric), not Event
      unless it is a specific crisis date (e.g. "Inflation hits 8.5% — RBI emergency meet")

POLICY  — A law, regulation, or standing government directive (not time-bounded)
SCHEME  — A government funding programme or welfare scheme with a scheme ID
ACTOR   — A government body, agency, PSU, international org, or named individual
REGION  — A geographic location: country, state, city, or strategic chokepoint
IMPACT  — A measurable outcome or consequence (deaths, displaced persons, ₹ loss)
EVIDENCE — A specific document, report, satellite image, or data source
ASSET   — A physical infrastructure asset (dam, power plant, road)

── Text ───────────────────────────────────────────────────────────────────────
{text}

── Output Format ──────────────────────────────────────────────────────────────
Return ONLY valid JSON — no markdown, no explanation, no code blocks.

{{
  "entities": [
    {{
      "id": "<use existing ID from context above, or snake_case new id>",
      "label": "<Event|Actor|Region|Scheme|Policy|Impact|Evidence|Asset|Domain>",
      "properties": {{
        "name": "<human-readable name>",
        "domain": "<DOM_GEOPOLITICS|DOM_ECONOMICS|DOM_DEFENSE|DOM_TECHNOLOGY|DOM_CLIMATE|DOM_SOCIETY|DOM_GOVERNANCE>",
        "date": "<YYYY-MM-DD if known>",
        "description": "<1-2 sentence summary>",
        "severity": "<critical|high|medium|low — for Events only>",
        "confidence": <0.0–1.0>
      }}
    }}
  ],
  "relations": [
    {{
      "from_id": "<id>", "from_label": "<label>",
      "to_id":   "<id>", "to_label":   "<label>",
      "type": "<CAUSED|TRIGGERED|FUNDS|BENEFITS|PROVES|BUILT_BY|LOCATED_IN|CONNECTED_TO|OCCURRED_IN|BELONGS_TO|MANAGED_BY>"
    }}
  ]
}}

── Examples ───────────────────────────────────────────────────────────────────

Geopolitics (Event — specific military operation):
  {{"id": "EVT_OPERATION_SINDOOR_2025", "label": "Event", "properties": {{"name": "Operation Sindoor", "domain": "DOM_DEFENSE", "severity": "critical", "date": "2025-05-07", "confidence": 0.95}}}}
  {{"id": "ACT_MOD", "label": "Actor", "properties": {{"name": "Ministry of Defence India", "confidence": 0.95}}}}
  Relation: {{"from_id": "EVT_OPERATION_SINDOOR_2025", "from_label": "Event", "to_id": "REG_JK", "to_label": "Region", "type": "OCCURRED_IN"}}

Economics (Event — specific market shock, not an ongoing metric):
  {{"id": "evt_rupee_crisis_2026", "label": "Event", "properties": {{"name": "INR/USD hits 90 — RBI intervention", "domain": "DOM_ECONOMICS", "severity": "high", "date": "2026-03-10", "confidence": 0.85}}}}

Economics (Policy — NOT an Event):
  {{"id": "pol_gst_amendment_2026", "label": "Policy", "properties": {{"name": "GST Rate Rationalisation 2026", "domain": "DOM_GOVERNANCE", "confidence": 0.9}}}}

Climate (Event — specific disaster):
  {{"id": "EVT_WAYANAD_2024", "label": "Event", "properties": {{"name": "Wayanad Landslide 2024", "domain": "DOM_CLIMATE", "severity": "high", "confidence": 0.95}}}}
  {{"id": "imp_wayanad_dead", "label": "Impact", "properties": {{"name": "231 deaths — Wayanad", "domain": "DOM_CLIMATE", "confidence": 0.95}}}}

Governance (Scheme — NOT an Event):
  {{"id": "SCH_PLI", "label": "Scheme", "properties": {{"name": "PLI Scheme", "domain": "DOM_GOVERNANCE", "confidence": 0.95}}}}

── Rules ──────────────────────────────────────────────────────────────────────
- ALWAYS reuse IDs from the IMPORTANT context above when the entity matches.
- For new entities use snake_case prefixes: evt_, act_, reg_, sch_, pol_, imp_, ev_, ast_
- Only label something Event if it passes the Event definition above — when in doubt use Policy, Impact, or skip.
- confidence: 1.0 = explicitly stated in text · 0.6 = inferred · below 0.6 = omit entity.
- Omit fields you cannot determine — do NOT guess dates or numbers.
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
You are a governance data extraction AI for India.
Analyze the following news snippet and determine its relevance to India governance, policy, or national interest.

Topic: {asset_name}
Scope: {ward_name}

News Snippet:
{text}

Extract the most critical 'key_fact'. Determine the 'relevance' category:
  "Direct Match"     — article is specifically about this topic
  "Zone Context"     — article is about the same region or domain
  "National Context" — article is relevant to India governance, economy, policy, geopolitics, or national security
  "Unrelated"        — not relevant to India or governance at all

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

    # ── 3. Domain-aware content classification ────────────────────────────────
    def classify_content(self, text: str, topic: str = "") -> dict:
        """
        Determine whether text is relevant to India's national interest across
        7 governance domains. Replaces ward-level score_evidence for ingestion.

        Returns:
          {
            "relevant":   bool,
            "domain":     "DOM_GEOPOLITICS|DOM_ECONOMICS|DOM_DEFENSE|DOM_TECHNOLOGY|DOM_CLIMATE|DOM_SOCIETY|DOM_GOVERNANCE",
            "confidence": float,
            "reason":     str
          }
        """
        _fallback = {
            "relevant":   True,
            "domain":     "DOM_GOVERNANCE",
            "confidence": 0.5,
            "reason":     "Fallback — no LLM available",
        }

        prompt = f"""
You are a relevance classifier for the PRAMAAN Global Ontology Engine — India intelligence platform.

Your job: decide if the following content is relevant to India's national interest across any of the 7 domains:
  DOM_GEOPOLITICS  — foreign policy, wars, diplomacy, border disputes, UN, global alliances
  DOM_ECONOMICS    — GDP, inflation, trade, FDI, rupee, oil prices, markets, RBI, budget
  DOM_DEFENSE      — armed forces, DRDO, defence procurement, terrorism, military operations
  DOM_TECHNOLOGY   — ISRO, space, semiconductors, AI policy, digital India, cyber, EV, telecom
  DOM_CLIMATE      — disasters, cyclones, floods, drought, heatwave, environment, green energy
  DOM_SOCIETY      — health, education, poverty, women, youth, religion, social movements
  DOM_GOVERNANCE   — government schemes, policies, Parliament, elections, infrastructure, law

Topic hint: {topic or "none"}

Text:
{text}

Answer ONLY with valid JSON. No markdown, no explanation:
{{
  "relevant":   true or false,
  "domain":     "DOM_GEOPOLITICS|DOM_ECONOMICS|DOM_DEFENSE|DOM_TECHNOLOGY|DOM_CLIMATE|DOM_SOCIETY|DOM_GOVERNANCE",
  "confidence": 0.0 to 1.0,
  "reason":     "one-sentence explanation"
}}

Rules:
- relevant=true if the content relates to India OR has direct impact on India (e.g. oil war affecting INR).
- relevant=false ONLY for purely local/foreign content with zero India relevance.
- Pick the single best-fit domain.
"""

        def _parse_classify(raw: str) -> dict:
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            result.setdefault("relevant",   True)
            result.setdefault("domain",     "DOM_GOVERNANCE")
            result.setdefault("confidence", 0.6)
            result.setdefault("reason",     "")
            return result

        # Ollama first
        if self.ollama_available:
            try:
                raw = self._call_ollama(prompt)
                result = _parse_classify(raw)
                logger.info("[ai] classify_content via Ollama — relevant=%s domain=%s",
                            result["relevant"], result["domain"])
                return result
            except Exception as e:
                logger.warning("[ai] Ollama classify_content failed, falling back: %s", e)

        # Groq second
        if self.client:
            try:
                chat = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                return _parse_classify(chat.choices[0].message.content)
            except Exception as e:
                if self._is_rate_limit_error(e) and self.gemini:
                    logger.warning("Groq rate-limited — falling back to Gemini for classify_content")
                else:
                    logger.error("[ai] classify_content Groq failed: %s", e)
                    return _fallback

        # Gemini fallback
        if self.gemini:
            try:
                raw = self._call_gemini(prompt)
                return _parse_classify(raw)
            except Exception as e:
                logger.error("[ai] classify_content Gemini also failed: %s", e)

        return _fallback

    # ── 4. Crisis sub-event extraction ───────────────────────────────────────
    def extract_crisis_update(self, text: str, parent_event_id: str, parent_event_name: str) -> dict:
        """
        Given a news article about an ongoing crisis, extract:
          - SubEvent nodes (specific daily developments)
          - Indicator updates (metric changes: oil price, INR, etc.)
          - Decision nodes (India policy responses)

        Returns: { subevents: [...], indicators: [...], decisions: [...] }
        """
        _fallback = {"subevents": [], "indicators": [], "decisions": []}
        if not self.client and not self.gemini:
            return _fallback

        prompt = f"""
You are a crisis intelligence analyst for the PRAMAAN India decision-support platform.

The following news article describes a development in an ongoing crisis:
  Crisis: {parent_event_name} (ID: {parent_event_id})

Extract structured updates from the text below.

── Text ────────────────────────────────────────────────────────────────────
{text}

── Output Format ────────────────────────────────────────────────────────────
Return ONLY valid JSON — no markdown, no explanation.

{{
  "subevents": [
    {{
      "subevent_id": "SE_<PARENT_SHORT>_<YYYYMMDD>_<slug>",
      "name": "<concise title of this specific development>",
      "date": "<YYYY-MM-DD>",
      "category": "<military|diplomatic|economic|policy|humanitarian>",
      "description": "<2-3 sentence factual summary>",
      "severity": "<critical|high|medium|low>",
      "india_impact": "<1 sentence — specific impact on India or blank if none>",
      "actors": ["<actor_id if known, else actor name>"]
    }}
  ],
  "indicators": [
    {{
      "indicator_id": "<IND_SLUG>",
      "name": "<metric name>",
      "value": <numeric value>,
      "unit": "<USD/bbl | INR/USD | % | days | vessels/day | persons>",
      "trend": "<rising|falling|stable|volatile_high|critically_low>",
      "as_of": "<YYYY-MM-DD>"
    }}
  ],
  "decisions": [
    {{
      "decision_id": "DEC_<YYYYMMDD>_<slug>",
      "name": "<decision title>",
      "decided_by": "<actor_id e.g. ACT_PMO, ACT_RBI, ACT_MEA, ACT_MoPNG>",
      "date": "<YYYY-MM-DD>",
      "status": "<pending|executed|active|cancelled>",
      "description": "<what was decided and why>"
    }}
  ]
}}

Rules:
- Only extract subevents that are NEW developments (not background context).
- Only extract indicators if a specific numeric value is mentioned.
- Only extract decisions if India (government/RBI/MEA) takes a specific action.
- If nothing fits a category, return an empty list for it.
- subevent_id must use parent prefix: e.g. SE_IRAN_WAR_20260326_ceasefire
"""
        def _parse(raw: str) -> dict:
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            result.setdefault("subevents",  [])
            result.setdefault("indicators", [])
            result.setdefault("decisions",  [])
            return result

        if self.ollama_available:
            try:
                return _parse(self._call_ollama(prompt))
            except Exception as e:
                logger.warning("[ai] Ollama extract_crisis_update failed: %s", e)

        if self.client:
            try:
                chat = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                return _parse(chat.choices[0].message.content)
            except Exception as e:
                if self._is_rate_limit_error(e) and self.gemini:
                    logger.warning("Groq rate-limited — falling back to Gemini for crisis update")
                else:
                    logger.error("[ai] extract_crisis_update Groq failed: %s", e)
                    return _fallback

        if self.gemini:
            try:
                return _parse(self._call_gemini(prompt))
            except Exception as e:
                logger.error("[ai] extract_crisis_update Gemini failed: %s", e)

        return _fallback

    # ── 5. Scenario generation ────────────────────────────────────────────────
    def generate_scenarios(self, event_name: str, subevents_summary: str,
                           indicators_summary: str, decisions_summary: str) -> dict:
        """
        Given current crisis state (sub-events, indicators, India decisions),
        generate 3 scenario branches with India action plans.

        Returns: { scenarios: [ {name, probability, timeline, india_impact, india_actions}, ... ] }
        """
        _fallback = {"scenarios": []}
        if not self.client and not self.gemini:
            return _fallback

        prompt = f"""
You are a senior strategic analyst advising the Indian National Security Council.

Crisis: {event_name}

Current situation:
── Recent Developments ──
{subevents_summary}

── India Impact Indicators ──
{indicators_summary}

── India Decisions Taken ──
{decisions_summary}

Generate EXACTLY 3 scenario branches for the next 60 days.
Each scenario must be mutually exclusive and cover the realistic spectrum.

Return ONLY valid JSON — no markdown.

{{
  "scenarios": [
    {{
      "scenario_id": "SCN_A",
      "name": "<short scenario name>",
      "label": "<Best Case|Base Case|Worst Case>",
      "probability": <0.0 to 1.0, all 3 must sum to 1.0>,
      "timeline": "<when this resolves or peaks — e.g. '30 days', '60-90 days'>",
      "trigger": "<what would cause this scenario to materialise>",
      "india_impact": {{
        "oil_supply": "<impact description>",
        "economy": "<GDP/INR/inflation impact>",
        "diplomacy": "<India's strategic position>",
        "security": "<any direct security implications>"
      }},
      "india_actions": [
        "<specific actionable recommendation for India — what to do NOW>",
        "<second action>",
        "<third action>"
      ],
      "warning_signals": ["<leading indicator to watch>"]
    }}
  ]
}}
"""
        def _parse(raw: str) -> dict:
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            result.setdefault("scenarios", [])
            return result

        if self.ollama_available:
            try:
                return _parse(self._call_ollama(prompt))
            except Exception as e:
                logger.warning("[ai] Ollama generate_scenarios failed: %s", e)

        if self.client:
            try:
                chat = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                return _parse(chat.choices[0].message.content)
            except Exception as e:
                if self._is_rate_limit_error(e) and self.gemini:
                    logger.warning("Groq rate-limited — falling back to Gemini for scenarios")
                else:
                    logger.error("[ai] generate_scenarios Groq failed: %s", e)
                    return _fallback

        if self.gemini:
            try:
                return _parse(self._call_gemini(prompt))
            except Exception as e:
                logger.error("[ai] generate_scenarios Gemini failed: %s", e)

        return _fallback


ai_service = AIService()
