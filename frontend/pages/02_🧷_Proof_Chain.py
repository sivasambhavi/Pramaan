import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

def render_chain_node(icon: str, label: str, content: str, color: str):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}22, {color}11);
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 6px;
    ">
        <div style="font-size:1.4em">{icon}</div>
        <div style="font-weight:700;color:{color};font-size:0.8em;text-transform:uppercase;letter-spacing:0.06em;margin-top:4px">{label}</div>
        <div style="margin-top:6px;font-size:0.95em;line-height:1.6">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def render_arrow():
    st.markdown('<div style="text-align:center;font-size:1.6em;color:#555;margin:2px 0">↓</div>', unsafe_allow_html=True)

def build_pyvis_graph(data: dict):
    """Build a pyvis HTML graph for the subgraph."""
    try:
        from pyvis.network import Network
        net = Network(height="400px", width="100%", bgcolor="#0D1117", font_color="white", directed=True)
        net.set_options('{"physics": {"enabled": true, "barnesHut": {"springLength": 150}}}')

        color_map = {"Scheme": "#3b82f6", "Asset": "#f59e0b", "Region": "#10b981",
                     "Beneficiary": "#8b5cf6", "Evidence": "#6b7280", "Actor": "#ef4444"}

        nodes_added = set()

        def add_node(nid, label, node_type):
            if nid and nid not in nodes_added:
                color = color_map.get(node_type, "#aaa")
                net.add_node(nid, label=f"{label[:20]}", color=color, title=f"{node_type}: {label}")
                nodes_added.add(nid)

        asset = data.get("asset", {})
        a_id = asset.get("asset_id", "asset")
        add_node(a_id, asset.get("name", a_id), "Asset")

        scheme = data.get("scheme")
        if scheme:
            s_id = scheme.get("scheme_id", "scheme")
            add_node(s_id, scheme.get("name", s_id), "Scheme")
            net.add_edge(s_id, a_id, label="FUNDS", color="#3b82f6")

        actor = data.get("built_by")
        if actor:
            act_id = actor.get("actor_id", "actor")
            add_node(act_id, actor.get("name", act_id), "Actor")
            net.add_edge(a_id, act_id, label="BUILT_BY", color="#ef4444")

        ward = data.get("ward")
        if ward:
            w_id = ward.get("region_id", "ward")
            add_node(w_id, ward.get("name", "Ward"), "Region")
            net.add_edge(a_id, w_id, label="LOCATED_IN", color="#10b981")

        for i, b in enumerate(data.get("beneficiaries", [])):
            b_id = b.get("beneficiary_id", f"ben_{i}")
            add_node(b_id, f"{b.get('count','?')} beneficiaries", "Beneficiary")
            if scheme:
                net.add_edge(scheme.get("scheme_id", "scheme"), b_id, label="BENEFITS", color="#8b5cf6")

        for i, e in enumerate(data.get("evidence", [])):
            e_id = e.get("evidence_id", f"ev_{i}")
            add_node(e_id, e.get("before_or_after", "evidence"), "Evidence")
            net.add_edge(e_id, a_id, label="PROVES", color="#6b7280")

        html = net.generate_html()
        return html
    except ImportError:
        return None

