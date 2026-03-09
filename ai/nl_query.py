"""
Natural language question → backend API call routing for Pramaan.

Supports 3 fixed demo questions via keyword matching.
No LLM needed — deterministic routing for demo reliability.
"""

import os
import httpx
from typing import Any
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Question templates
# ---------------------------------------------------------------------------

QUESTIONS = {
    "q1": {
        "text": "What was built in Ward 45 in last 2 years?",
        "description": "Returns all assets in Ward 45 with scheme, cost, and status.",
    },
    "q2": {
        "text": "For Gali 7, show full delivery chain.",
        "description": "Returns complete proof chain for the Gali 7 drain asset.",
    },
    "q3": {
        "text": "Which schemes have low delivery scores?",
        "description": "Returns gap analysis showing schemes with fewest proven assets.",
    },
}


def _match_question(question: str) -> str | None:
    """Match user input to one of the 3 fixed question keys."""
    q = question.lower()

    # Q3 checked first — "missing", "incomplete", "gap" are strong signals
    if any(kw in q for kw in ["scheme", "low", "gap", "score", "delivery score", "missing", "not performing", "incomplete"]):
        return "q3"

    if any(kw in q for kw in ["gali 7", "gali no", "drain", "delivery chain", "proof chain"]):
        return "q2"

    if any(kw in q for kw in ["built", "ward 45", "constructed", "2 years", "assets"]):
        return "q1"

    return None


def _call_q1() -> dict[str, Any]:
    """What was built in Ward 45?"""
    resp = httpx.get(f"{BASE_URL}/wards/REG_W45/assets", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "question": QUESTIONS["q1"]["text"],
        "answer_type": "asset_list",
        "ward_id": "REG_W45",
        "assets": data.get("assets", []),
        "total": len(data.get("assets", [])),
    }


def _call_q2() -> dict[str, Any]:
    """For Gali 7, show full delivery chain."""
    resp = httpx.get(f"{BASE_URL}/assets/ASSET_DRAIN_GALI7/chain", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "question": QUESTIONS["q2"]["text"],
        "answer_type": "proof_chain",
        **data,
    }


def _call_q3() -> dict[str, Any]:
    """Which schemes have low delivery scores?"""
    gaps_resp = httpx.get(f"{BASE_URL}/wards/REG_W45/gaps", timeout=10)
    score_resp = httpx.get(f"{BASE_URL}/wards/REG_W45/score", timeout=10)
    gaps_resp.raise_for_status()
    score_resp.raise_for_status()

    return {
        "question": QUESTIONS["q3"]["text"],
        "answer_type": "gap_analysis",
        "delivery_score": score_resp.json(),
        "gaps": gaps_resp.json().get("gaps", []),
    }


def generate_query(question: str) -> dict[str, Any]:
    """
    Match question to a template and call the backend.

    Returns structured result dict with answer_type and data.
    Returns an error dict if question is not recognised.
    """
    key = _match_question(question)

    if key == "q1":
        return _call_q1()
    elif key == "q2":
        return _call_q2()
    elif key == "q3":
        return _call_q3()
    else:
        return {
            "question": question,
            "answer_type": "unrecognised",
            "error": "Question not recognised. Try one of the 3 supported questions.",
            "supported_questions": [q["text"] for q in QUESTIONS.values()],
        }
