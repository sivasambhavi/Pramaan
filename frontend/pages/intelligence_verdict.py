"""
intelligence_verdict.py — PRAMAAN Intelligence Verdict

On-demand AI verdict across the full graph state.
Answers: What should India decide today? Where is it exposed? Where is the advantage?
"""

import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests as _req
from datetime import datetime
from components.topnav import render_topnav

API_BASE   = os.environ.get("PRAMAAN_API_URL", "http://localhost:8000")
GROQ_KEY   = os.environ.get("GROQ_API_KEY", "")

try:
    from groq import Groq as _Groq
    _GROQ_OK = bool(GROQ_KEY)
except ImportError:
    _GROQ_OK = False

_URG_COLOR  = {"48h": "#ef4444", "30d": "#f97316", "6m": "#facc15"}
_URG_LABEL  = {"48h": "URGENT — 48 HOURS", "30d": "SHORT-TERM — 30 DAYS", "6m": "STRUCTURAL — 6 MONTHS"}
_RISK_COLOR = {"critical": "#ef4444", "high": "#f97316", "medium": "#facc15", "low": "#22c55e"}
_DOM_ICON   = {
    "Economics": "📈", "Defense": "🛡", "Geopolitics": "🌐",
    "Climate": "🌿", "Society": "👥", "Governance": "🏛", "Technology": "⚡",
}


# ── LLM ───────────────────────────────────────────────────────────────────────

def _build_context(data: dict) -> str:
    lines = []

    events = data.get("events", [])
    if events:
        lines.append("=== ACTIVE EVENTS (high/critical) ===")
        for e in events:
            lines.append(
                f"[{e.get('severity','').upper()}] {e.get('name','')} | "
                f"Domain: {e.get('domain','')} | Region: {e.get('region','')} | "
                f"Date: {e.get('date','')} | {e.get('description','')[:200]}"
            )

    connections = data.get("connections", [])
    if connections:
        lines.append("\n=== CROSS-DOMAIN CONNECTIONS ===")
        for c in connections:
            lines.append(
                f"{c.get('from_event','')} → {c.get('to_event','')} | "
                f"Reason: {c.get('reason','')} | Strength: {c.get('strength','')}"
            )

    indicators = data.get("indicators", [])
    if indicators:
        lines.append("\n=== LIVE INDICATORS ===")
        for i in indicators:
            lines.append(
                f"{i.get('name','')} = {i.get('value','')} {i.get('unit','')} | Trend: {i.get('trend','')}"
            )

    impacts = data.get("impacts", [])
    if impacts:
        lines.append("\n=== KEY IMPACTS ===")
        for i in impacts:
            lines.append(
                f"[{i.get('severity','').upper()}] {i.get('impact','')} | "
                f"Domain: {i.get('domain','')} | From: {i.get('event','')}"
            )

    schemes = data.get("schemes", [])
    if schemes:
        lines.append("\n=== ACTIVE SCHEMES ===")
        for s in schemes:
            triggered = ", ".join(s.get("triggered_by", [])) or "none"
            lines.append(
                f"{s.get('name','')} | Budget: ₹{s.get('budget','')} Cr | "
                f"Status: {s.get('status','')} | Triggered by: {triggered}"
            )

    return "\n".join(lines)


