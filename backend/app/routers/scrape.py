"""
scrape.py — PRAMAAN Scrape Router

Fix 4 applied: Added POST /scrape/analyze-evidence endpoint so that
               llm_extractor.py (frontend) can delegate to the unified
               AIService instead of maintaining its own Groq client.
               Now there is ONE LLM client in the entire codebase.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.news_service import news_service
from app.services.ai_service import ai_service

router = APIRouter(prefix="/scrape", tags=["scrape"])


# ─── GET /scrape/news ─────────────────────────────────────────────────────────

@router.get("/news")
async def scrape_and_analyze(q: str = Query(..., description="Governance news search query")):
    """Scrape Google News RSS for a query and return AI-extracted ontology."""
    try:
        articles = news_service.fetch_google_news(q)
        if not articles:
            return {"entities": [], "relations": [], "articles": []}

        combined_text = "\n\n".join(
            [f"Headline: {a['title']}\nSummary: {a['summary']}" for a in articles]
        )
        extracted = ai_service.extract_governance_ontology(combined_text)
        extracted["articles"] = articles
        return extracted
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /scrape/analyze ─────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str


@router.post("/analyze")
async def analyze_text(payload: AnalyzeRequest):
    """
    Extract governance entities + relations from arbitrary text.
    Used by the Live Ingestion page for pasted press-release / report text.
    """
    try:
        return ai_service.extract_governance_ontology(payload.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /scrape/analyze-evidence ───────────────────────────────────────────
# Fix 4: New endpoint so llm_extractor.py delegates here instead of
#        maintaining its own Groq client.

class EvidenceRequest(BaseModel):
    text:       str
    asset_name: str = ""
    ward_name:  str = ""


@router.post("/analyze-evidence")
async def analyze_evidence(payload: EvidenceRequest):
    """
    Analyse a news / evidence snippet against a specific asset + ward.
    Returns: {"key_fact": str, "relevance": str, "confidence": float}

    Called by the Proof Chain page (frontend/pages/02_Proof_Chain.py)
    via ai/llm_extractor.py → this endpoint → AIService.analyze_evidence().
    Single LLM code path for the entire codebase.
    """
    try:
        result = ai_service.analyze_evidence(
            text=payload.text,
            asset_name=payload.asset_name,
            ward_name=payload.ward_name,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
