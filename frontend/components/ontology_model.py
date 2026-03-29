"""
components/ontology_model.py — PRAMAAN
Shared ontology knowledge model schema widget — same design as the original
right-panel card, surfaced as a collapsed expander at the bottom of any page.

Usage:
    from components.ontology_model import render_ontology_model
    render_ontology_model()
"""
import streamlit as st

_HTML = """
<div style="padding:9px 11px;background:#060f1e;
            border:1px solid #1e293b;border-radius:8px;">
  <div style="font-size:8px;color:#475569;margin-bottom:4px;font-weight:600;letter-spacing:.06em;">
    ENTITY TYPES
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px;">
    <span style="background:#0a1f2e;border:1px solid #38bdf844;color:#38bdf8;font-size:8px;padding:1px 6px;border-radius:10px;">Event</span>
    <span style="background:#0a1f2e;border:1px solid #22c55e44;color:#22c55e;font-size:8px;padding:1px 6px;border-radius:10px;">Region</span>
    <span style="background:#0a1f2e;border:1px solid #a78bfa44;color:#a78bfa;font-size:8px;padding:1px 6px;border-radius:10px;">Actor</span>
    <span style="background:#0a1f2e;border:1px solid #fb718544;color:#fb7185;font-size:8px;padding:1px 6px;border-radius:10px;">Beneficiary</span>
    <span style="background:#0a1f2e;border:1px solid #facc1544;color:#facc15;font-size:8px;padding:1px 6px;border-radius:10px;">Asset</span>
    <span style="background:#0a1f2e;border:1px solid #06b6d444;color:#06b6d4;font-size:8px;padding:1px 6px;border-radius:10px;">Scheme</span>
    <span style="background:#0a1f2e;border:1px solid #f97316;color:#f97316;font-size:8px;padding:1px 6px;border-radius:10px;">Policy</span>
    <span style="background:#0a1f2e;border:1px solid #e879f944;color:#e879f9;font-size:8px;padding:1px 6px;border-radius:10px;">Evidence</span>
    <span style="background:#0a1f2e;border:1px solid #f4364444;color:#f43f5e;font-size:8px;padding:1px 6px;border-radius:10px;">Impact</span>
    <span style="background:#0a1f2e;border:1px solid #94a3b844;color:#94a3b8;font-size:8px;padding:1px 6px;border-radius:10px;">Domain</span>
  </div>
  <div style="font-size:8px;color:#475569;margin-bottom:4px;font-weight:600;letter-spacing:.06em;">
    RELATIONSHIP TYPES
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:4px;">
    <span style="font-size:8px;color:#64748b;">CAUSED</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">TRIGGERED</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">FUNDS</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">BENEFITS</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">PROVES</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">BUILT_BY</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">LOCATED_IN</span>
    <span style="font-size:8px;color:#334155;">·</span>
    <span style="font-size:8px;color:#64748b;">CONNECTED_TO</span>
  </div>
</div>
"""


def render_ontology_model() -> None:
    """Render the ontology knowledge model schema as a collapsed expander."""
    st.markdown(
        "<div style='border-top:1px solid #1e293b;margin-top:18px;'></div>",
        unsafe_allow_html=True,
    )
    with st.expander("Ontology Knowledge Model", expanded=False):
        st.markdown(_HTML, unsafe_allow_html=True)
