"""
cleanup_orphans.py
Two-pass graph cleanup:
  Pass 1 — DELETE junk nodes (deleted-event remnants, null-name nodes, irrelevant local data)
  Pass 2 — CONNECT meaningful orphans to correct canonical events
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.app.neo4j_client import get_session

def run(q, **p):
    with get_session() as s:
        result = s.run(q, **p)
        summary = result.consume()
        deleted = summary.counters.nodes_deleted
        created = summary.counters.relationships_created
        return deleted, created

def report(label, deleted, created):
    parts = []
    if deleted: parts.append(f"{deleted} deleted")
    if created: parts.append(f"{created} rels created")
    print(f"  ✓ {label}: {', '.join(parts) if parts else 'ok'}")


# ══════════════════════════════════════════════════════════════════════════════
# PASS 1 — DELETE JUNK NODES
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Pass 1: Delete junk nodes ===")

# 1a. Impact nodes with null name (all from deleted/auto-ingested events)
d, _ = run("MATCH (i:Impact) WHERE NOT (i)--() AND i.name IS NULL DETACH DELETE i")
report("Null-name Impact nodes", d, 0)

# 1b. Evidence from deleted events (Joshimath, Manipur, IMEC, Tata Semi)
d, _ = run("""
    MATCH (e:Evidence) WHERE NOT (e)--() AND (
        e.title CONTAINS 'Joshimath' OR
        e.title CONTAINS 'Tata' OR
        e.title CONTAINS 'CG Power' OR
        e.title CONTAINS 'IMEC' OR
        e.title CONTAINS 'Manipur'
    ) DETACH DELETE e
""")
report("Deleted-event Evidence nodes", d, 0)

# 1c. Policy nodes from deleted events or irrelevant
d, _ = run("""
    MATCH (p:Policy) WHERE NOT (p)--() AND (
        p.name CONTAINS 'Joshimath' OR
        p.name CONTAINS 'IMEC' OR
        p.name CONTAINS 'Middle East-Europe' OR
        p.name CONTAINS 'Sports Policy' OR
        p.name CONTAINS 'Senior Citizens'
    ) DETACH DELETE p
""")
report("Irrelevant/remnant Policy nodes", d, 0)

# 1d. Regions from deleted events or truly irrelevant (ward-level)
d, _ = run("""
    MATCH (r:Region) WHERE NOT (r)--() AND r.name IN [
        'Chamoli', 'Joshimath', 'Uttarakhand', 'Manipur',
        'Gurgaon', 'Ward 92', 'Yamunanagar'
    ] DETACH DELETE r
""")
report("Deleted-event / ward-level Region nodes", d, 0)

# 1e. Actor nodes from deleted events or irrelevant local bodies
d, _ = run("""
    MATCH (a:Actor) WHERE NOT (a)--() AND a.name IN [
        'Government of Manipur',
        'Municipal Corporation of Gurgaon'
    ] DETACH DELETE a
""")
report("Deleted-event Actor nodes", d, 0)

# 1f. Impact "Yamunanagar development projects" (ward-level, orphaned)
d, _ = run("""
    MATCH (i:Impact) WHERE NOT (i)--() AND i.name = 'Yamunanagar development projects'
    DETACH DELETE i
""")
report("Yamunanagar ward Impact node", d, 0)

# 1g. Auto-ingested lowercase events with no relevance to project scope
JUNK_EVENTS = [
    'evt_mcd_bypolls',
    'evt_national_urban_conclave_2025',
    'evt_cyclone_ditwah',
    'evt_cyclone_montha',
]
d, _ = run("""
    MATCH (e:Event) WHERE e.event_id IN $ids DETACH DELETE e
""", ids=JUNK_EVENTS)
report("Irrelevant auto-ingested Events", d, 0)


# ══════════════════════════════════════════════════════════════════════════════
# PASS 2 — CONNECT MEANINGFUL ORPHANS
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Pass 2: Connect meaningful orphans ===")

# 2a. Regions → Events via OCCURRED_IN
REGION_EDGES = [
    ("Strait of Hormuz", "EVT_HORMUZ_BLOCKADE_2026"),
    ("Middle East",      "EVT_IRAN_WAR_2026"),
    ("Saudi Arabia",     "EVT_HORMUZ_BLOCKADE_2026"),
    ("Dholera",          "EVT_INDIA_SEMI_MICRON_2026"),
    ("Sri Lanka",        "EVT_IRAN_WAR_2026"),      # Indian Ocean shipping lane impact
    ("Guwahati",         "EVT_ARUNACHAL_STANDOFF_2026"),  # Nearest logistics hub
]
for reg_name, evt_id in REGION_EDGES:
    _, c = run("""
        MATCH (r:Region {name: $rname}), (e:Event {event_id: $eid})
        MERGE (r)-[:OCCURRED_IN]->(e)
    """, rname=reg_name, eid=evt_id)
    print(f"  ✓ Region '{reg_name}' → {evt_id}")

# 2b. Orphan Impact "Oil price shock" → HORMUZ event
_, c = run("""
    MATCH (i:Impact {name: 'Oil price shock'}), (e:Event {event_id: 'EVT_HORMUZ_BLOCKADE_2026'})
    WHERE NOT (e)-[:CAUSED]->(i)
    MERGE (e)-[:CAUSED]->(i)
