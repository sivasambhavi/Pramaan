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
    AMRUT_CACHE = os.path.join(CACHE_DIR, "amrut_delhi_cached.json")
    if os.path.exists(AMRUT_CACHE):
        with open(AMRUT_CACHE, "r") as f:
            return json.load(f)
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

                            # NEW FEATURE: Delivery Chain
                            response_chain = result.get("delivery_chain")
                            if response_chain:
                                st.markdown("---")
                                st.markdown("## 🔗 Governance Delivery Chain")
                                st.caption("This is the complete traceability path for the asset extracted from the article.")
                                
                                if response_chain.get("matched_existing"):
                                    st.success(f"✅ Matched existing asset: **{response_chain['asset_name']}**")
                                else:
                                    st.info(f"🆕 New asset added to graph: **{response_chain['asset_name']}**")
                                
                                col1, col2 = st.columns([3, 2])
                                with col1:
                                    scheme = response_chain.get("scheme", {})
                                    if scheme:
                                        st.markdown(f"""
                                        <div style='background:#1e3a5f;padding:16px;border-radius:8px;border-left:4px solid #3B82F6;margin-bottom:12px'>
                                        <p style='color:#60A5FA;font-size:11px;font-weight:700;margin:0'>💰 SCHEME / FUNDING</p>
                                        <p style='color:white;font-size:16px;font-weight:600;margin:4px 0'>{scheme.get('name','Unknown')}</p>
                                        <p style='color:#94A3B8;font-size:12px;margin:0'>Ministry: {scheme.get('ministry','—')} | Category: {scheme.get('category','—')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    st.markdown("<p style='text-align:center;color:#4B5563'>↓</p>", unsafe_allow_html=True)
                                    
                                    actor = response_chain.get("actor", {})
                                    if actor:
                                        st.markdown(f"""
                                        <div style='background:#2d1b69;padding:16px;border-radius:8px;border-left:4px solid #8B5CF6;margin-bottom:12px'>
                                        <p style='color:#A78BFA;font-size:11px;font-weight:700;margin:0'>🏛 IMPLEMENTING AGENCY</p>
                                        <p style='color:white;font-size:16px;font-weight:600;margin:4px 0'>{actor.get('name','Unknown')}</p>
                                        <p style='color:#94A3B8;font-size:12px;margin:0'>Type: {actor.get('type','—')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    st.markdown("<p style='text-align:center;color:#4B5563'>↓</p>", unsafe_allow_html=True)
                                    
                                    st.markdown(f"""
                                    <div style='background:#451a03;padding:16px;border-radius:8px;border-left:4px solid #F59E0B;margin-bottom:12px'>
                                    <p style='color:#FCD34D;font-size:11px;font-weight:700;margin:0'>🏗 ASSET / INFRASTRUCTURE</p>
                                    <p style='color:white;font-size:16px;font-weight:600;margin:4px 0'>{response_chain.get('asset_name','Unknown')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown("<p style='text-align:center;color:#4B5563'>↓</p>", unsafe_allow_html=True)
                                    
                                    region = response_chain.get("region", {})
                                    loc_str = f"Ward: {region.get('ward', 'Unknown')}"
                                    if region.get('street'):
                                        loc_str += f" | Street: {region.get('street')}"
                                    st.markdown(f"""
                                    <div style='background:#064e3b;padding:16px;border-radius:8px;border-left:4px solid #10B981;margin-bottom:12px'>
                                    <p style='color:#34D399;font-size:11px;font-weight:700;margin:0'>📍 LOCATION</p>
                                    <p style='color:white;font-size:16px;font-weight:600;margin:4px 0'>{loc_str}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown("#### 📸 Evidence Found")
                                    evidence = response_chain.get("evidence", [])
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
                                        st.info("No photo evidence linked yet.")

                                    st.markdown("#### 👥 People Served")
                                    people = response_chain.get("people_served")
                                    if people:
                                        st.metric("Households", f"{int(people):,}")
                                        st.caption(response_chain.get("beneficiary_desc", ""))
                                    else:
                                        st.info("Beneficiary data pending.")
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
                            if not data.get("success", True):
                                st.error(f"❌ Analysis failed: {data.get('error')}")
                                if data.get("raw"):
                                    with st.expander("Raw AI response (for debugging)"):
                                        st.code(data.get("raw"))
                                st.stop()
                                
                            st.json({"entities": data.get("entities", []), "relations": data.get("relations", [])})
                            if data.get("entities"):
                                ingest_resp = requests.post(f"{BASE_URL}/ingest/entities", json=data, timeout=15)
                                if ingest_resp.status_code == 200:
                                    r = ingest_resp.json()
                                    st.success(f"Added {r.get('entities_created',0)} entities and {r.get('relations_created',0)} relations.")
                                    st.page_link("pages/02_Proof_Chain.py", label="→ View in Proof Chain", icon="🧷")
                                else:
                                    st.error(f"Ingestion failed: {ingest_resp.text}")
                            else:
                                st.warning("No entities extracted.")
                        else:
                            st.error("Analysis failed network error.")
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
