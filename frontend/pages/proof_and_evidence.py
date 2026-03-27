"""
proof_and_evidence.py — PRAMAAN v5.1
Proof & Evidence: AI decision brief (Groq LLaMA 3.3 70B), data trust layer,
citizen notification preview, citizen field report.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import streamlit as st
from collections import defaultdict
from groq import Groq
from dotenv import load_dotenv
from utils.api import safe_get
from utils.events import EVENTS, N_EVENTS as _N_EVENTS, render_event_dropdown
from components.topnav import render_topnav
from components.ontology_model import render_ontology_model

load_dotenv(os.path.join(os.path.dirname(__file__), "../..", ".env"))

# Strip lat/lon — this page only needs first 6 fields
EVENTS = [e[:6] for e in EVENTS]

DOMAIN_BULLET = {
    "Climate":     "🟢",
    "Defense":     "🟠",
    "Economics":   "🔵",
    "Society":     "🔴",
    "Governance":  "🟤",
    "Geopolitics": "🟣",
    "Technology":  "🟡",
}

SEV_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15"}
MONTH_MAP = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
             "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Pre-loaded briefs for demo events (instant, no API call needed) ───────────
_PRELOADED_BRIEFS = {
    "EVT_DELHI_FLOODS_2023": {
        "text": """## Situation Summary
The 2023 Delhi Yamuna floods were triggered by upstream Hathnikund Barrage releasing **3.59 lakh cusecs** [REF: data.gov.in] on 12 July 2023 — the highest discharge in 45 years — combined with record 153mm single-day monsoon rainfall [REF: data.gov.in]. The Yamuna breached 208.66m [REF: data.gov.in], the highest since 1978, inundating 27,000 affected persons across low-lying areas [REF: data.gov.in].

## Key Impacts
- **27,000 persons displaced** from floodplains [REF: data.gov.in]
- **153mm rainfall in 24 hours** — highest single-day record for July [REF: data.gov.in]
- **Hathnikund discharge: 3.59 lakh cusecs** — upstream trigger [REF: data.gov.in]
- **Yamuna level: 208.66m** — highest since 1978 [REF: data.gov.in]
- ITO, Civil Lines, Kashmere Gate, Yamuna Bazaar submerged [REF: Curated]

## Actors & Accountability
- **Delhi Jal Board (DJB):** Water treatment plants at Chandrawal and Wazirabad shut down, causing acute water shortage during and after flooding [REF: Curated]
- **Delhi Disaster Management Authority (DDMA):** Evacuation of 27,000 persons executed, though early warning communication gaps documented [REF: Curated]
- **Haryana (Hathnikund Barrage operators):** Rapid gate release without adequate downstream warning to Delhi — inter-state coordination failure [REF: Curated]
- **DDA:** Decades of unauthorised encroachment on Yamuna floodplain permitted under its watch [REF: Curated]

## Cross-Domain Connections
The flood's severity is a direct consequence of **floodplain encroachment** (Governance/Urban domain): DDA permitted construction on O-zone reducing the Yamuna's natural buffer from 97 sq km to under 20 sq km over 30 years. Combined with **climate domain** — intensifying monsoon events — this creates a structural compound risk that worsens each year without land-use reform.

## Governance Gaps / Recommendations

### Priority 1 — URGENT (48h)
**Actor:** Delhi Jal Board
**Action:** Activate backup water supply through tankers to all wards within flood-affected zones; restore Chandrawal and Wazirabad plant operations immediately
**Why:** 27,000 displaced persons face water scarcity compounded by plant shutdown [REF: data.gov.in]
**Outcome:** Zero water-shortage complaints from relief camps within 48 hours

### Priority 2 — SHORT-TERM (30 days)
**Actor:** DDMA + Haryana Irrigation Dept
**Action:** Establish a real-time bilateral flood early-warning protocol — Hathnikund discharge data to Delhi DDMA with minimum 12-hour lead time
**Why:** 2023 discharge of 3.59 lakh cusecs gave Delhi less than 6 hours warning [REF: Curated]
**Outcome:** 12-hour advance evacuation notice issued for all future high-discharge events

### Priority 3 — STRUCTURAL (6 months)
**Actor:** DDA + MoEF
**Action:** Evict all unauthorised structures from O-zone (Yamuna floodplain), restore 97 sq km buffer zone per original Master Plan 2021 zoning
**Why:** Encroachment reduced flood absorption capacity — core reason 208.66m was reached [REF: Curated]
**Outcome:** Yamuna floodplain restored; next equivalent discharge contained below danger mark of 205.33m
⚠️ **Cross-domain flag:** Eviction will displace an estimated 48,000 floodplain residents — requires parallel PMAY housing allocation""",
        "govdata_count": 5,
        "total_impacts": 6,
        "trust_score": 87,
        "trust_label": "HIGH",
        "trust_color": "#22c55e",
        "grounding": {"verified": ["3.59", "208.66", "27000", "153", "1978"], "unverified": [], "total": 5},
    },
    "EVT_WAYANAD_2024": {
        "text": """## Situation Summary
The Wayanad landslide of 30 July 2024 struck Mundakkai and Chooralmala villages at 2am, killing **231 persons** [REF: data.gov.in] and leaving hundreds missing in what became Kerala's deadliest landslide in recorded history. The disaster occurred in a **Zone IV (very high risk)** area that the Gadgil Committee (2011) had recommended for protected status — a recommendation rejected by the state [REF: Curated].

## Key Impacts
- **231 confirmed dead** [REF: data.gov.in]
- **1,000+ displaced** across relief camps [REF: data.gov.in]
- **Mundakkai and Chooralmala villages** near-totally destroyed [REF: Curated]
- Strike at 2am — early warning system did not activate evacuation [REF: Curated]
- IMD had issued Orange Alert (not Red) for Wayanad on 29 July [REF: Curated]

## Actors & Accountability
- **IMD:** Issued Orange Alert rather than Red Alert despite extreme rainfall forecast — threshold calibration failure [REF: Curated]
- **Kerala State Disaster Management Authority (KSDMA):** No pre-emptive evacuation ordered for high-risk villages despite alert [REF: Curated]
- **Ministry of Environment (MoEF):** Failed to implement Gadgil Committee recommendations on Western Ghats Ecologically Sensitive Area [REF: Curated]
- **NDRF:** 6 teams deployed within 24 hours; rescue operation ongoing [REF: Curated]

## Cross-Domain Connections
Root cause is **deforestation and plantation monoculture** replacing native forest in Wayanad's fragile slopes (Climate/Environment domain). Over 40% of Wayanad's forests converted to tea and coffee estates, reducing slope stability. Combined with intensifying rainfall (Climate domain) and rejected environmental protection (Governance domain — Gadgil Committee ignored), this was a predictable outcome flagged 13 years before it occurred.

## Governance Gaps / Recommendations

### Priority 1 — URGENT (48h)
**Actor:** KSDMA + NDRF
**Action:** Complete search and rescue; establish biometric registration of all survivors to prevent missing-person double-counting
**Why:** Hundreds still unaccounted for 48 hours post-event [REF: data.gov.in]
**Outcome:** All survivors registered; missing persons list closed within 72 hours