def _call_groq(context: str) -> dict:
    client = _Groq(api_key=GROQ_KEY)

    system = (
        "You are PRAMAAN — India's AI governance intelligence engine. "
        "You have access to a live ontology graph of geopolitical, economic, defense, climate, "
        "society, and governance events. Your role is to synthesise this into a crisp, "
        "actionable intelligence verdict for India's senior decision-makers. "
        "Be direct, specific, and evidence-driven. No generic advice. "
        "Every claim must be traceable to the provided context data. "
        "Respond ONLY with valid JSON — no markdown fences, no explanation outside the JSON."
    )

    user = f"""
Given this live graph state from PRAMAAN's ontology engine:

{context}

Generate an Intelligence Verdict as a JSON object with exactly this structure:
{{
  "decisions": [
    {{
      "priority": 1,
      "title": "short title of the decision",
      "urgency": "48h",
      "actor": "named responsible body",
      "action": "specific executable action",
      "evidence": "cite the specific event/indicator/impact driving this",
      "consequence": "what happens if India delays by 30 days"
    }}
  ],
  "exposures": [
    {{
      "domain": "domain name",
      "risk": "critical",
      "headline": "one sentence on what India is exposed to",
      "events": ["event name 1", "event name 2"],
      "compound_effect": "what the combination of these events means for India specifically"
    }}
  ],
  "advantages": [
    {{
      "title": "opportunity title",
      "window": "how long this window is open",
      "action": "what India should do to capture it",
      "rationale": "why this is an advantage right now given the graph context"
    }}
  ],
  "one_line": "single sentence verdict — the most important thing India must do today"
}}

Rules:
- decisions: exactly 3, ordered by urgency (48h first)
- exposures: 3–5 domains where India is most at risk RIGHT NOW
- advantages: 2–3 strategic windows India can exploit
- Use only data from the context. No hallucination. Be specific about India's position.
"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.25,
        max_tokens=1800,
    )
    raw = resp.choices[0].message.content.strip()
    # Strip markdown fences if model adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ── Page ──────────────────────────────────────────────────────────────────────

def page():
    st.set_page_config(page_title="Intelligence Verdict – PRAMAAN", layout="wide")
    render_topnav(active_page="Intelligence Verdict")

    st.markdown("""
    <style>
    html, body, [class*="css"] { background-color: #020b14 !important; color: #e2e8f0 !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0 !important; min-height: 0 !important; }
    button[data-baseweb="tab"] { font-size: 11px !important; padding: 6px 12px !important; }
    @keyframes goldPulse {
        0%, 100% { text-shadow: 0 0 10px rgba(250,204,21,0.6), 0 0 30px rgba(250,204,21,0.3); }
        50%       { text-shadow: 0 0 25px rgba(250,204,21,1),   0 0 60px rgba(250,204,21,0.6); }
    }
    </style>
    """, unsafe_allow_html=True)

    if not _GROQ_OK:
        st.error("GROQ_API_KEY not set — cannot generate verdict.")
        return

    # ── Page header row ───────────────────────────────────────────────────────
    hcol, bcol = st.columns([3, 1], gap="small")
    with hcol:
        st.markdown(
            '<div style="padding:6px 0 4px;border-bottom:1px solid #1e293b;margin-bottom:6px;'
            'display:flex;align-items:center;gap:14px;">'
            '<span style="font-size:1.9em;font-weight:800;color:#facc15;'
            'font-family:\'Cinzel\',serif;letter-spacing:0.08em;white-space:nowrap;'
            'animation:goldPulse 2.5s ease-in-out infinite;">'
            'INTELLIGENCE VERDICT'
            '</span>'
            '<span style="font-size:0.75em;color:#64748b;white-space:nowrap;">'
            'Live graph state &nbsp;·&nbsp; AI synthesis &nbsp;·&nbsp; '
            'Strategic decisions for India'
            '</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with bcol:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        generate = st.button(
            "Generate Verdict",
            key="gen_verdict",
            type="primary",
            use_container_width=True,
        )

    if generate:
        with st.spinner("Querying live graph state..."):
            try:
                r = _req.get(f"{API_BASE}/verdict/context", timeout=15)
                ctx_data = r.json() if r.status_code == 200 else {}
            except Exception as ex:
                st.error(f"Failed to fetch graph context: {ex}")
                return

        context_str = _build_context(ctx_data)

        with st.spinner("Synthesising verdict with Groq LLaMA 3.3 70B..."):
            try:
                verdict = _call_groq(context_str)
                verdict["_generated_at"] = datetime.now().strftime("%d %b %Y, %H:%M IST")
                verdict["_event_count"]  = len(ctx_data.get("events", []))
                verdict["_conn_count"]   = len(ctx_data.get("connections", []))
                st.session_state["verdict"] = verdict
            except json.JSONDecodeError as ex:
                st.error(f"LLM returned malformed JSON: {ex}")
                return
            except Exception as ex:
                st.error(f"Groq error: {ex}")
                return

    verdict = st.session_state.get("verdict")
    if not verdict:
        st.markdown(
            '<div style="background:#060f1e;border:1px dashed #1e293b;border-radius:10px;'
            'padding:32px 20px;text-align:center;margin-top:12px;">'
            '<div style="font-size:11px;color:#334155;line-height:1.7;">'
            'Click <b style="color:#f97316;">Generate Verdict</b> to synthesise the full '
            'live graph state into strategic decisions, national exposure, and advantage windows.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── One-line verdict + meta ───────────────────────────────────────────────
    gen_at = verdict.get("_generated_at", "")
    ev_cnt = verdict.get("_event_count", 0)
    cn_cnt = verdict.get("_conn_count", 0)
    one_line = verdict.get("one_line", "")
    if one_line:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#1a0a00,#0d1628);'
            f'border:1px solid #f9731633;border-left:4px solid #f97316;'
            f'border-radius:10px;padding:12px 16px;margin-bottom:14px;">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;">'
            f'<div>'
            f'<div style="font-size:9px;font-weight:700;color:#f97316;letter-spacing:.1em;'
            f'text-transform:uppercase;margin-bottom:4px;">VERDICT</div>'
            f'<div style="font-size:13px;font-weight:600;color:#f1f5f9;line-height:1.5;">'
            f'{one_line}</div>'
            f'</div>'
            f'<div style="text-align:right;flex-shrink:0;margin-left:20px;">'
            f'<div style="font-size:9px;color:#334155;">{gen_at}</div>'
            f'<div style="font-size:9px;color:#334155;">{ev_cnt} events · {cn_cnt} connections</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── Three sections ────────────────────────────────────────────────────────
    col_dec, col_exp, col_adv = st.columns([1.1, 1, 0.9], gap="medium")

    # ── Section 1: Strategic Decisions ───────────────────────────────────────
    with col_dec:
        st.markdown(
            '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:.12em;margin-bottom:10px;">⚡ STRATEGIC DECISIONS</div>',
            unsafe_allow_html=True,
        )
        for dec in verdict.get("decisions", []):
            urg   = dec.get("urgency", "30d")
            uc    = _URG_COLOR.get(urg, "#94a3b8")
            ulbl  = _URG_LABEL.get(urg, urg.upper())
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid {uc}33;'
                f'border-left:4px solid {uc};border-radius:10px;'
                f'padding:12px 14px;margin-bottom:10px;">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                f'<span style="background:{uc}22;color:{uc};font-size:8px;font-weight:700;'
                f'padding:2px 7px;border-radius:4px;text-transform:uppercase;'
                f'letter-spacing:.06em;white-space:nowrap;">{ulbl}</span>'
                f'<span style="font-size:9px;color:#334155;">Priority {dec.get("priority","")}</span>'
                f'</div>'
                f'<div style="font-size:13px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">'
                f'{dec.get("title","")}</div>'
                f'<div style="font-size:10px;color:#64748b;margin-bottom:4px;">'
                f'<span style="color:#475569;">Actor:</span> {dec.get("actor","")}</div>'
                f'<div style="font-size:10px;color:#94a3b8;margin-bottom:6px;line-height:1.5;">'
                f'{dec.get("action","")}</div>'
                f'<div style="background:#0a1628;border-radius:6px;padding:7px 10px;">'
                f'<div style="font-size:9px;color:#475569;margin-bottom:3px;">EVIDENCE</div>'
                f'<div style="font-size:9.5px;color:#64748b;line-height:1.4;">'
                f'{dec.get("evidence","")}</div>'
                f'</div>'
                f'<div style="margin-top:6px;font-size:9px;color:#ef4444;line-height:1.4;">'
                f'⚠ If delayed: {dec.get("consequence","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Section 2: National Exposure ─────────────────────────────────────────
    with col_exp:
        st.markdown(
            '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:.12em;margin-bottom:10px;">🎯 NATIONAL EXPOSURE</div>',
            unsafe_allow_html=True,
        )
        for exp in verdict.get("exposures", []):
            dom   = exp.get("domain", "")
            risk  = exp.get("risk", "medium")
            rc    = _RISK_COLOR.get(risk, "#94a3b8")
            icon  = _DOM_ICON.get(dom, "●")
            evts  = exp.get("events", [])
            evts_html = " · ".join(
                f'<span style="color:{rc}88;font-size:8px;">{e}</span>' for e in evts
            )
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid {rc}22;'
                f'border-radius:10px;padding:11px 13px;margin-bottom:8px;">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'margin-bottom:5px;">'
                f'<span style="font-size:13px;font-weight:700;color:#f1f5f9;">'
                f'{icon} {dom}</span>'
                f'<span style="background:{rc}22;color:{rc};font-size:8px;font-weight:700;'
                f'padding:2px 7px;border-radius:4px;text-transform:uppercase;">{risk}</span>'
                f'</div>'
                f'<div style="font-size:10px;color:#94a3b8;line-height:1.5;margin-bottom:5px;">'
                f'{exp.get("headline","")}</div>'
                f'<div style="font-size:9px;color:#334155;margin-bottom:4px;">{evts_html}</div>'
                f'<div style="font-size:9.5px;color:#64748b;background:#0a1628;'
                f'border-radius:5px;padding:5px 8px;line-height:1.4;">'
                f'{exp.get("compound_effect","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Section 3: Strategic Advantages ──────────────────────────────────────
    with col_adv:
        st.markdown(
            '<div style="font-size:9px;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:.12em;margin-bottom:10px;">🚀 ADVANTAGE WINDOWS</div>',
            unsafe_allow_html=True,
        )
        for adv in verdict.get("advantages", []):
            st.markdown(
                f'<div style="background:#060f1e;border:1px solid #22c55e22;'
                f'border-left:4px solid #22c55e;border-radius:10px;'
                f'padding:12px 14px;margin-bottom:10px;">'
                f'<div style="font-size:12px;font-weight:700;color:#22c55e;margin-bottom:4px;">'
                f'{adv.get("title","")}</div>'
                f'<div style="font-size:9px;color:#475569;margin-bottom:6px;">'
                f'⏱ Window: {adv.get("window","")}</div>'
                f'<div style="font-size:10px;color:#94a3b8;line-height:1.5;margin-bottom:6px;">'
                f'{adv.get("action","")}</div>'
                f'<div style="font-size:9.5px;color:#64748b;background:#0a1628;'
                f'border-radius:5px;padding:5px 8px;line-height:1.4;">'
                f'{adv.get("rationale","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


page()
