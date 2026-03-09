import streamlit as st
import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "last_autosearch.json")

def save_cache(data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def main() -> None:
    st.set_page_config(page_title="AI Ingestion | Pramaan", layout="wide")
    st.title("⚡ Live Governance Ingestion")
    st.caption("Auto-search real governance news and map it to the Knowledge Graph.")

    tab1, tab2 = st.tabs(["🔍 Strategic Scraper", "✏️ Manual Ingestion"])

    # ── TAB 1: Auto-Search ──────────────────────────────────────────────────
    with tab1:
        st.subheader("🌐 Auto-Search from News")

        col_a, col_b = st.columns([3, 1])
        with col_a:
            search_query = st.text_input("Search Query", value="AMRUT 2.0 Delhi MCD")
        with col_b:
            # GAP-15: offline fallback
            use_cache = st.checkbox("📂 Use cached result", value=False,
                                    help="Load the last successful scrape result offline")

        if st.button("🔍 Auto-Search & Map to Graph"):
            if use_cache:
                cached = load_cache()
                if cached:
                    data = cached
                    st.info("📂 Loaded from cache (offline mode)")
                else:
                    st.warning("No cached result found. Please run a live search first.")
                    return
            else:
                with st.status("🔍 Scraping governance news...", expanded=True) as status:
                    try:
                        scrape_resp = requests.get(f"{BASE_URL}/scrape/news", params={"q": search_query}, timeout=30)
                    except Exception as e:
                        st.error(f"Network error: {e}")
                        return

                    if scrape_resp.status_code == 200:
                        data = scrape_resp.json()
                        save_cache(data)  # GAP-15: save to cache
                    else:
                        st.error("Scraping service unavailable.")
                        return

            articles = data.get('articles', [])
            st.success(f"✅ Found {len(articles)} relevant news items.")

            with st.expander("📄 View Scraped News Sources"):
                for a in articles:
                    st.markdown(f"**{a['title']}**")
                    st.caption(f"Published: {a.get('published', 'N/A')}")
                    st.write(a.get('summary', ''))
                    st.divider()

            # Show extracted knowledge map
            st.markdown("### 🧩 AI Extracted Knowledge Map")
            st.json({"entities": data.get("entities", []), "relations": data.get("relations", [])})

            if data.get("entities"):
                with st.spinner("Writing to Knowledge Graph..."):
                    try:
                        ingest_resp = requests.post(f"{BASE_URL}/ingest/entities", json=data, timeout=15)
                        if ingest_resp.status_code == 200:
                            result = ingest_resp.json()
                            n_ent = result.get('entities_created', len(data['entities']))
                            n_rel = result.get('relations_created', len(data.get('relations', [])))
                            st.success(f"🚀 Successfully mapped **{n_ent} entities** and **{n_rel} relations** to the Knowledge Graph!")

                            # GAP-16: show matched/new assets
                            assets = [e for e in data['entities'] if e.get('label') == 'Asset']
                            if assets:
                                st.markdown("**📦 Assets committed:**")
                                for asset in assets:
                                    st.info(f"🆕 New/Updated: **{asset['properties'].get('name', asset['id'])}**")

                            # GAP-17: link to Proof Chain
                            st.page_link("pages/02_🧷_Proof_Chain.py", label="→ View in Proof Chain", icon="🧷")
                        else:
                            st.error(f"Ingestion failed: {ingest_resp.text}")
                    except Exception as e:
                        st.error(f"Ingestion error: {e}")
            else:
                st.warning("The AI could not confidently identify specific governance entities in these headlines.")

    # ── TAB 2: Manual Ingestion ─────────────────────────────────────────────
    with tab2:
        st.subheader("✏️ Manual Text Ingestion")
        manual_text = st.text_area("Paste news article or governance text here", height=200)
        if st.button("🧠 Extract & Ingest"):
            if manual_text.strip():
                with st.spinner("Extracting governance entities with AI..."):
                    try:
                        resp = requests.post(f"{BASE_URL}/scrape/analyze", json={"text": manual_text}, timeout=30)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.json({"entities": data.get("entities", []), "relations": data.get("relations", [])})
                            if data.get("entities"):
                                ingest_resp = requests.post(f"{BASE_URL}/ingest/entities", json=data, timeout=15)
                                if ingest_resp.status_code == 200:
                                    r = ingest_resp.json()
                                    st.success(f"Added {r.get('entities_created',0)} entities and {r.get('relations_created',0)} relations.")
                                    st.page_link("pages/02_🧷_Proof_Chain.py", label="→ View in Proof Chain", icon="🧷")
                                else:
                                    st.error(f"Ingestion failed: {ingest_resp.text}")
                            else:
                                st.warning("No entities extracted.")
                        else:
                            st.error("Analysis failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please paste some text first.")

    # GAP-18: Dangerous button in expander with confirmation
    st.divider()
    with st.expander("⚠️ Developer Tools"):
        st.warning("**Danger zone.** These actions modify or clear the Knowledge Graph.")
        if st.button("🗑 Clear Demo Nodes (AI-ingested only)"):
            st.session_state['confirm_clear'] = True

        if st.session_state.get('confirm_clear'):
            st.error("Are you sure? This will delete all news-ingested nodes (not seeded data).")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirm Clear"):
                    try:
                        resp = requests.delete(f"{BASE_URL}/ingest/demo-nodes")
                        if resp.status_code == 200:
                            st.success("Demo nodes cleared.")
                            st.session_state['confirm_clear'] = False
                        else:
                            st.error("Clear failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state['confirm_clear'] = False
                    st.rerun()

if __name__ == "__main__":
    main()
