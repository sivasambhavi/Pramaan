from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.news_service import news_service
from app.services.ai_service import ai_service

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.get("/news")
async def scrape_and_analyze(q: str = Query(..., description="Query to search for governance news")):
    """Scrape RSS news for a query and extract governance ontology. source_type=unstructured_rss."""
    try:
        articles = news_service.fetch_google_news(q)
        if not articles:
            return {"entities": [], "relations": [], "articles": [], "source_type": "unstructured_rss"}

        combined_text = "\n\n".join([f"Headline: {a['title']}\nSummary: {a['summary']}" for a in articles])
        extracted_data = ai_service.extract_ontology(combined_text, source_type="unstructured_rss")
        extracted_data["articles"] = articles
        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AnalyzeRequest(BaseModel):
    text: str


@router.post("/analyze")
async def analyze_text(payload: AnalyzeRequest):
    """Analyze user-pasted text and extract governance ontology. source_type=unstructured_llm."""
    try:
        return ai_service.extract_ontology(payload.text, source_type="unstructured_llm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
