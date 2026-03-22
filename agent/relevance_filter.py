"""
relevance_filter.py — PRAMAAN Pre-Ingestion Scorer
Filters out noise from Tavily search results before passing to LLM/Crawl4AI.
"""
import logging

logger = logging.getLogger(__name__)

RELEVANCE_SIGNALS = {
    # High value — these words in a result = almost certainly useful
    "high": [
        "ward", "MCD", "municipality", "Delhi", "scheme",
        "beneficiary", "allotment", "completion", "fund",
        "tender", "work order", "inauguration", "status",
        "PMAY", "AMRUT", "SBM", "Swachh Bharat", "Jal Board",
        "DUSIB", "DDA", "NDMC", "Smart City",
    ],
    # Low value — these words = likely noise, skip
    "low": [
        "opinion", "editorial", "advertisement", "sponsored",
        "astrology", "cricket", "bollywood", "stock market",
        "Pakistan", "election rally", "party politics",
    ],
}

def score_result(result: dict) -> int:
    """
    Scores a single Tavily result 0-100.
    High score = relevant to PRAMAAN governance data.
    """
    text = (
        (result.get("title") or "") + " " +
        (result.get("content") or "") + " " +
        (result.get("url") or "")
    ).lower()

    score = 0
    for word in RELEVANCE_SIGNALS["high"]:
        if word.lower() in text:
            score += 10
    for word in RELEVANCE_SIGNALS["low"]:
        if word.lower() in text:
            score -= 20

    return max(0, min(100, score))


def filter_results(results: list, min_score: int = 30) -> list:
    """
    Returns only results scoring above threshold.
    Logs dropped results for audit.
    """
    if not results:
        return []
        
    scored = [(r, score_result(r)) for r in results]
    scored.sort(key=lambda x: x[1], reverse=True)

    kept = [(r, s) for r, s in scored if s >= min_score]
    dropped = len(results) - len(kept)

    if dropped:
        logger.info(f"[FILTER] Dropped {dropped}/{len(results)} low-relevance results.")

    return [r for r, s in kept]
