"""
scrape.py — PRAMAAN Scrape Router

Fix 4 applied: Added POST /scrape/analyze-evidence endpoint so that
               llm_extractor.py (frontend) can delegate to the unified
               AIService instead of maintaining its own Groq client.
               Now there is ONE LLM client in the entire codebase.

Validation Gate 4: /scrape/news now scores each article's relevance before
               extraction. Articles scoring "Unrelated" are dropped before
               any entity extraction, reducing hallucination risk upstream.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.news_service import news_service
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scrape"])

# Relevance values considered useful for ingestion
_INGESTIBLE_RELEVANCE = {"Direct Match", "Zone Context", "National Context"}

# ─── GET /scrape/news ─────────────────────────────────────────────────────────

@router.get("/news")
async def scrape_and_analyze(q: str = Query(..., description="Governance news search query")):
    """
    Scrape Google News RSS, pre-filter Unrelated articles (Gate 4),
    then extract governance ontology from the relevant ones only.
    Returns extracted entities, relations, kept articles, and dropped count.
    source_type=unstructured_rss
    """
    try:
        articles = news_service.fetch_google_news(q)
        if not articles:
            return {
                "entities": [], "relations": [], "articles": [],
                "source_type": "unstructured_rss",
                "articles_dropped": 0,
            }

        # ── Gate 4: score each article for relevance before extraction ───────
        relevant_articles = []
        dropped = 0
        for article in articles:
            snippet = f"{article.get('title', '')} {article.get('summary', '')}"
            scored  = ai_service.score_evidence(
                text=snippet,
                asset_name=q,          # query as proxy asset name
                ward_name="Delhi",
            )
            relevance = scored.get("relevance", "")
            if relevance in _INGESTIBLE_RELEVANCE:
                article["relevance"]  = relevance
                article["confidence"] = scored.get("confidence", 0.5)
                relevant_articles.append(article)
            else:
                dropped += 1
                logger.info("[scrape] DROPPED article (relevance=%r): %s", relevance, article.get("title", "")[:80])

        if not relevant_articles:
            return {
                "entities": [], "relations": [],
                "articles": [], "articles_dropped": dropped,
                "source_type": "unstructured_rss",
                "message": "All articles were Unrelated to the query — nothing ingested.",
            }

        # ── Extract ontology only from relevant articles ───────────────────
        combined_text = "\n\n".join(
            [f"Headline: {a['title']}\nSummary: {a['summary']}" for a in relevant_articles]
        )
        extracted = ai_service.extract_ontology(combined_text, source_type="unstructured_rss")
        extracted["articles"]         = relevant_articles
        extracted["articles_dropped"] = dropped
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
    source_type=unstructured_llm
    """
    try:
        return ai_service.extract_ontology(payload.text, source_type="unstructured_llm")
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
    via ai/llm_extractor.py → this endpoint → AIService.score_evidence().
    Single LLM code path for the entire codebase.
    """
    try:
        result = ai_service.score_evidence(
            text=payload.text,
            asset_name=payload.asset_name,
            ward_name=payload.ward_name,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