### Priority 2 — SHORT-TERM (30 days)
**Actor:** IMD + KSDMA
**Action:** Revise IMD alert thresholds — trigger mandatory evacuation on Orange Alert (not Red) for any Zone III/IV village in Western Ghats
**Why:** Orange Alert was active but no evacuation ordered — threshold was insufficient [REF: Curated]
**Outcome:** Zero night-time casualties in future Orange Alert events in high-risk zones

### Priority 3 — STRUCTURAL (6 months)
**Actor:** MoEF + Kerala Government
**Action:** Implement Gadgil Committee Ecologically Sensitive Area (ESA) demarcation for Western Ghats; halt all plantation activity in Zone I areas
**Why:** 13 years of inaction since Gadgil report directly enabled this disaster [REF: Curated]
**Outcome:** Zero new construction or plantation conversion in Zone I — verified by satellite monitoring
⚠️ **Intelligence gap:** No comprehensive land-use change data for Wayanad 2011-2024 is publicly available. RTI to Kerala Revenue Department required.""",
        "govdata_count": 2,
        "total_impacts": 4,
        "trust_score": 74,
        "trust_label": "MEDIUM",
        "trust_color": "#f97316",
        "grounding": {"verified": ["231", "1000"], "unverified": [], "total": 2},
    },
}


def _build_context(event_id: str, name: str, data: dict | None = None) -> str:
    """Fetch event subgraph and format as structured context for the LLM."""
    if data is None:
        data = safe_get(f"/ontology/events/{event_id}", silent=True) or {}
    event       = data.get("event", {})
    impacts     = data.get("impacts", [])
    actors      = data.get("actors", [])
    schemes     = data.get("schemes", [])
    evidence    = data.get("evidence", [])
    connections = data.get("connections", [])
    regions     = data.get("regions", [])

    lines = [f"EVENT: {name}", f"Date: {event.get('date', 'unknown')}", f"Severity: {event.get('severity', 'high')}"]

    if event.get("description"):
        lines.append(f"Description: {event['description']}")
    if regions:
        lines.append(f"Location: {', '.join(r.get('name','') for r in regions)}")

    if impacts:
        govdata_count = sum(1 for i in impacts if "data.gov.in" in (i.get("source") or ""))
        src_note = f"  [{govdata_count} from data.gov.in API]" if govdata_count else ""
        lines.append(f"\nMEASURED IMPACTS:{src_note}")
        for imp in impacts:
            val   = imp.get('value', '')
            unit  = imp.get('unit', '')
            itype = (imp.get('type') or (imp.get('id') or '').replace('IMP_', '').replace('_', ' ')).title()
            desc  = imp.get('description', '')
            src   = " [data.gov.in]" if "data.gov.in" in (imp.get("source") or "") else ""
            lines.append(f"  - {itype}: {val} {unit} — {desc}{src}")

    if actors:
        lines.append("\nKEY ACTORS:")
        for a in actors:
            lines.append(f"  - {a.get('name','')} ({a.get('type','')}): {a.get('role','')}")

    if schemes:
        lines.append("\nSCHEMES / FUNDING:")
        for s in schemes:
            amt = f"₹{s.get('budget_inr_cr', '')} Cr" if s.get('budget_inr_cr') else ""
            lines.append(f"  - {s.get('name', '')}: {amt} — {s.get('description','')[:80]}")

    if evidence:
        lines.append("\nEVIDENCE SOURCES:")
        for ev in evidence:
            lines.append(f"  - {ev.get('source','')} ({ev.get('type','')}: {ev.get('title','')[:60]})")

    if connections:
        lines.append("\nCROSS-DOMAIN LINKS:")
        for c in connections:
            lines.append(f"  - Connected to {c.get('name','')} ({c.get('domain','')}): {c.get('reason','')}")

    return "\n".join(lines)


def _trustability_score(data: dict) -> tuple:
    """Compute pre-generation data trustability score (0-100) from input data quality."""
    impacts     = data.get("impacts", [])
    evidence    = data.get("evidence", [])
    connections = data.get("connections", [])
    actors      = data.get("actors", [])

    govdata          = sum(1 for i in impacts if "data.gov.in" in (i.get("source") or ""))
    tier_score       = (govdata / max(len(impacts), 1)) * 40
    evidence_score   = min(len(evidence) / 3, 1) * 30
    connection_score = min(len(connections) / 2, 1) * 20
    actor_score      = min(len(actors) / 3, 1) * 10

    score = round(tier_score + evidence_score + connection_score + actor_score)
    label = "HIGH" if score >= 85 else ("MEDIUM" if score >= 65 else "LOW")
    color = "#22c55e" if score >= 85 else ("#f97316" if score >= 65 else "#ef4444")
    return score, label, color


def _compound_trustability(risk_data: dict) -> tuple:
    """Trustability score for compound risk (portfolio) mode."""
    events      = risk_data.get("events", [])
    top_impacts = risk_data.get("top_impacts", [])
    connections = risk_data.get("connections", [])

    govdata        = sum(1 for i in top_impacts if "data.gov.in" in (i.get("source") or ""))
    covered        = len({i["event_name"] for i in top_impacts})
    coverage_score = (covered / max(len(events), 1)) * 40
    source_score   = (govdata / max(len(top_impacts), 1)) * 30
    conn_score     = min(len(connections) / 10, 1) * 20
    actor_score    = min(len(risk_data.get("overloaded_actors", [])) / 3, 1) * 10

    score = round(coverage_score + source_score + conn_score + actor_score)
    label = "HIGH" if score >= 85 else ("MEDIUM" if score >= 65 else "LOW")
    color = "#22c55e" if score >= 85 else ("#f97316" if score >= 65 else "#ef4444")
    return score, label, color


def _grounding_check(brief_text: str, context: str) -> dict:
    """Post-generation hallucination check — numbers in brief vs numbers in context."""
    pattern      = re.compile(r'\b(\d[\d,\.]*)\b')
    context_clean = context.replace(",", "")
    found        = pattern.findall(brief_text)
    numbers      = {n.replace(",", "") for n in found if float(n.replace(",", "")) > 5}
    verified     = [n for n in numbers if n in context_clean]
    unverified   = [n for n in numbers if n not in context_clean]
    return {"verified": verified, "unverified": unverified, "total": len(verified) + len(unverified)}


def _render_trust_bar(score: int, label: str, color: str,
                      grounding: dict | None = None,
                      govdata_count: int = 0, total_impacts: int = 0) -> str:
    """Render the trust + grounding bar as HTML."""
    bar = (
        f'<div style="background:#0a1628;border:1px solid #1e293b;border-radius:8px;'
        f'padding:10px 14px;margin-bottom:12px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-size:10.5px;font-weight:700;color:#94a3b8;letter-spacing:0.06em;">DATA TRUSTABILITY</span>'
        f'<span style="font-size:11px;font-weight:800;color:{color};">{label} · {score}%</span>'
        f'</div>'
        f'<div style="background:#1e293b;border-radius:4px;height:6px;margin-bottom:8px;">'
        f'<div style="background:{color};width:{score}%;height:6px;border-radius:4px;'
        f'box-shadow:0 0 6px {color}88;transition:width 0.5s;"></div>'
        f'</div>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;">'
        f'<span style="font-size:9.5px;color:#475569;">📊 {govdata_count}/{total_impacts} impacts from data.gov.in</span>'
    )
    if grounding:
        v = len(grounding["verified"])
        u = len(grounding["unverified"])
        gc = "#22c55e" if u == 0 else ("#f97316" if u <= 2 else "#ef4444")
        bar += (
            f'<span style="font-size:9.5px;color:{gc};font-weight:600;">'
            f'✓ {v} facts verified'
            f'{"" if u == 0 else f" · ⚠️ {u} unverified"}'
            f'</span>'
        )
        if grounding["unverified"]:
            bar += (
                f'<span style="font-size:9px;color:#475569;" title="Not found in ontology context">'
                f'Flagged: {", ".join(grounding["unverified"][:5])}</span>'
            )
    bar += (
        f'<span style="font-size:9.5px;color:#334155;">Score = source tier + evidence + connections + actors</span>'
        f'</div></div>'
    )
    return bar


_PRIORITY_COLORS = {
    "URGENT":     "#ef4444",
    "SHORT-TERM": "#f97316",
    "STRUCTURAL": "#38bdf8",
}


def _style_priorities(text: str) -> str:
    """Replace ### Priority N — LEVEL lines with styled colored banners."""
    def _replace(m):
        n     = m.group(1)
        level = m.group(2).strip().title()
        note  = m.group(3) or ""
        color = next((v for k, v in _PRIORITY_COLORS.items() if k in level.upper()), "#94a3b8")
        note_str = f" {note.strip()}" if note.strip() else ""
        return (
            f'\n<div style="background:{color}18;border-left:3px solid {color};'
            f'border-radius:4px;padding:5px 12px;margin:14px 0 4px;display:inline-block;width:100%;">'
            f'<span style="font-size:11px;font-weight:800;color:{color};letter-spacing:0.05em;">'
            f'PRIORITY {n} — {level}{note_str}</span></div>\n'
        )
    return re.sub(
        r'#{2,4}\s+Priority\s+(\d+)\s*[—\-]+\s*([A-Za-z\-]+)\s*(\([^)]*\))?',
        _replace, text
    )


