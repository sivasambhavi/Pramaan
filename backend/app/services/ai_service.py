import os
from groq import Groq
from app.config import settings
import json

class AIService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def extract_governance_ontology(self, text: str) -> dict:
        """Extract 7-table ontology entities and relations using Groq (Llama 3)."""
        prompt = f"""
        Analyze the following Indian governance news headlines and summaries. 
        Extract any entities and relationships according to the PRAMAAN 7-table ontology.
        
        CRITICAL RULES:
        1. BE AGGRESSIVE: If a headline mentions a project or location, extract it even if details are sparse.
        2. ENTITY TYPES: 
           - Region: Delhi wards (e.g., Ward 45), neighborhoods, or cities.
           - Scheme: Governance programs (AMRUT, Swachh Bharat, SFC, etc.).
           - Actor: Agencies (MCD, DJB, PWD) or contractors.
           - Asset: Physical work (STP, Drain, Road, Park, Waterbody).
        3. ID GENERATION: Use snake_case IDs. e.g., 'mcd_engineering' or 'tahirpur_drain'.
        4. SPATIAL DATA: If a known Delhi neighborhood is mentioned, use representative Delhi coordinates if you know them.

        OUTPUT FORMAT (STRICT JSON):
        {{
          "entities": [
            {{ "id": "id", "label": "Region|Scheme|Actor|Asset", "properties": {{ "name": "...", "type": "...", "status": "..." }} }}
          ],
          "relations": [
            {{ "from_id": "id1", "from_label": "Label1", "to_id": "id2", "to_label": "Label2", "type": "FUNDS|LOCATED_IN|BUILT_BY|BENEFITS" }}
          ]
        }}

        NEWS CONTENT:
        {text}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized Knowledge Graph Extraction agent for Indian Governance data. Output ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            print(f"Error in Groq extraction: {e}")
            import traceback
            traceback.print_exc()
            return {"entities": [], "relations": []}

ai_service = AIService()
