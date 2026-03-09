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

BASE_URL = "http://127.0.0.1:8000"

VERIFY_LABELS = {
    "fully_verified": "✅ Fully Verified",
    "partial":        "📋 Structured Only",
    "news_only":      "📰 News Only",
    "unverified":     "❌ Unverified",
}
VERIFY_COLORS = {
    "fully_verified": "#10b981",
    "partial":        "#3b82f6",
    "news_only":      "#f59e0b",
    "unverified":     "#ef4444",
}

def hide_live_ingestion():
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] ul li:nth-child(4) { display: none; }
    </style>
    """, unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Ward Map | Pramaan", layout="wide")
    hide_live_ingestion()

    st.title("🗺️ Ward-Level Governance Map")
    st.caption("Browse India's governance delivery data — ward by ward.")

    # ── Geography cascade ──────────────────────────────────────────────────
    geo = render_geo_selector(sidebar=True)
    ward_id   = geo["ward_id"]
    ward_name = geo["ward_name"]

    st.markdown(f"**📍 Context:** `{geo_breadcrumb()}`")
    st.divider()

    # ── Delivery Score ─────────────────────────────────────────────────────
    try:
        score_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/score", timeout=10)
        if score_resp.status_code != 200:
            st.warning("Could not load delivery score from backend.")
            return

        sd = score_resp.json()
        total   = sd["total_assets"]
        proven  = sd["proven_assets"]
        score   = sd["delivery_score"]
        counts  = sd.get("counts", {})
        scheme_bk = sd.get("scheme_breakdown", {})
        breakdown = sd.get("asset_breakdown", [])

        # ── Gauge + Metrics ────────────────────────────────────────────────
        g_col, m1, m2, m3 = st.columns([3, 1, 1, 1])

        with g_col:
            needle_color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 40 else "#ef4444")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
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
                        "line": {"color": needle_color, "width": 4},
                        "thickness": 0.75, "value": score
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
        kpi(sp[1], "📋", "Partially Verified\n(data only)", counts.get("partial", 0),        "#3b82f6")
        kpi(sp[2], "📰", "News Only",                        counts.get("news_only", 0),      "#f59e0b")
        kpi(sp[3], "❌", "Unverified\n(no proof at all)",  counts.get("unverified", 0),      "#ef4444")

        # ── Scheme Breakdown ───────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 💰 Scheme-wise Asset Breakdown")
        scheme_cols = st.columns(min(len(scheme_bk), 6) or 1)
        for i, (sname, cnt) in enumerate(sorted(scheme_bk.items(), key=lambda x: -x[1])):
            scheme_cols[i % 6].metric(sname[:20], cnt)

        # ── Asset Table ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 Asset Verification Table  _(click View Chain to drill down)_")

        if breakdown:
            for asset in breakdown:
                v = asset["verification"]
                color = VERIFY_COLORS.get(v, "#444")
                label = VERIFY_LABELS.get(v, v)
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 2])
                    c1.markdown(f"**{asset['name']}**")
                    c2.markdown(f"`{asset.get('type','')}`")
                    c3.markdown(f"{asset.get('scheme_name','—')[:20]}")
                    c4.markdown(f"<span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
                    if c5.button("View Chain →", key=f"chain_{asset['asset_id']}"):
                        st.session_state["selected_asset"] = asset["asset_id"]
                        st.session_state["ward_id"] = ward_id
                        st.session_state["ward_name"] = ward_name
                        st.switch_page("pages/02_🧷_Proof_Chain.py")
        else:
            st.info("No asset data found for this ward.")

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

        m = folium.Map(location=[28.6692, 77.2945], zoom_start=14, tiles="CartoDB positron")
        for asset in map_assets:
            v = asset["verification"]
            pin_color = "green" if v == "fully_verified" else (
                        "blue"  if v == "partial"        else (
                        "orange"if v == "news_only"      else "red"))
            folium.CircleMarker(
                [float(asset["lat"]), float(asset["lon"])],
                radius=8, color=pin_color, fill=True, fill_opacity=0.85,
                popup=folium.Popup(
                    f"<b>{asset['name']}</b><br>Type: {asset['type']}<br>"
                    f"Status: {asset.get('status','?')}<br>{VERIFY_LABELS.get(v,v)}",
                    max_width=250
                ),
                tooltip=asset["name"]
            ).add_to(m)
        folium_static(m, width=1100, height=500)
    except Exception as e:
        st.warning(f"Map error: {e}")


if __name__ == "__main__":
    main()
