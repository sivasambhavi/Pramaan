"""
Pramaan — Governance Delivery Proof Engine
Main entry point for the Streamlit frontend.
"""

import streamlit as st
import pandas as pd
import requests
import time
import plotly.graph_objects as go
from datetime import datetime


def main() -> None:
    st.set_page_config(page_title="Pramaan | Governance Proof Engine", layout="wide", page_icon="🛡️")
    # Hide Live Ingestion from sidebar navigation (admin only via direct URL)
    st.markdown("""
    <style>[data-testid="stSidebarNav"] ul li:nth-child(4) { display: none; }</style>
    """, unsafe_allow_html=True)

    # GAP-19: Home page branding
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px 30px 20px;">
        <div style="font-size: 4em; margin-bottom: 0.2em;">🛡️</div>
        <h1 style="font-size: 3em; font-weight: 800; background: linear-gradient(90deg, #E63946, #f59e0b);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
            PRAMAAN
        </h1>
        <p style="font-size: 1.3em; color: #8b949e; margin-top: 0.5em; letter-spacing: 0.05em;">
            One Graph That Proves What India Built
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Premium card styling
    st.markdown("""
    <style>
        .feature-card {
            background: #161B22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 24px;
            height: 240px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div style="font-size:2em">🗺️</div>
                <h3 style="color:#E63946;margin:8px 0">Ward Map</h3>
                <p style="color:#8b949e;font-size:0.9em">Visualize infrastructure assets across Delhi wards with delivery scores and coverage gaps.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/01_🏙_Ward_Map.py", label="Explore Maps", icon="📍", use_container_width=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div style="font-size:2em">🧷</div>
                <h3 style="color:#f59e0b;margin:8px 0">Proof Chain</h3>
                <p style="color:#8b949e;font-size:0.9em">Trace every rupee from scheme → agency → physical asset → evidence → beneficiary.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/02_🧷_Proof_Chain.py", label="Verify Chains", icon="🖇️", use_container_width=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div style="font-size:2em">🔍</div>
                <h3 style="color:#10b981;margin:8px 0">Governance Audit</h3>
                <p style="color:#8b949e;font-size:0.9em">Interrogate the knowledge graph. Ask any question about what was built, funded, and proven.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/06_❓_Questions.py", label="Open Audit", icon="🔎", use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="text-align:center;color:#444;font-size:0.8em;padding:10px 0">
        Built for India Innovates Hackathon · Neo4j + FastAPI + Streamlit + Groq AI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
