"""
seed_2026_events.py — Pramaan V5 Demo Seeder
Injects 7 structured 2026 events into Neo4j with full rich data:
  - Event node (with all properties)
  - Impact nodes  ([:HAS_IMPACT])
  - Actor nodes   ([:INVOLVED_IN])
  - Scheme nodes  ([:TRIGGERED])
  - Beneficiary nodes ([:BENEFITS])
  - CONNECTED_TO edges to existing events

Run from project root:
  python scripts/seed_2026_events.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# ── 7 New 2026 Events ─────────────────────────────────────────────────────────
EVENTS = [
    {
        "event_id":    "EVT_INDIA_SEMI_MICRON_2026",
        "name":        "India Semiconductor Mission — Micron Fab Launch",
        "domain":      "Technology",
        "date":        "Aug 2026",
        "severity":    "high",
        "description": "Micron Technology's $825M ATMP facility becomes operational in Sanand, Gujarat — India's first advanced semiconductor packaging plant. Marks the inflexion point of India's PLI-driven chip self-sufficiency drive under the India Semiconductor Mission.",
        "confidence":  0.92,
        "lat":         23.0225,
        "lon":         72.5714,
        "region_id":   "REG_GUJARAT",
        "impacts": [
            {"impact_id": "IMP_SEMI_JOBS", "type": "Employment", "value": "5,000 direct + 15,000 indirect semiconductor jobs created in Gujarat", "source": "India Semiconductor Mission / MeitY"},
            {"impact_id": "IMP_SEMI_EXPORTS", "type": "Trade",  "value": "₹22,000 Cr annual chip export target by 2028 — reduces import bill by 18%", "source": "MeitY PLI Report 2026"},
            {"impact_id": "IMP_SEMI_TALENT", "type": "Capability", "value": "85,000 chip design engineers deficit nationally — IIT curriculum overhaul urgent", "source": "NASSCOM Semiconductor Talent Report"},
        ],
        "actors": [
            {"actor_id": "ACT_MICRON", "name": "Micron Technology", "type": "Corporation", "role": "Lead fab operator — $825M ATMP investment"},
            {"actor_id": "ACT_MEITY", "name": "MeitY",             "type": "Government",  "role": "PLI scheme disbursements and policy oversight"},
            {"actor_id": "ACT_ISM",   "name": "India Semiconductor Mission", "type": "Government", "role": "National coordinator for chip ecosystem development"},
        ],
        "schemes": [
            {"scheme_id": "SCH_PLI_SEMI", "name": "PLI Semiconductor", "status": "active",     "fund": "₹76,000 Cr", "ministry": "MeitY"},
            {"scheme_id": "SCH_ISM",      "name": "India Semiconductor Mission", "status": "active", "fund": "₹10,000 Cr", "ministry": "MeitY"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_GUJARAT_WORKERS", "group": "Industrial Workers — Gujarat", "count": 20000},
            {"ben_id": "BEN_CHIP_ENGINEERS",  "group": "Electronics Engineering Graduates", "count": 85000},
        ],
        "connections": ["EVT_HORMUZ_BLOCKADE_2026", "EVT_INDIA_US_DEFENSE_2025"],
    },
    {
        "event_id":    "EVT_RUPEE_INR_CRISIS_2026",
        "name":        "Rupee Depreciation Crisis — INR/USD at 94",
        "domain":      "Economics",
        "date":        "Nov 2026",
        "severity":    "critical",
        "description": "The Indian Rupee crosses ₹94/USD for the first time, triggered by sustained Hormuz blockade oil import pressure, FII outflows post-US Fed rate hold, and a widening current account deficit. RBI deploys $28B of forex reserves to defend the currency.",
        "confidence":  0.88,
        "lat":         18.9220,
        "lon":         72.8347,
        "region_id":   "REG_MUMBAI",
        "impacts": [
            {"impact_id": "IMP_INR_FOREX",  "type": "Currency",  "value": "RBI deploys $28B forex reserves — buffer drops from $680B to $652B", "source": "RBI Monthly Bulletin Nov 2026"},
            {"impact_id": "IMP_INR_IMPORT", "type": "Trade",     "value": "Oil import bill rises by ₹3.2 Lakh Cr annually at ₹94 — widening CAD to 3.8% of GDP", "source": "MoPNG Economic Analysis"},
            {"impact_id": "IMP_INR_INFLA",  "type": "Inflation", "value": "CPI spikes to 7.4% — above RBI 6% upper tolerance band — MPC emergency review", "source": "MOSPI CPI Data Nov 2026"},
        ],
        "actors": [
            {"actor_id": "ACT_RBI",    "name": "Reserve Bank of India", "type": "Government",  "role": "Forex intervention — sold $28B; repo rate emergency review"},
            {"actor_id": "ACT_FINMIN", "name": "Finance Ministry",      "type": "Government",  "role": "Emergency import duty rationalisation on gold and non-essentials"},
            {"actor_id": "ACT_FIIS",   "name": "Foreign Institutional Investors", "type": "Market", "role": "Net sellers — ₹45,000 Cr equity outflow in Oct-Nov 2026"},
        ],
        "schemes": [
            {"scheme_id": "SCH_SPR_RELEASE", "name": "SPR Emergency Release",         "status": "active",   "fund": "N/A",       "ministry": "MoPNG"},
            {"scheme_id": "SCH_RBI_SWP",     "name": "RBI Dollar-Rupee Swap Window",  "status": "active",   "fund": "$5B window", "ministry": "RBI"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_EXPORTERS",   "group": "Indian IT & Pharma Exporters (benefiting from weaker rupee)", "count": 5000000},
            {"ben_id": "BEN_IMPORTERS",   "group": "Oil & Electronics Importers (adversely impacted)", "count": 1200000},
        ],
        "connections": ["EVT_IRAN_WAR_2026", "EVT_HORMUZ_BLOCKADE_2026", "EVT_SP_UPGRADE_2025"],
    },
    {
        "event_id":    "EVT_INDIA_CLIMATE_TARGETS_2026",
        "name":        "India 2030 Climate Targets Review",
        "domain":      "Climate",
        "date":        "Apr 2026",
        "severity":    "high",
        "description": "India's mid-term NDC review reveals renewable energy capacity at 201 GW — ahead of 500 GW target trajectory — but EV adoption at only 8% vs 30% target and per-capita emissions rising. COP32 preparatory assessment triggers major Viksit Bharat green jobs push.",
        "confidence":  0.85,
        "lat":         28.6139,
        "lon":         77.2090,
        "region_id":   "REG_DELHI",
        "impacts": [
            {"impact_id": "IMP_CLIM_RE",  "type": "Energy",       "value": "201 GW renewable capacity operational — 40% of the 500 GW 2030 target achieved", "source": "MNRE Annual Report 2026"},
            {"impact_id": "IMP_CLIM_EV",  "type": "Transport",    "value": "EV penetration at 8% vs 30% target — 7 million EVs on road against 30M needed", "source": "VAHAN EV Registration Data"},
            {"impact_id": "IMP_CLIM_JOBS","type": "Employment",    "value": "Green economy jobs projected at 3.5 Cr by 2030 — current gap 1.8 Cr skilled workers", "source": "ILO India Green Jobs Report"},
        ],
        "actors": [
            {"actor_id": "ACT_MNRE",    "name": "Ministry of New & Renewable Energy", "type": "Government", "role": "Nodal ministry for 500 GW target"},
            {"actor_id": "ACT_NITI",    "name": "NITI Aayog",                          "type": "Government", "role": "NDC mid-term review and green finance roadmap"},
            {"actor_id": "ACT_UNFCCC",  "name": "UNFCCC",                              "type": "International", "role": "NDC registry and COP32 preparatory process"},
        ],
        "schemes": [
            {"scheme_id": "SCH_PM_SURYA", "name": "PM Surya Ghar — Rooftop Solar", "status": "active", "fund": "₹75,021 Cr", "ministry": "MNRE"},
            {"scheme_id": "SCH_FAME3",    "name": "FAME III — EV Adoption",        "status": "active", "fund": "₹40,000 Cr", "ministry": "MHI"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_SOLAR_HH",   "group": "Rooftop Solar Beneficiary Households", "count": 10000000},
            {"ben_id": "BEN_EV_BUYERS",  "group": "EV Subsidy Beneficiaries",             "count": 3500000},
        ],
        "connections": ["EVT_INDIA_EXTREME_WEATHER_2025", "EVT_WAYANAD_2024"],
    },
    {
        "event_id":    "EVT_TEESTA_TREATY_2026",
        "name":        "Teesta Water Treaty — India-Bangladesh Signing",
        "domain":      "Geopolitics",
        "date":        "Jan 2026",
        "severity":    "high",
        "description": "India and Bangladesh sign the long-pending Teesta River Water Sharing Treaty after 43 years of negotiations, allocating 48% of flow to Bangladesh and 52% to India during lean season. West Bengal's Chief Minister had blocked the treaty for 14 years.",
        "confidence":  0.90,
        "lat":         26.7271,
        "lon":         88.3953,
        "region_id":   "REG_WEST_BENGAL",
        "impacts": [
            {"impact_id": "IMP_TEESTA_AGRI",  "type": "Agriculture", "value": "3.2M Bangladeshi farmers in northern districts gain guaranteed lean-season irrigation rights", "source": "Joint Rivers Commission India-Bangladesh"},
            {"impact_id": "IMP_TEESTA_DIPLO", "type": "Diplomacy",   "value": "Landmark bilateral win — first major river treaty since Ganga Water Treaty 1996", "source": "MEA Treaty Archive"},
            {"impact_id": "IMP_TEESTA_WB",    "type": "Domestic",    "value": "West Bengal political backlash — TMC withdraws state-level cooperation with Centre", "source": "Curated"},
        ],
        "actors": [
            {"actor_id": "ACT_MEA_BD",  "name": "Ministry of External Affairs",         "type": "Government",     "role": "Lead negotiator — 43-year treaty finalization"},
            {"actor_id": "ACT_JRC",     "name": "Joint Rivers Commission",               "type": "International",  "role": "Technical flow data and allocation framework"},
            {"actor_id": "ACT_BD_GOV",  "name": "Bangladesh Government",                "type": "International",  "role": "Treaty co-signatory — Dhaka water security imperative"},
        ],
        "schemes": [
            {"scheme_id": "SCH_TEESTA_PROJECT", "name": "Teesta River Management Project", "status": "active", "fund": "₹8,000 Cr", "ministry": "Jal Shakti"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_BD_FARMERS",    "group": "Bangladeshi Farmers (Northern Belt)", "count": 3200000},
            {"ben_id": "BEN_WB_FARMERS",    "group": "West Bengal Farmers — Jalpaiguri / Cooch Behar", "count": 1800000},
        ],
        "connections": ["EVT_INDUS_WATERS_CRISIS_2025", "EVT_INDIA_PAK_DIPLO_CRISIS_2025"],
    },
    {
        "event_id":    "EVT_ARUNACHAL_STANDOFF_2026",
        "name":        "Arunachal Pradesh Standoff — PLA Forward Posture",
        "domain":      "Defense",
        "date":        "Jun 2026",
        "severity":    "critical",
        "description": "PLA troops advance 4.2 km into disputed Asaphila sector of Arunachal Pradesh, triggering the most serious Sino-Indian border incident since Galwan 2020. India deploys 3 additional mountain divisions and activates IAF advanced landing grounds at Tawang and Pasighat.",
        "confidence":  0.87,
        "lat":         27.1025,
        "lon":         92.9556,
        "region_id":   "REG_ARUNACHAL",
        "impacts": [
            {"impact_id": "IMP_ARUNA_TROOPS", "type": "Military",   "value": "3 Mountain Divisions deployed — 45,000 additional troops on Arunachal LoAC", "source": "MoD Press Release Jun 2026"},
            {"impact_id": "IMP_ARUNA_CIVCAS", "type": "Civilian",   "value": "12 border villages evacuated — 3,200 residents displaced to Itanagar relief camps", "source": "Arunachal Pradesh DM Office"},
            {"impact_id": "IMP_ARUNA_TRADE",  "type": "Economics",  "value": "India suspends China bilateral trade talks — $118B trade relationship under review", "source": "DPIIT Trade Monitor"},
        ],
        "actors": [
            {"actor_id": "ACT_PLA",     "name": "People's Liberation Army",   "type": "Military",    "role": "Forward posture into Asaphila sector"},
            {"actor_id": "ACT_IA_EAST", "name": "Indian Army Eastern Command","type": "Military",    "role": "Surge deployment — 3 mountain divisions activated"},
            {"actor_id": "ACT_IAF_ALG", "name": "IAF Eastern Air Command",   "type": "Military",    "role": "Advanced Landing Grounds at Tawang and Pasighat activated"},
        ],
        "schemes": [
            {"scheme_id": "SCH_VIBRANT_VILLAGES", "name": "Vibrant Villages Programme — Border Belt", "status": "active", "fund": "₹4,800 Cr", "ministry": "MHA"},
            {"scheme_id": "SCH_BRO_INFRA",        "name": "BRO Border Road Acceleration",            "status": "active", "fund": "₹14,000 Cr","ministry": "MoD"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_ARUNA_BORDER",  "group": "Arunachal Border Villagers — Vibrant Villages", "count": 320000},
            {"ben_id": "BEN_ARUNA_EVAC",    "group": "Evacuated Civilians in Relief Camps",            "count": 3200},
        ],
        "connections": ["EVT_OPERATION_SINDOOR_2025", "EVT_INDIA_PAK_DIPLO_CRISIS_2025"],
    },
    {
        "event_id":    "EVT_US_INDIA_TRADE_2026",
        "name":        "US-India Strategic Trade Framework",
        "domain":      "Economics",
        "date":        "Sep 2026",
        "severity":    "high",
        "description": "India and the US sign a Strategic Trade Framework covering semiconductors, critical minerals, AI governance, and pharma market access — the most comprehensive bilateral trade agreement since the 2005 NSSP. India gains preferential tariff on 400+ goods categories.",
        "confidence":  0.91,
        "lat":         28.6139,
        "lon":         77.2090,
        "region_id":   "REG_DELHI",
        "impacts": [
            {"impact_id": "IMP_USTRADE_PHARMA", "type": "Trade",       "value": "India pharma gets expedited FDA pathway — ₹28,000 Cr pipeline unblocked", "source": "DPIIT Trade Framework Annex IV"},
            {"impact_id": "IMP_USTRADE_MINERALS","type": "Strategic",  "value": "India added to US Strategic Minerals Supply Chain — cobalt, lithium, rare earth access", "source": "US DoD Critical Minerals \nList"},
            {"impact_id": "IMP_USTRADE_FDI",     "type": "Investment", "value": "US FDI committed: $50B over 5 years in tech, infrastructure, and defence manufacturing", "source": "USIBC Press Release Sep 2026"},
        ],
        "actors": [
            {"actor_id": "ACT_USSTR",   "name": "USTR (US Trade Representative)", "type": "Government",    "role": "Framework lead negotiator"},
            {"actor_id": "ACT_DPIIT",   "name": "DPIIT India",                    "type": "Government",    "role": "India lead negotiator and market access framework"},
            {"actor_id": "ACT_USIBC",   "name": "US-India Business Council",      "type": "Industry",      "role": "Private sector advocacy — 500+ member companies"},
        ],
        "schemes": [
            {"scheme_id": "SCH_PLI_PHARMA",  "name": "PLI Pharma — API Export Push", "status": "active", "fund": "₹15,000 Cr", "ministry": "MoC&I"},
            {"scheme_id": "SCH_CAMPA_MINERALS","name": "Critical Mineral Mission",   "status": "active", "fund": "₹34,000 Cr", "ministry": "MoMines"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_PHARMA_EXPORTERS", "group": "Indian Pharma Exporters to US Market",          "count": 3000000},
            {"ben_id": "BEN_TECH_MFG",         "group": "Indian Electronics & Semiconductor Manufacturers","count": 500000},
        ],
        "connections": ["EVT_INDIA_US_DEFENSE_2025", "EVT_INDIA_SEMI_MICRON_2026", "EVT_India_UK_CETA_2025"],
    },
    {
        "event_id":    "EVT_AI_REGULATION_ACT_2026",
        "name":        "India AI Regulation Act 2026",
        "domain":      "Governance",
        "date":        "Jul 2026",
        "severity":    "high",
        "description": "The Digital India AI Governance Act 2026 is passed by Parliament, placing Tier-1 risk classification on AI systems used in healthcare, judiciary, credit scoring, and public safety. MeitY establishes the AI Regulatory Board (AIRB) with SEBI-equivalent enforcement powers.",
        "confidence":  0.89,
        "lat":         28.6139,
        "lon":         77.2090,
        "region_id":   "REG_DELHI",
        "impacts": [
            {"impact_id": "IMP_AI_STARTUPS",  "type": "Industry",    "value": "1,400+ Indian AI startups must register and comply — estimated 18-month compliance cycle", "source": "MeitY AIRB Draft Rules"},
            {"impact_id": "IMP_AI_HEALTHCARE","type": "Healthcare",  "value": "AI diagnostic systems in 600+ hospitals require AIRB certification — 12-month transition", "source": "NHA + MoHFW Circular"},
            {"impact_id": "IMP_AI_JOBS",      "type": "Employment",  "value": "Projected 80,000 new AI ethics, compliance and audit jobs by 2028", "source": "NASSCOM AI Workforce Report 2026"},
        ],
        "actors": [
            {"actor_id": "ACT_MEITY_AI",  "name": "MeitY — AI Governance Division",  "type": "Government", "role": "Policy framer and AIRB parent body"},
            {"actor_id": "ACT_AIRB",      "name": "AI Regulatory Board (AIRB)",       "type": "Regulator",  "role": "Enforcement, certification, and audit authority"},
            {"actor_id": "ACT_NASSCOM",   "name": "NASSCOM",                          "type": "Industry",   "role": "Industry consultation and compliance framework design"},
        ],
        "schemes": [
            {"scheme_id": "SCH_INDIAAI",    "name": "IndiaAI Mission",          "status": "active", "fund": "₹10,372 Cr", "ministry": "MeitY"},
            {"scheme_id": "SCH_AI_COMPUTE", "name": "Public AI Compute Mission","status": "active", "fund": "₹4,500 Cr",  "ministry": "MeitY"},
        ],
        "beneficiaries": [
            {"ben_id": "BEN_AI_STARTUPS",  "group": "Indian AI Startups and Tech Companies", "count": 1400},
            {"ben_id": "BEN_AI_CITIZENS",  "group": "Citizens Protected by AI Governance Framework", "count": 1400000000},
        ],
        "connections": ["EVT_INDIA_US_DEFENSE_2025", "EVT_SHUKLA_ISS_2025"],
    },
]


def seed_event(tx, evt):
    now = datetime.utcnow().isoformat()

    # 1. MERGE the Event node
    tx.run("""
        MERGE (e:Event {event_id: $event_id})
        SET e.name        = $name,
            e.domain      = $domain,
            e.date        = $date,
            e.severity    = $severity,
            e.description = $description,
            e.confidence  = $confidence,
            e.lat         = $lat,
            e.lon         = $lon,
            e.status      = 'active',
            e.source      = 'seed_2026_events.py',
            e.created_at  = $now
    """, event_id=evt["event_id"], name=evt["name"], domain=evt["domain"],
         date=evt["date"], severity=evt["severity"], description=evt["description"],
         confidence=evt["confidence"], lat=evt["lat"], lon=evt["lon"], now=now)

    # 2. Region
    tx.run("""
        MERGE (r:Region {region_id: $region_id})
        MERGE (e:Event {event_id: $event_id})
        MERGE (e)-[:OCCURRED_IN]->(r)
    """, region_id=evt["region_id"], event_id=evt["event_id"])

    # 3. Impacts
    for imp in evt.get("impacts", []):
        tx.run("""
            MATCH (e:Event {event_id: $event_id})
            MERGE (i:Impact {impact_id: $impact_id})
            SET i.type  = $type,
                i.value = $value,
                i.source = $source
            MERGE (e)-[:HAS_IMPACT]->(i)
        """, event_id=evt["event_id"], **imp)

    # 4. Actors
    for act in evt.get("actors", []):
        tx.run("""
            MATCH (e:Event {event_id: $event_id})
            MERGE (a:Actor {actor_id: $actor_id})
            SET a.name = $name,
                a.type = $type,
                a.role = $role
            MERGE (a)-[:INVOLVED_IN]->(e)
        """, event_id=evt["event_id"], **act)

    # 5. Schemes + Beneficiaries
    for sch in evt.get("schemes", []):
        tx.run("""
            MATCH (e:Event {event_id: $event_id})
            MERGE (s:Scheme {scheme_id: $scheme_id})
            SET s.name     = $name,
                s.status   = $status,
                s.fund     = $fund,
                s.ministry = $ministry
            MERGE (e)-[:TRIGGERED]->(s)
        """, event_id=evt["event_id"], **sch)

    for ben in evt.get("beneficiaries", []):
        tx.run("""
            MATCH (e:Event {event_id: $event_id})
            MERGE (b:Beneficiary {ben_id: $ben_id})
            SET b.group = $group,
                b.count = $count
            MERGE (e)-[:BENEFITS]->(b)
        """, event_id=evt["event_id"], **ben)

    # 6. Cross-event CONNECTED_TO edges
    for target_id in evt.get("connections", []):
        tx.run("""
            MATCH (e:Event {event_id: $src}), (t:Event {event_id: $tgt})
            MERGE (e)-[:CONNECTED_TO]->(t)
        """, src=evt["event_id"], tgt=target_id)


def main():
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    with driver.session() as session:
        for evt in EVENTS:
            print(f"  Seeding: {evt['event_id']}...", end=" ")
            session.execute_write(seed_event, evt)
            print("✅")
    print(f"\nDone. {len(EVENTS)} events seeded into Neo4j.")
    driver.close()


if __name__ == "__main__":
    main()
