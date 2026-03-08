# AI Mapper Specification

## Overview

The **AI Mapper** (Automation Ingestion Layer) is the core AI component that takes fragmented, unstructured text/JSON from various sources (PIB releases, news articles, MCD posts, PDFs) and automatically maps them into PRAMAAN's canonical 7-table schema.

## Core Principle

> **"We don't change our schema for every new file. Instead, we keep our 7-Table Schema as the Anchor."**

The AI Mapper uses Named Entity Recognition (NER) via LLM to "force" any fragmented input into the standardized 7-table structure.

## 7-Table Schema (Anchor)

The AI Mapper must output JSON that matches these 7 entity types:

1. **Regions** (`regions.csv`)
2. **Schemes** (`schemes.csv`)
3. **Actors** (`actors.csv`)
4. **Assets** (`assets.csv`)
5. **Beneficiaries** (`beneficiaries.csv`)
6. **Evidence** (`evidence.csv`)
7. **Events** (`events.csv`)

## Entity Mapping Rules

### Region Mapping
- Input: "Ward 45", "W-45", "Shahdara Ward 45", "Gali No. 7"
- Output: `REG_W45` (ward), `STREET_W45_GALI7` (street)
- Pattern: Normalize to canonical region IDs

### Asset Mapping
- Input: "Construction", "drain", "road", "streetlight"
- Output: Asset entity with `type` field matching ontology
- Pattern: Map common terms to asset types (drain, road, streetlight, toilet, house, park)

### Scheme Mapping
- Input: "PMAY", "Pradhan Mantri Awas Yojana", "SFC Grant"
- Output: Canonical scheme IDs (e.g., `SCHEME_PMAY`, `SCHEME_SFC_GRANT_2024`)
- Pattern: Normalize scheme name variations to standard IDs

### Actor Mapping
- Input: "MCD East Zone", "Ward Councillor X", "Contractor ABC"
- Output: Actor entities with `type` (government, elected_rep, contractor)

## JSON Schema for AI Extraction Output

The `ai_extraction.py` function must return JSON matching this structure:

```json
{
  "entities": [
    {
      "id": "REG_W45",  // Optional - will be generated if missing
      "label": "Region",
      "properties": {
        "name": "Ward 45, Shahdara",
        "type": "ward"
      }
    },
    {
      "id": "ASSET_W45_GALI7_DRAIN_2024",  // Optional
      "label": "Asset",
      "properties": {
        "name": "Drain in Gali 7",
        "type": "drain",
        "cost": 1200000,
        "status": "completed"
      }
    }
    // ... more entities
  ],
  "relations": [
    {
      "from_id": "SCHEME_SFC_GRANT_2024",
      "to_id": "ASSET_W45_GALI7_DRAIN_2024",
      "type": "FUNDS",
      "properties": {}
    },
    {
      "from_id": "ASSET_W45_GALI7_DRAIN_2024",
      "to_id": "REG_W45",
      "type": "LOCATED_IN",
      "properties": {}
    }
    // ... more relations
  ]
}
```

## LLM Prompt Requirements

The prompt sent to the LLM must:

1. **Explain the 7-table ontology** (entities and relationships)
2. **Request structured JSON output** matching the schema above
3. **Specify ID generation rules** (or indicate when IDs are missing)
4. **Handle entity resolution** (map aliases to canonical names)
5. **Extract relationships** between entities

## Backend ID Filling Logic

When `POST /ingest/entities` receives JSON with missing IDs:

1. **Region IDs**: Generate using pattern `REG_{WARD_NUMBER}` or `STREET_{WARD}_{STREET_NAME}`
2. **Asset IDs**: Generate using pattern `ASSET_{WARD}_{LOCATION}_{TYPE}_{YEAR}`
3. **Scheme IDs**: Generate using pattern `SCHEME_{SCHEME_NAME}_{YEAR}` (or match existing)
4. **Actor IDs**: Generate using pattern `ACTOR_{NAME_HASH}` or match existing
5. **Evidence IDs**: Generate using pattern `EVID_{ASSET_ID}_{BEFORE_AFTER}_{DATE}`

## Entity Resolution

Before generating new IDs, the backend should:

1. **Fuzzy match** extracted names against existing graph entities
2. **Use confidence threshold** (e.g., 85% similarity) to decide if it's a match
3. **If match found**: Use existing ID
4. **If no match**: Generate new ID following patterns above

## Implementation Files

- **`ai/ai_extraction.py`**: LLM-based extraction function
- **`backend/app/routers/ingest.py`**: ID filling and entity resolution logic
- **`frontend/pages/04_⚡_Live_Ingestion.py`**: UI for pasting text and viewing extracted JSON

## Example Input/Output

### Input (Fragmented PIB Text)
```
"Under PMAY, MCD East Zone has completed construction of a drain 
in Ward 45, Gali No. 7, Shahdara. The project cost ₹12 lakh and 
was completed in March 2025. Before and after photos are available."
```

### Output (Structured JSON)
```json
{
  "entities": [
    {"id": "SCHEME_PMAY", "label": "Scheme", "properties": {"name": "PMAY", "ministry": "Housing"}},
    {"id": "ACTOR_MCD_EAST", "label": "Actor", "properties": {"name": "MCD East Zone", "type": "government"}},
    {"id": "REG_W45", "label": "Region", "properties": {"name": "Ward 45, Shahdara", "type": "ward"}},
    {"id": "STREET_W45_GALI7", "label": "Region", "properties": {"name": "Gali No. 7", "type": "street"}},
    {"id": "ASSET_W45_GALI7_DRAIN_2025", "label": "Asset", "properties": {"name": "Drain in Gali 7", "type": "drain", "cost": 1200000, "status": "completed"}},
    {"id": "EVID_W45_GALI7_DRAIN_BEFORE", "label": "Evidence", "properties": {"type": "image", "before_or_after": "before"}},
    {"id": "EVID_W45_GALI7_DRAIN_AFTER", "label": "Evidence", "properties": {"type": "image", "before_or_after": "after"}}
  ],
  "relations": [
    {"from_id": "SCHEME_PMAY", "to_id": "ASSET_W45_GALI7_DRAIN_2025", "type": "FUNDS"},
    {"from_id": "ACTOR_MCD_EAST", "to_id": "ASSET_W45_GALI7_DRAIN_2025", "type": "BUILT_BY"},
    {"from_id": "ASSET_W45_GALI7_DRAIN_2025", "to_id": "REG_W45", "type": "LOCATED_IN"},
    {"from_id": "ASSET_W45_GALI7_DRAIN_2025", "to_id": "STREET_W45_GALI7", "type": "LOCATED_IN"},
    {"from_id": "EVID_W45_GALI7_DRAIN_BEFORE", "to_id": "ASSET_W45_GALI7_DRAIN_2025", "type": "PROVES"},
    {"from_id": "EVID_W45_GALI7_DRAIN_AFTER", "to_id": "ASSET_W45_GALI7_DRAIN_2025", "type": "PROVES"}
  ]
}
```

---

**Status**: MVP Requirement (for Live Ingestion demo)  
**Owner**: Sreenu (AI & Frontend Lead)  
**Timeline**: Before March 10, 2026 submission
