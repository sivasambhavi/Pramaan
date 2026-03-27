"""
ontology_graph.py — PRAMAAN v5
Decision Engine: interactive knowledge graph (streamlit-agraph), Type 1/2 scheme panels,
cross-domain connections, node detail panel.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../..", ".env"))

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from utils.api import safe_get
from utils.events import EVENTS_BY_ID, render_event_dropdown
from components.topnav import render_topnav
from components.ontology_model import render_ontology_model

_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://192.168.48.1:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:latest")
_GROQ_OK = True   # kept for UI gate — Ollama always available


def _generate_insights(event_id: str, event_name: str, context: str):
    """Stream Ollama insights for a selected event."""
    import requests, json as _json
    prompt = (
        f"You are PRAMAAN, an AI governance intelligence engine.\n\n"
        f"Event: {event_name} ({event_id})\n\n"
        f"Context:\n{context}\n\n"
        "Reply with EXACTLY this structure. One line per point, no extra explanation.\n\n"
        "### Situation\n"
        "One sentence only.\n\n"
        "### Cross-Domain Impact\n"
        "Exactly 5 bullets, one line each:\n"
        "- **[Domain]** → [10 words max]\n\n"
        "### Actions\n"
        "3 bullets, one line each:\n"
        "- **[Actor]** · [action] · [outcome]"
    )
    resp = requests.post(
        f"{_OLLAMA_HOST}/api/generate",
        json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()

    class _StreamWrapper:
        """Wraps Ollama streaming response to match the iteration pattern."""
        def __init__(self, r):
            self._r = r

        def __iter__(self):
            for line in self._r.iter_lines():
                if line:
                    chunk = _json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        return

    return _StreamWrapper(resp)

NODE_CONFIG = {
    "Event":    {"color": "#f97316", "size": 26, "shape": "dot",     "desc": "High-impact incidents"},
    "Domain":   {"color": "#a78bfa", "size": 20, "shape": "diamond", "desc": "Policy areas"},
    "Region":   {"color": "#22c55e", "size": 16, "shape": "dot",     "desc": "Geographic locations"},
    "Actor":    {"color": "#38bdf8", "size": 16, "shape": "dot",     "desc": "Govt bodies & agencies"},
    "Scheme":   {"color": "#facc15", "size": 14, "shape": "dot",     "desc": "Funding programmes"},
    "Policy":   {"color": "#fb7185", "size": 14, "shape": "dot",     "desc": "Legislation & policy"},
    "Impact":   {"color": "#94a3b8", "size": 8,  "shape": "dot",     "desc": "Measured outcomes"},
    "Evidence": {"color": "#e2e8f0", "size": 7,  "shape": "dot",     "desc": "PIB · NDMA · ISRO sources"},
}

# Node types that show labels — Impact/Evidence hidden to reduce clutter
_LABELLED_TYPES = {"Event", "Domain", "Actor", "Region", "Scheme", "Policy"}

DOMAIN_COLORS = {
    "Climate":     "#22c55e",
    "Defense":     "#f97316",
    "Economics":   "#38bdf8",
    "Society":     "#fb7185",
    "Governance":  "#06b6d4",
    "Geopolitics": "#a78bfa",
    "Technology":  "#facc15",
}

EDGE_COLORS = {
    # Cross-domain — gold, dashed, thick
    "CONNECTED_TO": "#FFD700", # Causation / action — orange
    "TRIGGERED":    "#f97316",
    "CAUSED":       "#f97316",
    "CAUSED_BY":    "#f97316",
    # Impact / harm — red
    "IMPACTED":     "#ef4444",
    "IMPACTS":      "#ef4444",
    # Positive / activated — green
    "ACTIVATED":    "#22c55e",
    "PROVEN_BY":    "#22c55e",
    "OCCURRED_IN":  "#22c55e",
    # Policy / governance — purple
    "GOVERNED_BY":  "#a78bfa",
    "MANAGED_BY":   "#a78bfa",
    "BELONGS_TO":   "#a78bfa",
    "ALSO_IN":      "#a78bfa",
    # Funding — yellow
    "FUNDED_BY":    "#facc15",
    # Structural — muted
    "PART_OF":      "#475569",
    "LOCATED_IN":   "#475569",
}

_DECISION_PANELS = {
    "EVT_DELHI_FLOODS_2023": {
        "scheme": "AMRUT 2.0 — Delhi NCT · Storm Water Drainage",
        "allocated": "₹5.38 Cr", "status": "1 / 3 unverified",
        "action": "Investigate Ward 46",
        "detail": "Asset unverified · Audit due · data.gov.in",
        "color": "#f97316",
    },
    "EVT_CYCLONE_DANA_2024": {
        "scheme": "SDRF — Odisha · Cyclone Relief",
        "allocated": "₹800 Cr", "status": "87% delivered",
        "action": "Verify fisheries livelihood coverage",
        "detail": "SDRF covers disaster not livelihood recovery · PM-KISAN gap",
        "color": "#38bdf8",
    },
    "EVT_WAYANAD_2024": {
        "scheme": "Kerala SDRF · Landslide Rehabilitation",
        "allocated": "₹300 Cr", "status": "Relief registration ongoing",
        "action": "Expedite PMAY reconstruction tokens",
        "detail": "Chooralmala families unhoused · 90 day deadline",
        "color": "#22c55e",
    },
    "EVT_ARUNACHAL_STANDOFF_2026": {
        "scheme": "BRO Emergency Road Works + Vibrant Villages Phase 2",
        "allocated": "₹17,200 Cr", "status": "Fast-track approved",
        "action": "Complete 3 critical all-weather corridors by March 2027",
        "detail": "Only 60% of forward posts road-accessible year-round — BRO gap",
        "color": "#f97316",
    },
    "EVT_INDIA_SEMI_MICRON_2026": {
        "scheme": "PLI Semiconductor + India Semiconductor Mission",
        "allocated": "₹86,000 Cr", "status": "Micron Phase 1 operational",
        "action": "Onboard 25 IITs to chip design curriculum by Dec 2026",
        "detail": "85,000 engineer deficit — IIT/NIT pipeline critical for Phase 2",
        "color": "#facc15",
    },
}

# Per-relationship visual properties: (width, dashes, arrows)
EDGE_STYLE = {
    "CONNECTED_TO": (3,   True,  True),   # gold dashed thick
    "TRIGGERED":    (2,   False, True),
    "CAUSED":       (2,   False, True),
    "CAUSED_BY":    (2,   False, True),
    "IMPACTED":     (2,   False, True),
    "IMPACTS":      (2,   False, True),
    "ACTIVATED":    (2,   False, True),
    "PROVEN_BY":    (1.5, False, False),
    "GOVERNED_BY":  (1.5, False, False),
    "MANAGED_BY":   (1.5, False, False),
    "BELONGS_TO":   (1,   False, False),
    "ALSO_IN":      (1,   False, False),
    "FUNDED_BY":    (1.5, False, True),
    "OCCURRED_IN":  (1,   False, False),
    "PART_OF":      (1,   False, False),
    "LOCATED_IN":   (1,   False, False),
}

# --- Fix 14: Hardcoded fallback graph for demo (when Neo4j is down) ----------
_FALLBACK_GRAPH = {
    "stats": {"total_nodes": 89, "total_edges": 134},
    "nodes": [
        # Events — current clean set (2026/2025/2024/2023)
        {"id": "Event_EVT_DELHI_FLOODS_2023",  "label": "Delhi Floods 2023",       "type": "Event", "domain": "Climate",     "props": {"severity": "critical", "date": "Jul 2023", "description": "Record Yamuna flooding — 3.59 lakh cusecs, 208.66m river level, 27,000 displaced."}},
        {"id": "Event_EVT_WAYANAD_2024",        "label": "Wayanad Landslide",       "type": "Event", "domain": "Climate",     "props": {"severity": "critical", "date": "Jul 2024", "description": "India's deadliest landslide — 231 dead, 1,000+ displaced, Mundakkai & Chooralmala."}},
        {"id": "Event_EVT_CHAMOLI_2021",        "label": "Chamoli Glacier",         "type": "Event", "domain": "Climate",     "props": {"severity": "critical", "date": "Feb 2021", "description": "Rock-ice avalanche destroyed NTPC Tapovan (520 MW). 204 killed or missing."}},
        {"id": "Event_EVT_CYCLONE_DANA_2024",   "label": "Cyclone Dana",            "type": "Event", "domain": "Climate",     "props": {"severity": "high",     "date": "Oct 2024", "description": "800,000+ evacuated. ₹6,000 Cr damage across Odisha & Andhra Pradesh."}},
        {"id": "Event_EVT_CHANDRAYAAN3_2023",   "label": "Chandrayaan-3",           "type": "Event", "domain": "Technology",  "props": {"severity": "high",     "date": "Aug 2023", "description": "Lunar south pole soft landing. ₹615 Cr mission cost. ISRO milestone."}},
        {"id": "Event_EVT_INDIA_SEMI_MICRON_2026","label": "Micron Fab Launch",    "type": "Event", "domain": "Technology",  "props": {"severity": "high",     "date": "Aug 2026", "description": "Micron's $825M ATMP fab operational in Sanand — India's first advanced chip packaging plant."}},
        {"id": "Event_EVT_BALAKOT_2019",        "label": "Balakot Strikes",         "type": "Event", "domain": "Defense",     "props": {"severity": "high",     "date": "Feb 2019", "description": "IAF airstrike on JeM camp post-Pulwama. India-Pakistan escalation."}},
        {"id": "Event_EVT_ARUNACHAL_STANDOFF_2026","label": "Arunachal PLA Standoff","type": "Event", "domain": "Defense",  "props": {"severity": "critical", "date": "Jun 2026", "description": "PLA advances 4.2 km into Asaphila sector — India deploys 3 mountain divisions."}},
        {"id": "Event_EVT_ART370_2019",         "label": "Article 370",             "type": "Event", "domain": "Governance",  "props": {"severity": "high",     "date": "Aug 2019", "description": "J&K bifurcated into UTs. ₹56,000 Cr investment pledges post-abrogation."}},
        {"id": "Event_EVT_G20_INDIA_2023",      "label": "G20 India 2023",          "type": "Event", "domain": "Geopolitics", "props": {"severity": "medium",  "date": "Sep 2023", "description": "Delhi Declaration consensus. 83 outcomes. Global South leadership claim."}},
        {"id": "Event_EVT_RUSSIA_UKRAINE_2022", "label": "Russia-Ukraine War",      "type": "Event", "domain": "Geopolitics", "props": {"severity": "high",     "date": "Feb 2022", "description": "India's strategic autonomy tested. Discounted Russian oil — $3B savings."}},
        {"id": "Event_EVT_IRAN_WAR_2026",       "label": "Iran-US-Israel War",      "type": "Event", "domain": "Geopolitics", "props": {"severity": "critical", "date": "Feb 2026", "description": "US strikes on Iranian nuclear facilities — Hormuz closure and regional escalation."}},
        # Actors
        {"id": "ACT_NDMA",    "label": "NDMA",    "type": "Actor", "props": {"role": "National Disaster Management Authority — policy & coordination"}},
        {"id": "ACT_NDRF",    "label": "NDRF",    "type": "Actor", "props": {"role": "National Disaster Response Force — field rescue operations"}},
        {"id": "ACT_DJB",     "label": "DJB",     "type": "Actor", "props": {"role": "Delhi Jal Board — water supply & treatment"}},
        {"id": "ACT_NTPC",    "label": "NTPC",    "type": "Actor", "props": {"role": "National Thermal Power Corp — hydropower construction, Tapovan"}},
        {"id": "ACT_ISRO",    "label": "ISRO",    "type": "Actor", "props": {"role": "Indian Space Research Organisation — space & remote sensing"}},
        {"id": "ACT_MHA",     "label": "MHA",     "type": "Actor", "props": {"role": "Ministry of Home Affairs — SDRF/NDRF fund release"}},
        {"id": "ACT_MOEF",    "label": "MoEF",    "type": "Actor", "props": {"role": "Ministry of Environment — environmental clearances"}},
        {"id": "ACT_IMD",     "label": "IMD",     "type": "Actor", "props": {"role": "India Meteorological Department — weather alerts"}},
        # Schemes
        {"id": "SCH_SDRF",    "label": "SDRF",         "type": "Scheme", "props": {"budget_inr_cr": "43900", "description": "State Disaster Response Fund — disaster relief disbursement"}},
        {"id": "SCH_AMRUT",   "label": "AMRUT 2.0",    "type": "Scheme", "props": {"budget_inr_cr": "66750", "description": "Urban water & drainage infrastructure"}},
        {"id": "SCH_PMAY",    "label": "PMAY-U",        "type": "Scheme", "props": {"budget_inr_cr": "401",   "description": "Affordable urban housing — 17,067 houses Delhi"}},
        {"id": "SCH_PLI_SEMI","label": "PLI Semicon",   "type": "Scheme", "props": {"budget_inr_cr": "76000", "description": "Production Linked Incentive — semiconductor manufacturing"}},
        {"id": "SCH_JJM",     "label": "Jal Jeevan",   "type": "Scheme", "props": {"budget_inr_cr": "197000","description": "Tap water to every household — 76.7% complete"}},
        # Regions
        {"id": "REG_DELHI",   "label": "Delhi",         "type": "Region", "props": {}},
        {"id": "REG_WAYANAD", "label": "Wayanad",       "type": "Region", "props": {}},
        {"id": "REG_CHAMOLI", "label": "Chamoli",       "type": "Region", "props": {}},
        {"id": "REG_ODISHA",  "label": "Odisha",        "type": "Region", "props": {}},
        {"id": "REG_GUJARAT", "label": "Gujarat",       "type": "Region", "props": {}},
        # Domains
        {"id": "DOM_CLIMATE",    "label": "Climate",    "type": "Domain", "props": {}},
        {"id": "DOM_SOCIETY",    "label": "Society",    "type": "Domain", "props": {}},
        {"id": "DOM_TECHNOLOGY", "label": "Technology", "type": "Domain", "props": {}},
        {"id": "DOM_GOVERNANCE", "label": "Governance", "type": "Domain", "props": {}},
        {"id": "DOM_DEFENSE",    "label": "Defense",    "type": "Domain", "props": {}},
        {"id": "DOM_GEOPOLITICS","label": "Geopolitics","type": "Domain", "props": {}},
        {"id": "DOM_ECONOMICS",  "label": "Economics",  "type": "Domain", "props": {}},
        # Evidence
        {"id": "EVD_DELHI_DATAGOV",  "label": "data.gov.in — Yamuna Level",   "type": "Evidence", "props": {"source": "data.gov.in", "type": "sensor_data"}},
        {"id": "EVD_WAYANAD_IMD",    "label": "IMD Orange Alert Jul 2024",     "type": "Evidence", "props": {"source": "IMD",         "type": "weather_alert"}},
        {"id": "EVD_CHAMOLI_ISRO",   "label": "ISRO Glacier Imagery Feb 2021", "type": "Evidence", "props": {"source": "ISRO",        "type": "satellite_imagery"}},
        # Impacts
        {"id": "IMP_DELHI_DISPLACED", "label": "27,000 Displaced",    "type": "Impact", "props": {"value": "27000", "unit": "persons", "type": "displacement"}},
        {"id": "IMP_WAYANAD_DEAD",    "label": "231 Deaths",          "type": "Impact", "props": {"value": "231",   "unit": "persons", "type": "fatalities"}},
        {"id": "IMP_CHAMOLI_DEAD",    "label": "204 Missing/Dead",    "type": "Impact", "props": {"value": "204",   "unit": "persons", "type": "fatalities"}},
        {"id": "IMP_CYCLONE_EVAC",    "label": "800K Evacuated",      "type": "Impact", "props": {"value": "800000","unit": "persons", "type": "evacuation"}},
    ],
    "edges": [
        # ── Event → Domain ──────────────────────────────────────────────────
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "DOM_CLIMATE",     "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "DOM_CLIMATE",     "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "DOM_CLIMATE",     "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_CYCLONE_DANA_2024",   "to": "DOM_CLIMATE",     "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_CHANDRAYAAN3_2023",   "to": "DOM_TECHNOLOGY",  "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_INDIA_SEMI_MICRON_2026","to": "DOM_TECHNOLOGY","type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_BALAKOT_2019",        "to": "DOM_DEFENSE",     "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_ARUNACHAL_STANDOFF_2026","to": "DOM_DEFENSE",  "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_ART370_2019",         "to": "DOM_GOVERNANCE",  "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_G20_INDIA_2023",      "to": "DOM_GEOPOLITICS", "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_RUSSIA_UKRAINE_2022", "to": "DOM_GEOPOLITICS", "type": "BELONGS_TO",  "reason": ""},
        {"from": "Event_EVT_IRAN_WAR_2026",       "to": "DOM_GEOPOLITICS", "type": "BELONGS_TO",  "reason": ""},

        # ── Event → Region ──────────────────────────────────────────────────
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "REG_DELHI",   "type": "OCCURRED_IN", "reason": ""},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "REG_WAYANAD", "type": "OCCURRED_IN", "reason": ""},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "REG_CHAMOLI", "type": "OCCURRED_IN", "reason": ""},
        {"from": "Event_EVT_CYCLONE_DANA_2024",   "to": "REG_ODISHA",  "type": "OCCURRED_IN", "reason": ""},
        {"from": "Event_EVT_INDIA_SEMI_MICRON_2026","to": "REG_GUJARAT","type": "OCCURRED_IN","reason": ""},

        # ── Event → Actor ───────────────────────────────────────────────────
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "ACT_NDMA",  "type": "MANAGED_BY",  "reason": "DDMA coordination and evacuation"},
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "ACT_NDRF",  "type": "MANAGED_BY",  "reason": "Flood rescue operations"},
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "ACT_DJB",   "type": "MANAGED_BY",  "reason": "Chandrawal & Wazirabad plant shutdown"},
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "ACT_IMD",   "type": "MANAGED_BY",  "reason": "Flood alert and rainfall monitoring"},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "ACT_NDRF",  "type": "MANAGED_BY",  "reason": "6 NDRF teams deployed within 24h"},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "ACT_IMD",   "type": "MANAGED_BY",  "reason": "Orange Alert issued 29 Jul — insufficient"},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "ACT_MOEF",  "type": "MANAGED_BY",  "reason": "Gadgil Committee ESA recommendations ignored"},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "ACT_NTPC",  "type": "CAUSED_BY",   "reason": "Tapovan project in Zone V avalanche corridor"},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "ACT_NDRF",  "type": "MANAGED_BY",  "reason": "16 NDRF teams — tunnel rescue"},
        {"from": "Event_EVT_CYCLONE_DANA_2024",   "to": "ACT_NDRF",  "type": "MANAGED_BY",  "reason": "Pre-cyclone NDRF pre-positioning"},
        {"from": "Event_EVT_CYCLONE_DANA_2024",   "to": "ACT_IMD",   "type": "MANAGED_BY",  "reason": "Cyclone track and landfall forecast"},
        {"from": "Event_EVT_CHANDRAYAAN3_2023",   "to": "ACT_ISRO",  "type": "MANAGED_BY",  "reason": "Mission design and execution"},
        {"from": "Event_EVT_INDIA_SEMI_MICRON_2026","to": "ACT_MHA", "type": "MANAGED_BY",  "reason": "PLI scheme approval — MeitY/Cabinet"},

        # ── Event → Scheme ──────────────────────────────────────────────────
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "SCH_SDRF",    "type": "ACTIVATED",  "reason": "Flood disaster — SDRF disbursement triggered"},
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "SCH_AMRUT",   "type": "ACTIVATED",  "reason": "Post-flood storm drain upgrade — AMRUT 2.0"},
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "SCH_PMAY",    "type": "ACTIVATED",  "reason": "Flood-displaced families — PMAY-U housing"},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "SCH_SDRF",    "type": "ACTIVATED",  "reason": "Landslide disaster — Kerala SDRF"},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "SCH_SDRF",    "type": "ACTIVATED",  "reason": "Glacier disaster — Uttarakhand SDRF"},
        {"from": "Event_EVT_CYCLONE_DANA_2024",   "to": "SCH_SDRF",    "type": "ACTIVATED",  "reason": "Cyclone — Odisha SDRF release"},
        {"from": "Event_EVT_INDIA_SEMI_MICRON_2026","to": "SCH_PLI_SEMI","type": "FUNDED_BY","reason": "₹76,000 Cr PLI incentive for Micron/Tata fabs"},

        # ── Event → Evidence ────────────────────────────────────────────────
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "EVD_DELHI_DATAGOV", "type": "PROVEN_BY", "reason": "208.66m river level — data.gov.in sensor"},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "EVD_WAYANAD_IMD",   "type": "PROVEN_BY", "reason": "Orange Alert record — IMD archive"},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "EVD_CHAMOLI_ISRO",  "type": "PROVEN_BY", "reason": "ISRO satellite imagery — glacier rupture"},

        # ── Event → Impact (IMPACTED) ───────────────────────────────────────
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "IMP_DELHI_DISPLACED", "type": "IMPACTED", "reason": "27,000 displaced from Yamuna floodplain"},
        {"from": "Event_EVT_WAYANAD_2024",        "to": "IMP_WAYANAD_DEAD",   "type": "IMPACTED", "reason": "231 confirmed deaths"},
        {"from": "Event_EVT_CHAMOLI_2021",        "to": "IMP_CHAMOLI_DEAD",   "type": "IMPACTED", "reason": "204 killed or missing"},
        {"from": "Event_EVT_CYCLONE_DANA_2024",   "to": "IMP_CYCLONE_EVAC",   "type": "IMPACTED", "reason": "800,000+ evacuated pre-landfall"},

        # ── Cross-domain CONNECTED_TO (gold dashed) ─────────────────────────
        {"from": "Event_EVT_CHAMOLI_2021",       "to": "Event_EVT_JOSHIMATH_2023",    "type": "CONNECTED_TO", "reason": "NTPC Tapovan tunnel boring destabilised same Himalayan ridge — Chamoli triggered Joshimath subsidence"},
        {"from": "Event_EVT_DELHI_FLOODS_2023",  "to": "Event_EVT_WAYANAD_2024",      "type": "CONNECTED_TO", "reason": "Both driven by intensifying monsoon patterns — shared climate root cause"},
        {"from": "Event_EVT_TATA_SEMI_2024",     "to": "Event_EVT_BALAKOT_2019",      "type": "CONNECTED_TO", "reason": "Semiconductor self-sufficiency directly reduces defence electronics import dependency exposed post-Balakot"},
        {"from": "Event_EVT_RUSSIA_UKRAINE_2022","to": "Event_EVT_G20_INDIA_2023",    "type": "CONNECTED_TO", "reason": "Russia-Ukraine war forced India to articulate strategic autonomy — G20 presidency used to cement Global South leadership"},
        {"from": "Event_EVT_COVID_WAVE2_2021",   "to": "Event_EVT_MANIPUR_2023",      "type": "CONNECTED_TO", "reason": "COVID economic disruption deepened ethnic grievances in Manipur — healthcare collapse amplified community tensions"},
    ],
}

# --- Fix 14: Fallback cross-domain connections for the Connections tab --------
_FALLBACK_CROSS_DOMAIN = {
    "connections": [
        {
            "from_name":   "Chamoli Glacier Burst",
            "from_domain": "DOM_CLIMATE",
            "to_name":     "Joshimath Subsidence",
            "to_domain":   "DOM_CLIMATE",
            "reason":      "NTPC Tapovan tunnel boring under the same Himalayan ridge system triggered both events. Chamoli's debris flow damaged surface infrastructure; the same underground excavation destabilised Joshimath's glacial moraine foundation two years later.",
        },
        {
            "from_name":   "Delhi Floods 2023",
            "from_domain": "DOM_CLIMATE",
            "to_name":     "Wayanad Landslide 2024",
            "to_domain":   "DOM_CLIMATE",
            "reason":      "Both driven by record-intensity monsoon rainfall exceeding IMD warning thresholds. Shared root cause: climate-driven precipitation intensification without corresponding upgrade to early-warning and evacuation protocols.",
        },
        {
            "from_name":   "Tata Semiconductor Fab",
            "from_domain": "DOM_TECHNOLOGY",
            "to_name":     "Balakot Strikes",
            "to_domain":   "DOM_DEFENSE",
            "reason":      "Post-Balakot analysis identified India's critical dependency on imported defence electronics (avionics, radar, missiles). The PLI semiconductor programme directly addresses this strategic vulnerability by building domestic chip manufacturing capacity.",
        },
        {
            "from_name":   "Russia-Ukraine War",
            "from_domain": "DOM_GEOPOLITICS",
            "to_name":     "G20 India 2023",
            "to_domain":   "DOM_GEOPOLITICS",
            "reason":      "Russia-Ukraine war forced India to publicly defend strategic autonomy (UN abstentions). G20 presidency was used to translate that posture into diplomatic capital — Delhi Declaration's Global South framing was a direct consequence.",
        },
        {
            "from_name":   "COVID Wave 2",
            "from_domain": "DOM_SOCIETY",
            "to_name":     "Manipur Conflict 2023",
            "to_domain":   "DOM_SOCIETY",
            "reason":      "COVID-19 second wave's economic devastation — job losses, healthcare collapse, tribal community exclusion from PMJAY coverage — deepened pre-existing Kuki-Meitei grievances, accelerating the breakdown that erupted in May 2023.",
        },
    ]
}

# Known source/agency suffixes to strip from labels
_SOURCE_TOKENS = {"pib", "ndma", "isro", "imd", "ndrf", "mha", "moe", "army",
                  "navy", "govt", "press", "rep", "rpt", "doc", "ord"}

# Type prefix → short readable suffix added to label
_TYPE_SUFFIX = {
    "EVD_":      "Evd",
    "Evidence_": "Evd",
    "IMP_":      "Impact",
    "Impact_":   "Impact",
    "ACT_":      "",
    "Actor_":    "",
    "EVT_":      "",
    "Event_":    "",
    "SCH_":      "Scheme",
    "Scheme_":   "Scheme",
    "REG_":      "",
    "Region_":   "",
    "POL_":      "Policy",
    "Policy_":   "Policy",
    "DOM_":      "",
    "Domain_":   "",
}


def _humanize(raw_id: str) -> str:
    """
    Clean readable label from a raw DB node ID.
    EVD_WAYANAD_PIB    → "Wayanad"
    IMP_DANA_NDRF_2024 → "Dana"
    EVT_CHAMOLI_2021   → "Chamoli 2021"
    ACT_NDMA           → "NDMA"
    DOM_CLIMATE        → "Climate"
    """
    # Strip type prefix
    for prefix in _TYPE_SUFFIX:
        if raw_id.startswith(prefix):
            raw_id = raw_id[len(prefix):]
            break

    # Keep tokens that are not source/agency names
    # Preserve known acronyms (all-caps ≤ 5 chars) as-is; title-case others
    parts = []
    for tok in raw_id.split("_"):
        tl = tok.lower()
        if tl in _SOURCE_TOKENS:
            continue
        # Keep short ALL-CAPS tokens as acronyms (e.g. NDMA, IMD, MHA)
        if tok.isupper() and len(tok) <= 5:
            parts.append(tok)
        else:
            parts.append(tok.capitalize())

    label = " ".join(parts).strip()
    return label if label else raw_id


def _humanize_edge(edge_type: str) -> str:
    return edge_type.replace("_", " ").title()


def _get_ego_ids(event_id: str, graph_data: dict) -> set:
    """Return the event node + all directly connected node IDs."""
    ids = {event_id}
    for e in graph_data.get("edges", []):
        if e["from"] == event_id:
            ids.add(e["to"])
        elif e["to"] == event_id:
            ids.add(e["from"])
    return ids


def _build_graph(graph_data: dict, filter_type: set | None = None, focus_ids: set | None = None):
    nodes, edges, seen_ids = [], [], set()

    for n in graph_data.get("nodes", []):
        ntype = n.get("type", "Event")
        if filter_type and ntype not in filter_type:
            continue
        in_focus   = focus_ids is None or n["id"] in focus_ids
        cfg        = NODE_CONFIG.get(ntype, NODE_CONFIG["Event"])
        full_name  = n.get("label") or n["id"]          # full name for tooltip
        short_label = _humanize(full_name)               # short label for canvas

        # Only show canvas labels for important types — hide Impact/Evidence
        canvas_label = short_label if ntype in _LABELLED_TYPES else ""

        color      = cfg["color"] if in_focus else "#2d3f55"
        size       = cfg["size"]  if in_focus else max(cfg["size"] - 4, 5)
        font_color = "#e2e8f0"    if in_focus else "#475569"
        font_size  = 10           if in_focus else 8

        # Rich tooltip: full name + type + description if available
        props       = n.get("props", {})
        tooltip     = f"{ntype}: {full_name}"
        if props.get("description"):
            tooltip += f"\n{props['description'][:120]}"
        elif props.get("type"):
            tooltip += f"\nType: {props['type']}"

        nodes.append(Node(
            id=n["id"],
            label=canvas_label,
            size=size,
            color=color,
            title=tooltip,
            shape=cfg["shape"],
            font={"color": font_color, "size": font_size, "strokeWidth": 1, "strokeColor": "#020b14"},
        ))
        seen_ids.add(n["id"])

    for e in graph_data.get("edges", []):
        if e["from"] not in seen_ids or e["to"] not in seen_ids:
            continue
        etype    = e.get("type", "")
        in_focus = focus_ids is None or (e["from"] in focus_ids and e["to"] in focus_ids)
        if in_focus:
            color                = EDGE_COLORS.get(etype, "#475569")
            width, dashes, arrow = EDGE_STYLE.get(etype, (1.5, False, True))
        else:
            color, width, dashes, arrow = "#2d3f55", 0.5, False, False
        hover = _humanize_edge(etype)
        if e.get("reason"):
            hover += f": {e['reason']}"
        edges.append(Edge(
            source=e["from"], target=e["to"],
            color=color, width=width,
            dashes=dashes,
            arrows="to" if arrow else "",
            title=hover,
        ))

    return nodes, edges


_TREND_ICON = {
    "rising": "↑", "falling": "↓", "stable": "→",
    "volatile_high": "⚡", "critically_low": "🔴", "depreciating": "↓",
    "extreme": "⚡", "evacuation_ongoing": "🚁", "negative": "↓", "high": "⚠️",
}
_TREND_COLOR = {
    "rising": "#ef4444", "falling": "#22c55e", "stable": "#94a3b8",
    "volatile_high": "#f97316", "critically_low": "#ef4444", "depreciating": "#ef4444",
    "extreme": "#ef4444", "evacuation_ongoing": "#f97316", "negative": "#ef4444", "high": "#f97316",
}
_SEVERITY_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15", "low": "#22c55e"}
_CAT_ICON = {"military": "🪖", "diplomatic": "🤝", "economic": "📈",
             "policy": "📋", "humanitarian": "🏥"}
_STATUS_COLOR = {"executed": "#22c55e", "active": "#38bdf8", "pending": "#facc15", "cancelled": "#ef4444", "ongoing": "#38bdf8"}
_SCENARIO_COLOR = {"Best Case": "#22c55e", "Base Case": "#f97316", "Worst Case": "#ef4444"}


def _crisis_timeline_chart(subevents: list) -> None:
    """Plotly horizontal timeline — each sub-event as a dot on a date axis."""
    import plotly.graph_objects as go
    from datetime import datetime, timedelta

    _CAT_COLOR_HEX = {
        "military":    "#ef4444",
        "diplomatic":  "#38bdf8",
        "economic":    "#22c55e",
        "policy":      "#facc15",
        "humanitarian":"#a78bfa",
    }
    _SEV_SIZE = {"critical": 18, "high": 14, "medium": 10, "low": 7}

    # Build per-category traces so legend works
    by_cat: dict = {}
    for se in subevents:
        cat = se.get("category", "other")
        by_cat.setdefault(cat, []).append(se)

    fig = go.Figure()
    for cat, events in by_cat.items():
        color = _CAT_COLOR_HEX.get(cat, "#94a3b8")
        dates, days, names, hovers, sizes = [], [], [], [], []
        for se in events:
            d = se.get("date", "")
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
            except Exception:
                continue
            dates.append(dt)
            days.append(f"Day {se.get('day_number','?')}")
            names.append(se.get("name",""))
            impact = se.get("india_impact","")
            hovers.append(
                f"<b>{se.get('name','')}</b><br>"
                f"Day {se.get('day_number','?')} · {d}<br>"
                f"<i>{se.get('description','')[:120]}…</i>"
                + (f"<br><span style='color:#f97316'>🇮🇳 {impact}</span>" if impact else "")
            )
            sizes.append(_SEV_SIZE.get(se.get("severity","medium"), 10))

        fig.add_trace(go.Scatter(
            x=dates, y=[cat] * len(dates),
            mode="markers+text",
            marker=dict(color=color, size=sizes, line=dict(color="#020b14", width=2),
                        symbol="circle"),
            text=days, textposition="top center",
            textfont=dict(color=color, size=9),
            name=cat.title(),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
        ))

    # Connector lines per category
    for cat, events in by_cat.items():
        color = _CAT_COLOR_HEX.get(cat, "#94a3b8")
        dates = []
        for se in sorted(events, key=lambda x: x.get("day_number", 0)):
            d = se.get("date","")
            try:
                dates.append(datetime.strptime(d, "%Y-%m-%d"))
            except Exception:
                pass
        if len(dates) > 1:
            fig.add_trace(go.Scatter(
                x=dates, y=[cat]*len(dates),
                mode="lines",
                line=dict(color=color, width=1, dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))

    fig.update_layout(
        height=280,
        paper_bgcolor="#020b14", plot_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif", size=10),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            showgrid=True, gridcolor="#0f1e35", gridwidth=1,
            tickfont=dict(size=9, color="#475569"),
            tickformat="%b %d",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color="#94a3b8"),
            categoryorder="array",
            categoryarray=["humanitarian","policy","economic","diplomatic","military"],
        ),
        legend=dict(
            orientation="h", x=0, y=-0.18,
            font=dict(size=9, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#0d1f35", bordercolor="#1e3a5f",
            font=dict(color="#e2e8f0", size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _crisis_radar_chart(indicators: list) -> None:
    """Plotly radar chart — India's multi-domain exposure to the crisis."""
    import plotly.graph_objects as go

    # Map indicator_ids to radar axes with normalized 0-100 threat scores
    _IND_TO_AXIS = {
        "IND_BRENT_CRUDE":     ("Oil Price",     lambda v: min(100, max(0, (v - 70) / 80 * 100))),
        "IND_INR_USD":         ("Currency",      lambda v: min(100, max(0, (v - 82) / 15 * 100))),
        "IND_HORMUZ_TRAFFIC":  ("Trade Routes",  lambda v: min(100, max(0, (1 - v/25) * 100))),
        "IND_INDIA_SPR_DAYS":  ("Energy Buffer", lambda v: min(100, max(0, (1 - v/30) * 100))),
        "IND_INDIA_OIL_IMPORT":("Supply Risk",   lambda v: min(100, max(0, v))),
        "IND_NIFTY_DROP":      ("Markets",       lambda v: min(100, max(0, abs(v) / 20 * 100))),
        "IND_INDIA_NATIONALS": ("Nationals",     lambda v: min(100, max(0, v / 200000 * 100))),
        "IND_FREIGHT_RATE":    ("Freight",       lambda v: min(100, max(0, v / 500 * 100))),
    }

    axes, scores = [], []
    for ind in indicators:
        iid = ind.get("indicator_id","")
        val = float(ind.get("value", 0))
        if iid in _IND_TO_AXIS:
            label, fn = _IND_TO_AXIS[iid]
            axes.append(label)
            scores.append(round(fn(val), 1))

    if len(axes) < 3:
        return

    # Close the polygon
    axes_closed   = axes + [axes[0]]
    scores_closed = scores + [scores[0]]

    # Color based on avg threat
    avg = sum(scores) / len(scores)
    fill_color = "rgba(239,68,68,0.25)"   if avg > 65 else \
                 "rgba(249,115,22,0.25)"  if avg > 40 else \
                 "rgba(34,197,94,0.25)"

    line_color = "#ef4444" if avg > 65 else "#f97316" if avg > 40 else "#22c55e"

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed, theta=axes_closed,
        fill="toself", fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        marker=dict(color=line_color, size=6),
        hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
        name="Threat Level",
    ))
    # Reference rings at 25, 50, 75
    for ring, rc in [(25,"#0f1e35"),(50,"#162236"),(75,"#1e2e42")]:
        fig.add_trace(go.Scatterpolar(
            r=[ring]*len(axes_closed), theta=axes_closed,
            mode="lines", line=dict(color=rc, width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))

    fig.update_layout(
        height=300,
        paper_bgcolor="#020b14", plot_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif", size=10),
        margin=dict(l=20, r=20, t=20, b=20),
        polar=dict(
            bgcolor="#020b14",
            radialaxis=dict(
                visible=True, range=[0,100],
                tickfont=dict(size=8, color="#334155"),
                gridcolor="#0f1e35", linecolor="#0f1e35",
                tickvals=[25,50,75,100],
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color="#94a3b8"),
                linecolor="#1e293b", gridcolor="#0f1e35",
            ),
        ),
        showlegend=False,
        hoverlabel=dict(bgcolor="#0d1f35", bordercolor="#1e3a5f",
                        font=dict(color="#e2e8f0", size=11)),
    )

    # Threat level label
    threat_label = "CRITICAL" if avg > 65 else "HIGH" if avg > 40 else "MODERATE"
    st.markdown(
        f'<div style="text-align:center;font-size:9px;font-weight:700;color:{line_color};'
        f'letter-spacing:.1em;margin-bottom:2px;">INDIA EXPOSURE — {threat_label} ({avg:.0f}/100)</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _crisis_scenario_chart(scenarios: list) -> None:
    """Plotly donut arc showing scenario probability split."""
    import plotly.graph_objects as go

    if not scenarios:
        return

    labels = [f"{s.get('label','?')}<br>{s.get('name','')}" for s in scenarios]
    values = [s.get("probability", 0.33) for s in scenarios]
    colors = [_SCENARIO_COLOR.get(s.get("label",""), "#94a3b8") for s in scenarios]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.62,
        marker=dict(colors=colors,
                    line=dict(color="#020b14", width=3)),
        textfont=dict(size=10, color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>Probability: %{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    ))

    # Centre annotation
    fig.update_layout(
        height=260,
        paper_bgcolor="#020b14", plot_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif"),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(
            orientation="v", x=1.02, y=0.5,
            font=dict(size=9, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)",
        ),
        annotations=[dict(
            text=f"<b>{len(scenarios)}</b><br><span style='font-size:10px'>Scenarios</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#e2e8f0"),
        )],
        hoverlabel=dict(bgcolor="#0d1f35", bordercolor="#1e3a5f",
                        font=dict(color="#e2e8f0", size=11)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_crisis_dashboard(event_id: str):
    """Render the full crisis intelligence panel for an ongoing event."""
    API_BASE = os.environ.get("PRAMAAN_API_URL", "http://localhost:8000")
    import requests as _req

    st.markdown(
        '<div style="font-size:0.7em;color:#ef4444;text-transform:uppercase;letter-spacing:0.1em;'
        'font-weight:700;margin:16px 0 8px 0;border-top:1px solid #ef444422;padding-top:14px;">'
        '🔴 LIVE CRISIS INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )

    # Fetch crisis data
    try:
        resp = _req.get(f"{API_BASE}/crisis/{event_id}", timeout=8)
        data = resp.json() if resp.status_code == 200 else {}
    except Exception:
        data = {}

    if not data:
        st.markdown('<div style="color:#475569;font-size:11px;">Crisis data unavailable.</div>',
                    unsafe_allow_html=True)
        return

    event      = data.get("event", {})
    subevents  = data.get("subevents", [])
    indicators = data.get("indicators", [])
    decisions  = data.get("decisions", [])

    # ── Event header ──────────────────────────────────────────────────────────
    ev_sev   = event.get("severity", "high")
    ev_color = _SEVERITY_COLOR.get(ev_sev, "#f97316")
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a0000,#0d0f1e);'
        f'border:1px solid {ev_color}55;border-left:4px solid {ev_color};'
        f'border-radius:10px;padding:12px 14px;margin-bottom:10px;">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
        f'<span style="background:{ev_color}22;color:{ev_color};font-size:9px;font-weight:700;'
        f'padding:2px 7px;border-radius:4px;text-transform:uppercase;">ACTIVE CRISIS</span>'
        f'<span style="font-size:9px;color:#475569;">Day {len(subevents)} · {event.get("date","")}</span>'
        f'</div>'
        f'<div style="font-size:13px;font-weight:700;color:#f1f5f9;">{event.get("name","")}</div>'
        f'<div style="font-size:10px;color:#94a3b8;margin-top:4px;line-height:1.5;">'
        f'{event.get("description","")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_timeline, tab_exposure, tab_decisions, tab_scenarios = st.tabs(
        ["📅  Timeline", "🎯  India Exposure", "🇮🇳  Decisions", "🔭  Scenarios"]
    )

    # ── Tab 1: Crisis Timeline chart ──────────────────────────────────────────
    with tab_timeline:
        if not subevents:
            st.markdown('<div style="font-size:11px;color:#475569;">No sub-events yet.</div>',
                        unsafe_allow_html=True)
        else:
            _crisis_timeline_chart(subevents)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            # Detail cards below chart — latest first
            for se in reversed(subevents):
                sev    = se.get("severity", "medium")
                scolor = _SEVERITY_COLOR.get(sev, "#94a3b8")
                cat    = se.get("category", "")
                cicon  = _CAT_ICON.get(cat, "📌")
                impact = se.get("india_impact", "")
                st.markdown(
                    f'<div style="border-left:3px solid {scolor}55;padding:5px 8px 5px 10px;'
                    f'margin-bottom:4px;background:#060f1e;border-radius:0 6px 6px 0;">'
                    f'<div style="display:flex;align-items:center;gap:6px;">'
                    f'<span style="font-size:9px;color:#334155;min-width:38px;">Day {se.get("day_number","?")}</span>'
                    f'<span style="font-size:9px;color:{scolor};font-weight:700;">{cicon} {cat}</span>'
                    f'<span style="font-size:10px;font-weight:600;color:#cbd5e1;">{se.get("name","")}</span>'
                    f'</div>'
                    + (f'<div style="font-size:9px;color:#f97316;margin-top:2px;padding-left:44px;">🇮🇳 {impact}</div>' if impact else "")
                    + f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 2: India Exposure Radar ───────────────────────────────────────────
    with tab_exposure:
        if not indicators:
            st.markdown('<div style="font-size:11px;color:#475569;">No indicators yet.</div>',
                        unsafe_allow_html=True)
        else:
            _crisis_radar_chart(indicators)
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            # Compact metric rows below radar
            for ind in indicators:
                trend  = ind.get("trend", "stable")
                tcolor = _TREND_COLOR.get(trend, "#94a3b8")
                ticon  = _TREND_ICON.get(trend, "→")
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:4px 8px;border-bottom:1px solid #0f1e35;">'
                    f'<span style="font-size:10px;color:#64748b;">{ind.get("name","")}</span>'
                    f'<span style="font-size:11px;font-weight:700;color:#e2e8f0;">'
                    f'{ind.get("value","")} <span style="font-size:9px;color:#334155;">{ind.get("unit","")}</span></span>'
                    f'<span style="font-size:10px;color:{tcolor};">{ticon}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 3: India Decisions ────────────────────────────────────────────────
    with tab_decisions:
        if not decisions:
            st.markdown('<div style="font-size:11px;color:#475569;">No India decisions recorded yet.</div>',
                        unsafe_allow_html=True)
        else:
            for dec in decisions:
                status = dec.get("status", "")
                sc     = _STATUS_COLOR.get(status, "#94a3b8")
                actor  = dec.get("actor_name") or dec.get("decided_by", "")
                st.markdown(
                    f'<div style="background:#060f1e;border:1px solid #1e293b;'
                    f'border-radius:8px;padding:8px 12px;margin-bottom:6px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<span style="font-size:11px;font-weight:600;color:#e2e8f0;">{dec.get("name","")}</span>'
                    f'<span style="background:{sc}22;color:{sc};font-size:9px;font-weight:700;'
                    f'padding:2px 6px;border-radius:4px;text-transform:uppercase;">{status}</span>'
                    f'</div>'
                    f'<div style="font-size:9px;color:#475569;margin-top:2px;">'
                    f'{actor} · {dec.get("date","")}</div>'
                    f'<div style="font-size:10px;color:#64748b;margin-top:4px;line-height:1.4;">'
                    f'{dec.get("description","")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 4: Scenarios ──────────────────────────────────────────────────────
    with tab_scenarios:
        st.markdown(
            '<div style="font-size:10px;color:#64748b;margin-bottom:8px;">'
            'AI scenario analysis — probabilities and India action plans for next 60 days.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Generate / Refresh Scenarios", key=f"gen_scn_{event_id}", type="primary"):
            with st.spinner("Generating scenarios via AI..."):
                try:
                    scn_resp = _req.post(f"{API_BASE}/crisis/{event_id}/scenarios", timeout=60)
                    if scn_resp.status_code == 200:
                        st.session_state[f"scenarios_{event_id}"] = scn_resp.json().get("scenarios", [])
                    else:
                        st.error(f"Scenario generation failed: {scn_resp.status_code}")
                except Exception as ex:
                    st.error(f"Error: {ex}")

        scenarios = st.session_state.get(f"scenarios_{event_id}", [])
        if scenarios:
            _crisis_scenario_chart(scenarios)

        for scn in scenarios:
            label   = scn.get("label", "")
            sc      = _SCENARIO_COLOR.get(label, "#94a3b8")
            impact  = scn.get("india_impact", {})
            actions = scn.get("india_actions", [])
            signals = scn.get("warning_signals", [])
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid {sc}33;border-left:3px solid {sc};'
                f'border-radius:8px;padding:8px 12px;margin-bottom:6px;">'
                f'<div style="font-size:11px;font-weight:700;color:{sc};margin-bottom:3px;">'
                f'{scn.get("name","")}</div>'
                f'<div style="font-size:9px;color:#475569;margin-bottom:5px;">'
                f'⏱ {scn.get("timeline","")} · {scn.get("trigger","")}</div>'
                + "".join(
                    f'<div style="font-size:10px;color:#64748b;margin-bottom:1px;">'
                    f'<span style="color:#334155">{k.replace("_"," ").title()}:</span> {v}</div>'
                    for k, v in (impact.items() if isinstance(impact, dict) else {}.items())
                )
                + (
                    '<div style="margin-top:6px;padding:5px 8px;background:#0a1628;border-radius:5px;">'
                    '<div style="font-size:9px;color:#475569;font-weight:700;margin-bottom:3px;">INDIA ACTIONS</div>'
                    + "".join(f'<div style="font-size:10px;color:#e2e8f0;margin-bottom:2px;">• {a}</div>' for a in actions)
                    + '</div>' if actions else ""
                )
                + (
                    '<div style="margin-top:4px;">'
                    + "".join(f'<div style="font-size:9px;color:#f97316;">⚠ {s}</div>' for s in signals)
                    + '</div>' if signals else ""
                )
                + '</div>',
                unsafe_allow_html=True,
            )


def page():
    st.set_page_config(page_title="Ontology Graph – PRAMAAN", layout="wide")
    render_topnav(active_page="Ontology Graph")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(167,139,250,0.7), 0 0 30px rgba(167,139,250,0.4), 0 0 50px rgba(167,139,250,0.2); }
        50%       { text-shadow: 0 0 25px rgba(167,139,250,1), 0 0 60px rgba(167,139,250,0.8), 0 0 100px rgba(167,139,250,0.5); }
    }
    iframe { background-color: #f8fafc !important; }
    /* Style tabs to match brand */
    button[data-baseweb="tab"] { font-size: 11px !important; padding: 6px 12px !important; }
    div[data-baseweb="select"] * { font-size: 12px !important; }
    div[data-testid="stToggle"] label p { font-size: 10px !important; }
    /* Compact node-type checkboxes */
    div[data-testid="stCheckbox"] { margin-bottom: 0 !important; padding-bottom: 0 !important; }
    div[data-testid="stCheckbox"] label { min-height: 0 !important; padding: 2px 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCheckbox"]) { gap: 2px !important; margin-bottom: 2px !important; }
    div[data-testid="stCheckbox"] label p { font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

    if "graph_clicked" not in st.session_state:
        st.session_state.graph_clicked = None
    if "ontology_sel" not in st.session_state:
        st.session_state.ontology_sel = None    # bare event_id or None = All Events
    if "active_types" not in st.session_state:
        st.session_state.active_types = set(NODE_CONFIG.keys())

    # Deep-link from Intelligence Map — auto-focus the passed event
    if "deep_link_event" in st.session_state:
        raw = st.session_state.pop("deep_link_event")
        # raw may be "Event_EVT_..." or bare "EVT_..." — normalise to bare id
        bare = raw[len("Event_"):] if raw.startswith("Event_") else raw
        st.session_state.ontology_sel = bare
        st.session_state.pop("focus_select", None)

    header_slot = st.empty()

    st.markdown(
        '<div style="font-size:12px;color:#475569;margin-bottom:4px;margin-top:2px;">'
        'Interactive knowledge graph — how events, actors, schemes and evidence connect '
        'across 7 domains. Click any node to explore. Scroll to zoom · Drag to pan.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Fetch (cached in session so node clicks don't trigger a reload) ────────
    if "graph_data_cache" not in st.session_state:
        with st.spinner("Loading ontology graph..."):
            graph_data = safe_get("/ontology/graph", timeout=20, silent=True)
        st.session_state.graph_data_cache = graph_data or _FALLBACK_GRAPH
    graph_data = st.session_state.graph_data_cache

    stats       = graph_data.get("stats", {})
    total_nodes = stats.get("total_nodes", len(graph_data.get("nodes", [])))
    total_edges = stats.get("total_edges", len(graph_data.get("edges", [])))
    domains     = len(set(n.get("domain", "") for n in graph_data.get("nodes", []) if n.get("domain"))) or 7
    cross_count = sum(1 for e in graph_data.get("edges", []) if e.get("type") == "CONNECTED_TO")

    header_slot.markdown(f"""
    <div style="position:sticky;top:52px;z-index:100;background:#020b14;
                padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:6px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#a78bfa;font-family:'Cinzel',serif;
                   letter-spacing:0.08em;white-space:nowrap;animation:glowPulse 2.5s ease-in-out infinite;">
        ONTOLOGY GRAPH
      </span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        {total_nodes} Entities &nbsp;·&nbsp; {total_edges} Relationships &nbsp;·&nbsp;
        {domains} Domains &nbsp;·&nbsp; {cross_count} Cross-Domain Links
        &nbsp;·&nbsp; <span style="color:#475569;">Neo4j · PIB · NDMA · ISRO</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Top control row: event focus + refresh + reset ───────────────────────
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        font-size:10px !important; padding:2px 10px !important;
        height:28px !important; min-height:0 !important;
    }
    </style>""", unsafe_allow_html=True)

    ecol, r1col, r2col = st.columns([4, 0.4, 0.4], gap="small")
    with ecol:
        render_event_dropdown("ontology_sel", "focus_select", include_all=True)

    # Derive the Neo4j node ID used for ego-graph highlighting
    _oid = st.session_state.get("ontology_sel")
    focus_event = f"Event_{_oid}" if _oid else None

    with r1col:
        if st.button("↺", use_container_width=True, help="Refresh graph"):
            st.session_state.pop("graph_data_cache", None)
            st.rerun()
    with r2col:
        if focus_event:
            if st.button("✕", use_container_width=True, help="Reset focus"):
                st.session_state.ontology_sel = None
                st.session_state.pop("focus_select", None)
                st.rerun()

    active_filter = st.session_state.active_types or set(NODE_CONFIG.keys())
    focus_ids = _get_ego_ids(focus_event, graph_data) if focus_event else None

    # ── 3-column layout ───────────────────────────────────────────────────────
    col_left, col_graph, col_detail = st.columns([0.55, 3.2, 1], gap="small")

    # ══ LEFT — tabbed panel ═══════════════════════════════════════════════════
    with col_left:

        # ── Node type filter checkboxes ───────────────────────────────────────
        all_type_counts = {}
        for n in graph_data.get("nodes", []):
            t = n.get("type", "Event")
            all_type_counts[t] = all_type_counts.get(t, 0) + 1

        sel_type = None
        if st.session_state.graph_clicked:
            nd = next((n for n in graph_data.get("nodes", [])
                       if n["id"] == st.session_state.graph_clicked), None)
            if nd:
                sel_type = nd.get("type")

        for ntype, cfg in NODE_CONFIG.items():
            count    = all_type_counts.get(ntype, 0)
            is_on    = ntype in st.session_state.active_types
            color    = cfg["color"] if is_on else "#334155"
            bg       = "#1a2035" if ntype == sel_type else ("#0d1117" if is_on else "#080d14")
            border_c = f'{cfg["color"]}99' if is_on else "#1e293b"

            chk_col, lbl_col = st.columns([1, 5], gap="small")
            with chk_col:
                val = st.checkbox("", value=is_on, key=f"chk_{ntype}",
                                  label_visibility="collapsed")
            with lbl_col:
                st.markdown(
                    f'<div style="border-left:3px solid {border_c};background:{bg};'
                    f'border-radius:4px;padding:4px 8px;margin-bottom:0;">'
                    f'<span style="font-size:11px;font-weight:600;color:{color};">{ntype}</span>'
                    f'<span style="font-size:10px;color:#334155;float:right;">{count}</span>'
                    f'<div style="font-size:9px;color:#334155;margin-top:1px;">{cfg["desc"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if val != is_on:
                if val:
                    st.session_state.active_types.add(ntype)
                else:
                    st.session_state.active_types.discard(ntype)
                st.rerun()

    # ══ RIGHT — full graph ════════════════════════════════════════════════════
    with col_graph:
        # Focus mode banner
        if focus_ids:
            _focus_tuple   = EVENTS_BY_ID.get(st.session_state.get("ontology_sel"))
            focused_name   = _focus_tuple[1] if _focus_tuple else st.session_state.get("ontology_sel", "")
            neighbor_count = len(focus_ids) - 1
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #f97316;border-left:4px solid #f97316;'
                f'border-radius:8px;padding:7px 12px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">'
                f'<span style="font-size:11px;font-weight:700;color:#f97316;">Focus Mode</span>'
                f'<span style="font-size:11px;color:#94a3b8;">{focused_name}</span>'
                f'<span style="font-size:10px;color:#475569;margin-left:4px;">· {neighbor_count} connected nodes</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        nodes, edges = _build_graph(graph_data, filter_type=active_filter, focus_ids=focus_ids)


        config = Config(
            width="100%",
            height=650,
            directed=True,
            physics=True,
            solver="barnesHut",
            minVelocity=5,
            hierarchical=False,
            node={"labelProperty": "label"},
            edge={"labelProperty": "title", "smooth": {"type": "continuous"}},
            interaction={
                "hover": True,
                "tooltipDelay": 100,
                "navigationButtons": False,
                "keyboard": True,
                "zoomView": True,
                "zoomSpeed": 1,
                "minZoom": 0.4,
                "maxZoom": 2.5,
                "dragView": True,
                "selectConnectedEdges": True,
                "multiselect": False,
                "hideEdgesOnDrag": True,
            },
            manipulation=False,
        )
        # barnesHut params must be nested under physics["barnesHut"] —
        # passing them as kwargs puts them at the top level which vis-network ignores
        config.physics["barnesHut"] = {
            "gravitationalConstant": -8000,   # strong repulsion — pushes nodes apart
            "centralGravity":        0.05,    # very weak centre pull — allows distribution
            "springLength":          160,     # longer edges — connected nodes have breathing room
            "springConstant":        0.03,    # soft springs — don't over-cluster connected nodes
            "damping":               0.9,     # high damping — settles fast, no wiggle
            "avoidOverlap":          0.8,
        }
        config.physics["stabilization"] = {
            "enabled":    True,
            "iterations": 300,
            "fit":        True,
        }

        clicked = agraph(nodes=nodes, edges=edges, config=config)

        if clicked:
            st.session_state.graph_clicked = clicked
            # Auto-focus when an Event node is clicked
            clicked_node = next((n for n in graph_data.get("nodes", []) if n["id"] == clicked), None)
            if clicked_node and clicked_node.get("type") == "Event":
                # clicked is "Event_EVT_..." — strip prefix to get bare event_id
                bare = clicked[len("Event_"):] if clicked.startswith("Event_") else clicked
                if st.session_state.get("ontology_sel") != bare:
                    st.session_state.ontology_sel = bare
                    # Clear selectbox cache so it reflects new focus on rerun
                    st.session_state.pop("focus_select", None)
                    st.rerun()

    # ══ RIGHT — node detail panel ══════════════════════════════════════════════
    with col_detail:
        st.markdown(
            "<div style='font-size:0.7em;color:#475569;text-transform:uppercase;"
            "letter-spacing:0.1em;font-weight:700;margin-bottom:8px;'>NODE DETAIL</div>",
            unsafe_allow_html=True,
        )

        sel_node_id = st.session_state.graph_clicked
        if not sel_node_id:
            st.markdown(
                '<div style="background:#0a1628;border:1px dashed #1e293b;border-radius:10px;'
                'padding:24px 14px;text-align:center;margin-top:8px;">'
                '<div style="font-size:18px;margin-bottom:8px;">🔍</div>'
                '<div style="font-size:11px;color:#334155;line-height:1.6;">'
                'Click any node on the graph to explore its details</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            nd = next((n for n in graph_data.get("nodes", []) if n["id"] == sel_node_id), None)
            if nd:
                ntype  = nd.get("type", "Event")
                color  = NODE_CONFIG.get(ntype, {}).get("color", "#f97316")
                nlabel = _humanize(nd.get("label") or sel_node_id)
                props  = nd.get("props", {})

                # Clean field name mapping
                FIELD_LABELS = {
                    "description": "Description",
                    "date":        "Date",
                    "severity":    "Severity",
                    "value":       "Value",
                    "unit":        "Unit",
                    "source":      "Source",
                    "url":         "Source URL",
                    "budget_inr_cr": "Budget (₹ Cr)",
                    "role":        "Role",
                    "type":        "Sub-type",
                    "title":       "Title",
                }
                # Fields to skip (raw IDs, redundant keys)
                SKIP_FIELDS = {"name", "impact_id", "event_id", "actor_id",
                               "scheme_id", "evidence_id", "region_id", "policy_id"}

                # Type badge + name
                st.markdown(
                    f'<div style="background:#0a1628;border:1px solid {color}44;'
                    f'border-left:4px solid {color};border-radius:10px;padding:12px 14px;'
                    f'overflow:hidden;word-break:break-word;">'
                    f'<span style="background:{color}22;color:{color};font-size:9.5px;font-weight:700;'
                    f'padding:2px 7px;border-radius:4px;border:1px solid {color}44;'
                    f'text-transform:uppercase;letter-spacing:0.05em;">{ntype}</span>'
                    f'<div style="font-size:13px;font-weight:700;color:{color};margin-top:8px;'
                    f'line-height:1.3;overflow-wrap:break-word;">{nlabel}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Clean property rows
                rows_html = ""
                for k, v in props.items():
                    if not v or k in SKIP_FIELDS:
                        continue
                    label = FIELD_LABELS.get(k, k.replace("_", " ").title())
                    display_v = str(v).replace("_", " ").title() if isinstance(v, str) else str(v)
                    if k == "url":
                        display_v = f'<a href="{v}" target="_blank" style="color:{color};font-size:10px;">View source →</a>'
                    rows_html += (
                        f'<div style="display:flex;gap:8px;padding:6px 0;'
                        f'border-bottom:1px solid #0f1e35;">'
                        f'<span style="font-size:10px;color:#475569;min-width:72px;max-width:72px;'
                        f'flex-shrink:0;overflow:hidden;">{label}</span>'
                        f'<span style="font-size:10px;color:#94a3b8;line-height:1.4;'
                        f'overflow-wrap:break-word;word-break:break-word;min-width:0;">{display_v}</span>'
                        f'</div>'
                    )

                if rows_html:
                    st.markdown(
                        f'<div style="background:#060f1e;border:1px solid #1e293b;border-radius:8px;'
                        f'padding:8px 12px;margin-top:6px;overflow:hidden;">{rows_html}</div>',
                        unsafe_allow_html=True,
                    )

                # Live Feed button — only for Event nodes
                if ntype == "Event":
                    bare_id = sel_node_id.replace("Event_", "", 1)
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <style>
                    button[kind="primary"] {{
                        background: linear-gradient(135deg, {color}, {color}cc) !important;
                        border: none !important;
                        color: #fff !important;
                        font-family: Outfit, sans-serif !important;
                        font-weight: 700 !important;
                        font-size: 0.82em !important;
                        letter-spacing: 0.03em !important;
                        border-radius: 10px !important;
                        box-shadow: 0 4px 16px {color}55 !important;
                    }}
                    button[kind="primary"]:hover {{
                        box-shadow: 0 6px 24px {color}88 !important;
                        opacity: 0.92 !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    if st.button("View in Scheme Delivery  →", key=f"goto_feed_{sel_node_id}",
                                 use_container_width=True, type="primary"):
                        st.session_state["deep_link_feed"] = bare_id
                        st.switch_page("pages/scheme_delivery.py")

        # ── AI Insights ──────────────────────────────────────────────────────
        _ai_event_id = st.session_state.get("ontology_sel")
        if _ai_event_id and _GROQ_OK:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
                'letter-spacing:.08em;margin-bottom:6px;">AI INSIGHTS</div>',
                unsafe_allow_html=True,
            )
            if st.button("Generate Brief →", key=f"btn_ai_brief_{_ai_event_id}",
                         use_container_width=True, type="primary"):
                _ev_detail = safe_get(f"/ontology/events/{_ai_event_id}") or {}
                _ev        = _ev_detail.get("event", {})
                _actors    = _ev_detail.get("actors", [])
                _schemes   = _ev_detail.get("schemes", [])
                _connected = _ev_detail.get("connected_events", [])
                _impacts   = _ev_detail.get("impacts", [])
                _evidence  = _ev_detail.get("evidence", [])
                _ctx = (
                    f"Event: {_ev.get('name','')} | Date: {_ev.get('date','')} | "
                    f"Severity: {_ev.get('severity','')} | Domain: {_ev.get('domain','')}\n"
                    f"Description: {_ev.get('description','')}\n\n"
                    + (f"Actors: {', '.join(a.get('name','') for a in _actors)}\n" if _actors else "")
                    + (f"Schemes triggered: {', '.join(s.get('name','') for s in _schemes)}\n" if _schemes else "")
                    + (f"Impacts: {'; '.join(i.get('name','') + ' (' + i.get('severity','') + ')' for i in _impacts)}\n" if _impacts else "")
                    + (f"Connected events: {', '.join(c.get('name','') for c in _connected)}\n" if _connected else "")
                    + (f"Evidence sources: {', '.join(e.get('title', e.get('source','')) for e in _evidence[:3])}\n" if _evidence else "")
                )
                _ev_name = _ev.get("name", _ai_event_id)
                with st.spinner("Generating insights..."):
                    try:
                        stream = _generate_insights(_ai_event_id, _ev_name, _ctx)
                        out = ""
                        for token in stream:
                            out += token
                        st.session_state[f"ai_brief_{_ai_event_id}"] = out
                    except Exception as ex:
                        st.error(f"Ollama error: {ex}")

            _brief = st.session_state.get(f"ai_brief_{_ai_event_id}", "")
            if _brief:
                import markdown as _md
                _html_body = _md.markdown(_brief, extensions=["nl2br"])
                st.markdown(
                    f'<div style="background:#060f1e;border:1px solid #1e293b;'
                    f'border-radius:8px;padding:10px 14px;margin-top:6px;'
                    f'max-height:340px;overflow-y:auto;">'
                    f'<div style="font-size:10px;line-height:1.6;color:#94a3b8;'
                    f'font-family:\'Inter\',sans-serif;">'
                    f'{_html_body}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        # ── Crisis Monitor CTA (inside right panel) ──────────────────────────
        _ONGOING_CRISIS_IDS = {
            "EVT_IRAN_WAR_2026", "EVT_IRAN_CEASEFIRE_TALKS_2026",
            "EVT_HORMUZ_BLOCKADE_2026", "EVT_INDIA_PAK_DIPLO_CRISIS_2025",
            "EVT_INDUS_WATERS_CRISIS_2025",
        }
        _crisis_event_id = st.session_state.get("ontology_sel")
        if _crisis_event_id in _ONGOING_CRISIS_IDS:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown(
                '<div style="display:flex;align-items:center;gap:6px;'
                'background:#1a000088;border:1px solid #ef444433;border-radius:8px;'
                'padding:7px 10px;margin-bottom:6px;">'
                '<span style="font-size:11px;">🔴</span>'
                '<span style="font-size:10px;font-weight:700;color:#ef4444;'
                'letter-spacing:.06em;text-transform:uppercase;">Active Crisis</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Open Crisis Tracker →", key=f"crisis_cta_{_crisis_event_id}",
                         use_container_width=True, type="primary"):
                st.session_state["crisis_sel"] = _crisis_event_id
                st.switch_page("pages/crisis_tracker.py")

        # ══ DECISION ENGINE PANEL (Event-Aware Fix 13) ══════════════════════════
        _sel = st.session_state.get("ontology_sel")
        _panel = _DECISION_PANELS.get(_sel)

        if _panel:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a0a00,#0d1628);
            border:2px solid {_panel['color']}88;border-radius:14px;padding:16px 20px;margin:12px 0">
              <div style="font-size:10px;font-weight:700;color:{_panel['color']};
              letter-spacing:.1em;margin-bottom:10px">⚡ DECISION ENGINE — ACTION REQUIRED</div>
              <div style="font-size:12px;font-weight:700;color:#e2e8f0">{_panel['scheme']}</div>
              <div style="font-size:11px;color:#94a3b8;margin:4px 0">{_panel['allocated']} · {_panel['status']}</div>
              <div style="background:{_panel['color']}22;border:1px solid {_panel['color']}66;
              border-radius:8px;padding:8px 12px;margin-top:10px">
                <div style="font-size:9px;font-weight:700;color:{_panel['color']}">RECOMMENDED ACTION</div>
                <div style="font-size:12px;font-weight:700;color:#e2e8f0;margin:3px 0">🔍 {_panel['action']}</div>
                <div style="font-size:9px;color:#94a3b8">{_panel['detail']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)








page()