""")
report("Impact 'Oil price shock' → HORMUZ_BLOCKADE", 0, c)

# 2c. Policy "India Semiconductor Mission" → SEMI_MICRON event
_, c = run("""
    MATCH (p:Policy {name: 'India Semiconductor Mission'}), (e:Event {event_id: 'EVT_INDIA_SEMI_MICRON_2026'})
    MERGE (e)-[:TRIGGERED]->(p)
""")
report("Policy 'India Semiconductor Mission' → SEMI_MICRON", 0, c)

# 2d. Policy "Armed Forces Special Powers Act" → PAHALGAM + ARUNACHAL
_, c = run("""
    MATCH (p:Policy {name: 'Armed Forces Special Powers Act'})
    MATCH (e1:Event {event_id: 'EVT_PAHALGAM_2025'})
    MATCH (e2:Event {event_id: 'EVT_ARUNACHAL_STANDOFF_2026'})
    MERGE (e1)-[:TRIGGERED]->(p)
    MERGE (e2)-[:TRIGGERED]->(p)
""")
report("Policy 'AFSPA' → PAHALGAM + ARUNACHAL", 0, c)

# 2e. Actors → Events via MANAGED_BY
ACTOR_EDGES = [
    ("UN Security Council",                          "EVT_IRAN_WAR_2026"),
    ("US State Department",                          "EVT_IRAN_CEASEFIRE_TALKS_2026"),
    ("US Government",                                "EVT_IRAN_WAR_2026"),
    ("OPEC+",                                        "EVT_HORMUZ_BLOCKADE_2026"),
    ("Ministry of Defence India",                    "EVT_OPERATION_SINDOOR_2025"),
    ("Ministry of Electronics & Information Technology", "EVT_INDIA_SEMI_MICRON_2026"),
    ("CG Power and Industrial Solutions",            "EVT_INDIA_SEMI_MICRON_2026"),
    ("NTPC Limited",                                 "EVT_INDIA_CLIMATE_TARGETS_2026"),
    ("Press Information Bureau India",               "EVT_OPERATION_SINDOOR_2025"),
]
for actor_name, evt_id in ACTOR_EDGES:
    _, c = run("""
        MATCH (a:Actor {name: $aname}), (e:Event {event_id: $eid})
        MERGE (a)-[:MANAGED_BY]->(e)
    """, aname=actor_name, eid=evt_id)
    print(f"  ✓ Actor '{actor_name}' → {evt_id}")

# 2f. Connect surviving lowercase auto-ingested events → canonical events
AUTO_CONNECTIONS = [
    ("evt_energy_shock",                  "EVT_HORMUZ_BLOCKADE_2026"),
    ("evt_unsc_iran_resolution_2026",     "EVT_IRAN_WAR_2026"),
    ("evt_india_foreign_policy_crisis_2026", "EVT_ARUNACHAL_STANDOFF_2026"),
    ("evt_operation_sagar_bandhu",        "EVT_INDIA_US_DEFENSE_2025"),
]
for src, tgt in AUTO_CONNECTIONS:
    _, c = run("""
        MATCH (a:Event {event_id: $src}), (b:Event {event_id: $tgt})
        MERGE (a)-[:CONNECTED_TO]->(b)
        MERGE (b)-[:CONNECTED_TO]->(a)
    """, src=src, tgt=tgt)
    print(f"  ✓ evt '{src}' ↔ {tgt}")


# ══════════════════════════════════════════════════════════════════════════════
# FINAL VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Final verification ===")
with get_session() as s:
    loose = s.run("""
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n)[0] AS label, count(n) AS cnt
        ORDER BY label
    """).data()
    total = sum(r["cnt"] for r in loose)
    print(f"  Remaining loose nodes: {total}")
    for r in loose:
        print(f"    [{r['label']}]: {r['cnt']}")

    counts = s.run("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS cnt
        ORDER BY cnt DESC
    """).data()
    print("\n  Node counts after cleanup:")
    for r in counts:
        print(f"    {r['label']:20s}: {r['cnt']}")
