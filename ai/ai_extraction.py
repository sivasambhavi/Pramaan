"""
AI-based entity extraction for Pramaan.

Takes raw text (PIB press release, news article, field notes) and extracts
entities/relations into the 7-table schema using Groq LLM.

Responses are cached to ai/cache/ for offline demo reliability.
"""

import json
import hashlib
from pathlib import Path
from groq import Groq

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Canonical ID maps — used in the prompt to guide the LLM
REGION_MAP = {
    "ward 45": "REG_W45",
    "shahdara": "REG_W45",
    "gali 7": "REG_W45_GALI7",
    "gali no. 7": "REG_W45_GALI7",
    "shahdara market": "REG_W45_MARKET_ROAD",
    "block a": "REG_W45_BLOCKA",
    "colony y": "REG_W45_COLONY_Y",
}

SCHEME_MAP = {
    "sfc": "SCH_SFC",
    "local development": "SCH_SFC",
    "swachh bharat": "SCH_SWACHH",
    "sbm": "SCH_SWACHH",
    "pmay": "SCH_PMAY",
    "pradhan mantri awas": "SCH_PMAY",
    "streetlight": "SCH_LOCAL_LIGHTS",
    "led": "SCH_LOCAL_LIGHTS",
}

ACTOR_MAP = {
    "mcd": "ACT_MCD_SHAHDARA_WORKS",
    "shahdara works": "ACT_MCD_SHAHDARA_WORKS",
    "sanitation": "ACT_MCD_SHAHDARA_SANITATION",
    "electrical": "ACT_MCD_ELECTRICAL",
    "councillor": "ACT_W45_COUNCILLOR",
}

SYSTEM_PROMPT = """You are a governance data extraction assistant for the Pramaan platform.

Extract entities from the given text and return a JSON object with exactly this structure:
{
  "regions": [{"region_id": "", "name": "", "type": "ward|street|zone", "parent_region_id": ""}],
  "schemes": [{"scheme_id": "", "name": "", "ministry": "", "category": ""}],
  "actors": [{"actor_id": "", "name": "", "type": "government|contractor|elected_rep", "region_id": ""}],
  "assets": [{"asset_id": "", "name": "", "type": "drain|road|toilet|housing|streetlight|water_body", "region_id": "", "scheme_id": "", "actor_id": "", "cost": null, "status": "completed|in_progress|planned"}],
  "beneficiaries": [{"beneficiary_id": "", "scheme_id": "", "region_id": "", "count": null, "description": ""}],
  "evidence": [{"evidence_id": "", "asset_id": "", "region_id": "", "type": "image|document|certificate", "url": "", "before_or_after": "before|after", "capture_date": ""}],
  "events": [{"event_id": "", "name": "", "event_type": "completion|inauguration|handover", "date": "", "asset_id": ""}]
}

ID naming rules:
- Regions: REG_W45, REG_W45_GALI7, REG_SHAHDARA_SOUTH
- Schemes: SCH_SFC, SCH_SWACHH, SCH_PMAY, SCH_LOCAL_LIGHTS
- Actors: ACT_MCD_SHAHDARA_WORKS, ACT_W45_COUNCILLOR
- Assets: ASSET_<TYPE>_<LOCATION> e.g. ASSET_DRAIN_GALI7
- Evidence: EVD_<ASSET>_<BEFORE|AFTER>
- Events: EVT_<ASSET>_<TYPE>
- Beneficiaries: BEN_<LOCATION>_<SCHEME>

Known canonical IDs to reuse when text refers to them:
- "Ward 45" or "Shahdara" → REG_W45
- "Gali No. 7" or "Gali 7" → REG_W45_GALI7
- "SFC" or "Local Development Grants" → SCH_SFC, scheme_id: SCH_SFC
- "Swachh Bharat" or "SBM" → SCH_SWACHH
- "PMAY" or "Pradhan Mantri Awas" → SCH_PMAY
- "MCD" or "Shahdara Works" → ACT_MCD_SHAHDARA_WORKS

Return ONLY valid JSON. No explanation, no markdown, no code blocks."""


def _cache_path(text: str) -> Path:
    key = hashlib.md5(text.encode()).hexdigest()
    return CACHE_DIR / f"{key}.json"


def _load_cache(text: str) -> dict | None:
    path = _cache_path(text)
    if path.exists():
        return json.loads(path.read_text())
    return None


def _save_cache(text: str, result: dict) -> None:
    _cache_path(text).write_text(json.dumps(result, indent=2))


def extract_entities_and_relations(text: str, api_key: str, use_cache: bool = True) -> dict:
    """
    Extract governance entities from raw text using Groq LLM.

    Returns a dict with keys: regions, schemes, actors, assets,
    beneficiaries, evidence, events.

    Results are cached by MD5 of the input text.
    """
    if use_cache:
        cached = _load_cache(text)
        if cached:
            cached["_source"] = "cache"
            return cached

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract governance entities from this text:\n\n{text}"},
        ],
        temperature=0.1,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw)
    result["_source"] = "llm"

    if use_cache:
        _save_cache(text, result)

    return result