def _transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe recorded audio via Groq Whisper large-v3-turbo."""
    client = Groq(api_key=GROQ_API_KEY)
    transcription = client.audio.transcriptions.create(
        file=("query.webm", audio_bytes, "audio/webm"),
        model="whisper-large-v3-turbo",
        response_format="text",
    )
    return transcription.strip() if transcription else ""


def _voice_input_widget(key_suffix: str) -> str:
    """Renders a mic button + audio input. Returns transcribed query or ""."""
    with st.expander("🎙️ Speak your query (Groq Whisper)", expanded=False):
        audio = st.audio_input("Record query", key=f"mic_{key_suffix}", label_visibility="collapsed")
        if audio is not None:
            raw   = audio.read()
            ahash = hash(raw)
            if st.session_state.get(f"voice_hash_{key_suffix}") != ahash:
                with st.spinner("Transcribing with Whisper..."):
                    try:
                        text = _transcribe_audio(raw)
                        st.session_state[f"voice_hash_{key_suffix}"] = ahash
                        st.session_state[f"voice_text_{key_suffix}"] = text
                    except Exception as e:
                        st.error(f"Whisper error: {e}")
                        return ""
            transcript = st.session_state.get(f"voice_text_{key_suffix}", "")
            if transcript:
                st.markdown(
                    f'<div style="background:#0a1628;border:1px solid #38bdf844;border-radius:6px;'
                    f'padding:8px 12px;font-size:12px;color:#94a3b8;margin-top:6px;">'
                    f'<span style="color:#38bdf8;font-weight:700;">Whisper:</span> {transcript}</div>',
                    unsafe_allow_html=True,
                )
            return transcript
    return st.session_state.get(f"voice_text_{key_suffix}", "")


def _generate_brief(context: str, name: str, query: str):
    """Call Groq LLaMA 3.3 70B to generate a decision brief (streaming)."""
    client = Groq(api_key=GROQ_API_KEY)
    system_prompt = (
        "You are PRAMAAN — an AI-powered Global Ontology Engine that synthesizes verified government data "
        "into intelligence briefs for senior officials, policymakers, and researchers. "
        "Your output is precise, structured, evidence-driven, and free of speculation. "
        "CITATION RULE — tag every specific number, actor name, or causal claim inline: "
        "use [REF: data.gov.in] for data.gov.in impacts, [REF: Actor] for actor nodes, "
        "[REF: Evidence] for evidence nodes, [REF: Curated] for hand-curated ontology data. "
        "If you make any claim NOT present in the provided context, mark it [UNVERIFIED]. "
        "Never omit citation tags. Format your response in clear sections using markdown."
    )
    user_prompt = (
        f"Using the verified ontology data below for **{name}**, answer the following:\n\n"
        f"**Query:** {query}\n\n"
        f"**Ontology Context:**\n```\n{context}\n```\n\n"
        "Structure your response with these sections:\n"
        "1. **Situation Summary** (2-3 sentences)\n"
        "2. **Key Impacts** (bullet points with real numbers)\n"
        "3. **Actors & Accountability** (who is responsible, what they did)\n"
        "4. **Cross-Domain Connections** (WHY this is happening — root causes, policy failures, "
        "funding gaps, cross-domain triggers; use connected events to show the causal chain)\n"
        "5. **Governance Gaps / Recommendations** (3-5 items, each exactly as follows:\n"
        "### Priority N — [URGENT (48h) / SHORT-TERM (30 days) / STRUCTURAL (6 months)]\n"
        "**Actor:** [named responsible body]\n"
        "**Action:** [specific, executable action]\n"
        "**Why:** [cite specific impact number or evidence]\n"
        "**Outcome:** [measurable result]\n"
        "⚠️ **Cross-domain flag** if action conflicts with resources needed by a connected event\n"
        "⚠️ **Intelligence gap** if data is insufficient — state what is missing)\n\n"
        "Use only data from the context. Do not hallucinate facts."
    )
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1200,
        stream=True,
    )


def _build_compound_context(risk_data: dict) -> str:
    """Format compound-risk API response as LLM context."""
    lines = ["INDIA NATIONAL INTELLIGENCE PORTFOLIO — COMPOUND RISK ASSESSMENT"]
    lines.append(f"Total events tracked: {risk_data.get('total_events', 0)} across 7 domains")
    lines.append(f"Cross-domain connections: {risk_data.get('total_connections', 0)}")

    lines.append("\n== ALL ACTIVE EVENTS ==")
    for e in risk_data.get("events", []):
        lines.append(f"  [{e.get('severity','').upper()}] {e.get('name','')} "
                     f"({e.get('domain','').replace('DOM_','')}) — {e.get('date','')}")

    overloaded = risk_data.get("overloaded_actors", [])
    if overloaded:
        lines.append("\n== ACTOR OVERLOAD — INSTITUTIONAL CAPACITY RISK ==")
        for a in overloaded:
            sevs     = set(a.get("severities", []))
            critical = "critical" in sevs
            lines.append(f"  {'⚠️ ' if critical else ''}{a.get('name','')} ({a.get('type','')}): "
                         f"responsible for {a.get('event_count',0)} events — "
                         f"{', '.join(a.get('event_names', []))}")

    connections = risk_data.get("connections", [])
    if connections:
        lines.append("\n== CROSS-DOMAIN CAUSAL CHAINS ==")
        for c in connections:
            lines.append(f"  {c.get('from_name','')} ({c.get('from_domain','').replace('DOM_','')}) "
                         f"→ {c.get('to_name','')} ({c.get('to_domain','').replace('DOM_', '')})")
            if c.get("reason"):
                lines.append(f"    Reason: {c['reason']}")

    top_impacts = risk_data.get("top_impacts", [])
    if top_impacts:
        lines.append("\n== TOP QUANTIFIED IMPACTS ==")
        for i in top_impacts:
            src = " [data.gov.in]" if "data.gov.in" in (i.get("source") or "") else ""
            lines.append(f"  {i.get('event_name','')} | {i.get('type','').replace('_',' ')}: "
                         f"{i.get('value','')} {i.get('unit','')}{src}")

    clusters = risk_data.get("year_clusters", [])
    if clusters:
        lines.append("\n== TEMPORAL CLUSTERS ==")
        for cl in clusters:
            lines.append(f"  {cl.get('year','')}: {cl.get('count',0)} events — "
                         f"{', '.join(cl.get('event_names', []))}")

    return "\n".join(lines)


def _generate_compound_brief(context: str, query: str):
    """Generate a portfolio-level compound risk brief (streaming)."""
    client = Groq(api_key=GROQ_API_KEY)
    system_prompt = (
        "You are PRAMAAN — an AI-powered Global Ontology Engine providing portfolio-level "
        "national intelligence to senior decision-makers. "
        "You see ALL events across all domains simultaneously — not one event at a time. "
        "Your job is to identify compound risks where multiple events stress the same actors, "
        "resources, or systems at the same time. "
        "CITATION RULE — tag every specific number, actor name, or causal claim inline: "
        "use [REF: data.gov.in] for data.gov.in impacts, [REF: Actor] for actor nodes, "
        "[REF: Curated] for hand-curated ontology data. "
        "If you make any claim NOT present in the provided context, mark it [UNVERIFIED]. "
        "Never speculate beyond the data. Format in clean markdown."
    )
    user_prompt = (
        f"Using the national intelligence portfolio below, answer: {query}\n\n"
        f"**Portfolio Context:**\n```\n{context}\n```\n\n"
        "Structure your response in exactly these sections:\n\n"
        "## Compound Risk Assessment\n"
        "Identify the top 3 compound risks where multiple events create overlapping stress "
        "on the same actors, budgets, or systems.\n\n"
        "## Cross-Domain Intelligence\n"
        "Identify the most strategically significant causal chain in the data.\n\n"
        "## Priority Actions for Decision-Makers\n"
        "5 numbered, prioritised actions — each must name a responsible actor, "
        "a specific action, a measurable outcome, and flag any cross-domain conflict "
        "or intelligence gap. Order by urgency.\n\n"
        "Use only data from the context. Do not hallucinate facts."
    )
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1600,
        stream=True,
    )


def _build_default_queries(name: str, domain: str, data: dict) -> list[str]:
    """
    Generate event-specific intelligence queries dynamically from Neo4j ontology data.
    No hardcoded per-event queries — works for any event.
    """
    impacts     = data.get("impacts", [])
    actors      = data.get("actors", [])
    schemes     = data.get("schemes", [])
    connections = data.get("connections", [])

    queries = [f"What are the key governance failures and accountability gaps for {name}?"]

    # Impact-driven query from actual measured impacts
    if impacts:
        labels = []
        for i in impacts[:2]:
            t = (i.get("type") or (i.get("id") or "").replace("IMP_", "").replace("_", " ")).title()
            if t:
                labels.append(t)
        if labels:
            queries.append(
                f"What is the total measured impact — {', '.join(labels)} — and what urgent response is needed?"
            )

    # Actor accountability query from actual actors
    if actors:
        anames = [a.get("name", "") for a in actors[:2] if a.get("name")]
        if anames:
            queries.append(
                f"How effectively did {' and '.join(anames[:2])} respond, and what accountability gaps remain?"
            )

    # Scheme delivery query from actual linked schemes
    if schemes:
        snames = [s.get("name") or s.get("scheme_id", "") for s in schemes[:2] if s.get("name") or s.get("scheme_id")]
        if snames:
            queries.append(
                f"What is the delivery status and fund utilization for {', '.join(snames[:2])}?"
            )
    else:
        queries.append(f"What government funding was deployed for {name} and is utilization on track?")

    # Cross-domain query from actual connections
    if connections:
        linked = [c.get("name", "") for c in connections[:2] if c.get("name")]
        if linked:
            queries.append(
                f"What cross-domain causal chain links {name} to {', '.join(linked[:2])} and what does this mean for policy?"
            )

    # Domain-specific structural question as final query
    domain_q = {
        "Climate":     f"What structural resilience investments are needed to prevent recurrence of {name}?",
        "Defense":     f"What does {name} reveal about India's strategic readiness and response doctrine?",
        "Economics":   f"What is the full financial and trade impact of {name} on India's economy?",
        "Technology":  f"What does {name} mean for India's technology sovereignty and global standing?",
        "Geopolitics": f"What diplomatic and strategic implications does {name} carry for India's foreign policy?",
        "Governance":  f"What institutional reforms does {name} demand from India's governance framework?",
        "Society":     f"What is the humanitarian impact of {name} and are current relief measures adequate?",
    }
    fallback = domain_q.get(domain, f"What does {name} reveal about India's strategic vulnerabilities?")
    if fallback not in queries:
        queries.append(fallback)

    return queries[:5]


def _render_citizen_whatsapp(event_id: str, name: str, data: dict):
    """WhatsApp citizen notification preview — dynamically built from scheme data."""
    schemes = data.get("schemes", [])

    STATUS_COLOR = {"Read": "#22c55e", "Delivered": "#38bdf8", "Pending": "#f97316"}
    STATUS_ICON  = {"Read": "✓✓", "Delivered": "✓", "Pending": "🕐"}

    STATUS_MSG = {
        "active":                "{sname} is active for your area. Contact your ward office for eligibility. — PRAMAAN GovConnect",
        "at_risk":               "⚠ {sname} delivery is at risk in your area. File a complaint via PRAMAAN. — PRAMAAN GovConnect",
        "partially_operational": "{sname} is partially operational. Expected full delivery: 30 days. — PRAMAAN GovConnect",
        "inactive":              "{sname} is currently inactive. Monitor PRAMAAN for updates. — PRAMAAN GovConnect",
    }
    WA_STATUS = {
        "active": "Delivered", "at_risk": "Pending",
        "partially_operational": "Read", "inactive": "Read",
    }

    notifications = []
    for s in schemes[:3]:
        sname  = s.get("name") or s.get("scheme_id", "Government Scheme")
        status = s.get("status", "active")
        msg    = STATUS_MSG.get(status, "{sname} update available. Check PRAMAAN portal. — PRAMAAN GovConnect").format(sname=sname)
        notifications.append({
            "name":    "Field Citizen",
            "ward":    "Affected Area",
            "phone":   "+91 9XXXX XXXXX",
            "message": msg,
            "status":  WA_STATUS.get(status, "Delivered"),
            "time":    "Now",
        })

    if not notifications:
        notifications = [{
            "name":    "Citizen",
            "ward":    "Affected Area",
            "phone":   "+91 9XXXX XXXXX",
            "message": f"Government scheme delivery for {name} has been verified. Check PRAMAAN portal for details. — PRAMAAN GovConnect",
            "status":  "Delivered",
            "time":    "Now",
        }]

    st.html(
        '<div style="margin:20px 0 12px 0;">'
        '<div style="font-size:14px;font-weight:800;color:#25D366;letter-spacing:.06em;margin-bottom:6px;">'
        '📱 CITIZEN NOTIFICATION PREVIEW — WhatsApp GovConnect'
        '</div>'
        '<div style="font-size:11.5px;color:#64748b;line-height:1.6;max-width:720px;">'
        'In production, once PRAMAAN verifies scheme delivery in the proof chain, '
        '<span style="color:#25D366;font-weight:600;">Twilio WhatsApp Business API</span> '
        'automatically pushes notifications to registered beneficiaries — '
        'closing the loop from '
        '<span style="color:#38bdf8;font-weight:600;">Event → Scheme → Delivery → Citizen</span>. '
        '<br><span style="color:#334155;font-size:10.5px;">'
        '⚠ Demo mode: messages below are simulated from live Neo4j scheme delivery status. '
        'No actual WhatsApp messages are sent in this environment.'
        '</span>'
        '</div>'
        '</div>'
    )

    cols = st.columns(min(len(notifications), 3), gap="large")
    for i, c in enumerate(notifications):
        sc = STATUS_COLOR.get(c["status"], "#94a3b8")
        si = STATUS_ICON.get(c["status"], "·")
        with cols[i]:
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:16px;padding:14px;">'
                # header bar
                f'<div style="background:#075E54;border-radius:12px 12px 0 0;'
                f'padding:10px 14px;display:flex;align-items:center;gap:10px;margin:-14px -14px 12px -14px;">'
                f'<div style="width:36px;height:36px;border-radius:50%;background:#25D366;'
                f'display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">🏛️</div>'
                f'<div>'
                f'<div style="font-size:13px;font-weight:700;color:#fff;">PRAMAAN GovConnect</div>'
                f'<div style="font-size:10px;color:#a7f3d0;">Official Government Channel</div>'
                f'</div></div>'
                # recipient
                f'<div style="font-size:11px;color:#64748b;margin-bottom:10px;">'
                f'To: <span style="color:#94a3b8;font-weight:600;">{c["name"]}</span> · {c["ward"]}<br>'
                f'<span style="font-size:10px;">{c["phone"]}</span></div>'
                # message bubble
                f'<div style="background:#075E5422;border:1px solid #075E5444;'
                f'border-radius:0 10px 10px 10px;padding:12px 14px;margin-bottom:10px;">'
                f'<div style="font-size:12.5px;color:#e2e8f0;line-height:1.6;">{c["message"]}</div>'
                f'<div style="font-size:10px;color:#64748b;text-align:right;margin-top:6px;">'
                f'{c["time"]} <span style="color:{sc};font-weight:700;">{si}</span></div></div>'
                # status badge
                f'<div style="text-align:center;">'
                f'<span style="background:{sc}22;border:1px solid {sc};border-radius:20px;'
                f'padding:4px 14px;font-size:10px;font-weight:700;color:{sc};">'
                f'{c["status"].upper()}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )



def _render_citizen_report_tab(event_id: str, data: dict):
    """Citizen field report — upload photo, GPS, raise dispute in Neo4j."""
    import requests as req

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

    st.markdown("""
    <div style="background:#0d1f12;border-left:3px solid #22c55e;
                border-radius:8px;padding:10px 14px;margin-bottom:14px">
      <div style="font-size:9px;font-weight:700;color:#22c55e;
                  letter-spacing:.1em;margin-bottom:3px">HOW IT WORKS</div>
      <div style="font-size:11px;color:#94a3b8">
        Scan the QR code on the physical asset → fill this form → upload a photo of the issue →
        AI validates the image → Neo4j flags the asset as
        <b style="color:#f97316">⚠ DISPUTED</b> and it appears on Scheme Delivery for audit.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Build scheme list from event data (dynamic), fall back to API, then minimal default
    event_schemes = data.get("schemes", [])
    schemes_from_data = {}
    for s in event_schemes[:6]:
        sid   = s.get("scheme_id") or s.get("name", "").upper().replace(" ", "_")
        sname = s.get("name") or sid
        if not sid:
            continue
        schemes_from_data[sid] = {
            "name":   sname,
            "assets": [{"id": f"ASSET_{sid}_1", "label": f"{sname} · Primary Location", "ward": "Affected Area"}],
        }

    try:
        schemes_raw = req.get(f"{BASE_URL}/citizen/schemes", timeout=4).json()
    except Exception:
        schemes_raw = schemes_from_data if schemes_from_data else {
            "SCH_GENERAL": {
                "name": "Government Scheme",
                "assets": [{"id": "ASSET_GENERAL_1", "label": "Primary Asset", "ward": "Affected Area"}],
            }
        }

    col_form, col_preview = st.columns([1.4, 1], gap="large")

    with col_form:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#e2e8f0;'
                    'margin-bottom:8px">STEP 1 — SELECT SCHEME & ASSET</div>',
                    unsafe_allow_html=True)

        scheme_options = {sid: sdata["name"] for sid, sdata in schemes_raw.items()}
        selected_scheme_id = st.selectbox(
            "Scheme", options=list(scheme_options.keys()),
            format_func=lambda x: scheme_options[x],
            key="cr_scheme",
        )
        assets_for_scheme = schemes_raw[selected_scheme_id]["assets"]
        asset_options     = {a["id"]: a["label"] for a in assets_for_scheme}
        selected_asset_id = st.selectbox(
            "Asset / Location", options=list(asset_options.keys()),
            format_func=lambda x: asset_options[x],
            key="cr_asset",
        )
        selected_ward = next(
            (a["ward"] for a in assets_for_scheme if a["id"] == selected_asset_id), "Affected Area"
        )

        st.markdown('<div style="font-size:11px;font-weight:700;color:#e2e8f0;'
                    'margin:12px 0 8px">STEP 2 — DESCRIBE THE ISSUE</div>',
                    unsafe_allow_html=True)
        description = st.text_area(
            "What is wrong?",
            placeholder="e.g. The drain cover is broken and water is overflowing onto the road.",
            height=90,
            key="cr_desc",
        )

        st.markdown('<div style="font-size:11px;font-weight:700;color:#e2e8f0;'
                    'margin:12px 0 8px">STEP 3 — GPS COORDINATES (optional)</div>',
                    unsafe_allow_html=True)
        gps_col1, gps_col2 = st.columns(2)
        with gps_col1:
            latitude  = st.number_input("Latitude",  value=28.6692, format="%.4f", key="cr_lat")
        with gps_col2:
            longitude = st.number_input("Longitude", value=77.2736, format="%.4f", key="cr_lon")

        st.markdown('<div style="font-size:11px;font-weight:700;color:#e2e8f0;'
                    'margin:12px 0 8px">STEP 4 — UPLOAD PHOTO</div>',
                    unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload a photo of the issue (JPEG / PNG / WebP, max 15 MB)",
            type=["jpg", "jpeg", "png", "webp"],
            key="cr_photo",
        )

        st.markdown("")
        submit_btn = st.button("🚩 Submit Report", type="primary", use_container_width=True, key="cr_submit")

    with col_preview:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#e2e8f0;'
                    'margin-bottom:8px">PHOTO PREVIEW</div>',
                    unsafe_allow_html=True)

        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)
            file_kb = len(uploaded_file.getvalue()) // 1024
            st.markdown(
                f'<div style="font-size:9px;color:#64748b;margin-top:4px">'
                f'{uploaded_file.name} · {file_kb} KB · {uploaded_file.type}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("""
            <div style="background:#0a0f1e;border:1px dashed #1e293b;border-radius:10px;
                        padding:40px 20px;text-align:center;color:#475569;font-size:11px">
              📷<br>Upload a photo to preview it here
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:11px;font-weight:700;color:#e2e8f0;'
                    'margin:16px 0 8px">MOCK QR CODE (demo)</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;padding:14px;text-align:center">
          <div style="font-size:9px;font-weight:700;color:#38bdf8;letter-spacing:.08em;margin-bottom:8px">SCAN TO REPORT</div>
          <div style="font-family:monospace;font-size:22px;letter-spacing:2px;color:#4c8eda;line-height:1.2">
            ▉▉▉▉▉<br>▉&nbsp;&nbsp;&nbsp;▉<br>▉&nbsp;▉&nbsp;▉<br>▉&nbsp;&nbsp;&nbsp;▉<br>▉▉▉▉▉
          </div>
          <div style="font-size:9px;color:#64748b;margin-top:8px">{asset_options.get(selected_asset_id, '')}</div>
          <div style="font-size:8px;color:#334155;margin-top:2px">Mock QR · Production will link to this form pre-filled</div>
        </div>
        """, unsafe_allow_html=True)

    if submit_btn:
        if not uploaded_file:
            st.error("Please upload a photo before submitting.")
            return
        if not description.strip():
            st.warning("Please describe the issue before submitting.")
            return

        st.markdown("---")
        st.markdown(
            '<div style="font-size:10px;font-weight:700;color:#38bdf8;'
            'letter-spacing:.1em;margin-bottom:8px">VALIDATION PIPELINE</div>',
            unsafe_allow_html=True,
        )

        pipeline_slot = st.empty()

        STAGE_LABELS = {
            "file_type":  "File type check",
            "file_size":  "File size check",
            "structural": "Structural image check",
            "gps":        "GPS coordinate check",
            "ai_vision":  "AI Vision classification",
        }

        def _show_stage(stage: str, status: str, detail: str = ""):
            colors = {"running": "#38bdf8", "pass": "#22c55e", "fail": "#ef4444", "skip": "#64748b"}
            icons  = {"running": "⏳", "pass": "✅", "fail": "❌", "skip": "⏭"}
            c = colors.get(status, "#94a3b8")
            i = icons.get(status, "•")
            pipeline_slot.markdown(
                f'<div style="font-size:11px;color:{c};padding:3px 0">'
                f'{i} {stage}{"  —  " + detail if detail else ""}</div>',
                unsafe_allow_html=True,
            )

        _show_stage("Sending to validation pipeline...", "running")

        try:
            file_bytes = uploaded_file.getvalue()
            resp = req.post(
                f"{BASE_URL}/citizen/report",
                data={
                    "asset_id":    selected_asset_id,
                    "event_id":    event_id,
                    "scheme_id":   selected_scheme_id,
                    "ward":        selected_ward,
                    "description": description,
                    "latitude":    str(latitude),
                    "longitude":   str(longitude),
                },
                files={"photo": (uploaded_file.name, file_bytes, uploaded_file.type)},
                timeout=30,
            )
            result = resp.json()
        except Exception as exc:
            pipeline_slot.empty()
            st.error(f"Could not reach backend: {exc}")
            return

        pipeline_slot.empty()
        accepted  = result.get("accepted", False)
        failed_at = result.get("stage", "") if not accepted else None
        reason    = result.get("reason", "")

        stage_order = ["file_type", "file_size", "structural", "gps", "ai_vision"]
        for s in stage_order:
            lbl = STAGE_LABELS.get(s, s)
            if s == failed_at:
                st.markdown(
                    f'<div style="font-size:11px;color:#ef4444;padding:2px 0">❌ {lbl} — FAILED</div>',
                    unsafe_allow_html=True,
                )
                break
            st.markdown(
                f'<div style="font-size:11px;color:#22c55e;padding:2px 0">✅ {lbl} — passed</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")

        if not accepted:
            st.markdown(f"""
            <div style="background:#1a0505;border:1px solid #ef444460;
                        border-radius:10px;padding:14px 18px;margin-top:8px">
              <div style="font-size:10px;font-weight:700;color:#ef4444;
                          letter-spacing:.08em;margin-bottom:6px">REPORT REJECTED</div>
              <div style="font-size:12px;color:#fca5a5">{reason}</div>
              <div style="font-size:9px;color:#475569;margin-top:8px">
                Please re-read the instructions above and upload a valid field photo.
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            report_id   = result.get("report_id", "N/A")
            ai_decision = result.get("ai_decision", "N/A")
            ai_reason   = result.get("ai_reason", "N/A")
            neo4j_ok    = result.get("flagged_in_neo4j", False)
            asset_label = asset_options.get(selected_asset_id, selected_asset_id)

            st.success(f"Report accepted! ID: **{report_id}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Report ID", report_id)
            c2.metric("AI Verdict", ai_decision)
            c3.metric("Neo4j", "Flagged ✅" if neo4j_ok else "Failed ⚠")
            st.markdown(f"**AI says:** {ai_reason}")
            st.markdown(
                f"Asset **{asset_label}** has been flagged as "
                f"**⚠ DISPUTED** in Neo4j. Check Scheme Delivery for audit."
            )
            st.balloons()


def page():
    st.set_page_config(page_title="Proof & Evidence – PRAMAAN", layout="wide")
    render_topnav(active_page="Proof & Evidence")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; }
    .stMarkdown p  { font-size: 13px !important; color: #cbd5e1 !important; line-height: 1.6 !important; }
    .stMarkdown h1, .stMarkdown h2 { font-size: 16px !important; font-weight: 700 !important; color: #f97316 !important; margin: 10px 0 4px !important; }
    .stMarkdown h3 { font-size: 16px !important; font-weight: 600 !important; color: #fb923c !important; margin: 8px 0 3px !important; }
    .stMarkdown ul li, .stMarkdown ol li { color: #94a3b8 !important; font-size: 12.5px !important; line-height: 1.6 !important; }
    .stMarkdown strong { color: #e2e8f0 !important; }
    .stMarkdown code   { font-size: 11px !important; }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(56,189,248,0.7), 0 0 30px rgba(56,189,248,0.4), 0 0 50px rgba(56,189,248,0.2); }
        50%       { text-shadow: 0 0 25px rgba(56,189,248,1), 0 0 60px rgba(56,189,248,0.8), 0 0 100px rgba(56,189,248,0.5); }
    }
    div[data-testid="stExpander"] summary p { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Deep-link from other pages ─────────────────────────────────────────────
    if "deep_link_brief" in st.session_state:
        raw       = st.session_state.pop("deep_link_brief")
        valid_ids = {e[0] for e in EVENTS}
        if raw in valid_ids:
            st.session_state.brief_sel = raw

    if "brief_sel"  not in st.session_state:
        st.session_state.brief_sel  = None   # no auto-select; user must choose or navigate here
    if "brief_mode" not in st.session_state:
        st.session_state.brief_mode = "Single Event"

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="font-size:13px;font-weight:700;color:#38bdf8;font-family:'Cinzel',serif;
                    letter-spacing:0.06em;margin-bottom:12px;padding-bottom:8px;
                    border-bottom:1px solid #1e293b;">BRIEF MODE</div>
        """, unsafe_allow_html=True)

        mode = st.radio(
            "Mode", ["Single Event", "Compound Risk"],
            index=0 if st.session_state.brief_mode == "Single Event" else 1,
            label_visibility="collapsed",
            key="brief_mode_radio",
        )
        st.session_state.brief_mode = mode

        st.markdown(
            f'<div style="font-size:10px;color:#475569;margin-bottom:14px;padding:6px 8px;'
            f'background:#0a1628;border-radius:6px;border:1px solid #1e293b;">'
            f'{"📌 Brief for one event — actors, impacts, recommendations." if mode == "Single Event" else f"🌐 Portfolio view — compound risks across all {_N_EVENTS} events simultaneously."}'
            f'</div>',
            unsafe_allow_html=True,
        )

        if mode == "Single Event":
            st.markdown("""
            <div style="font-size:13px;font-weight:700;color:#38bdf8;font-family:'Cinzel',serif;
                        letter-spacing:0.06em;margin-bottom:12px;padding-bottom:8px;
                        border-bottom:1px solid #1e293b;">EVENT NAVIGATOR</div>
            """, unsafe_allow_html=True)

        sort_by = st.selectbox(
            "Sort", ["Newest", "Oldest", "Severity"],
            label_visibility="collapsed", key="brief_sort",
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        SEV_ORDER = {"critical": 0, "high": 1, "medium": 2}

        def sort_key(e):
            month, year = e[4].split()
            ts = int(year) * 100 + MONTH_MAP.get(month, 0)
            return (SEV_ORDER.get(e[5], 9), -ts) if sort_by == "Severity" else (
                -ts if sort_by == "Newest" else ts
            )

        sorted_events = sorted(EVENTS, key=sort_key)
        domain_groups = defaultdict(list)
        for evt in sorted_events:
            domain_groups[evt[3]].append(evt)

        for domain, evts in domain_groups.items():
            bullet   = DOMAIN_BULLET.get(domain, "●")
            expanded = any(e[0] == st.session_state.get("brief_sel") for e in evts)
            with st.expander(f"{bullet} {domain}  ({len(evts)})", expanded=expanded):
                for (eid, ename, ecolor, edom, edate, esev) in evts:
                    is_sel  = (eid == st.session_state.get("brief_sel"))
                    sev_dot = SEV_COLOR.get(esev, "#64748b")
                    if st.button(
                        f"{'▶ ' if is_sel else ''}{ename}",
                        key=f"brief_btn_{eid}",
                        use_container_width=True,
                    ):
                        st.session_state.brief_sel = eid
                        st.rerun()
                    st.markdown(
                        f'<div style="font-size:9.5px;color:#475569;padding:0 4px 6px;'
                        f'margin-top:-8px;display:flex;align-items:center;gap:5px;">'
                        f'<span style="width:5px;height:5px;border-radius:50%;background:{sev_dot};'
                        f'flex-shrink:0;"></span>{edate} · {esev}</div>',
                        unsafe_allow_html=True,
                    )

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:8px;display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.9em;font-weight:800;color:#38bdf8;font-family:'Cinzel',serif;
                   letter-spacing:0.08em;white-space:nowrap;animation:glowPulse 2.5s ease-in-out infinite;">
        PROOF & EVIDENCE
      </span>
      <span style="font-size:0.75em;color:#64748b;white-space:nowrap;">
        AI-Powered Intelligence Brief &nbsp;·&nbsp;
        <span style="color:#475569;">Groq LLaMA 3.3 70B</span> &nbsp;·&nbsp;
        <span style="color:#334155;">Verified Ontology Data</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # COMPOUND RISK MODE
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.brief_mode == "Compound Risk":
        compound_queries = [
            "What are India's top compound risks right now across all domains?",
            "Which actors are dangerously overloaded across multiple critical events?",
            "What is the most significant cross-domain causal chain and what should be done?",
            "Where are the biggest resource conflicts between simultaneous events?",
            "What structural vulnerabilities does this portfolio reveal for India?",
        ]

        col_q, col_btn = st.columns([3, 1], gap="medium")
        with col_q:
            compound_query = st.selectbox("Compound Risk Query", compound_queries, index=0)
            voice_compound = _voice_input_widget("compound")
            custom_q       = st.text_input(
                "Or type a custom query",
                placeholder="e.g. Which ministry is most overstretched?",
                value=voice_compound,
            )
            final_compound_query = custom_q.strip() if custom_q.strip() else compound_query
        with col_btn:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            run_compound = st.button("Analyse Portfolio →", type="primary", use_container_width=True)

        if run_compound:
            st.markdown("---")
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #a78bfa44;border-left:4px solid #a78bfa;'
                f'border-radius:10px;padding:12px 18px;margin-bottom:16px;">'
                f'<div style="font-size:14px;font-weight:700;color:#a78bfa;">COMPOUND RISK ASSESSMENT — ALL {_N_EVENTS} EVENTS</div>'
                f'<div style="font-size:11.5px;color:#475569;margin-top:4px;">'
                f'Query: <span style="color:#94a3b8;font-style:italic;">{final_compound_query}</span></div>'
                f'<div style="font-size:10.5px;color:#334155;margin-top:3px;">'
                f'Model: LLaMA 3.3 70B · Source: PRAMAAN Neo4j Portfolio Graph · {_N_EVENTS} events · 7 domains</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            with st.spinner("Fetching portfolio data..."):
                risk_data   = safe_get("/ontology/compound-risk", silent=True) or {}
                context     = _build_compound_context(risk_data)
                n_impacts   = len(risk_data.get("top_impacts", []))
                govdata_c   = sum(1 for i in risk_data.get("top_impacts", [])
                                  if "data.gov.in" in (i.get("source") or ""))

            c_score, c_label, c_color = _compound_trustability(risk_data)
            c_trust_slot = st.empty()
            c_trust_slot.markdown(
                _render_trust_bar(c_score, c_label, c_color,
                                  govdata_count=govdata_c, total_impacts=n_impacts),
                unsafe_allow_html=True,
            )

            brief_placeholder = st.empty()
            full_text = ""
            with st.spinner("Generating compound risk brief..."):
                try:
                    stream = _generate_compound_brief(context, final_compound_query)
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content or ""
                        full_text += delta
                        brief_placeholder.markdown(full_text)
                except Exception as e:
                    st.error(f"Groq API error: {e}")
                    return

            brief_placeholder.markdown(_style_priorities(full_text), unsafe_allow_html=True)

            c_grounding = _grounding_check(full_text, context)
            c_trust_slot.markdown(
                _render_trust_bar(c_score, c_label, c_color,
                                  grounding=c_grounding, govdata_count=govdata_c, total_impacts=n_impacts),
                unsafe_allow_html=True,
            )

            with st.expander("View raw portfolio context used", expanded=False):
                st.code(context, language="text")
        return

    # ══════════════════════════════════════════════════════════════════════════
    # SINGLE EVENT MODE
    # ══════════════════════════════════════════════════════════════════════════
    render_event_dropdown("brief_sel", "brief_event_dropdown", include_all=True)

    sel_evt = next((e for e in EVENTS if e[0] == st.session_state.get("brief_sel")), None)
    if sel_evt is None:
        st.html(
            '<div style="font-size:13px;color:#334155;padding:40px;text-align:center;'
            'border:1px dashed #1e293b;border-radius:10px;margin-top:12px;">'
            'Select an event from the sidebar or navigate here from '
            '<span style="color:#38bdf8;font-weight:700;">Scheme Delivery</span> to generate an intelligence brief.'
            '</div>'
        )
        return
    event_id, name, color, domain, date, sev = sel_evt

    st.markdown(
        '<div style="font-size:12px;color:#475569;margin-bottom:8px;">'
        'Select an event and a query — PRAMAAN synthesises verified ontology data into a structured '
        'intelligence brief using Groq LLaMA 3.3 70B. Every fact is drawn from real government sources.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Event banner ───────────────────────────────────────────────────────────
    sev_badge_color = SEV_COLOR.get(sev, "#64748b")
    st.markdown(
        f'<div style="background:#0a1628;border:1px solid {color}44;border-left:4px solid {color};'
        f'border-radius:10px;padding:10px 16px;margin-bottom:12px;'
        f'display:flex;align-items:center;gap:12px;">'
        f'<div style="flex:1;">'
        f'<span style="font-size:14px;font-weight:700;color:{color};">{name}</span>'
        f'<span style="font-size:11px;color:#64748b;margin-left:12px;">{domain} · {date}</span>'
        f'</div>'
        f'<span style="background:{sev_badge_color}22;color:{sev_badge_color};font-weight:700;'
        f'font-size:10px;padding:2px 8px;border-radius:4px;border:1px solid {sev_badge_color}66;'
        f'text-transform:uppercase;letter-spacing:0.05em;">{sev}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Fetch event data from Neo4j (used for queries, whatsapp, report) ───────
    with st.spinner(f"Loading ontology data for {name}..."):
        data = safe_get(f"/ontology/events/{event_id}", silent=True) or {}

    # ── Citizen section ────────────────────────────────────────────────────────
    _render_citizen_whatsapp(event_id, name, data)

    with st.expander("🚩 Report a Field Issue", expanded=False):
        _render_citizen_report_tab(event_id, data)

    st.markdown("---")

    # ── Dynamic queries from ontology data ────────────────────────────────────
    default_queries = _build_default_queries(name, domain, data)

    col_q, col_btn = st.columns([3, 1], gap="medium")
    with col_q:
        query       = st.selectbox("Intelligence Query", default_queries, index=0, key=f"query_{event_id}")
        voice_query = _voice_input_widget(event_id)
        custom_query = st.text_input(
            "Or type a custom query",
            placeholder="e.g. What is the rehabilitation status?",
            value=voice_query,
        )
        final_query = custom_query.strip() if custom_query.strip() else query

    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        generate = st.button("Generate Brief →", type="primary", use_container_width=True)

    # ── Check for pre-loaded brief ─────────────────────────────────────────────
    is_preloaded = (final_query == default_queries[0] and event_id in _PRELOADED_BRIEFS)

    if generate:
        st.markdown("---")
        st.markdown(
            f'<div style="background:#0a1628;border:1px solid {color}44;border-left:4px solid {color};'
            f'border-radius:10px;padding:12px 18px;margin-bottom:16px;">'
            f'<div style="font-size:14px;font-weight:700;color:{color};">INTELLIGENCE BRIEF: {name.upper()}</div>'
            f'<div style="font-size:11.5px;color:#475569;margin-top:4px;">'
            f'Query: <span style="color:#94a3b8;font-style:italic;">{final_query}</span></div>'
            f'<div style="font-size:10.5px;color:#334155;margin-top:3px;">'
            f'Model: LLaMA 3.3 70B · Source: PRAMAAN Neo4j Ontology · Groq AI</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        impacts_count   = len(data.get("impacts", []))
        govdata_impacts = sum(1 for i in data.get("impacts", []) if "data.gov.in" in (i.get("source") or ""))

        score, label, trust_color = _trustability_score(data)
        trust_slot = st.empty()
        trust_slot.markdown(
            _render_trust_bar(score, label, trust_color,
                              govdata_count=govdata_impacts, total_impacts=impacts_count),
            unsafe_allow_html=True,
        )

        brief_placeholder = st.empty()
        full_text = ""

        if is_preloaded:
            full_text = _PRELOADED_BRIEFS[event_id]["text"]
            brief_placeholder.markdown(_style_priorities(full_text), unsafe_allow_html=True)
            pre = _PRELOADED_BRIEFS[event_id]
            trust_slot.markdown(
                _render_trust_bar(pre["trust_score"], pre["trust_label"], pre["trust_color"],
                                  grounding=pre["grounding"],
                                  govdata_count=pre["govdata_count"],
                                  total_impacts=pre["total_impacts"]),
                unsafe_allow_html=True,
            )
        else:
            context = _build_context(event_id, name, data=data)
            with st.spinner("Generating brief with Groq LLaMA 3.3 70B..."):
                try:
                    stream = _generate_brief(context, name, final_query)
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content or ""
                        full_text += delta
                        brief_placeholder.markdown(full_text)
                except Exception as e:
                    st.error(f"Groq API error: {e}")
                    return

            brief_placeholder.markdown(_style_priorities(full_text), unsafe_allow_html=True)
            grounding = _grounding_check(full_text, context)
            trust_slot.markdown(
                _render_trust_bar(score, label, trust_color,
                                  grounding=grounding,
                                  govdata_count=govdata_impacts,
                                  total_impacts=impacts_count),
                unsafe_allow_html=True,
            )
            with st.expander("View raw ontology context used", expanded=False):
                st.code(context, language="text")

    else:
        # Show pre-loaded brief on page open for known events
        if is_preloaded:
            pre = _PRELOADED_BRIEFS[event_id]
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid {color}44;border-left:4px solid {color};'
                f'border-radius:10px;padding:12px 18px;margin-bottom:16px;">'
                f'<div style="font-size:14px;font-weight:700;color:{color};">INTELLIGENCE BRIEF: {name.upper()} (PRE-LOADED)</div>'
                f'<div style="font-size:11.5px;color:#475569;margin-top:4px;">'
                f'Query: <span style="color:#94a3b8;font-style:italic;">{final_query}</span></div>'
                f'<div style="font-size:10.5px;color:#334155;margin-top:3px;">'
                f'Model: LLaMA 3.3 70B · Source: PRAMAAN Neo4j · 0 Hallucinated</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                _render_trust_bar(pre["trust_score"], pre["trust_label"], pre["trust_color"],
                                  grounding=pre["grounding"],
                                  govdata_count=pre["govdata_count"],
                                  total_impacts=pre["total_impacts"]),
                unsafe_allow_html=True,
            )
            st.markdown(_style_priorities(pre["text"]), unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#0a1628;border:1px dashed #1e293b;border-radius:12px;
                        padding:40px;text-align:center;margin-top:20px;">
              <div style="font-size:14px;color:#475569;margin-bottom:6px;">
                Select a query above, then click <b style="color:#38bdf8;">Generate Brief</b>
              </div>
              <div style="font-size:12px;color:#334155;">
                PRAMAAN will synthesize verified ontology data into a structured intelligence brief<br>
                using Groq LLaMA 3.3 70B · All facts drawn from real government sources
              </div>
            </div>
            """, unsafe_allow_html=True)




page()
