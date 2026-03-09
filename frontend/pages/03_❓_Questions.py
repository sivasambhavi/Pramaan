import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

def main() -> None:
    st.set_page_config(page_title="Governance Discovery | Pramaan", layout="wide")
    st.title("❓ Governance Discovery & Gap Analysis")
    st.caption("Ask competency questions to uncover delivery gaps and fund utilisation patterns.")

    # GAP-11: Ward selector from session state
    try:
        wards_resp = requests.get(f"{BASE_URL}/wards/with-assets")
        wards = wards_resp.json() if wards_resp.status_code == 200 else []
    except:
        wards = []
    ward_options = {f"{w['name']}": w['region_id'] for w in wards} or {"Ward 45": "REG_W45"}

    default_name = st.session_state.get('selected_ward_name', 'Ward 45')
    selected_ward_name = st.selectbox("🗺 Select Ward", list(ward_options.keys()),
                                       index=list(ward_options.keys()).index(default_name) if default_name in ward_options else 0)
    ward_id = ward_options[selected_ward_name]

    st.divider()

    # GAP-13: NL query input
    nl_input = st.text_input("💬 Ask a question (natural language)", placeholder="e.g. What was built in this ward?")

    st.subheader("Or select a Competency Question")
    questions = [
        f"What was built in {selected_ward_name}?",
        f"Show me all assets funded by any scheme in {selected_ward_name}.",
        f"Which schemes have the highest gap in {selected_ward_name}?",
        "Compare delivery scores across all districts (Delhi Overview).",
    ]
    selected_q = st.radio("Questions", questions)

    query_to_use = nl_input.strip() if nl_input.strip() else selected_q

    if st.button("🔍 Query Knowledge Graph"):
        st.divider()
        if "built in" in query_to_use.lower() or "assets" in query_to_use.lower():
            resp = requests.get(f"{BASE_URL}/wards/{ward_id}/assets")
            if resp.status_code == 200:
                data = resp.json()['assets']
                st.markdown(f"### Found {len(data)} assets in {selected_ward_name}")
                if data:
                    df = pd.DataFrame(data)
                    cols = [c for c in ['name', 'type', 'status', 'cost'] if c in df.columns]
                    st.dataframe(df[cols], use_container_width=True)
                else:
                    st.info("No assets found.")

        elif "gap" in query_to_use.lower() or "scheme" in query_to_use.lower():
            resp = requests.get(f"{BASE_URL}/wards/{ward_id}/gaps")
            if resp.status_code == 200:
                data = resp.json()['gaps']
                st.markdown("### Scheme Gap Analysis")
                st.dataframe(pd.DataFrame(data), use_container_width=True)

        elif "delhi overview" in query_to_use.lower() or "compare" in query_to_use.lower():
            st.markdown("### Sectoral Distribution across Delhi (Simulated)")
            st.bar_chart({"Roads": 45, "Drains": 32, "Housing": 28, "Toilets": 15})

        else:
            st.info(f"Routing query to Knowledge Graph: *'{query_to_use}'*")
            resp = requests.get(f"{BASE_URL}/wards/{ward_id}/assets")
            if resp.status_code == 200:
                data = resp.json()['assets']
                st.markdown(f"### Assets in {selected_ward_name}")
                st.dataframe(pd.DataFrame(data), use_container_width=True)

if __name__ == "__main__":
    main()
