from fastapi import APIRouter, HTTPException, Query
from app.services.news_service import news_service
from app.services.ai_service import ai_service
from typing import List, Dict

router = APIRouter(prefix="/scrape", tags=["scrape"])

@router.get("/news")
async def scrape_and_analyze(q: str = Query(..., description="Query to search for governance news")):
    """Scrape news for a query and return AI-extracted ontology."""
    try:
        articles = news_service.fetch_google_news(q)
        if not articles:
            return {"entities": [], "relations": [], "articles": []}
            
        # Combine headlines for extraction
        combined_text = "\n\n".join([f"Headline: {a['title']}\nSummary: {a['summary']}" for a in articles])
        
        extracted_data = ai_service.extract_governance_ontology(combined_text)
        extracted_data["articles"] = articles # Include source for UI
        
        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
