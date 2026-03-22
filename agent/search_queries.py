"""
PRAMAAN — Approved Search Query Registry
Agent MUST pick from these templates only.
No freeform queries allowed.
"""

import random

ANCHORS = ["Delhi MCD", "Delhi municipal", "Delhi NCT"]

SCHEMES = [
    "PMAY housing", "SBM toilet", "AMRUT drain",
    "Smart Cities", "Delhi Jal Board water supply",
    "DDA housing allotment", "DUSIB slum redevelopment",
    "road repair", "stormwater drain", "solid waste",
    "streetlight", "public toilet", "pothole repair",
]

QUALIFIERS = [
    "2026", "2025 2026", "ward report",
    "status update", "tender", "completion",
    "fund utilization", "beneficiary",
]

def build_query(scheme: str, qualifier: str = "", anchor: str = "Delhi MCD") -> str:
    """ Builds a natural, realistic search query. """
    parts = [anchor, scheme]
    if qualifier:
        parts.append(qualifier)
    return " ".join(parts)

def generate_query_batch(batch_size: int = 10) -> list:
    """ Generates a diverse but controlled batch of queries for one agent run. """
    schemes_sample = random.sample(SCHEMES, min(batch_size, len(SCHEMES)))
    qualifiers_cycle = QUALIFIERS * ((batch_size // len(QUALIFIERS)) + 1)

    queries = []
    for i, scheme in enumerate(schemes_sample):
        anchor = random.choice(ANCHORS)
        qualifier = qualifiers_cycle[i]
        queries.append(build_query(scheme, qualifier, anchor))

    return queries[:batch_size]

# PRE-BAKED HIGH PRIORITY QUERIES (always run first)
PRIORITY_QUERIES = [
    "Delhi MCD AMRUT stormwater drain fund utilization 2026",
    "PMAY Delhi housing scheme beneficiary allotment 2025 2026",
    "Swachh Bharat Delhi toilet construction ward status",
    "Delhi Jal Board water supply pipeline repair 2026",
    "MCD Delhi road repair pothole ward 2026",
    "DUSIB Delhi slum redevelopment progress report",
    "Smart Cities Delhi ward infrastructure completion 2026",
    "MCD Delhi solid waste management ward report 2026",
]
