import os
from groq import Groq
from app.config import settings
import json

class AIService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def extract_governance_ontology(self, text: str) -> dict:
        prompt = f"""
You are a governance data extraction assistant for India.
Extract entities from the following governance text and return ONLY valid JSON. No explanation, no markdown, no code blocks.

Text: {text}

Extract and return this exact JSON structure:
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
- confidence must be a float 0.0–1.0 reflecting how certain you are about this entity from the text.
- Return ONLY the JSON object. Nothing else.
"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.0
            )
            raw = chat_completion.choices[0].message.content.strip()
            # Strip markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            
            result = json.loads(raw)
            # Make sure it matches the expected structure structure for ingest response
            result["success"] = True
            if "entities" not in result:
                result["entities"] = []
            if "relations" not in result:
                result["relations"] = []
            return result
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError in AI: {e}\nRaw: {raw}")
            return {"success": False, "error": f"AI returned invalid JSON: {str(e)}", "raw": raw if 'raw' in locals() else "no response", "entities": [], "relations": []}
        except Exception as e:
            print(f"Error in Groq extraction: {e}")
            return {"success": False, "error": f"Extraction failed: {str(e)}", "entities": [], "relations": []}

ai_service = AIService()
