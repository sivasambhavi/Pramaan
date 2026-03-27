"""
seed_scheme_types.py
Add scheme_type property to all Scheme nodes in Neo4j.

Type 1 — Emergency/Reactive:
  Activated immediately when a crisis hits (reserves, relief funds, at-risk assets).

Type 2 — Structural/Ongoing:
  Ongoing development programmes accelerated or realigned as strategic response.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.neo4j_client import get_session

def run(q, **p):
    with get_session() as s:
        s.run(q, **p)
    print(f"  ✓ {q[:80].strip()}")


# ── Type 1: Emergency / Reactive ──────────────────────────────────────────────
TYPE1 = [
    "SCH_NDRF_FUND",    # National Disaster Response Fund
    "SCH_SDRF",         # State Disaster Response Fund
    "SCH_SPR",          # Strategic Petroleum Reserve — activated on supply shock
    "SCH_CHABAHAR",     # Chabahar investment — at risk, needs emergency protection
    "SCH_ONGC_VIDESH",  # ONGC equity oil assets — at risk in Iran War
]

# ── Type 2: Structural / Ongoing ──────────────────────────────────────────────
TYPE2 = [
    "SCH_AMRUT",        # AMRUT 2.0 urban infrastructure
    "SCH_PMAY",         # PM Awas Yojana housing
    "SCH_ISM",          # India Semiconductor Mission
    "SCH_ISRO_BUDGET",  # ISRO mission budget
    "SCH_INSTC",        # INSTC corridor (strategic infra — ongoing)
    "SCH_GREEN_H2",     # National Green Hydrogen Mission
    "SCH_PLI_SOLAR",    # PLI Solar PV Manufacturing
]

print("\n=== Setting Type 1 scheme_type ===")
for sid in TYPE1:
    run("""
    MATCH (sc:Scheme {scheme_id: $id})
    SET sc.scheme_type = 'Type 1',
        sc.scheme_type_label = 'Type 1 — Emergency'
    """, id=sid)

print("\n=== Setting Type 2 scheme_type ===")
for sid in TYPE2:
    run("""
    MATCH (sc:Scheme {scheme_id: $id})
    SET sc.scheme_type = 'Type 2',
        sc.scheme_type_label = 'Type 2 — Structural'
    """, id=sid)

# Fallback: any remaining schemes without type → Type 2
run("""
MATCH (sc:Scheme)
WHERE sc.scheme_type IS NULL
SET sc.scheme_type = 'Type 2',
    sc.scheme_type_label = 'Type 2 — Structural'
""")

print("\n✅ scheme_type set on all Scheme nodes.")
print("   Type 1 (Emergency):", len(TYPE1), "schemes")
print("   Type 2 (Structural):", len(TYPE2), "schemes")
print("   Remaining: auto-assigned Type 2")
