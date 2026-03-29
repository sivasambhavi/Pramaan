"""
seed_crisis_events.py — PRAMAAN Crisis Data Seeder

Seeds SubEvent, Indicator, and Decision nodes for the 4 crisis events
that are missing from Neo4j:
  - EVT_HORMUZ_BLOCKADE_2026
  - EVT_IRAN_CEASEFIRE_TALKS_2026
  - EVT_INDUS_WATERS_CRISIS_2025
  - EVT_INDIA_PAK_DIPLO_CRISIS_2025

Run: python backend/scripts/seed_crisis_events.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.neo4j_client import get_session



# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

CRISIS_DATA = {

    # ── Hormuz Blockade ───────────────────────────────────────────────────────
    "EVT_HORMUZ_BLOCKADE_2026": {
        "subevents": [
            {"subevent_id": "SE_HORMUZ_D01", "name": "Iran declares Hormuz closure",
             "date": "2026-03-01", "day_number": 1, "category": "military", "severity": "critical",
             "description": "IRGC naval forces halt all tanker traffic. 21M bbl/day global flow disrupted.",
             "india_impact": "40-45% of India's crude supply route blocked; IOC/BPCL emergency procurement activated."},
            {"subevent_id": "SE_HORMUZ_D05", "name": "Brent Crude hits $127/bbl",
             "date": "2026-03-05", "day_number": 5, "category": "economic", "severity": "critical",
             "description": "Oil markets spike on supply shock; US SPR release announced.",
             "india_impact": "Fuel price revision imminent — ₹8-12/litre increase modelled by MoPNG."},
            {"subevent_id": "SE_HORMUZ_D09", "name": "UN Security Council emergency session",
             "date": "2026-03-09", "day_number": 9, "category": "diplomatic", "severity": "high",
             "description": "UNSC convenes emergency session; India abstains, calls for humanitarian passage.",
             "india_impact": "India maintains strategic neutrality; SCI tankers rerouted via Cape of Good Hope."},
            {"subevent_id": "SE_HORMUZ_D14", "name": "Cape of Good Hope rerouting operational",
             "date": "2026-03-14", "day_number": 14, "category": "policy", "severity": "high",
             "description": "Indian PSU tankers adopt 12-14 day longer route; freight up $4/bbl.",
             "india_impact": "Jamnagar refinery throughput down 35%; demand-side rationing under review."},
            {"subevent_id": "SE_HORMUZ_D18", "name": "Oman-brokered partial corridor opens",
             "date": "2026-03-18", "day_number": 18, "category": "diplomatic", "severity": "high",
             "description": "Oman negotiates limited tanker corridor through Musandam strait.",
             "india_impact": "2 Indian LNG vessels cleared; SPR buffer pressure slightly eased."},
            {"subevent_id": "SE_HORMUZ_D22", "name": "India-Oman emergency energy protocol",
             "date": "2026-03-22", "day_number": 22, "category": "policy", "severity": "high",
             "description": "India and Oman sign emergency energy corridor MOU; Musandam route formalized.",
             "india_impact": "Crude import gap partially bridged; SPR cover extended to 9 days."},
        ],
        "indicators": [
            {"indicator_id": "IND_HORMUZ_BRENT", "name": "Brent Crude Price", "value": 127.0,
             "unit": "USD/bbl", "trend": "rising", "domain": "economics"},
            {"indicator_id": "IND_HORMUZ_INR", "name": "INR/USD Rate", "value": 87.8,
             "unit": "INR/USD", "trend": "depreciating", "domain": "economics"},
            {"indicator_id": "IND_HORMUZ_SPR", "name": "India SPR Cover", "value": 7.2,
             "unit": "days", "trend": "critically_low", "domain": "economics"},
            {"indicator_id": "IND_HORMUZ_TRAFFIC", "name": "Hormuz Daily Traffic", "value": 3.0,
             "unit": "vessels/day", "trend": "critically_low", "domain": "geopolitics"},
            {"indicator_id": "IND_HORMUZ_FREIGHT", "name": "Gulf-India Freight Rate", "value": 340.0,
             "unit": "% vs baseline", "trend": "volatile_high", "domain": "economics"},
            {"indicator_id": "IND_HORMUZ_REFINERY", "name": "India Refinery Throughput", "value": 65.0,
             "unit": "% of capacity", "trend": "falling", "domain": "economics"},
        ],
        "decisions": [
            {"decision_id": "DEC_HORMUZ_SPR", "name": "Strategic Petroleum Reserve Emergency Release",
             "date": "2026-03-03", "status": "active", "actor_id": "ACT_MOPNG",
             "description": "Full SPR draw-down authorised; 7-day buffer deployed to IOC, BPCL, HPCL refineries."},
            {"decision_id": "DEC_HORMUZ_CRUDE", "name": "Emergency Crude — Russia + West Africa",
             "date": "2026-03-06", "status": "executed", "actor_id": "ACT_IOC",
             "description": "Spot purchases from Rosneft (+15%) and Nigerian NNPC; Vladivostok route tanker chartered."},
            {"decision_id": "DEC_HORMUZ_RBI", "name": "RBI Forex Intervention $7.4B",
             "date": "2026-03-08", "status": "executed", "actor_id": "ACT_RBI",
             "description": "RBI sold $7.4B reserves to defend INR; further intervention authorised if INR crosses 89."},
            {"decision_id": "DEC_HORMUZ_WTO", "name": "WTO Safe Passage Complaint Filed",
             "date": "2026-03-12", "status": "pending", "actor_id": "ACT_MEA",
             "description": "India files WTO complaint on Iran blockade as discriminatory trade restriction under GATT Art XXI."},
            {"decision_id": "DEC_HORMUZ_OMAN", "name": "India-Oman Emergency Energy MOU",
             "date": "2026-03-22", "status": "executed", "actor_id": "ACT_MEA",
             "description": "Emergency energy corridor MOU signed with Oman; Musandam route formalized for Indian tankers."},
        ],
    },

    # ── Iran Ceasefire Talks ──────────────────────────────────────────────────
    "EVT_IRAN_CEASEFIRE_TALKS_2026": {
        "subevents": [
            {"subevent_id": "SE_CF_D01", "name": "Oman begins Tehran-Washington shuttle",
             "date": "2026-03-05", "day_number": 1, "category": "diplomatic", "severity": "high",
             "description": "Omani FM begins shuttle diplomacy after Saudi back-channel established.",
             "india_impact": "India offers New Delhi as neutral venue; MEA contacts Omani counterpart."},
            {"subevent_id": "SE_CF_D07", "name": "UNSC Resolution 2847 adopted",
             "date": "2026-03-11", "day_number": 7, "category": "diplomatic", "severity": "high",
             "description": "Framework resolution for ceasefire monitoring adopted; India votes yes.",
             "india_impact": "India formally included in ceasefire monitoring working group."},
            {"subevent_id": "SE_CF_D12", "name": "Round 1 — Muscat talks",
             "date": "2026-03-16", "day_number": 12, "category": "diplomatic", "severity": "high",
             "description": "First formal ceasefire round. Iran demands full US carrier withdrawal; US offers 30-day pause.",
             "india_impact": "Jaishankar meets Omani FM; India $50M humanitarian pledge activated."},
            {"subevent_id": "SE_CF_D18", "name": "Humanitarian corridor agreed",
             "date": "2026-03-22", "day_number": 18, "category": "humanitarian", "severity": "high",
             "description": "Partial LNG and food humanitarian corridor through Hormuz agreed.",
             "india_impact": "3 Indian LNG vessels cleared; Brent falls $12 on ceasefire progress."},
            {"subevent_id": "SE_CF_D22", "name": "Round 2 — Geneva Track II",
             "date": "2026-03-26", "day_number": 22, "category": "diplomatic", "severity": "high",
             "description": "Geneva Track II opens; India invited as observer — first non-P5 inclusion.",
             "india_impact": "Strategic autonomy narrative strengthened; India positions for post-conflict reconstruction."},
        ],
        "indicators": [
            {"indicator_id": "IND_CF_BRENT", "name": "Brent Crude Price", "value": 114.0,
             "unit": "USD/bbl", "trend": "falling", "domain": "economics"},
            {"indicator_id": "IND_CF_INR", "name": "INR/USD Rate", "value": 86.9,
             "unit": "INR/USD", "trend": "stable", "domain": "economics"},
            {"indicator_id": "IND_CF_ROUNDS", "name": "Ceasefire Rounds Completed", "value": 3.0,
             "unit": "rounds", "trend": "rising", "domain": "geopolitics"},
            {"indicator_id": "IND_CF_HORMUZ", "name": "Hormuz Traffic", "value": 8.0,
             "unit": "vessels/day", "trend": "rising", "domain": "geopolitics"},
            {"indicator_id": "IND_CF_INDIA_COST", "name": "India Weekly Crisis Cost", "value": 14700.0,
             "unit": "Cr INR/week", "trend": "falling", "domain": "economics"},
        ],
        "decisions": [
            {"decision_id": "DEC_CF_AID", "name": "$50M Humanitarian Aid Deployed",
             "date": "2026-03-12", "status": "executed", "actor_id": "ACT_MEA",
             "description": "India's $50M humanitarian contribution to UN-coordinated relief corridor activated."},
            {"decision_id": "DEC_CF_OBSERVER", "name": "India Ceasefire Observer Status Secured",
             "date": "2026-03-22", "status": "active", "actor_id": "ACT_MEA",
             "description": "India accepted as observer in Geneva Track II — first non-P5 inclusion; EAM Jaishankar attending."},
            {"decision_id": "DEC_CF_CHABAHAR", "name": "Chabahar Phase 2 MOU Tabled",
             "date": "2026-03-24", "status": "pending", "actor_id": "ACT_MEA",
             "description": "India tables $2B MOU for post-ceasefire Chabahar Phase 2 — first-mover reconstruction commitment."},
            {"decision_id": "DEC_CF_ENVOY", "name": "Gulf Special Envoy Appointed",
             "date": "2026-03-10", "status": "active", "actor_id": "ACT_MEA",
             "description": "India appoints first permanent Special Envoy for Gulf Affairs to manage Iran crisis diplomacy."},
        ],
    },

    # ── Indus Waters Crisis ───────────────────────────────────────────────────
    "EVT_INDUS_WATERS_CRISIS_2025": {
        "subevents": [
            {"subevent_id": "SE_INDUS_D01", "name": "IWT formally suspended by Cabinet",
             "date": "2025-04-24", "day_number": 1, "category": "policy", "severity": "critical",
             "description": "Cabinet approves suspension of Indus Waters Treaty (1960) — first in 65 years.",
             "india_impact": "India no longer obligated to share hydrological data; Jal Shakti accelerates Western river projects."},
            {"subevent_id": "SE_INDUS_D05", "name": "Pakistan files World Bank objection",
             "date": "2025-04-28", "day_number": 5, "category": "diplomatic", "severity": "high",
             "description": "Pakistan Indus Commission formally objects to World Bank; arbitration tribunal initiated.",
             "india_impact": "MEA files preemptive legal brief citing Article XII(3) — material breach by Pakistan."},
            {"subevent_id": "SE_INDUS_D12", "name": "Kishanganga works accelerated",
             "date": "2025-05-05", "day_number": 12, "category": "policy", "severity": "high",
             "description": "NHPC announces accelerated Kishanganga (330 MW) timeline — 18-month commissioning target.",
             "india_impact": "330 MW hydro capacity added to northern grid; reduces coal dependency."},
            {"subevent_id": "SE_INDUS_D18", "name": "Ratle project fast-tracked",
             "date": "2025-05-12", "day_number": 18, "category": "policy", "severity": "high",
             "description": "Ratle (850 MW) fast-tracked under national security emergency provision.",
             "india_impact": "Combined Kishanganga + Ratle = 1,180 MW renewable addition operational within 24 months."},
            {"subevent_id": "SE_INDUS_D25", "name": "Permanent Indus Commission halted",
             "date": "2025-05-18", "day_number": 25, "category": "diplomatic", "severity": "high",
             "description": "Biannual Indus Commission meeting cancelled; dispute resolution mechanism non-functional.",
             "india_impact": "No diplomatic channel for water disputes — bilateral escalation risk elevated."},
            {"subevent_id": "SE_INDUS_D35", "name": "IWT renegotiation study commissioned",
             "date": "2025-05-28", "day_number": 35, "category": "policy", "severity": "high",
             "description": "Ministry of Jal Shakti commissions comprehensive re-evaluation of 1960 IWT terms.",
             "india_impact": "India's position for treaty renegotiation to be formally tabled at World Bank in 6 months."},
        ],
        "indicators": [
            {"indicator_id": "IND_INDUS_KISHANGANGA", "name": "Kishanganga Completion", "value": 68.0,
             "unit": "% complete", "trend": "rising", "domain": "governance"},
            {"indicator_id": "IND_INDUS_DATA_SHARE", "name": "Hydrological Data Sharing", "value": 0.0,
             "unit": "% (suspended)", "trend": "stable", "domain": "governance"},
            {"indicator_id": "IND_INDUS_WB", "name": "World Bank Arbitration Cases", "value": 1.0,
             "unit": "active cases", "trend": "high", "domain": "geopolitics"},
            {"indicator_id": "IND_INDUS_RATLE_MW", "name": "Ratle Hydro Target", "value": 850.0,
             "unit": "MW", "trend": "rising", "domain": "governance"},
            {"indicator_id": "IND_INDUS_PAK_AGRI", "name": "Pakistan Irrigated Farmland at Risk", "value": 80.0,
             "unit": "% of total", "trend": "rising", "domain": "geopolitics"},
            {"indicator_id": "IND_INDUS_WESTERN_RIVERS", "name": "Western River Storage Rights", "value": 100.0,
             "unit": "% unlocked", "trend": "rising", "domain": "governance"},
        ],
        "decisions": [
            {"decision_id": "DEC_INDUS_SUSPEND", "name": "IWT Suspension — Cabinet Decision",
             "date": "2025-04-24", "status": "executed", "actor_id": "ACT_CCS",
             "description": "Formal suspension of Indus Waters Treaty approved; legal justification citing Article XII(3) filed."},
            {"decision_id": "DEC_INDUS_KISH", "name": "Kishanganga Fast-Track Order",
             "date": "2025-05-05", "status": "active", "actor_id": "ACT_NHPC",
             "description": "Emergency commissioning for Kishanganga 330 MW; 18-month target with quarterly NHPC milestones."},
            {"decision_id": "DEC_INDUS_LEGAL", "name": "World Bank Legal Brief Filed",
             "date": "2025-05-02", "status": "executed", "actor_id": "ACT_MEA",
             "description": "India's preemptive legal position filed at World Bank — grounds citing Pakistan-sponsored terrorism."},
            {"decision_id": "DEC_INDUS_RENEGOTIATE", "name": "IWT Renegotiation Study Commissioned",
             "date": "2025-05-15", "status": "active", "actor_id": "ACT_JAL_SHAKTI",
             "description": "6-month study on IWT renegotiation options; position paper for World Bank formally tabled."},
            {"decision_id": "DEC_INDUS_RATLE", "name": "Ratle Emergency Clearance",
             "date": "2025-05-12", "status": "executed", "actor_id": "ACT_MOE",
             "description": "Environmental clearance for Ratle 850 MW expedited under national security emergency provision."},
        ],
    },

    # ── India-Pakistan Diplomatic Crisis ─────────────────────────────────────
    "EVT_INDIA_PAK_DIPLO_CRISIS_2025": {
        "subevents": [
            {"subevent_id": "SE_DIPLO_D01", "name": "India downgrades diplomatic relations",
             "date": "2025-05-02", "day_number": 1, "category": "diplomatic", "severity": "critical",
             "description": "India expels Pakistani HC staff; relations reduced to Chargé d'Affaires level — worst since 1971.",
             "india_impact": "Attari-Wagah border closed; $2.4B annual bilateral trade halted immediately."},
            {"subevent_id": "SE_DIPLO_D03", "name": "Pakistan closes airspace to India",
             "date": "2025-05-04", "day_number": 3, "category": "diplomatic", "severity": "high",
             "description": "Pakistan retaliates by closing airspace to all Indian commercial aircraft.",
             "india_impact": "200+ daily India-Europe flights rerouted; ₹170 Cr/month detour cost to airlines."},
            {"subevent_id": "SE_DIPLO_D05", "name": "SAARC processes frozen",
             "date": "2025-05-06", "day_number": 5, "category": "diplomatic", "severity": "high",
             "description": "India formally suspends participation in all SAARC processes pending normalisation.",
             "india_impact": "Regional cooperation architecture suspended; SAARC trade negotiations halted."},
            {"subevent_id": "SE_DIPLO_D08", "name": "MEA briefs UNSC P5 — India's case",
             "date": "2025-05-09", "day_number": 8, "category": "diplomatic", "severity": "high",
             "description": "Jaishankar briefs UNSC P5 individually with dossier evidence; US and UK condemn Pakistan-based terror.",
             "india_impact": "Pakistan's UNSC emergency session request blocked by US/UK diplomatic support."},
            {"subevent_id": "SE_DIPLO_D14", "name": "Central Asian airspace agreements signed",
             "date": "2025-05-16", "day_number": 14, "category": "economic", "severity": "high",
             "description": "India signs bilateral airspace agreements with Tajikistan and Kazakhstan.",
             "india_impact": "Per-flight cost premium reduced from $112 to $38; permanent routing via Central Asia established."},
            {"subevent_id": "SE_DIPLO_D21", "name": "WTO airspace complaint formally filed",
             "date": "2025-05-23", "day_number": 21, "category": "policy", "severity": "high",
             "description": "India files WTO dispute on Pakistan airspace closure as discriminatory trade restriction.",
             "india_impact": "Legal pressure on Pakistan; UAE alternative routing operationalized as backup."},
        ],
        "indicators": [
            {"indicator_id": "IND_DIPLO_TRADE", "name": "India-Pakistan Bilateral Trade", "value": 0.0,
             "unit": "% of normal", "trend": "critically_low", "domain": "economics"},
            {"indicator_id": "IND_DIPLO_AIRSPACE", "name": "Airspace Detour Cost", "value": 38.0,
             "unit": "USD/flight extra", "trend": "falling", "domain": "economics"},
            {"indicator_id": "IND_DIPLO_LEVEL", "name": "Diplomatic Relations Level", "value": 1.0,
             "unit": "Chargé level", "trend": "negative", "domain": "geopolitics"},
            {"indicator_id": "IND_DIPLO_LOC", "name": "LoC Ceasefire Compliance", "value": 85.0,
             "unit": "% compliance", "trend": "stable", "domain": "defense"},
            {"indicator_id": "IND_DIPLO_ISOLATION", "name": "Pakistan Diplomatic Isolation Index", "value": 72.0,
             "unit": "/100", "trend": "rising", "domain": "geopolitics"},
            {"indicator_id": "IND_DIPLO_PAK_ECO", "name": "Pakistan Economic Pressure Index", "value": 68.0,
             "unit": "/100", "trend": "rising", "domain": "economics"},
        ],
        "decisions": [
            {"decision_id": "DEC_DIPLO_BORDER", "name": "Attari-Wagah Border Closure",
             "date": "2025-05-02", "status": "active", "actor_id": "ACT_MHA",
             "description": "Attari-Wagah land border closed indefinitely; all bilateral trade suspended pending normalisation."},
            {"decision_id": "DEC_DIPLO_SAARC", "name": "SAARC Visa Scheme Suspended",
             "date": "2025-05-03", "status": "executed", "actor_id": "ACT_MEA",
             "description": "SAARC Visa Exemption Scheme suspended for Pakistani nationals; existing visas revoked."},
            {"decision_id": "DEC_DIPLO_DOSSIER", "name": "Pakistan Dossier Submitted to UNSC",
             "date": "2025-05-08", "status": "executed", "actor_id": "ACT_IB",
             "description": "Formal dossier on Pahalgam attack perpetrators submitted to UN Counter-Terrorism Committee with ISI links evidence."},
            {"decision_id": "DEC_DIPLO_ROUTING", "name": "Central Asian Airspace Agreements",
             "date": "2025-05-16", "status": "executed", "actor_id": "ACT_DGCA",
             "description": "Bilateral airspace agreements with Tajikistan and Kazakhstan signed; permanent routes operational."},
            {"decision_id": "DEC_DIPLO_WTO", "name": "WTO Airspace Complaint Filed",
             "date": "2025-05-23", "status": "executed", "actor_id": "ACT_MEA",
             "description": "Formal WTO complaint filed on Pakistan airspace denial as discriminatory restriction under GATT Article XXI."},
            {"decision_id": "DEC_DIPLO_DOCTRINE", "name": "Nuclear Deterrence Doctrine Review",
             "date": "2025-05-20", "status": "active", "actor_id": "ACT_NSA",
             "description": "NSA commission to formalize India's crisis de-escalation doctrine with nuclear-armed neighbours; P5 to be briefed."},
        ],
    },
}


def seed_crisis_data():
    """Seed SubEvent, Indicator, and Decision nodes for all crisis events into Neo4j."""
    ts = "2026-03-28T00:00:00Z"

    with get_session() as s:
        for event_id, crisis in CRISIS_DATA.items():
            print(f"\n{'='*60}")
            print(f"Seeding: {event_id}")

            # Verify parent event exists
            row = s.run("MATCH (e:Event {event_id: $eid}) RETURN e.name AS name", eid=event_id).single()
            if not row:
                print(f"  ⚠  Event {event_id} NOT FOUND in Neo4j — skipping")
                continue
            print(f"  ✓  Parent event found: {row['name']}")

            # ── SubEvents ─────────────────────────────────────────────────────
            se_count = 0
            prev_se_id = None
            for se in crisis["subevents"]:
                s.run("""
                    MERGE (n:SubEvent {subevent_id: $sid})
                    SET n.name        = $name,
                        n.date        = $date,
                        n.day_number  = $day,
                        n.category    = $cat,
                        n.severity    = $sev,
                        n.description = $desc,
                        n.india_impact = $impact,
                        n.source      = 'seeded',
                        n.ingested_at = $ts
                    WITH n
                    MATCH (e:Event {event_id: $eid})
                    MERGE (e)-[:CONTAINS]->(n)
                """, sid=se["subevent_id"], name=se["name"], date=se["date"],
                     day=se["day_number"], cat=se["category"], sev=se["severity"],
                     desc=se["description"], impact=se["india_impact"],
                     eid=event_id, ts=ts)

                if prev_se_id:
                    s.run("""
                        MATCH (a:SubEvent {subevent_id: $a})
                        MATCH (b:SubEvent {subevent_id: $b})
                        MERGE (a)-[:PRECEDES]->(b)
                    """, a=prev_se_id, b=se["subevent_id"])

                prev_se_id = se["subevent_id"]
                se_count += 1
            print(f"  ✓  {se_count} SubEvents seeded")

            # ── Indicators ────────────────────────────────────────────────────
            ind_count = 0
            for ind in crisis["indicators"]:
                s.run("""
                    MERGE (n:Indicator {indicator_id: $iid})
                    SET n.name   = $name,
                        n.value  = $val,
                        n.unit   = $unit,
                        n.trend  = $trend,
                        n.domain = $domain,
                        n.as_of  = $ts,
                        n.source = 'seeded'
                    WITH n
                    MATCH (e:Event {event_id: $eid})
                    MERGE (e)-[:SIGNALS]->(n)
                """, iid=ind["indicator_id"], name=ind["name"],
                     val=float(ind["value"]), unit=ind["unit"],
                     trend=ind["trend"], domain=ind.get("domain", ""),
                     eid=event_id, ts=ts)
                ind_count += 1
            print(f"  ✓  {ind_count} Indicators seeded")

            # ── Decisions ─────────────────────────────────────────────────────
            dec_count = 0
            for dec in crisis["decisions"]:
                s.run("""
                    MERGE (n:Decision {decision_id: $did})
                    SET n.name        = $name,
                        n.date        = $date,
                        n.status      = $status,
                        n.description = $desc,
                        n.source      = 'seeded',
                        n.ingested_at = $ts
                    WITH n
                    MATCH (e:Event {event_id: $eid})
                    MERGE (n)-[:RESPONDS_TO]->(e)
                """, did=dec["decision_id"], name=dec["name"],
                     date=dec["date"], status=dec["status"],
                     desc=dec["description"], eid=event_id, ts=ts)
                dec_count += 1
            print(f"  ✓  {dec_count} Decisions seeded")

    print(f"\n{'='*60}")
    print("✅  Crisis seeding complete.")


if __name__ == "__main__":
    seed_crisis_data()
