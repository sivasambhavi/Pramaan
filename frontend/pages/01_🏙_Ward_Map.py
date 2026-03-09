import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

def main() -> None:
    st.set_page_config(page_title="Ward Map | Pramaan", layout="wide")
    st.title("🏙 Ward-Level Governance Map")
    st.caption("Zoom into a ward to see infrastructure assets, delivery scores, and traceability gaps.")

    # Sidebar: Ward Selection (GAP-1: only wards with assets)
    try:
        wards_resp = requests.get(f"{BASE_URL}/wards/with-assets")
        if wards_resp.status_code == 200:
            wards = wards_resp.json()
            if not wards:
                st.warning("No wards with assets found in the Knowledge Graph.")
                return
            ward_options = {f"{w['name']} ({w['asset_count']} assets)": w['region_id'] for w in wards}
            selected_label = st.sidebar.selectbox("Select Ward", options=list(ward_options.keys()))
            ward_id = ward_options[selected_label]
            selected_ward_name = selected_label.split(" (")[0]
            # GAP-11: store in session state for other pages
            st.session_state['selected_ward'] = ward_id
            st.session_state['selected_ward_name'] = selected_ward_name
        else:
            st.error("Failed to load wards from backend.")
            return
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return

    # Ward Score Dashboard (GAP-2 + GAP-5)
    col1, col2, col3 = st.columns(3)
    try:
        score_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/score")
        if score_resp.status_code == 200:
            score_data = score_resp.json()
            total = score_data['total_assets']
            proven = score_data['proven_assets']
            score = score_data['delivery_score']
            col1.metric("🏆 Governance Delivery Score", f"{score}%")
            col2.metric("🏗 Total Assets", total)
            col3.metric("✅ Verified (with Proof)", proven)
            # GAP-2: show formula
            st.caption("📐 Score = assets with at least 1 evidence ÷ total assets × 100")
            # GAP-5: gap warning
            missing = total - proven
            if missing > 0:
                st.warning(f"⚠️ {missing} asset(s) are missing evidence links — delivery unverified.")
    except:
        st.warning("Could not load ward score.")

    st.divider()

    # Assets Map
    st.subheader(f"📍 Assets in {selected_ward_name}")
    try:
        assets_resp = requests.get(f"{BASE_URL}/wards/{ward_id}/assets")
        if assets_resp.status_code == 200:
            assets = assets_resp.json()['assets']

            m = folium.Map(location=[28.6692, 77.2945], zoom_start=15, tiles="CartoDB positron")
            for asset in assets:
                if asset.get('lat') and asset.get('lon'):
                    color = "green" if asset.get('status') == 'completed' else "orange"
                    icon_name = {"drain": "tint", "road": "road", "water_body": "cloud"}.get(asset.get('type', ''), "info-sign")
                    folium.Marker(
                        [asset['lat'], asset['lon']],
                        popup=f"<b>{asset['name']}</b><br>Type: {asset['type']}<br>Status: {asset['status']}",
                        tooltip=asset['name'],
                        icon=folium.Icon(color=color, icon=icon_name)
                    ).add_to(m)
            folium_static(m, width=1000)

            st.markdown("### 📋 Detailed Asset List")
            df = pd.DataFrame(assets)
            if not df.empty:
                cols = [c for c in ['asset_id', 'name', 'type', 'status', 'cost'] if c in df.columns]
                st.dataframe(df[cols], use_container_width=True)
        else:
            st.info("No assets found for this ward.")
    except Exception as e:
        st.error(f"Error loading assets: {e}")

if __name__ == "__main__":
    main()
