"""
Stub module for AI-based extraction.

Intended responsibility:
- Take raw text (e.g. survey notes, documents)
- Extract entities and relations into a structured JSON format
"""

from typing import Any, Dict


def extract_entities_and_relations(text: str) -> Dict[str, Any]:
    """Return a placeholder extraction result for the given text."""
    return {
        "text": text,
        "entities": [],
        "relations": [],
        "note": "AI extraction not implemented yet.",
    }


