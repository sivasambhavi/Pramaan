# PRAMAAN — Fix History (v1–v20)

This document summarizes the 20 surgical fixes and enhancements applied to ensure the PRAMAAN application is demo-ready with "zero-fail" resilience and high-impact AI/Graph features.

---

### Phase 1: Foundational Enhancements (v1–v11)
*   **Fix 1–3:** Initial environment setup and Neo4j connectivity fixes for Windows.
*   **Fix 4:** Unified AI Service for LLM extraction (delegating all Groq calls to backend).
*   **Fix 5–7:** Improved News Scraper relevance scoring (Gate 4 pre-filter for "Zone Context").
*   **Fix 8–9:** Entity Resolver refinement (entity ID canonicalization for Neo4j).
*   **Fix 10:** Photo Evidence mapping (ensuring photos only appear for matching asset IDs).
*   **Fix 11:** Micro-Accountability trigger (linking verification events to Twilio notifications).

### Phase 2: Demo Resilience & "WOW" Moments (v12–v20)

#### **National Intelligence (Fix 12–13)**
- **Fix 12:** Added Hero Counters with hardcoded demo stats and a live-scrolling ingestion ticker strip to the Home page.
- **Fix 13:** Implemented `_FALLBACK_DETAIL` for National Intelligence. Clicking on Yamuna/Wayanad/Chamoli now shows rich descriptions and impacts even if Neo4j is offline.
- **Visual Enhancement:** Added **Gold Polylines** on the map to visualize cross-domain causal chains (e.g., *Climate in Joshimath → Energy in India*).

#### **Scheme Tracker / Decision Engine (Fix 14–15)**
- **Fix 14:** Hardcoded Neo4j graph fallback data for the Decision Engine to prevent blank screens during the mock graph rendering.
- **Fix 15:** Added **Fund Utilization Bars** (🟢/🟠/🔴) to scheme cards, comparing allocated funds vs. actually spent funds.

#### **Delivery Monitor (Fix 16–17)**
- **Fix 16:** Added Event Intelligence fallbacks to the Delivery Monitor feed.
- **Fix 17:** Created the **Citizen Verification Mock View** in the Delhi Pilot tab, featuring QR-code enabled asset cards and "what a citizen sees" mobile previews.

#### **Citizen Pipeline & AI Vision (Fix 18)**
- **Fix 18:** Implemented the end-to-end **Citizen Report** feature:
    - **Backend:** 3-layer validation (Structural → GPS → Groq Vision AI).
    - **Neo4j:** Logic to flag assets as `DISPUTED` upon valid image submission.
    - **Frontend:** A new "🚩 Report Issue" tab with a live validation pipeline tracker.

#### **Backend Orchestration & Safety (Fix 20)**
- **Fix 19:** (Skipped/Unified into Fix 18).
- **Fix 20:** Implemented **Demo Safety Net** in `frontend/utils/api.py`.
    - Added a **Stale-Cache Fallback Layer** to `safe_get()`. If the backend hits a glitch, the app returns the last known good result with a subtle toast notification.
    - Added **Startup Warm-up** logic to pre-fetch critical data, ensuring the first click on any page is lightning-fast.

---
### Phase 3: Final UX Polishing & Feedback Loop
*   **FIX 1 (Proof & Evidence):** Fixed "Double Navigation" (redundant sidebar + topnav trigger) by removing `show_sidebar=True` from `render_topnav`.
*   **FIX 2 (Topnav):** Renamed "Scheme Tracker" → "Decision Engine" in the navigation bar to match the page's focus and branding.
*   **FIX 3 (National Intelligence):** Implemented "Two-State Map" disclosure flow. The map now defaults to a high-zoom India view, revealing global causal links and zooming out only when the "Cross-links" toggle is enabled.
*   **FIX 4 (National Intelligence):** Eliminated the "blank" right panel on startup. The panel now pre-loads a "Featured Event" (Delhi Floods) so the UI is immediately informative for judges.
*   **FIX 5 (Delivery Monitor):** Implemented an encoding sanitiser (`_sanitise`) to fix visual artifacts like `â€"` appearing in place of dashes (`—`). Applied across all impact, evidence, and event descriptions.
*   **FIX 6 (Proof & Evidence):** Enabled a "zero-click" intelligence brief. The page now defaults to "Delhi Yamuna Floods" and automatically renders its pre-loaded AI brief on startup, eliminating the "Click Generate" friction for demo audiences.
*   **FIX 7 (Proof & Evidence):** Hidden the WhatsApp Mock UI disclaimer behind an expander to maintain a "production-ready" look for the demo.
*   **FIX 8 (Decision Engine):** Stabilized the knowledge graph. Removed the "Physics" checkbox and hardcoded a 300-iteration stabilization routine, preventing the "bouncing blob" effect. Upgraded the "Cross-links" control to a modern UI toggle.
*   **FIX 9 (Decision Engine):** Shortened the side panel tab labels from "Node Index" and "Connections" to "Nodes" and "Cross-Links". This prevents truncation where labels were previously cutting off as "Con▶".
*   **FIX 10 (Home):** Updated the "Verified Assets" stat from the generic "847" to a precise "6" (representing the 3 Drains, PMAY, SBM, and LED assets in the Delhi Pilot). Refined the labels to "WARD-LEVEL ASSETS VERIFIED" with "data.gov.in · pilot audit" as subtext.
*   **FIX 11 (National Intelligence):** Renamed the "Full ingestion panel" expander to "⚡ Live Data Sources" and the "Fetch & Extract" button to "Refresh Live Sources" for a more professional demo feel. Updated internal placeholder text for consistency.
*   **FIX 13 (Decision Engine):** Replaced the static "Action Required" panel with an event-aware dynamic panel. Recommendations for AMRUT (Delhi), SDRF (Odisha/Kerala), and NDMA (Joshimath) now only appear when relevant events are selected.
*   **FIX 20 (API Cache):** Implemented a stale-while-revalidating cache in `utils/api.py`. The app is now resilient to backend downtime, showing cached data and a subtle warning toast instead of blank screens.
*   **FIX 21 (Live Ingestion):** Created `scripts/simulate_live.py` with prebuilt demo payloads. This provides a "zero-fail" live ticker experience during the hackathon, bypassing external network dependencies.
