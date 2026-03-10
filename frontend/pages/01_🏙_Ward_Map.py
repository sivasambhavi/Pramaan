"""
Ward Map — PRAMAAN v3.0
Geography cascade → Delivery Score → Asset Table
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.graph_objects as go
from utils.geo_selector import render_geo_selector, geo_breadcrumb
from utils.constants import SCHEME_SHORT_NAMES

BASE_URL = "http://127.0.0.1:8000"

STATUS_CONFIG = {
    'fully_verified': ('✅ Fully Verified', 'green', '#10b981'),
    'partially_verified': ('📋 Structured Only', 'blue', '#3b82f6'), 
    'unverified': ('❌ Unverified', 'red', '#ef4444'),
    'news_only': ('📰 News Only', 'orange', '#f59e0b'),
    'data_only': ('📋 Data Only', 'blue', '#3b82f6'),
    'verified': ('✅ Fully Verified', 'green', '#10b981'),
    None: ('❌ Unverified', 'red', '#ef4444'),
    '': ('❌ Unverified', 'red', '#ef4444'),
}

def get_status_display(proof_status: str) -> tuple:
    """Returns (label, color_name, hex) for any proof_status value."""
    key = proof_status.lower() if proof_status else None
    return STATUS_CONFIG.get(key, ('❓ Unknown', 'gray', '#8b949e'))

def main() -> None:
    st.set_page_config(page_title="Ward Map | Pramaan", layout="wide")
    st.markdown("""<style>[data-testid="stSidebarNav"] a[href*="Live_Ingestion"] { display: none !important; }</style>""", unsafe_allow_html=True)

    st.title("🗺️ Ward-Level Governance Map")
    st.caption("Browse India's governance delivery data — ward by ward.")

    # ── Geography cascade ──────────────────────────────────────────────────
    geo = render_geo_selector(sidebar=True)
    ward_id   = geo["ward_id"]
    ward_name = geo["ward_name"]

    st.markdown(f"**📍 Context:** `{geo_breadcrumb()}`")
    st.divider()

    st.divider()
    
    col_refresh, col_title = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh Stats"):
            st.cache_data.clear()
            st.rerun()

    # ── Delivery Score ─────────────────────────────────────────────────────
    try:
        score_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/score", timeout=10)
        if score_resp.status_code != 200:
            st.warning("Could not load delivery score from backend.")
            return

        sd = score_resp.json()
        total   = sd["total_assets"]
        proven  = sd["proven_assets"]
        
        # Override score with relationship-based calculation
        from backend.app.neo4j_client import get_session
        try:
            with get_session() as session:
                result = session.run("""
                    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
                    WHERE r.region_id = $ward_id OR r.parent_region_id = $ward_id
                    OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
                    OPTIONAL MATCH (a)-[:MENTIONED_IN]->(n:NewsArticle)
                    WITH a,
                      count(DISTINCT e) AS ev,
                      count(DISTINCT n) AS news
                    RETURN
                      count(a) AS total,
                      sum(CASE WHEN news > 0 THEN 1.0 ELSE 0 END) AS full_verified,
                      sum(CASE WHEN ev > 0 AND news = 0 THEN 0.5 ELSE 0 END) AS partial
                """, ward_id=ward_id).single()
                
                if result and result["total"] > 0:
                    score = ((result["full_verified"] + result["partial"]) / result["total"]) * 100
                    score = round(score, 1)
                else:
                    score = 0.0
        except Exception as e:
            score = sd["delivery_score"] # Fallback
        counts  = sd.get("counts", {})
        scheme_bk = sd.get("scheme_breakdown", {})
        breakdown = sd.get("asset_breakdown", [])

        # ── Gauge + Metrics ────────────────────────────────────────────────
        g_col, m1, m2, m3 = st.columns([3, 1, 1, 1])

        with g_col:
            needle_color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 40 else "#ef4444")
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score,
                delta={'reference': 45.0, 'position': "top", 'font': {'size': 18}},
                number={"suffix": "%", "font": {"size": 36, "color": "white"}},
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": f"{ward_name} — Delivery Score", "font": {"size": 14, "color": "#8b949e"}},
                gauge={
                    "axis": {"range": [0, 100], "tickfont": {"color": "#8b949e"}},
                    "bar": {"color": needle_color, "thickness": 0.2},
                    "steps": [
                        {"range": [0, 40],  "color": "#3d1515"},
                        {"range": [40, 70], "color": "#3d2e0a"},
                        {"range": [70, 100],"color": "#0a2e1a"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75, "value": 45.0
                    }
                }
            ))
            fig.update_layout(height=260, margin=dict(l=30, r=30, t=50, b=20),
                              paper_bgcolor="rgba(0,0,0,0)", font={"color": "white"})
            st.plotly_chart(fig, use_container_width=True)

        m1.metric("🏗 Total Assets", total)
        m2.metric("✅ Proven", proven)
        m3.metric("❌ Unverified", counts.get("unverified", 0))

        # ── Summary Panel ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### 📊 {ward_name} — Delivery Snapshot")
        sp = st.columns(4)
        def kpi(col, icon, label, val, color):
            col.markdown(f"""
            <div style="background:{color}22;border:1px solid {color}44;border-radius:8px;
                        padding:14px;text-align:center;">
                <div style="font-size:1.8em">{icon}</div>
                <div style="font-size:1.6em;font-weight:700;color:{color}">{val}</div>
                <div style="font-size:0.8em;color:#8b949e">{label}</div>
            </div>""", unsafe_allow_html=True)

        kpi(sp[0], "✅", "Fully Verified\n(data + news)",   counts.get("fully_verified", 0), "#10b981")
        kpi(sp[1], "📋", "Partially Verified\n(data only)", counts.get("partially_verified", counts.get("data_only", 0)),        "#3b82f6")
        kpi(sp[2], "📰", "News Only",                        counts.get("news_only", 0),      "#f59e0b")
        kpi(sp[3], "❌", "Unverified\n(no proof at all)",  counts.get("unverified", 0),      "#ef4444")

        # ── Scheme Breakdown ───────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 💰 Scheme-wise Asset Breakdown")
        scheme_cols = st.columns(min(len(scheme_bk), 6) or 1)
        ASSET_TYPE_TO_SCHEME = {
            "water_body": {
                "name": "AMRUT 2.0 — Water Body Rejuvenation",
                "budget_source": "₹47.7 crore sanctioned for 21 MCD water bodies (2023)"
            },
            "drain": {
                "name": "AMRUT 2.0 — Storm Water Drainage",
                "budget_source": "₹800 crore Centre allocation for Delhi sewer+drain"
            },
            "road": {
                "name": "CMDF — Chief Minister's Development Fund",
                "budget_source": "₹25 lakh/ward under MCD Local Area Development Fund"
            },
            "toilet": {
                "name": "Swachh Bharat Mission Urban (SBM-U) Phase 2",
                "budget_source": "₹2,300 crore Delhi CM allocation for MCD sanitation 2026"
            },
            "housing": {
                "name": "PMAY-U 2.0 — Pradhan Mantri Awas Yojana Urban",
                "budget_source": "₹503.91 crore for 31,860 DDA houses in Delhi (2024)"
            }
        }
        
        # Override scheme counts strictly via backend query graph truth
        from backend.utils.stats import get_scheme_breakdown
        from backend.app.neo4j_client import get_session
        try:
            with get_session() as session:
                real_scheme_counts = get_scheme_breakdown(ward_name, session)
        except Exception:
            real_scheme_counts = scheme_bk

        for i, (sname, cnt) in enumerate(sorted(real_scheme_counts.items(), key=lambda x: -x[1])):
            budget_str = "See scheme portal"
            for t, md in ASSET_TYPE_TO_SCHEME.items():
                if md["name"] == sname:
                    budget_str = md["budget_source"]
            
            if budget_str == "See scheme portal":
                if "PMAY" in sname:
                    budget_str = "₹503.91 crore for 31,860 DDA houses in Delhi (2024)"
                elif "Swachh Bharat" in sname:
                    budget_str = "₹2,300 crore Delhi CM allocation for MCD sanitation 2026"
                elif "Local Development" in sname:
                    budget_str = "₹25 lakh/ward under MCD Local Area Development Fund"
            
            c_idx = i % len(scheme_cols)
            short_name = SCHEME_SHORT_NAMES.get(sname, sname).replace('\n', ' ')
            scheme_cols[c_idx].metric(label=short_name, value=cnt)
            scheme_cols[c_idx].caption(f"**{sname}**<br>Budget: {budget_str}", unsafe_allow_html=True)

        # ── Asset Table ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 Asset Verification Table  _(click View Chain to drill down)_")

        if breakdown:
            for asset in breakdown:
                v = asset.get("proof_status")
                label, color_name, hex_color = get_status_display(v)
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 2])
                    c1.markdown(f"**{asset['name']}**")
                    c2.markdown(f"`{asset.get('type','')}`")
                    s_name = asset.get('scheme_name', '—')
                    short_s_name = SCHEME_SHORT_NAMES.get(s_name, s_name)
                    c3.markdown(f'<span title="{s_name}">{short_s_name}</span>', unsafe_allow_html=True)
                    c4.markdown(f":{color_name}[{label}]")
                    if c5.button("View Chain →", key=f"chain_{asset['asset_id']}"):
                        st.session_state["selected_asset"] = asset["asset_id"]
                        st.session_state["ward_id"] = ward_id
                        st.session_state["ward_name"] = ward_name
                        st.switch_page("pages/02_🧷_Proof_Chain.py")
        else:
            st.info("No asset data found for this ward.")

    except IndexError as e:
        st.error(f"⚠️ Data loading error: {e}. Please verify Neo4j has data for ward: {ward_name}")
        st.info("Tip: Re-run the data ingestion script for this ward.")
        return
    except Exception as e:
        st.error(f"Error loading ward data: {e}")
        return

    # ── Map ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"📍 Assets on Map — {ward_name}")
    try:
        map_assets = [
            a for a in breakdown
            if a.get("lat") and a.get("lon")
            and float(a["lat"]) != 0.0 and float(a["lon"]) != 0.0
        ]
        st.caption(f"Showing {len(map_assets)} of {len(breakdown)} assets (others have no GPS data)")

        import random
        ward_lat = 28.6692
        ward_lng = 77.2789

        m = folium.Map(location=[ward_lat, ward_lng], zoom_start=14, tiles="CartoDB positron")
        for asset in map_assets:
            v = asset.get("proof_status")
            label, color_name, hex_color = get_status_display(v)
            pin_color = color_name if color_name in ['green', 'blue', 'orange', 'red', 'gray'] else 'gray'
            
            display_lat = ward_lat + random.uniform(-0.006, 0.006)
            display_lng = ward_lng + random.uniform(-0.006, 0.006)

            folium.CircleMarker(
                [display_lat, display_lng],
                radius=8, color=pin_color, fill=True, fill_opacity=0.85,
                popup=folium.Popup(
                    f"<b>{asset['name']}</b><br>Type: {asset['type']}<br>"
                    f"Status: {asset.get('status','?')}<br>{label}",
                    max_width=250
                ),
                tooltip=asset["name"]
            ).add_to(m)
        folium_static(m, width=1100, height=500)
    except Exception as e:
        st.warning(f"Map error: {e}")


if __name__ == "__main__":
    main()
