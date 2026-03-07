"""
Stub module for natural-language question → graph query translation.

Intended responsibility:
- Take a user question as input
- Produce a Cypher template and parameter dictionary that can be run against Neo4j
"""

from typing import Any, Dict


def generate_query(question: str) -> Dict[str, Any]:
    """Return a placeholder Cypher template and parameters for a question."""
    return {
        "question": question,
        "cypher": "MATCH (n) RETURN n LIMIT 5",
        "params": {},
        "note": "NL query generation not implemented yet.",
    }


