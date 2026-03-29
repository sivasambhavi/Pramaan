"""
relevance_filter.py — PRAMAAN Global Ontology Engine Pre-Ingestion Scorer
Filters search results across 7 domains before passing to LLM extraction.
"""
import logging

logger = logging.getLogger(__name__)

RELEVANCE_SIGNALS = {
    # High value — relevant to any of the 7 domains
    "high": [
        # Climate / Disaster
        "NDMA", "NDRF", "landslide", "cyclone", "flood", "disaster",
        "relief", "evacuation", "IMD", "rainfall", "subsidence",
        # Defense
        "Army", "CRPF", "Assam Rifles", "deployment", "paramilitary",
        "security forces", "IAF", "helicopter rescue",
        # Economics
        "scheme", "fund", "crore", "investment", "PLI", "allocation",
        "CAG", "audit", "expenditure", "budget",
        # Geopolitics
        "Parliament", "Lok Sabha", "Rajya Sabha", "ministry",
        "Centre state", "policy", "PIB", "press release",
        # Technology
        "semiconductor", "ISRO", "satellite", "digital India",
        "fab", "chip", "technology mission",
        # Society
        "displaced", "rehabilitation", "beneficiary", "welfare",
        "casualties", "deaths", "affected",
        # Governance
        "accountability", "transparency", "RTI", "delivery",
        "governance", "implementation",
        # Specific events
        "Wayanad", "Joshimath", "Manipur", "Yamuna", "Dana",
        "Dholera", "Tata Electronics", "Mundakkai",
    ],
    # Low value — noise
    "low": [
        "opinion", "editorial", "advertisement", "sponsored",
        "astrology", "cricket", "bollywood", "stock market",
        "recipe", "fashion", "horoscope", "celebrity",
        "IPL", "movie review", "entertainment",
    ],
}

# Domain-specific boosters — extra weight if result matches a known event
EVENT_BOOSTERS = {
    "wayanad":      15,
    "joshimath":    15,
    "manipur":      15,
    "yamuna flood": 15,
    "cyclone dana": 15,
    "tata semiconductor": 15,
    "dholera":      10,
    "mundakkai":    10,
    "chooralmala":  10,
}


def score_result(result: dict) -> int:
    """
    Scores a single search result 0-100.
    High score = relevant to PRAMAAN Global Ontology domains.
    """
    text = (
        (result.get("title") or "") + " " +
        (result.get("content") or "") + " " +
        (result.get("url") or "")
    ).lower()

    score = 0

    for word in RELEVANCE_SIGNALS["high"]:
        if word.lower() in text:
            score += 8

    for word in RELEVANCE_SIGNALS["low"]:
        if word.lower() in text:
            score -= 25

    # Event-specific boost
    for phrase, boost in EVENT_BOOSTERS.items():
        if phrase in text:
            score += boost

    return max(0, min(100, score))


def filter_results(results: list, min_score: int = 25) -> list:
    """
    Returns only results scoring above threshold, sorted by relevance.
    """
    if not results:
        return []

    scored = [(r, score_result(r)) for r in results]
    scored.sort(key=lambda x: x[1], reverse=True)

    kept    = [(r, s) for r, s in scored if s >= min_score]
    dropped = len(results) - len(kept)

    if dropped:
        logger.info("[FILTER] Dropped %d/%d low-relevance results.", dropped, len(results))
    if kept:
        logger.info("[FILTER] Top result score: %d — %s",
                    kept[0][1], kept[0][0].get("title", "")[:60])

    return [r for r, s in kept]
