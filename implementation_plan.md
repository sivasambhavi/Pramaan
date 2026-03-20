# PRAMAAN Gap Fix Plan

## MUST FIX (4 gaps)

### [GAP-6] Beneficiary not showing in Proof Chain
#### [MODIFY] [queries.py](file:///E:/INDIA_INNOVATES/Pramaan/backend/app/queries.py)
- Fix `ASSET_CHAIN` Cypher: `OPTIONAL MATCH (s)-[:BENEFITS]->(b:Beneficiary)-[:LIVES_IN]->(br:Region)`
- Return `b.count`, `b.description` alongside existing returns.
#### [MODIFY] [02_🧷_Proof_Chain.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/02_🧷_Proof_Chain.py)
- Render beneficiaries with `st.metric()` for count + `st.caption()` for description.

---

### [GAP-7] Markdown asterisks showing as raw text
#### [MODIFY] [02_🧷_Proof_Chain.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/02_🧷_Proof_Chain.py)
- Replace all `st.write(f"**{x}**")` with `st.markdown(f"**{x}**")`.
- Chain node content already uses HTML — remove the `**` from the f-string inside the HTML block.

---

### [GAP-15] Auto-Search has no offline fallback/cache
#### [MODIFY] [04_⚡_Live_Ingestion.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/04_⚡_Live_Ingestion.py)
- After a successful scrape, save result to `data/cache/last_autosearch.json`.
- Add "Use cached result" checkbox. If checked, load from that file instead of calling network.

---

### [GAP-18] "Clear Graph Demo Nodes" is dangerous
#### [MODIFY] [04_⚡_Live_Ingestion.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/04_⚡_Live_Ingestion.py)
- Wrap in `st.expander("⚠️ Developer Tools")`.
- Inside: add `st.warning("This will remove demo nodes from Neo4j.") + st.button("Confirm Clear")`.

---

## SHOULD FIX (6 gaps)

### [GAP-1] Only Ward 45 has data — filter ward dropdown
#### [MODIFY] [queries.py](file:///E:/INDIA_INNOVATES/Pramaan/backend/app/queries.py)
- Add `GET_WARDS_WITH_ASSETS` Cypher query.
#### [MODIFY] [wards.py](file:///E:/INDIA_INNOVATES/Pramaan/backend/app/routers/wards.py)
- Add `/wards/with-assets` endpoint.
#### [MODIFY] [01_🏙_Ward_Map.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/01_🏙_Ward_Map.py)
- Use `with-assets` endpoint for dropdown. Store selection in `st.session_state.selected_ward`.

---

### [GAP-2] Delivery score formula hidden + [GAP-5] No gap warning
#### [MODIFY] [01_🏙_Ward_Map.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/01_🏙_Ward_Map.py)
- Add `st.caption("Score = assets with at least 1 evidence ÷ total assets × 100")` below score metric.
- Add `st.warning(f"⚠️ {total - verified} assets are missing evidence links.")`.

---

### [GAP-9] KML auto-import badge in Proof Chain
#### [MODIFY] [02_🧷_Proof_Chain.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/02_🧷_Proof_Chain.py)
- After asset name, check `asset.get('source') == 'KML_auto'` and show `st.caption("📌 Auto-imported from KML. Evidence pending.")`.

---

### [GAP-10] No graph visualization in Proof Chain
#### [MODIFY] [02_🧷_Proof_Chain.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/02_🧷_Proof_Chain.py)
- Add a pyvis network graph showing: Scheme → Asset → Region → Beneficiary.
- Colors: blue=Scheme, orange=Asset, green=Region, purple=Beneficiary, grey=Evidence.

---

### [GAP-11] Questions hardcoded to Ward 45
#### [MODIFY] [03_❓_Questions.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/03_❓_Questions.py)
- Add ward selector at top, reading from `st.session_state.get('selected_ward', 'REG_W45')`.
- Pass ward_id to all 4 query functions.

---

### [GAP-16 + GAP-17] No post-ingestion confirmation or redirect
#### [MODIFY] [04_⚡_Live_Ingestion.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/04_⚡_Live_Ingestion.py)
- After ingest, show matched/new asset names.
- Add `st.page_link("pages/02_🧷_Proof_Chain.py", ...)`.

---

## NICE TO HAVE (3 gaps)

### [GAP-19] Empty home page + [GAP-20] Branding
#### [MODIFY] [app.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/app.py)
- Add PRAMAAN logo (emoji header), tagline, 3 bullet points, page link to Ward Map.
#### [MODIFY] [config.toml](file:///E:/INDIA_INNOVATES/Pramaan/frontend/.streamlit/config.toml)
- Add theme colors: primaryColor="#E63946", backgroundColor="#0D1117", etc.

### [GAP-13] NL query in Questions page
#### [MODIFY] [03_❓_Questions.py](file:///E:/INDIA_INNOVATES/Pramaan/frontend/pages/03_❓_Questions.py)
- Add freetext input above radio buttons, route to correct endpoint.

## Verification Plan
- Hit `/wards/with-assets` to confirm filtered list.
- Navigate to Proof Chain → select ASSET_DRAIN_GALI7 → confirm beneficiaries render and subgraph shows.
- Try Auto-Search → check `data/cache/last_autosearch.json` is created.
- Use cached result checkbox → confirm offline load works.