def main() -> None:
    st.set_page_config(page_title="Proof Chain | Pramaan", layout="wide")
    st.title("🧷 Governance Delivery Proof Chain")
    st.caption("Trace any asset back to its funding source, implementing agency, and physical evidence.")

    # Global Asset Selection
    st.divider()
    try:
        assets_resp = requests.get(f"{BASE_URL}/assets/list", timeout=5)
        if assets_resp.status_code == 200:
            all_assets = assets_resp.json()["assets"]
            if not all_assets:
                st.warning("No assets yet. Run the Auto-Search on the Live Ingestion page first.")
                return
            asset_options = {f"{a['name']} ({a.get('type', '?')})": a['asset_id'] for a in all_assets}
            selected_label = st.selectbox("🔍 Select Asset to Trace", options=list(asset_options.keys()))
            asset_id = asset_options[selected_label]
        else:
            st.error("Could not load assets.")
            return
    except Exception as e:
        st.error(f"Backend error: {e}")
        return

    st.divider()

    try:
        chain_resp = requests.get(f"{BASE_URL}/assets/{asset_id}/chain", timeout=10)
        if chain_resp.status_code == 200:
            data = chain_resp.json()
            asset = data["asset"]
            scheme = data.get("scheme")
            actor = data.get("built_by")
            region = data.get("region")
            ward = data.get("ward")
            evidence = data.get("evidence", [])
            beneficiaries = data.get("beneficiaries", [])

            asset_name = asset.get("name", asset_id)
            st.subheader(f"🔗 Proof Chain: {asset_name}")

            # GAP-9: KML auto-import badge
            if asset.get("source") == "KML_auto":
                st.caption("📌 Auto-imported from KML. Evidence pending.")

            chain_col, right_col = st.columns([3, 2])

            with chain_col:
                st.caption("Full traceability: Funding Source → Implementing Agency → Asset → Location")
                st.markdown("")

                if scheme:
                    content = f"<b>{scheme.get('name','N/A')}</b><br/>Ministry: {scheme.get('ministry','N/A')} &nbsp;|&nbsp; Category: {scheme.get('category','N/A')}"
                    render_chain_node("💰", "Scheme / Funding", content, "#3b82f6")
                    render_arrow()

                if actor:
                    content = f"<b>{actor.get('name','N/A')}</b><br/>Type: {actor.get('type','N/A')}"
                    render_chain_node("🏛️", "Implementing Agency", content, "#8b5cf6")
                    render_arrow()

                cost_str = f"₹{asset.get('cost','N/A')}" if asset.get('cost') else "N/A"
                content = f"<b>{asset_name}</b><br/>Type: {asset.get('type','N/A')} &nbsp;|&nbsp; Status: {asset.get('status','N/A')} &nbsp;|&nbsp; Cost: {cost_str}"
                render_chain_node("🏗️", "Asset / Infrastructure", content, "#f59e0b")

                location_parts = []
                if ward:
                    location_parts.append(f"Ward: {ward.get('name','')}")
                if region:
                    location_parts.append(f"Street: {region.get('name','')}")
                if location_parts:
                    render_arrow()
                    render_chain_node("📍", "Location", "<br/>".join(location_parts), "#10b981")

            with right_col:
                # Evidence section (GAP-7: use markdown)
                st.subheader("📸 Evidence")
                if evidence:
                    for ev in evidence:
                        label = "✅ AFTER" if ev.get("before_or_after") == "after" else "⏳ BEFORE"
                        st.markdown(f"**{label}** — {ev.get('capture_date', 'N/A')}")
                        url = ev.get("url", "")
                        if url.startswith("http"):
                            st.image(url, use_container_width=True)
                        else:
                            st.caption(f"📁 Path: {url}")
                else:
                    st.info("No photo evidence linked to this asset yet.")

                # Beneficiaries (GAP-6: metric + caption)
                st.subheader("👥 Beneficiaries")
                if beneficiaries:
                    for b in beneficiaries:
                        count = b.get("count", "N/A")
                        desc = b.get("description", "")
                        st.metric("People Served", count)
                        st.caption(desc)
                else:
                    st.info("Beneficiary data not yet linked.")

            # GAP-10: Graph visualization
            st.divider()
            st.subheader("🕸️ Subgraph Visualization")
            graph_html = build_pyvis_graph(data)
            if graph_html:
                st.components.v1.html(graph_html, height=420, scrolling=False)
            else:
                st.caption("Install `pyvis` to see graph visualization: `pip install pyvis`")
                # Fallback: simple text chain
                nodes = []
                if scheme: nodes.append(f"💰 {scheme.get('name','Scheme')}")
                nodes.append(f"🏗️ {asset_name}")
                if ward: nodes.append(f"📍 {ward.get('name','')}")
                st.markdown(" → ".join(nodes))

        elif chain_resp.status_code == 404:
            st.warning("No chain data found for this asset. It may have been ingested without full linkage.")
            st.page_link("pages/04_⚡_Live_Ingestion.py", label="→ Go to Live Ingestion to add more data", icon="⚡")
        else:
            st.error("Failed to load chain data.")
    except Exception as e:
        st.error(f"Error loading chain: {e}")

if __name__ == "__main__":
    main()
