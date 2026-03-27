# Implementation Plan: Pramaan V5 Dynamic Transformation

# Implementation Plan: 10/10 Master Architecture (True Agentic Graph)

# Implementation Plan: Pramaan V5 Demo Survival Protocol

## Phase 0: Initialization
1. **Branch Management:** Run `git checkout -b feature/v5-demo-safe` before executing any operations to protect the [main](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/main_app.py#191-207) branch.

## Phase 1: Database Purge
1. **Graph Cleanup:** Execute `DETACH DELETE` in Neo4j to permanently remove the 4 hollow events: `EVT_MANIPUR_2023`, `EVT_JOSHIMATH_2023`, `EVT_IMEC_2023`, and `EVT_TATA_SEMI_2024`.
2. **UI Cleanup:** Safely remove these exact 4 events from the `EVENTS` map in [frontend/utils/events.py](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/utils/events.py) so they vanish from the dropdowns and the map.

## Phase 2: Structured Demo Seeding
*We will not use the live web scraper. We will strictly control the data to ensure the 10 AM demo is visually perfect and error-free.*
1. **Neo4j Seed Script:** Write a targeted Python script to inject 2 massive new 2026 events (e.g., "India Semiconductor Mission" and "Rupee Crisis") directly into the Graph with perfect canonical nodes and edges.
2. **Curated Intelligence Tying:** Safely append these 2 new event IDs to the existing 400 lines of curated dictionaries (`NEEDS_MAP`, `WATCH_POINTS`, `CROSS_PAIRS`) inside [national_intelligence.py](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/pages/national_intelligence.py). This guarantees the dashboard tabs light up flawlessly for the new events without breaking the architecture.
3. **Map Tying:** Safely add the GPS coordinates for the 2 new events to the `MAP_EVENTS` array in [events.py](file://wsl.localhost/Ubuntu/home/chinni/india_innovates/Pramaan/frontend/utils/events.py).

## Phase 3: Final Verification & PRD
- Verify the map renders perfectly, tabs display rich curated intelligence, and the 4 hollow events are completely gone.
- Write the V5 PRD documenting the current robust demo state (including the blast score engine and scheme beneficiary models).
