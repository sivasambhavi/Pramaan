"""
Ward Map — PRAMAAN v4.6.3
Geography cascade → Delivery Score (deterministic override) → Color-coded Map → Asset Table
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
from utils.geo_selector import render_geo_selector, geo_breadcrumb
from utils.constants import SCHEME_SHORT_NAMES, ASSET_VERIFICATION_OVERRIDE

BASE_URL = "http://127.0.0.1:8000"

# ── Status display config ───────────────────────────────────────────────────
STATUS_CONFIG = {
    'fully_verified':    ('✅ Fully Verified',      'green',  '#10b981', '#22c55e'),
    'partially_verified':('⚠️ Partially Verified',  'orange', '#f59e0b', '#f59e0b'),
    'unverified':        ('❌ Unverified',           'red',    '#ef4444', '#ef4444'),
    'news_only':         ('📰 News Only',            'orange', '#f59e0b', '#f59e0b'),
    'verified':          ('✅ Fully Verified',       'green',  '#10b981', '#22c55e'),
    None:                ('❌ Unverified',           'red',    '#ef4444', '#ef4444'),
    '':                  ('❌ Unverified',           'red',    '#ef4444', '#ef4444'),
}

def apply_override(breakdown: list) -> list:
    """Apply ASSET_VERIFICATION_OVERRIDE to each asset in breakdown list."""
    for asset in breakdown:
        aid = asset.get("asset_id", "")
        if aid in ASSET_VERIFICATION_OVERRIDE:
            asset["proof_status"] = ASSET_VERIFICATION_OVERRIDE[aid]
    return breakdown

def compute_score(breakdown: list) -> tuple[float, dict]:
    """Compute weighted delivery score and counts from breakdown list."""
    counts = {"fully_verified": 0, "partially_verified": 0, "news_only": 0, "unverified": 0}
    weighted = 0.0
    for b in breakdown:
        ps = b.get("proof_status", "unverified")
        if ps in ("fully_verified", "verified"):
            weighted += 1.0
            counts["fully_verified"] += 1
        elif ps == "partially_verified":
            weighted += 0.5
            counts["partially_verified"] += 1
        elif ps == "news_only":
            weighted += 0.25
            counts["news_only"] += 1
        else:
            counts["unverified"] += 1
    total = len(breakdown)
    score = round(100 * weighted / total, 1) if total > 0 else 0.0
    return score, counts

def get_status_display(proof_status: str) -> tuple:
    key = proof_status.lower() if proof_status else None
    cfg = STATUS_CONFIG.get(key, ('❓ Unknown', 'gray', '#8b949e', '#8b949e'))
    return cfg[0], cfg[1], cfg[2]

def get_map_color(proof_status: str) -> str:
    key = proof_status.lower() if proof_status else None
    return STATUS_CONFIG.get(key, ('', '', '', '#8b949e'))[3]

def main() -> None:
    st.set_page_config(page_title="Ward Map | Pramaan", layout="wide")

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Outfit:wght@500;700&display=swap');
        .main { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Outfit', sans-serif; font-weight: 700; color: #f0f6fc; }
        [data-testid="stSidebar"] {
            background-color: hsla(220, 30%, 10%, 0.8) !important;
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        .stMetric { background: rgba(255,255,255,0.03); padding:15px; border-radius:12px;
                    border:1px solid rgba(255,255,255,0.1); }
        [data-testid="stSidebarNav"] a[href*="Live_Ingestion"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🏙 Ward-Level Governance Map")
    st.caption("Browse India's governance delivery data — ward by ward.")

    # ── Geography ─────────────────────────────────────────────────────────────
    geo       = render_geo_selector(sidebar=True)
    ward_id   = geo["ward_id"]
    ward_name = geo["ward_name"]

    st.markdown(f"**📍 Context:** `{geo_breadcrumb()}`")
    st.divider()

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh Stats"):
            st.cache_data.clear(); st.rerun()

    # ── Load from API ─────────────────────────────────────────────────────────
    try:
        score_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/score", timeout=10)
        if score_resp.status_code != 200:
            st.warning("Could not load delivery score from backend.")
            return

        sd        = score_resp.json()
        total     = sd["total_assets"]
        breakdown = sd.get("asset_breakdown", [])
        scheme_bk = sd.get("scheme_breakdown", {})

        # Apply deterministic override then recompute score
        breakdown = apply_override(breakdown)
        score, counts = compute_score(breakdown)

        # ── Gauge + Top Metrics ───────────────────────────────────────────────
        g_col, m1, m2, m3 = st.columns([3, 1, 1, 1])
        with g_col:
            needle_color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 35 else "#ef4444")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "%", "font": {"size": 48, "color": "white"}},
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": f"{ward_name} — Delivery Score", "font": {"size": 14, "color": "#8b949e"}},
                gauge={
                    "axis": {"range": [0, 100], "tickfont": {"color": "#8b949e"}},
                    "bar": {"color": needle_color, "thickness": 0.25},
                    "steps": [
                        {"range": [0, 35],  "color": "#3d1515"},
                        {"range": [35, 70], "color": "#3d2e0a"},
                        {"range": [70, 100],"color": "#0a2e1a"},
                    ],
                    "threshold": {"line": {"color": "#f59e0b", "width": 4}, "thickness": 0.75, "value": 37.5}
                }
            ))
            fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20),
                              paper_bgcolor="rgba(0,0,0,0)", font={"color": "white"})
            st.plotly_chart(fig, use_container_width=True)

        m1.metric("🏗 Total Assets",  total)
        m2.metric("✅ Fully Verified", counts.get("fully_verified", 0))
        m3.metric("❌ Unverified",     counts.get("unverified", 0))

        # ── KPI Summary Panel ─────────────────────────────────────────────────
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

        kpi(sp[0], "✅", "FULLY VERIFIED\n(DATA + NEWS)",     counts.get("fully_verified", 0),    "#10b981")
        kpi(sp[1], "⚠️", "PARTIALLY VERIFIED\n(EVIDENCE ONLY)", counts.get("partially_verified", 0), "#f59e0b")
        kpi(sp[2], "📰", "NEWS ONLY",                           counts.get("news_only", 0),          "#06b6d4")
        kpi(sp[3], "❌", "UNVERIFIED\n(NO PROOF)",              counts.get("unverified", 0),          "#ef4444")

        # ── Scheme Breakdown ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 💰 Scheme-wise Asset Breakdown")

        if scheme_bk:
            n_cols = min(len(scheme_bk), 5)
            scheme_cols = st.columns(n_cols)
            for i, (sname, cnt) in enumerate(sorted(scheme_bk.items(), key=lambda x: -x[1])):
                short = SCHEME_SHORT_NAMES.get(sname, sname)
                scheme_cols[i % n_cols].metric(label=short, value=cnt, help=sname)

        # ── Asset Verification Table ──────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 Asset Verification Table  _(click View Chain to drill down)_")

        for asset in breakdown:
            v = asset.get("proof_status")
            label, color_name, _ = get_status_display(v)
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 2])
                c1.markdown(f"**{asset['name']}**")
                c2.markdown(f"`{asset.get('type', '')}`")
                s_name = asset.get("scheme_name", "—")
                c3.markdown(f'<span title="{s_name}">{SCHEME_SHORT_NAMES.get(s_name, s_name)}</span>',
                            unsafe_allow_html=True)
                badge_color = {"green": "🟢", "orange": "🟡", "red": "🔴"}.get(color_name, "⚪")
                c4.markdown(f"{badge_color} {label}")
                if c5.button("View Chain →", key=f"chain_{asset['asset_id']}"):
                    st.session_state["selected_asset"] = asset["asset_id"]
                    st.session_state["ward_id"]   = ward_id
                    st.session_state["ward_name"] = ward_name
                    st.switch_page("pages/02_🧷_Proof_Chain.py")

    except Exception as e:
        st.error(f"Error loading ward data: {e}")
        return

    # ── Color-coded Map ───────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"📍 Assets on Map — {ward_name}")
    st.caption("🟢 Fully Verified  🟡 Partially Verified  🔴 Unverified")

    try:
        import random
        ward_lat, ward_lng = 28.6692, 77.2789
        m = folium.Map(location=[ward_lat, ward_lng], zoom_start=14, tiles="CartoDB positron")

        for asset in breakdown:
            ps = asset.get("proof_status", "unverified")
            hex_color = get_map_color(ps)
            label, _, _ = get_status_display(ps)

            lat = float(asset.get("lat") or ward_lat) + random.uniform(-0.003, 0.003)
            lng = float(asset.get("lon") or ward_lng) + random.uniform(-0.003, 0.003)

            # Larger, more visible circle for demo
            folium.CircleMarker(
                [lat, lng],
                radius=10, color=hex_color, fill=True, fill_color=hex_color, fill_opacity=0.85,
                weight=2,
                popup=folium.Popup(
                    f"<b>{asset['name']}</b><br>Type: {asset.get('type','?')}<br>"
                    f"Status: {asset.get('status','?')}<br>{label}",
                    max_width=260
                ),
                tooltip=f"{asset['name']} — {label}"
            ).add_to(m)

        folium_static(m, width=1100, height=500)
    except Exception as e:
        st.warning(f"Map error: {e}")


if __name__ == "__main__":
    main()
