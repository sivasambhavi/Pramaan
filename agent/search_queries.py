"""
PRAMAAN Global Ontology Engine — Search Query Registry
Agent picks from these domain-aligned query templates only.
Covers all 6 events across 7 domains.
"""

import random

# ── Per-event priority queries (always run first) ─────────────────────────────

PRIORITY_QUERIES = [
    # Wayanad Landslide — Climate + Society
    "Wayanad landslide 2024 NDMA relief fund Kerala",
    "Mundakkai Chooralmala landslide rescue update 2024",
    "Wayanad disaster reconstruction Kerala government 2024 2025",

    # Cyclone Dana — Climate + Defense
    "Cyclone Dana Odisha 2024 NDRF deployment Puri",
    "Cyclone Dana Andhra Pradesh damage relief October 2024",
    "Odisha cyclone preparedness evacuation 2024",

    # Joshimath — Climate + Technology
    "Joshimath land subsidence ISRO satellite data 2023",
    "Joshimath NTPC tunnel sinking Uttarakhand update",
    "Joshimath reconstruction relief package 2023 2024",

    # Delhi Floods — Economics + Geopolitics
    "Yamuna flood Delhi 2023 record level relief",
    "Delhi floods Haryana dam water release controversy 2023",
    "Delhi flood encroachment Yamuna floodplain 2023 2024",

    # Manipur — Geopolitics + Defense
    "Manipur ethnic violence CRPF Army deployment 2023",
    "Manipur conflict relief displaced citizens 2023 2024",
    "Manipur internet shutdown lifted update 2023",

    # Tata Semiconductor — Technology + Economics
    "Tata semiconductor fab Dholera Gujarat progress 2024 2025",
    "India Semiconductor Mission ISMC fab update 2024",
    "CG Power semiconductor Sanand Gujarat construction 2024",
]

# ── Domain-level query templates ──────────────────────────────────────────────

DOMAIN_QUERIES = {
    "climate": [
        "NDMA disaster response India {year}",
        "India flood cyclone landslide relief fund {year}",
        "IMD early warning system India disaster {year}",
        "NDRF deployment rescue India natural disaster {year}",
    ],
    "economics": [
        "India infrastructure investment scheme fund release {year}",
        "PLI scheme India progress report {year}",
        "India GDP growth sector investment {year}",
        "Central government scheme fund utilization {year}",
    ],
    "geopolitics": [
        "India Parliament session debate policy {year}",
        "India state Centre relations dispute fund {year}",
        "India foreign policy strategic decision {year}",
        "Lok Sabha Rajya Sabha question answer {year}",
    ],
    "defense": [
        "Indian Army deployment internal security {year}",
        "CRPF Assam Rifles deployment Northeast India {year}",
        "India defense ministry strategic asset {year}",
        "India border security infrastructure {year}",
    ],
    "technology": [
        "India semiconductor chip manufacturing progress {year}",
        "Digital India initiative update {year}",
        "ISRO satellite launch mission {year}",
        "India technology investment startup {year}",
    ],
    "society": [
        "India displaced persons relief rehabilitation {year}",
        "India welfare scheme beneficiary update {year}",
        "India poverty reduction program {year}",
        "India healthcare scheme coverage {year}",
    ],
    "governance": [
        "India government scheme accountability audit {year}",
        "CAG report India scheme fund misuse {year}",
        "India RTI response governance transparency {year}",
        "India public asset delivery accountability {year}",
    ],
}

QUALIFIERS = ["2024", "2025", "2024 2025", "latest update", "PIB press release"]


def generate_query_batch(batch_size: int = 10) -> list:
    """Generates a diverse batch of queries across all domains."""
    queries = []
    domains = list(DOMAIN_QUERIES.keys())

    for i in range(batch_size):
        domain = domains[i % len(domains)]
        template = random.choice(DOMAIN_QUERIES[domain])
        year = random.choice(QUALIFIERS)
        queries.append(template.format(year=year))

    return queries[:batch_size]


def get_priority_queries() -> list:
    """Returns the high-priority event-specific queries."""
    return PRIORITY_QUERIES.copy()
