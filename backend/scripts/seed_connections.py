"""
seed_connections.py
Fix all CONNECTED_TO edges:
  1. Remove duplicate edges
  2. Add all logically missing connections across all clusters
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.neo4j_client import get_session

def run(q, **p):
    with get_session() as s:
        result = s.run(q, **p)
        return result.data()

# ── Step 1: Remove duplicate CONNECTED_TO edges ───────────────────────────────
print("\n=== Step 1: Removing duplicate edges ===")
run("""
    MATCH (a:Event)-[r:CONNECTED_TO]->(b:Event)
    WITH a, b, collect(r) AS rels
    WHERE size(rels) > 1
    FOREACH (r IN tail(rels) | DELETE r)
""")
print("  ✓ Duplicates removed")

# ── Step 2: Add all missing CONNECTED_TO edges ────────────────────────────────
print("\n=== Step 2: Adding missing connections ===")

EDGES = [
    # ── Iran / Middle East cluster ─────────────────────────────────────────────
    # (all Iran-related events should form a tight cluster)
    ("EVT_IRAN_CEASEFIRE_TALKS_2026",  "EVT_TWELVE_DAY_WAR_2025",       "Ceasefire follows Twelve-Day War"),
    ("EVT_IRAN_CEASEFIRE_TALKS_2026",  "EVT_GAZA_REDSEA_2023",          "Ceasefire rooted in Gaza conflict chain"),
    ("EVT_IRAN_CEASEFIRE_TALKS_2026",  "EVT_RUPEE_INR_CRISIS_2026",     "Ceasefire eases oil supply pressure on INR"),
    ("EVT_HORMUZ_BLOCKADE_2026",       "EVT_TWELVE_DAY_WAR_2025",       "Hormuz blockade triggered by Twelve-Day War"),
    ("EVT_RUPEE_INR_CRISIS_2026",      "EVT_US_INDIA_TRADE_2026",       "Rupee weakness affects US-India trade terms"),
    ("EVT_RUPEE_INR_CRISIS_2026",      "EVT_SP_UPGRADE_2025",           "Credit rating gain at risk from rupee crisis"),

    # ── India-Pakistan cluster ─────────────────────────────────────────────────
    # (all 6 Pak events should be fully connected)
    ("EVT_PAHALGAM_2025",              "EVT_INDIA_PAK_DIPLO_CRISIS_2025","Pahalgam attack triggers diplomatic expulsion"),
    ("EVT_PAHALGAM_2025",              "EVT_INDIA_PAK_CEASEFIRE_2025",   "Pahalgam → Sindoor → ceasefire chain"),
    ("EVT_OPERATION_SINDOOR_2025",     "EVT_INDUS_WATERS_CRISIS_2025",   "Sindoor retaliation tied to Indus suspension"),
    ("EVT_OPERATION_SINDOOR_2025",     "EVT_INDIA_PAK_DIPLO_CRISIS_2025","Sindoor causes full diplomatic breakdown"),
    ("EVT_LOC_SKIRMISHES_2025",        "EVT_INDUS_WATERS_CRISIS_2025",   "LoC escalation triggers water treaty crisis"),
    ("EVT_LOC_SKIRMISHES_2025",        "EVT_INDIA_PAK_DIPLO_CRISIS_2025","LoC violence worsens diplomatic crisis"),
    ("EVT_LOC_SKIRMISHES_2025",        "EVT_INDIA_PAK_CEASEFIRE_2025",   "LoC skirmishes precede ceasefire"),
    ("EVT_INDUS_WATERS_CRISIS_2025",   "EVT_INDIA_PAK_CEASEFIRE_2025",   "Water treaty restoration part of ceasefire deal"),

    # ── Climate cluster ────────────────────────────────────────────────────────
    # (Delhi Floods isolated — connect to all climate events)
    ("EVT_DELHI_FLOODS_2023",          "EVT_INDIA_EXTREME_WEATHER_2025", "Part of India extreme weather pattern"),
    ("EVT_DELHI_FLOODS_2023",          "EVT_WAYANAD_2024",               "Same climate-driven disaster pattern"),
    ("EVT_DELHI_FLOODS_2023",          "EVT_CYCLONE_DANA_2024",          "Urban flooding linked to cyclone risk"),
    ("EVT_DELHI_FLOODS_2023",          "EVT_INDIA_CLIMATE_TARGETS_2026", "Flood damage accelerates climate policy"),
    ("EVT_INDIA_CLIMATE_TARGETS_2026", "EVT_CYCLONE_DANA_2024",          "Cyclone losses drive 2030 target revision"),
    ("EVT_INDIA_CLIMATE_TARGETS_2026", "EVT_WAYANAD_2024",               "Landslide losses cited in climate targets"),

    # ── Space / Technology cluster ─────────────────────────────────────────────
    ("EVT_CHANDRAYAAN3_2023",          "EVT_SHUKLA_ISS_2025",            "Chandrayaan success leads to ISS posting"),
    ("EVT_ADITYAL1_2023",              "EVT_SHUKLA_ISS_2025",            "Solar mission builds toward ISS milestone"),

    # ── Economics / Trade cluster ──────────────────────────────────────────────
    ("EVT_SP_UPGRADE_2025",            "EVT_RUPEE_INR_CRISIS_2026",      "Rating upgrade undercut by rupee depreciation"),
    ("EVT_INDIA_UK_CETA_2025",         "EVT_G20_INDIA_2023",             "G20 summit catalysed UK trade negotiation"),
    ("EVT_US_INDIA_TRADE_2026",        "EVT_G20_INDIA_2023",             "G20 India presidency laid framework for US trade deal"),

    # ── Defense / Geopolitics ──────────────────────────────────────────────────
    ("EVT_ARUNACHAL_STANDOFF_2026",    "EVT_TEESTA_TREATY_2026",         "Arunachal standoff pressures Bangladesh water deal"),

    # ── Diplomacy cross-links ─────────────────────────────────────────────────
    ("EVT_INDIA_CANADA_2023",          "EVT_INDIA_PAK_DIPLO_CRISIS_2025","Both represent India isolating hostile actors"),

    # ── Economics cross-cluster ───────────────────────────────────────────────
    ("EVT_US_INDIA_TRADE_2026",        "EVT_RUPEE_INR_CRISIS_2026",      "Trade framework partially stabilises rupee"),
    ("EVT_LABOUR_CODES_2025",          "EVT_INDIA_SEMI_MICRON_2026",     "Labour codes reform enables fab employment"),
    ("EVT_AI_REGULATION_ACT_2026",     "EVT_US_INDIA_TRADE_2026",        "AI regulation shapes US-India tech trade terms"),
]

added = 0
for src, tgt, reason in EDGES:
    with get_session() as s:
        result = s.run("""
            MATCH (a:Event {event_id: $src}), (b:Event {event_id: $tgt})
            MERGE (a)-[:CONNECTED_TO {reason: $reason}]->(b)
            MERGE (b)-[:CONNECTED_TO {reason: $reason}]->(a)
            RETURN a.event_id, b.event_id
        """, src=src, tgt=tgt, reason=reason).data()
    if result:
        added += 1
        print(f"  ✓ {src}  <->  {tgt}")
    else:
        print(f"  ✗ MISSING NODE: {src} or {tgt}")

print(f"\n=== Done: {added} edge pairs added ===")

# ── Step 3: Final count ───────────────────────────────────────────────────────
print("\n=== Step 3: Final state ===")
with get_session() as s:
    pairs = s.run("""
        MATCH (a:Event)-[:CONNECTED_TO]-(b:Event)
        WHERE a.event_id < b.event_id
        RETURN count(*) AS total
    """).data()
    total = pairs[0]["total"] if pairs else 0
    print(f"  Total unique CONNECTED_TO pairs: {total}")

    per_event = s.run("""
        MATCH (e:Event)
        WHERE e.event_id STARTS WITH 'EVT_'
        OPTIONAL MATCH (e)-[:CONNECTED_TO]-(other:Event)
        RETURN e.event_id AS eid, count(DISTINCT other) AS cnt
        ORDER BY cnt DESC
    """).data()
    print("\n  Connection count per canonical event:")
    for r in per_event:
        bar = "█" * r["cnt"]
        print(f"    {r['eid']:45s} {r['cnt']:2d}  {bar}")
