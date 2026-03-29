"""
crisis_tracker.py — PRAMAAN Crisis Tracker

Dedicated full-width dashboard for ongoing crisis events.
Shows: live timeline · India exposure radar · scenario analysis · decisions
Only events marked as ongoing appear in the sidebar.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests as _req
import plotly.graph_objects as go
from datetime import datetime
from components.topnav import render_topnav

API_BASE = os.environ.get("PRAMAAN_API_URL", "http://localhost:8000")

# ── Active crisis registry ────────────────────────────────────────────────────
ACTIVE_CRISES = [
    {"event_id": "EVT_IRAN_WAR_2026",             "name": "Iran-US-Israel War",               "severity": "critical", "domain": "Geopolitics · Defense · Economics"},
    {"event_id": "EVT_HORMUZ_BLOCKADE_2026",       "name": "Strait of Hormuz Blockade",        "severity": "critical", "domain": "Economics · Geopolitics"},
    {"event_id": "EVT_IRAN_CEASEFIRE_TALKS_2026",  "name": "Iran War Ceasefire Negotiations",  "severity": "high",     "domain": "Geopolitics · Diplomacy"},
    {"event_id": "EVT_INDUS_WATERS_CRISIS_2025",   "name": "Indus Waters Treaty Suspension",   "severity": "high",     "domain": "Governance · Geopolitics"},
    {"event_id": "EVT_INDIA_PAK_DIPLO_CRISIS_2025","name": "India-Pakistan Diplomatic Crisis", "severity": "high",     "domain": "Geopolitics · Defense"},
]

_SEV_COLOR   = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15", "low": "#22c55e"}
_TREND_ICON  = {"rising":"↑","falling":"↓","stable":"→","volatile_high":"⚡","critically_low":"🔴",
                "depreciating":"↓","extreme":"⚡","evacuation_ongoing":"🚁","negative":"↓","high":"⚠️"}
_TREND_COLOR = {"rising":"#ef4444","falling":"#22c55e","stable":"#94a3b8","volatile_high":"#f97316",
                "critically_low":"#ef4444","depreciating":"#ef4444","extreme":"#ef4444",
                "evacuation_ongoing":"#f97316","negative":"#ef4444","high":"#f97316"}
_CAT_COLOR   = {"military":"#ef4444","diplomatic":"#38bdf8","economic":"#22c55e",
                "policy":"#facc15","humanitarian":"#a78bfa"}
_CAT_ICON    = {"military":"🪖","diplomatic":"🤝","economic":"📈","policy":"📋","humanitarian":"🏥"}
_STATUS_COLOR= {"executed":"#22c55e","active":"#38bdf8","pending":"#facc15",
                "cancelled":"#ef4444","ongoing":"#38bdf8"}
_SCN_COLOR   = {"Best Case":"#22c55e","Base Case":"#f97316","Worst Case":"#ef4444"}


@st.cache_data(ttl=30)
def _fetch_crisis(event_id: str) -> dict:
    try:
        r = _req.get(f"{API_BASE}/crisis/{event_id}", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

@st.cache_data(ttl=60)
def _fetch_cascade(event_id: str) -> dict:
    try:
        r = _req.get(f"{API_BASE}/crisis/{event_id}/cascade", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


# ── Static fallback data — shown when Neo4j has no seeded subevents/indicators ─
_STATIC_CRISIS_DATA: dict[str, dict] = {
    "EVT_HORMUZ_BLOCKADE_2026": {
        "subevents": [
            {"subevent_id": "SE_HORMUZ_D1", "name": "Iran declares Hormuz closure", "date": "2026-03-01", "day_number": 1,
             "category": "military", "severity": "critical", "description": "IRGC naval forces halt all tanker traffic through the strait.", "india_impact": "India's 40-45% crude supply route blocked; IOC/BPCL emergency procurement activated."},
            {"subevent_id": "SE_HORMUZ_D5", "name": "Brent Crude hits $127/bbl", "date": "2026-03-05", "day_number": 5,
             "category": "economic", "severity": "critical", "description": "Oil markets spike on supply shock; US strategic reserve release announced.", "india_impact": "Fuel price revision expected — ₹8-12/litre increase modelled by MoPNG."},
            {"subevent_id": "SE_HORMUZ_D9", "name": "UN Security Council emergency session", "date": "2026-03-09", "day_number": 9,
             "category": "diplomatic", "severity": "high", "description": "UNSC convenes; India abstains, calls for humanitarian passage.", "india_impact": "India maintains neutrality; SCI tankers rerouted via Cape of Good Hope."},
            {"subevent_id": "SE_HORMUZ_D14", "name": "Cape of Good Hope rerouting operational", "date": "2026-03-14", "day_number": 14,
             "category": "policy", "severity": "high", "description": "Indian PSU tankers adopt 12-14 day longer route; freight costs up $4/bbl.", "india_impact": "Refinery throughput at Jamnagar reduced 35%; demand-side rationing under review."},
            {"subevent_id": "SE_HORMUZ_D18", "name": "Oman-brokered partial corridor", "date": "2026-03-18", "day_number": 18,
             "category": "diplomatic", "severity": "high", "description": "Oman negotiates limited tanker corridor through Musandam — India included.", "india_impact": "2 LNG vessels cleared; SPR pressure slightly eased."},
        ],
        "indicators": [
            {"indicator_id": "IND_BRENT_CRUDE", "name": "Brent Crude", "value": 127, "unit": "USD/bbl", "trend": "rising", "domain": "economics"},
            {"indicator_id": "IND_INR_USD", "name": "INR/USD Rate", "value": 87.8, "unit": "INR/USD", "trend": "depreciating", "domain": "economics"},
            {"indicator_id": "IND_INDIA_SPR_DAYS", "name": "India SPR Cover", "value": 7.2, "unit": "days", "trend": "critically_low", "domain": "economics"},
            {"indicator_id": "IND_HORMUZ_TRAFFIC", "name": "Hormuz Traffic", "value": 3, "unit": "vessels/day", "trend": "critically_low", "domain": "geopolitics"},
            {"indicator_id": "IND_FREIGHT_PREMIUM", "name": "Freight Premium", "value": 340, "unit": "% vs baseline", "trend": "volatile_high", "domain": "economics"},
        ],
        "decisions": [
            {"decision_id": "DEC_HORMUZ_1", "name": "SPR Emergency Release Activated", "date": "2026-03-03", "status": "active",
             "actor_name": "MoPNG", "description": "Full Strategic Petroleum Reserve draw-down authorised; 7-day buffer being deployed to refineries."},
            {"decision_id": "DEC_HORMUZ_2", "name": "Emergency Crude Procurement — Russia + West Africa", "date": "2026-03-06", "status": "executed",
             "actor_name": "Indian Oil Corporation", "description": "Spot purchases from Rosneft (+15%) and Nigerian NNPC signed; Vladivostok route vessel chartered."},
            {"decision_id": "DEC_HORMUZ_3", "name": "RBI Forex Intervention $7.4B", "date": "2026-03-08", "status": "executed",
             "actor_name": "RBI", "description": "RBI sold $7.4 billion in forex reserves to defend INR; further intervention authorised if INR crosses 89."},
            {"decision_id": "DEC_HORMUZ_4", "name": "WTO Safe Passage Complaint Filed", "date": "2026-03-12", "status": "pending",
             "actor_name": "MEA", "description": "India files formal WTO complaint on Iran's blockade as discriminatory trade restriction under GATT Article XXI."},
        ],
    },

    "EVT_IRAN_CEASEFIRE_TALKS_2026": {
        "subevents": [
            {"subevent_id": "SE_CEASEFIRE_D1", "name": "Oman begins shuttle diplomacy", "date": "2026-03-05", "day_number": 1,
             "category": "diplomatic", "severity": "high", "description": "Omani FM begins Tehran-Washington shuttle after Saudi back-channel opens.", "india_impact": "India offers New Delhi as neutral venue; MEA contacts Omani FM."},
            {"subevent_id": "SE_CEASEFIRE_D7", "name": "UNSC Resolution 2847 adopted", "date": "2026-03-11", "day_number": 7,
             "category": "diplomatic", "severity": "high", "description": "Framework resolution for ceasefire monitoring adopted; India votes yes.", "india_impact": "India formally included in ceasefire monitoring working group."},
            {"subevent_id": "SE_CEASEFIRE_D12", "name": "Round 1 talks — Muscat", "date": "2026-03-16", "day_number": 12,
             "category": "diplomatic", "severity": "high", "description": "First formal ceasefire round; Iran demands full US carrier withdrawal; US offers 30-day pause.", "india_impact": "India $50M humanitarian pledge deployed; Jaishankar meets Omani FM."},
            {"subevent_id": "SE_CEASEFIRE_D18", "name": "Iran humanitarian corridor agreed", "date": "2026-03-22", "day_number": 18,
             "category": "humanitarian", "severity": "high", "description": "Partial humanitarian corridor agreed for LNG and food vessels through Hormuz.", "india_impact": "3 Indian LNG vessels cleared; Brent drops $12 on news."},
            {"subevent_id": "SE_CEASEFIRE_D22", "name": "Round 2 — Geneva", "date": "2026-03-26", "day_number": 22,
             "category": "diplomatic", "severity": "high", "description": "Geneva Track II; India invited as observer — first non-P5 participant.", "india_impact": "Strategic autonomy narrative strengthened; India positions for post-conflict reconstruction role."},
        ],
        "indicators": [
            {"indicator_id": "IND_BRENT_CRUDE", "name": "Brent Crude", "value": 114, "unit": "USD/bbl", "trend": "falling", "domain": "economics"},
            {"indicator_id": "IND_INR_USD", "name": "INR/USD Rate", "value": 86.9, "unit": "INR/USD", "trend": "stable", "domain": "economics"},
            {"indicator_id": "IND_CEASEFIRE_ROUNDS", "name": "Negotiation Rounds", "value": 3, "unit": "completed", "trend": "rising", "domain": "geopolitics"},
            {"indicator_id": "IND_HORMUZ_TRAFFIC", "name": "Hormuz Traffic", "value": 8, "unit": "vessels/day", "trend": "rising", "domain": "geopolitics"},
            {"indicator_id": "IND_INDIA_COST_WK", "name": "India Weekly Crisis Cost", "value": 14700, "unit": "Cr INR/week", "trend": "falling", "domain": "economics"},
        ],
        "decisions": [
            {"decision_id": "DEC_CF_1", "name": "$50M Humanitarian Aid Deployed", "date": "2026-03-12", "status": "executed",
             "actor_name": "MEA", "description": "India's $50M humanitarian contribution to UN-coordinated relief corridor activated."},
            {"decision_id": "DEC_CF_2", "name": "India Ceasefire Observer Status", "date": "2026-03-22", "status": "active",
             "actor_name": "MEA", "description": "India accepted as observer in Geneva Track II — first non-P5 inclusion; EAM Jaishankar attending."},
            {"decision_id": "DEC_CF_3", "name": "Chabahar Phase 2 MOU Tabled", "date": "2026-03-24", "status": "pending",
             "actor_name": "Ministry of Commerce", "description": "India tables MOU for post-ceasefire Chabahar Phase 2 resumption as reconstruction commitment."},
        ],
    },

    "EVT_INDUS_WATERS_CRISIS_2025": {
        "subevents": [
            {"subevent_id": "SE_INDUS_D1", "name": "IWT formally suspended", "date": "2025-04-24", "day_number": 1,
             "category": "policy", "severity": "critical", "description": "Cabinet approves suspension of Indus Waters Treaty — first in 65 years.", "india_impact": "India no longer obligated to share hydrological data with Pakistan; Jal Shakti accelerates Western river projects."},
            {"subevent_id": "SE_INDUS_D5", "name": "Pakistan files World Bank objection", "date": "2025-04-28", "day_number": 5,
             "category": "diplomatic", "severity": "high", "description": "Pakistan Indus Commission formally objects to World Bank; arbitration tribunal procedures initiated.", "india_impact": "MEA files preemptive legal justification citing Article XII(3) — material breach by Pakistan."},
            {"subevent_id": "SE_INDUS_D12", "name": "Kishanganga works accelerated", "date": "2025-05-05", "day_number": 12,
             "category": "policy", "severity": "high", "description": "NHPC announces accelerated timeline for Kishanganga (330 MW) — target 18-month commissioning.", "india_impact": "330 MW of hydro capacity to be added to northern grid within 18 months."},
            {"subevent_id": "SE_INDUS_D18", "name": "Ratle project fast-tracked", "date": "2025-05-12", "day_number": 18,
             "category": "policy", "severity": "high", "description": "Ratle (850 MW) fast-tracked under national security emergency provision; environmental clearance expedited.", "india_impact": "Combined Kishanganga + Ratle = 1,180 MW renewable addition — reduces coal dependency."},
            {"subevent_id": "SE_INDUS_D25", "name": "India-Pakistan Joint Commission halted", "date": "2025-05-18", "day_number": 25,
             "category": "diplomatic", "severity": "high", "description": "Permanent Indus Commission biannual meeting cancelled; dispute mechanism fully non-functional.", "india_impact": "No diplomatic channel for water disputes — escalation risk elevated."},
        ],
        "indicators": [
            {"indicator_id": "IND_KISHANGANGA_PROGRESS", "name": "Kishanganga Completion", "value": 68, "unit": "% complete", "trend": "rising", "domain": "governance"},
            {"indicator_id": "IND_INDUS_FLOW_SHARING", "name": "Data Sharing Status", "value": 0, "unit": "% (suspended)", "trend": "stable", "domain": "governance"},
            {"indicator_id": "IND_WB_ARBITRATION", "name": "World Bank Arbitration", "value": 1, "unit": "case filed", "trend": "high", "domain": "geopolitics"},
            {"indicator_id": "IND_RATLE_MW", "name": "Ratle Capacity Target", "value": 850, "unit": "MW", "trend": "rising", "domain": "governance"},
            {"indicator_id": "IND_PAKISTAN_AGRI_RISK", "name": "Pak Irrigated Farm Risk", "value": 80, "unit": "% at risk", "trend": "rising", "domain": "geopolitics"},
        ],
        "decisions": [
            {"decision_id": "DEC_INDUS_1", "name": "IWT Suspension Cabinet Decision", "date": "2025-04-24", "status": "executed",
             "actor_name": "Cabinet Committee on Security", "description": "Formal suspension of Indus Waters Treaty approved; legal justification invoking Article XII(3) filed."},
            {"decision_id": "DEC_INDUS_2", "name": "Kishanganga Fast-Track Order", "date": "2025-05-05", "status": "active",
             "actor_name": "Ministry of Power / NHPC", "description": "Emergency commissioning order for Kishanganga 330 MW; 18-month target with quarterly milestones."},
            {"decision_id": "DEC_INDUS_3", "name": "World Bank Legal Brief Filed", "date": "2025-05-02", "status": "executed",
             "actor_name": "MEA", "description": "India's preemptive legal position submitted to World Bank — grounds for suspension citing Pakistan-sponsored cross-border terrorism."},
            {"decision_id": "DEC_INDUS_4", "name": "IWT Renegotiation Study Commissioned", "date": "2025-05-15", "status": "active",
             "actor_name": "Ministry of Jal Shakti", "description": "Comprehensive re-evaluation of 1960 IWT terms commissioned; position paper for treaty renegotiation to be ready in 6 months."},
        ],
    },

    "EVT_INDIA_PAK_DIPLO_CRISIS_2025": {
        "subevents": [
            {"subevent_id": "SE_DIPLO_D1", "name": "Diplomatic relations downgraded", "date": "2025-05-02", "day_number": 1,
             "category": "diplomatic", "severity": "critical", "description": "India expels Pakistani High Commission staff; relations reduced to Chargé d'Affaires level.", "india_impact": "Attari-Wagah border closed; $2.4B annual bilateral trade halted."},
            {"subevent_id": "SE_DIPLO_D3", "name": "Pakistani airspace closed to India", "date": "2025-05-04", "day_number": 3,
             "category": "diplomatic", "severity": "high", "description": "Pakistan closes airspace to Indian commercial aircraft — retaliation for expulsions.", "india_impact": "200 daily India-Europe flights rerouted; ₹170 Cr/month detour cost."},
            {"subevent_id": "SE_DIPLO_D5", "name": "SAARC processes frozen", "date": "2025-05-06", "day_number": 5,
             "category": "diplomatic", "severity": "high", "description": "India formally suspends participation in SAARC framework pending resolution.", "india_impact": "Regional cooperation architecture suspended; SAARCrelated trade negotiations halted."},
            {"subevent_id": "SE_DIPLO_D8", "name": "MEA P5 briefing — India's case made", "date": "2025-05-09", "day_number": 8,
             "category": "diplomatic", "severity": "high", "description": "Jaishankar briefs UNSC P5 individually; US and UK issue statements condemning Pakistan-based terror.", "india_impact": "Pakistan's UNSC emergency session request blocked by US/UK veto support."},
            {"subevent_id": "SE_DIPLO_D14", "name": "Central Asian airspace agreements signed", "date": "2025-05-16", "day_number": 14,
             "category": "economic", "severity": "high", "description": "India signs bilateral airspace agreements with Tajikistan, Kazakhstan for permanent India-Europe routing.", "india_impact": "Per-flight cost premium reduced to $38; DGCA issues revised routing advisories."},
        ],
        "indicators": [
            {"indicator_id": "IND_BILATERAL_TRADE", "name": "India-Pak Trade", "value": 0, "unit": "% of normal", "trend": "critically_low", "domain": "economics"},
            {"indicator_id": "IND_AIRSPACE_COST", "name": "Airspace Detour Cost", "value": 112, "unit": "USD/flight extra", "trend": "falling", "domain": "economics"},
            {"indicator_id": "IND_DIPLO_STATUS", "name": "Diplomatic Level", "value": 1, "unit": "Chargé d'Affaires", "trend": "negative", "domain": "geopolitics"},
            {"indicator_id": "IND_LOC_CEASEFIRE", "name": "LoC Ceasefire Status", "value": 85, "unit": "% compliance", "trend": "stable", "domain": "defense"},
            {"indicator_id": "IND_PAK_ISOLATION_SCORE", "name": "Pakistan Diplomatic Isolation", "value": 72, "unit": "/100", "trend": "rising", "domain": "geopolitics"},
        ],
        "decisions": [
            {"decision_id": "DEC_DIPLO_1", "name": "Attari-Wagah Border Closure", "date": "2025-05-02", "status": "active",
             "actor_name": "Ministry of Home Affairs", "description": "Attari-Wagah land border closed indefinitely; all bilateral trade suspended pending diplomatic normalisation."},
            {"decision_id": "DEC_DIPLO_2", "name": "SAARC Visa Scheme Suspended", "date": "2025-05-03", "status": "executed",
             "actor_name": "MEA", "description": "SAARC Visa Exemption Scheme suspended for Pakistani nationals; existing visas revoked."},
            {"decision_id": "DEC_DIPLO_3", "name": "WTO Airspace Complaint Filed", "date": "2025-05-10", "status": "executed",
             "actor_name": "MEA / Ministry of Commerce", "description": "Formal WTO complaint filed on Pakistan airspace denial as discriminatory trade restriction under GATT Article XXI."},
            {"decision_id": "DEC_DIPLO_4", "name": "Central Asian Routing Agreements", "date": "2025-05-16", "status": "executed",
             "actor_name": "Ministry of Civil Aviation", "description": "Bilateral airspace agreements with Tajikistan and Kazakhstan signed; permanent India-Europe routing via Central Asia operational."},
            {"decision_id": "DEC_DIPLO_5", "name": "Pakistan Dossier to UNSC", "date": "2025-05-08", "status": "executed",
             "actor_name": "Intelligence Bureau + MEA", "description": "Formal dossier on Pahalgam attack perpetrators submitted to UN Counter-Terrorism Committee with evidence of Pakistan ISI links."},
        ],
    },
}



# ── Chart helpers ─────────────────────────────────────────────────────────────

def _timeline_chart(subevents: list) -> None:
    by_cat: dict = {}
    for se in subevents:
        by_cat.setdefault(se.get("category","other"), []).append(se)

    fig = go.Figure()
    for cat, events in by_cat.items():
        color = _CAT_COLOR.get(cat, "#94a3b8")
        dates, labels, hovers, sizes = [], [], [], []
        for se in events:
            try:
                dates.append(datetime.strptime(se["date"], "%Y-%m-%d"))
            except Exception:
                continue
            labels.append(f"Day {se.get('day_number','?')}")
            impact = se.get("india_impact","")
            hovers.append(
                f"<b>{se.get('name','')}</b><br>"
                f"Day {se.get('day_number','?')} · {se.get('date','')}<br>"
                f"<i>{se.get('description','')[:140]}</i>"
                + (f"<br><span style='color:#f97316'>🇮🇳 {impact}</span>" if impact else "")
            )
            sizes.append({"critical":18,"high":14,"medium":10,"low":7}.get(se.get("severity","medium"),10))

        if not dates:
            continue

        fig.add_trace(go.Scatter(
            x=dates, y=[cat]*len(dates), mode="markers+text",
            marker=dict(color=color, size=sizes, line=dict(color="#020b14", width=2)),
            text=labels, textposition="top center",
            textfont=dict(color=color, size=9),
            name=cat.title(),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
        ))
        # connector line
        sorted_dates = sorted(dates)
        if len(sorted_dates) > 1:
            fig.add_trace(go.Scatter(
                x=sorted_dates, y=[cat]*len(sorted_dates), mode="lines",
                line=dict(color=color, width=1, dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))

    fig.update_layout(
        height=300, paper_bgcolor="#020b14", plot_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif", size=10),
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(showgrid=True, gridcolor="#0f1e35", tickfont=dict(size=9,color="#475569"),
                   tickformat="%b %d", zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11,color="#94a3b8"),
                   categoryorder="array",
                   categoryarray=["humanitarian","policy","economic","diplomatic","military"]),
        legend=dict(orientation="h", x=0, y=-0.15, font=dict(size=9,color="#94a3b8"),
                    bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#0d1f35", bordercolor="#1e3a5f",
                        font=dict(color="#e2e8f0", size=11)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _radar_chart(indicators: list, impacts: list) -> None:
    """
    Radar built from two sources:
    1. Impact nodes from the ontology graph (primary — truly ontology-driven)
    2. Indicator nodes as fallback axes if impacts < 3
    """
    _DOMAIN_AXIS = {
        "DOM_ECONOMICS":   "Economic",
        "DOM_DEFENSE":     "Security",
        "DOM_GEOPOLITICS": "Geopolitical",
        "DOM_SOCIETY":     "Social",
        "DOM_CLIMATE":     "Environmental",
        "DOM_GOVERNANCE":  "Governance",
        "DOM_TECHNOLOGY":  "Technology",
    }
    _SEV_SCORE = {"critical": 90, "high": 70, "medium": 45, "low": 20}

    axes, scores = [], []

    # Primary: derive axes from Impact nodes grouped by domain
    domain_max: dict[str, int] = {}
    for imp in impacts:
        domain = imp.get("domain","")
        axis   = _DOMAIN_AXIS.get(domain, domain.replace("DOM_","").title())
        score  = _SEV_SCORE.get(imp.get("severity","medium"), 45)
        domain_max[axis] = max(domain_max.get(axis, 0), score)
    axes   = list(domain_max.keys())
    scores = [domain_max[a] for a in axes]

    # Fallback: if fewer than 3 axes from impacts, supplement with indicators
    if len(axes) < 3:
        _IND_TO_AXIS = {
            "IND_BRENT_CRUDE":     ("Oil Price",     lambda v: min(100, max(0, (v-70)/80*100))),
            "IND_INR_USD":         ("Currency",      lambda v: min(100, max(0, (v-82)/15*100))),
            "IND_HORMUZ_TRAFFIC":  ("Trade Routes",  lambda v: min(100, max(0, (1-v/25)*100))),
            "IND_INDIA_SPR_DAYS":  ("Energy Buffer", lambda v: min(100, max(0, (1-v/30)*100))),
            "IND_INDIA_OIL_IMPORT":("Supply Risk",   lambda v: min(100, max(0, v))),
            "IND_NIFTY_DROP":      ("Markets",       lambda v: min(100, max(0, abs(v)/20*100))),
        }
        for ind in indicators:
            iid = ind.get("indicator_id","")
            if iid in _IND_TO_AXIS:
                label, fn = _IND_TO_AXIS[iid]
                if label not in axes:
                    axes.append(label)
                    scores.append(round(fn(float(ind.get("value",0))), 1))

    if len(axes) < 3:
        return

    axes_c   = axes + [axes[0]]
    scores_c = scores + [scores[0]]
    avg      = sum(scores) / len(scores)
    lc = "#ef4444" if avg > 65 else "#f97316" if avg > 40 else "#22c55e"
    fc = f"rgba({239 if avg>65 else 249 if avg>40 else 34},{68 if avg>65 else 115 if avg>40 else 197},{68 if avg>65 else 22 if avg>40 else 94},0.2)"

    fig = go.Figure()
    for ring in [25, 50, 75]:
        fig.add_trace(go.Scatterpolar(
            r=[ring]*len(axes_c), theta=axes_c, mode="lines",
            line=dict(color="#0f1e35", width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))
    fig.add_trace(go.Scatterpolar(
        r=scores_c, theta=axes_c, fill="toself", fillcolor=fc,
        line=dict(color=lc, width=2),
        marker=dict(color=lc, size=6),
        hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
        name="Threat Level",
    ))
    fig.update_layout(
        height=340, paper_bgcolor="#020b14", plot_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif", size=10),
        margin=dict(l=20, r=20, t=30, b=20),
        polar=dict(
            bgcolor="#020b14",
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=8,color="#334155"),
                            gridcolor="#0f1e35", linecolor="#0f1e35", tickvals=[25,50,75,100]),
            angularaxis=dict(tickfont=dict(size=11,color="#94a3b8"),
                             linecolor="#1e293b", gridcolor="#0f1e35"),
        ),
        showlegend=False,
        hoverlabel=dict(bgcolor="#0d1f35", bordercolor="#1e3a5f",
                        font=dict(color="#e2e8f0", size=11)),
    )
    threat = "CRITICAL" if avg>65 else "HIGH" if avg>40 else "MODERATE"
    st.markdown(
        f'<div style="text-align:center;font-size:10px;font-weight:700;color:{lc};'
        f'letter-spacing:.1em;margin-bottom:4px;">INDIA EXPOSURE — {threat} ({avg:.0f}/100)</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _cascade_sankey(cascade: dict) -> None:
    """Plotly Sankey showing crisis → impacts → connected events → schemes → actors."""
    nodes = cascade.get("sankey_nodes", [])
    links = cascade.get("sankey_links", [])

    if not nodes or not links:
        st.markdown(
            '<div style="color:#475569;font-size:12px;margin-top:20px;text-align:center;">'
            'No cascade data available — run seed scripts to populate Impact, Scheme, and Actor nodes.</div>',
            unsafe_allow_html=True,
        )
        return

    _NODE_COLOR = {
        "event":   "#ef4444",
        "impact":  "#f97316",
        "scheme":  "#38bdf8",
        "actor":   "#a78bfa",
        "default": "#94a3b8",
    }
    node_colors = [_NODE_COLOR.get(n.get("type", "default"), _NODE_COLOR["default"]) for n in nodes]
    link_colors = [f"rgba(148,163,184,0.18)"] * len(links)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18, thickness=18,
            line=dict(color="#020b14", width=0.5),
            label=[n["label"] for n in nodes],
            color=node_colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=[lk["source"] for lk in links],
            target=[lk["target"] for lk in links],
            value=[lk.get("value", 1) for lk in links],
            color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<extra></extra>",
        ),
    ))
    fig.update_layout(
        height=420,
        paper_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif", size=11),
        margin=dict(l=10, r=10, t=30, b=10),
        hoverlabel=dict(bgcolor="#0d1f35", bordercolor="#1e3a5f",
                        font=dict(color="#e2e8f0", size=11)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Legend
    st.markdown(
        '<div style="display:flex;gap:16px;margin-top:4px;">'
        + "".join(
            f'<span style="font-size:9px;color:{c};font-weight:700;">■ {lbl}</span>'
            for lbl, c in [("Crisis Event","#ef4444"),("Impact","#f97316"),
                           ("Scheme","#38bdf8"),("Actor","#a78bfa")]
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    # Connected events + schemes + actors as text summary
    connected = cascade.get("connected_events", [])
    schemes   = cascade.get("schemes", [])
    actors    = cascade.get("actors", [])
    if connected or schemes or actors:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="small")
        with c1:
            st.markdown(
                '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
                'letter-spacing:.08em;margin-bottom:6px;">CONNECTED EVENTS</div>',
                unsafe_allow_html=True,
            )
            for ev in connected:
                st.markdown(
                    f'<div style="font-size:10px;color:#ef4444;padding:3px 0;border-bottom:1px solid #0f1e35;">'
                    f'🔗 {ev.get("name","")}</div>',
                    unsafe_allow_html=True,
                )
        with c2:
            st.markdown(
                '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
                'letter-spacing:.08em;margin-bottom:6px;">TRIGGERED SCHEMES</div>',
                unsafe_allow_html=True,
            )
            for sc in schemes:
                st.markdown(
                    f'<div style="font-size:10px;color:#38bdf8;padding:3px 0;border-bottom:1px solid #0f1e35;">'
                    f'📋 {sc.get("name","")}</div>',
                    unsafe_allow_html=True,
                )
        with c3:
            st.markdown(
                '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
                'letter-spacing:.08em;margin-bottom:6px;">RESPONDING ACTORS</div>',
                unsafe_allow_html=True,
            )
            for act in actors:
                st.markdown(
                    f'<div style="font-size:10px;color:#a78bfa;padding:3px 0;border-bottom:1px solid #0f1e35;">'
                    f'🏛 {act.get("name","")}</div>',
                    unsafe_allow_html=True,
                )


def _scenario_donut(scenarios: list) -> None:
    if not scenarios:
        return
    labels = [f"{s.get('label','?')}<br><span style='font-size:9px'>{s.get('name','')}</span>"
              for s in scenarios]
    values = [s.get("probability", 0.33) for s in scenarios]
    colors = [_SCN_COLOR.get(s.get("label",""), "#94a3b8") for s in scenarios]

    fig = go.Figure(go.Pie(
        labels=[s.get("label","?") for s in scenarios],
        values=values, hole=0.60,
        marker=dict(colors=colors, line=dict(color="#020b14", width=3)),
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>P=%{percent}<extra></extra>",
        direction="clockwise", sort=False,
    ))
    fig.update_layout(
        height=300, paper_bgcolor="#020b14", plot_bgcolor="#020b14",
        font=dict(color="#94a3b8", family="Outfit, sans-serif"),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="v", x=1.0, y=0.5,
                    font=dict(size=10,color="#94a3b8"), bgcolor="rgba(0,0,0,0)"),
        annotations=[dict(text=f"<b>{len(scenarios)}</b><br>Scenarios",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color="#e2e8f0"))],
        hoverlabel=dict(bgcolor="#0d1f35", bordercolor="#1e3a5f",
                        font=dict(color="#e2e8f0", size=11)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Page ──────────────────────────────────────────────────────────────────────

def page():
    st.set_page_config(page_title="Crisis Tracker – PRAMAAN", layout="wide")
    render_topnav(active_page="Crisis Tracker")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    button[data-baseweb="tab"] { font-size: 11px !important; padding: 6px 12px !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(239,68,68,0.7), 0 0 30px rgba(239,68,68,0.4), 0 0 50px rgba(249,115,22,0.2); }
        50%       { text-shadow: 0 0 25px rgba(239,68,68,1), 0 0 60px rgba(249,115,22,0.8), 0 0 100px rgba(239,68,68,0.5); }
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Resolve selected crisis early ────────────────────────────────────────
    if "crisis_sel" not in st.session_state:
        st.session_state.crisis_sel = ACTIVE_CRISES[0]["event_id"]
    if "crisis_sel" in st.query_params:
        st.session_state.crisis_sel = st.query_params["crisis_sel"]
    
    sel_id = st.session_state.crisis_sel

    # ── Page Header ─────────────────────────────────────────────────────────
    col_t1, col_t2 = st.columns([0.75, 0.25])
    with col_t1:
        _critical_count = sum(1 for c in ACTIVE_CRISES if c["severity"] == "critical")
        _high_count     = sum(1 for c in ACTIVE_CRISES if c["severity"] == "high")
        st.markdown(f"""
        <div style="position:sticky;top:52px;z-index:100;background:#020b14;
                    padding:6px 0 4px;display:flex;align-items:center;gap:14px;">
          <span style="font-size:1.9em;font-weight:800;color:#ef4444;font-family:'Cinzel',serif;
                       letter-spacing:0.08em;animation:glowPulse 5s ease-in-out infinite;">
            CRISIS TRACKER
          </span>
          <span style="font-size:0.75em;color:#64748b;white-space:nowrap;margin-top:4px;">
            {_critical_count} Critical · {_high_count} High Active Events
          </span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_t2:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:flex-end;height:100%;padding-top:6px;">'
            '<a href="/Delivery_Monitor" target="_self" '
            'style="background:linear-gradient(135deg,#f97316,#ea580c);color:#fff;'
            'text-decoration:none;border-radius:8px;padding:6px 16px;'
            'font-size:11px;font-weight:700;letter-spacing:0.04em;'
            'box-shadow:0 2px 10px rgba(249,115,22,0.35);white-space:nowrap;">'
            'Scheme Delivery →'
            '</a></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="border-bottom:1px solid #1e293b; margin-top:-6px; margin-bottom:12px;"></div>', unsafe_allow_html=True)

    # (Sidebar selection handled below)

    # ── Layout: sidebar list + main content ──────────────────────────────────
    col_sidebar, col_main = st.columns([0.22, 0.78], gap="medium")

    with col_sidebar:
        st.markdown(
            '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:.1em;margin:8px 0 12px 4px;">ACTIVE CRISES</div>',
            unsafe_allow_html=True,
        )
        
        for crisis in ACTIVE_CRISES:
            eid    = crisis["event_id"]
            sev    = crisis["severity"]
            is_sel = eid == st.session_state.crisis_sel
            sc     = _SEV_COLOR.get(sev, "#94a3b8")
            
            # Fetch real confidence for sub-label
            data = _fetch_crisis(eid)
            event_meta = data.get("event", {})
            conf = event_meta.get("confidence", 0.85)

            # Consistent Selection Button (Single-purpose)
            if st.button(
                crisis["name"],
                key=f"sel_{eid}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state.crisis_sel = eid
                st.session_state.pop(f"scenarios_{eid}", None)
                st.rerun()
            
            # Sub-label for Trust & Domain (consistent with button width)
            st.markdown(
                f'<div style="font-size:10px;color:#475569;font-weight:700;'
                f'text-transform:uppercase;margin-top:-10px;padding:0 4px 10px 4px; '
                f'display:flex; justify-content:space-between;">'
                f'<span>{sev} · {crisis["domain"].split("·")[0]}</span>'
                f'<span>TRUST: {int(conf*100)}%</span></div>',
                unsafe_allow_html=True,
            )

    # ── Main content ──────────────────────────────────────────────────────────
    with col_main:
        sel_id = st.session_state.crisis_sel
        data   = _fetch_crisis(sel_id)

        if not data:
            st.markdown(
                '<div style="color:#475569;font-size:12px;margin-top:40px;text-align:center;">'
                'Crisis data unavailable — backend may be loading.</div>',
                unsafe_allow_html=True,
            )
            return

        event      = data.get("event", {})
        subevents  = data.get("subevents", [])
        indicators = data.get("indicators", [])
        decisions  = data.get("decisions", [])
        impacts    = data.get("impacts", [])

        # ── Merge static fallback when Neo4j has no seeded data ───────────────
        _static = _STATIC_CRISIS_DATA.get(sel_id, {})
        if not subevents  and _static.get("subevents"):  subevents  = _static["subevents"]
        if not indicators and _static.get("indicators"): indicators = _static["indicators"]
        if not decisions  and _static.get("decisions"):  decisions  = _static["decisions"]


        ev_sev   = event.get("severity", "high")
        ev_color = _SEV_COLOR.get(ev_sev, "#f97316")
        conf     = event.get("confidence", 0.85)
        tier     = "high" if conf >= 0.8 else "medium" if conf >= 0.6 else "low"

        st.markdown(
            f'<div style="background:linear-gradient(135deg,#1a0000,#0d0f1e);'
            f'border:1px solid {ev_color}44;border-left:4px solid {ev_color};'
            f'border-radius:12px;padding:14px 18px;margin-bottom:14px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:start;">'
            f'  <div>'
            f'    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'      <span style="background:{ev_color}22;color:{ev_color};font-size:9px;font-weight:700;'
            f'                   padding:3px 8px;border-radius:4px;text-transform:uppercase;letter-spacing:.08em;">'
            f'        🔴 ACTIVE CRISIS</span>'
            f'      <span style="font-size:10.5px;color:#475569;">Day {len(subevents)} of conflict · '
            f'        Started {event.get("date","")}</span>'
            f'    </div>'
            f'    <div style="font-size:18px;font-weight:700;color:#f1f5f9;">{event.get("name","")}</div>'
            f'  </div>'
            f'  <div style="text-align:right;">'
            f'    <div style="font-size:10px;font-weight:800;color:#475569;margin-bottom:4px;">AI TRUST TIER</div>'
            f'    <div style="font-size:14px;color:{ev_color};font-weight:800;">{int(conf*100)}% {tier.upper()}</div>'
            f'  </div>'
            f'</div>'
            f'<div style="font-size:10.5px;color:#64748b;margin-top:4px;line-height:1.6;">'
            f'{event.get("description","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # ── Key indicator tiles (top row) ─────────────────────────────────────
        KEY_INDICATORS = ["IND_BRENT_CRUDE","IND_INR_USD","IND_INDIA_SPR_DAYS","IND_HORMUZ_TRAFFIC"]
        key_inds = [i for i in indicators if i.get("indicator_id") in KEY_INDICATORS]
        if key_inds:
            cols = st.columns(len(key_inds), gap="small")
            for idx, ind in enumerate(key_inds):
                trend  = ind.get("trend","stable")
                tc     = _TREND_COLOR.get(trend, "#94a3b8")
                ti     = _TREND_ICON.get(trend, "→")
                with cols[idx]:
                    st.markdown(
                        f'<div style="background:#060f1e;border:1px solid #1e293b;'
                        f'border-radius:10px;padding:12px 14px;text-align:center;">'
                        f'<div style="font-size:9px;color:#475569;margin-bottom:4px;">{ind.get("name","")}</div>'
                        f'<div style="font-size:22px;font-weight:700;color:#f1f5f9;line-height:1;">'
                        f'{ind.get("value","")}</div>'
                        f'<div style="font-size:10px;color:#334155;margin-bottom:4px;">{ind.get("unit","")}</div>'
                        f'<div style="font-size:10px;color:{tc};font-weight:600;">{ti} {trend.replace("_"," ")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # ── Main tabs ─────────────────────────────────────────────────────────
        tab_tl, tab_exp, tab_dec, tab_scn, tab_cas = st.tabs([
            "📅  Crisis Timeline",
            "🎯  India Exposure",
            "🇮🇳  India Decisions",
            "🔭  Scenarios",
            "🔗  Cascade",
        ])

        # ── Timeline ─────────────────────────────────────────────────────────
        with tab_tl:
            if not subevents:
                st.markdown('<div style="color:#475569;font-size:10px;margin-top:20px;">No sub-events recorded yet.</div>',
                            unsafe_allow_html=True)
            else:
                _timeline_chart(subevents)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                for se in reversed(subevents):
                    sev    = se.get("severity","medium")
                    sc     = _SEV_COLOR.get(sev,"#94a3b8")
                    cat    = se.get("category","")
                    impact = se.get("india_impact","")
                    st.markdown(
                        f'<div style="border-left:3px solid {sc}55;padding:5px 10px 5px 12px;'
                        f'margin-bottom:4px;background:#060f1e;border-radius:0 6px 6px 0;">'
                        f'<div style="display:flex;align-items:center;gap:8px;">'
                        f'<span style="font-size:9px;color:#334155;min-width:42px;flex-shrink:0;">'
                        f'Day {se.get("day_number","?")}</span>'
                        f'<span style="font-size:9px;color:{_CAT_COLOR.get(cat,"#94a3b8")};'
                        f'font-weight:700;min-width:80px;flex-shrink:0;">'
                        f'{_CAT_ICON.get(cat,"📌")} {cat}</span>'
                        f'<span style="font-size:10.5px;font-weight:600;color:#cbd5e1;">{se.get("name","")}</span>'
                        f'</div>'
                        + (f'<div style="font-size:9.5px;color:#f97316;margin-top:2px;padding-left:130px;">'
                           f'🇮🇳 {impact}</div>' if impact else "")
                        + f'</div>',
                        unsafe_allow_html=True,
                    )

        # ── India Exposure ────────────────────────────────────────────────────
        with tab_exp:
            if not indicators:
                st.markdown('<div style="color:#475569;font-size:10px;margin-top:20px;">No indicators recorded yet.</div>',
                            unsafe_allow_html=True)
            else:
                col_radar, col_metrics = st.columns([1.1, 1], gap="medium")
                with col_radar:
                    _radar_chart(indicators, impacts)
                with col_metrics:
                    st.markdown(
                        '<div style="font-size:9px;font-weight:700;color:#475569;'
                        'text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">'
                        'ALL INDICATORS</div>',
                        unsafe_allow_html=True,
                    )
                    for ind in indicators:
                        trend  = ind.get("trend","stable")
                        tc     = _TREND_COLOR.get(trend,"#94a3b8")
                        ti     = _TREND_ICON.get(trend,"→")
                        st.markdown(
                            f'<div style="display:flex;justify-content:space-between;align-items:center;'
                            f'padding:7px 10px;border-bottom:1px solid #0f1e35;border-radius:4px;">'
                            f'<span style="font-size:10.5px;color:#64748b;">{ind.get("name","")}</span>'
                            f'<div style="display:flex;align-items:center;gap:10px;">'
                            f'<span style="font-size:13px;font-weight:700;color:#f1f5f9;">'
                            f'{ind.get("value","")} '
                            f'<span style="font-size:9px;color:#334155;">{ind.get("unit","")}</span></span>'
                            f'<span style="font-size:12px;color:{tc};">{ti}</span>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

        # ── India Decisions ───────────────────────────────────────────────────
        with tab_dec:
            if not decisions:
                st.markdown('<div style="color:#475569;font-size:10px;margin-top:20px;">No India decisions recorded yet.</div>',
                            unsafe_allow_html=True)
            else:
                # Status summary counts
                status_counts = {}
                for d in decisions:
                    s = d.get("status","")
                    status_counts[s] = status_counts.get(s, 0) + 1
                summary_html = " · ".join(
                    f'<span style="color:{_STATUS_COLOR.get(s,"#94a3b8")};font-weight:700;">'
                    f'{c} {s}</span>'
                    for s, c in status_counts.items()
                )
                st.markdown(
                    f'<div style="font-size:10px;color:#475569;margin-bottom:10px;">'
                    f'{summary_html}</div>',
                    unsafe_allow_html=True,
                )
                for dec in decisions:
                    status = dec.get("status","")
                    sc     = _STATUS_COLOR.get(status,"#94a3b8")
                    actor  = dec.get("actor_name") or dec.get("decided_by","")
                    st.markdown(
                        f'<div style="background:#060f1e;border:1px solid #1e293b;'
                        f'border-radius:10px;padding:10px 14px;margin-bottom:8px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                        f'<span style="font-size:12px;font-weight:600;color:#e2e8f0;">{dec.get("name","")}</span>'
                        f'<span style="background:{sc}22;color:{sc};font-size:9.5px;font-weight:700;'
                        f'padding:3px 8px;border-radius:4px;text-transform:uppercase;">{status}</span>'
                        f'</div>'
                        f'<div style="font-size:9.5px;color:#475569;margin-top:3px;">'
                        f'{actor} · {dec.get("date","")}</div>'
                        f'<div style="font-size:10.5px;color:#64748b;margin-top:6px;line-height:1.5;">'
                        f'{dec.get("description","")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        # ── Scenarios ─────────────────────────────────────────────────────────
        with tab_scn:
            st.markdown(
                '<div style="font-size:9.5px;color:#64748b;margin-bottom:10px;">'
                'AI-generated scenario analysis based on current sub-events, '
                'indicators, and India decisions.</div>',
                unsafe_allow_html=True,
            )
            if st.button("Generate / Refresh Scenarios", key=f"gen_scn_{sel_id}", type="primary"):
                with st.spinner("Analysing crisis state and generating scenarios..."):
                    try:
                        r = _req.post(f"{API_BASE}/crisis/{sel_id}/scenarios", timeout=60)
                        if r.status_code == 200:
                            st.session_state[f"scenarios_{sel_id}"] = r.json().get("scenarios", [])
                        else:
                            st.error(f"Generation failed ({r.status_code})")
                    except Exception as ex:
                        st.error(f"Error: {ex}")

            scenarios = st.session_state.get(f"scenarios_{sel_id}", [])
            if scenarios:
                col_donut, col_cards = st.columns([1, 1.4], gap="medium")
                with col_donut:
                    _scenario_donut(scenarios)
                with col_cards:
                    for scn in scenarios:
                        label   = scn.get("label","")
                        sc      = _SCN_COLOR.get(label,"#94a3b8")
                        impact  = scn.get("india_impact",{})
                        actions = scn.get("india_actions",[])
                        signals = scn.get("warning_signals",[])
                        st.markdown(
                            f'<div style="background:#060f1e;border:1px solid {sc}33;'
                            f'border-left:4px solid {sc};border-radius:8px;'
                            f'padding:10px 14px;margin-bottom:8px;">'
                            f'<div style="font-size:10.5px;font-weight:700;color:{sc};margin-bottom:3px;">'
                            f'{scn.get("name","")}</div>'
                            f'<div style="font-size:9.5px;color:#475569;margin-bottom:6px;">'
                            f'⏱ {scn.get("timeline","")} · {scn.get("trigger","")}</div>'
                            + "".join(
                                f'<div style="font-size:10.5px;color:#64748b;margin-bottom:1px;">'
                                f'<span style="color:#334155">{k.replace("_"," ").title()}:</span> {v}</div>'
                                for k,v in (impact.items() if isinstance(impact,dict) else {}.items())
                            )
                            + (
                                '<div style="margin-top:6px;padding:6px 8px;background:#0a1628;border-radius:5px;">'
                                '<div style="font-size:9.5px;color:#475569;font-weight:700;margin-bottom:3px;">INDIA ACTIONS</div>'
                                + "".join(f'<div style="font-size:10.5px;color:#e2e8f0;margin-bottom:2px;">• {a}</div>' for a in actions)
                                + '</div>' if actions else ""
                            )
                            + (
                                '<div style="margin-top:4px;">'
                                + "".join(f'<div style="font-size:9.5px;color:#f97316;">⚠ {s}</div>' for s in signals)
                                + '</div>' if signals else ""
                            )
                            + '</div>',
                            unsafe_allow_html=True,
                        )

        # ── Cascade ───────────────────────────────────────────────────────────
        with tab_cas:
            st.markdown(
                '<div style="font-size:9px;color:#64748b;margin-bottom:10px;">'
                'Ontology cascade: how this crisis propagates through the governance graph — '
                'impacts → connected events → triggered schemes → responding actors.</div>',
                unsafe_allow_html=True,
            )
            cascade = _fetch_cascade(sel_id)
            if not cascade:
                st.markdown(
                    '<div style="color:#475569;font-size:10.5px;margin-top:20px;text-align:center;">'
                    'Cascade data unavailable — backend may be loading.</div>',
                    unsafe_allow_html=True,
                )
            else:
                _cascade_sankey(cascade)


page()
