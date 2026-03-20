# Pending AI Implementation Tasks

## Status: All AI Components Are Stubs

Current state: Both `ai_extraction.py` and `nl_query.py` are placeholder stubs that return empty/mock data.

---

## 1. Dependencies & Configuration

### Missing Dependencies
- [ ] **LLM SDK** - Add to `requirements.txt`:
  - Option A: `openai>=1.0.0` (for OpenAI/GPT models)
  - Option B: `anthropic>=0.18.0` (for Claude models)
  - Option C: `google-generativeai` (for Gemini)
  - Option D: `groq` (for GROK via Groq API)
  - **Decision needed**: Which LLM provider? (PRD mentions GROK/GEMINI)

### Missing Configuration
- [ ] **Add LLM config to `backend/app/config.py`**:
  ```python
  llm_provider: str = "openai"  # or "anthropic", "google", "groq"
  llm_api_key: str = ""
  llm_model: str = "gpt-4o-mini"  # or "claude-3-haiku", "gemini-pro", etc.
  offline_mode: bool = False
  ```
- [ ] **Create `.env.example`** with LLM API key placeholder
- [ ] **Update `.gitignore`** to ensure `.env` is ignored

---

## 2. Core AI Implementation: `ai/ai_extraction.py`

### Current State
- ✅ File exists but is a stub
- ❌ No LLM integration
- ❌ No prompt engineering
- ❌ No JSON schema validation
- ❌ No entity mapping logic

### Pending Tasks

#### 2.1 LLM Integration
- [ ] **Choose LLM provider** (OpenAI/Anthropic/Google/Groq)
- [ ] **Install and import LLM SDK**
- [ ] **Implement API call function**:
  ```python
  def call_llm(prompt: str, system_prompt: str) -> str
  ```
- [ ] **Add error handling** for API failures
- [ ] **Add retry logic** with exponential backoff

#### 2.2 Prompt Engineering
- [ ] **Build system prompt** that explains:
  - The 7-table ontology (Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event)
  - Entity mapping rules (see `AI_MAPPER_SPEC.md`)
  - ID generation patterns
  - Relationship types
- [ ] **Build user prompt template** that:
  - Takes input text
  - Requests structured JSON output
  - Specifies exact JSON schema format
- [ ] **Test prompt** on sample PIB text to ensure quality extraction

#### 2.3 Entity Extraction Function
- [ ] **Implement `extract_entities_and_relations(text: str)`**:
  - Call LLM with prompts
  - Parse JSON response
  - Validate JSON structure matches schema
  - Map entities to canonical IDs (or mark for ID generation)
  - Return structured dict with `entities` and `relations` arrays

#### 2.4 Entity Mapping Logic
- [ ] **Region mapping**:
  - "Ward 45" → `REG_W45`
  - "Gali No. 7" → `STREET_W45_GALI7`
  - Handle aliases and variations
- [ ] **Asset type mapping**:
  - "Construction", "drain" → Asset type "drain"
  - "road", "street" → Asset type "road"
- [ ] **Scheme name normalization**:
  - "PMAY", "Pradhan Mantri Awas Yojana" → `SCHEME_PMAY`
- [ ] **Actor type classification**:
  - "MCD East Zone" → type "government"
  - "Ward Councillor" → type "elected_rep"

#### 2.5 JSON Schema Validation
- [ ] **Validate extracted JSON** matches expected structure:
  - Required fields per entity type
  - Valid entity labels (Region, Scheme, Actor, Asset, Beneficiary, Evidence, Event)
  - Valid relationship types (FUNDS, LOCATED_IN, BUILT_BY, etc.)
- [ ] **Handle validation errors** gracefully (log, return partial results)

#### 2.6 Caching for Offline Demo
- [ ] **Create cache directory**: `ai/cache/`
- [ ] **Implement cache save function**:
  ```python
  def save_extraction_cache(text_hash: str, result: dict) -> None
  ```
- [ ] **Implement cache load function**:
  ```python
  def load_extraction_cache(text_hash: str) -> Optional[dict]
  ```
- [ ] **Add offline mode flag** - if True, skip LLM call and use cache
- [ ] **Pre-generate cache** for main demo PIB text

---

## 3. Core AI Implementation: `ai/nl_query.py`

### Current State
- ✅ File exists but is a stub
- ❌ No query classification
- ❌ No parameter extraction
- ❌ No query template mapping

### Pending Tasks

#### 3.1 Query Classification (Simple MVP Approach)
- [ ] **Implement pattern matching** for 3 fixed questions:
  - "What was built in Ward X?" → `WARD_SUMMARY`
  - "For Gali Y, show full delivery chain." → `GALI_CHAIN`
  - "Which schemes have low delivery scores?" → `SCHEME_GAPS`
- [ ] **OR use LLM** to classify question type (optional enhancement)

#### 3.2 Parameter Extraction
- [ ] **Extract ward number** from question (e.g., "Ward 45" → "45")
- [ ] **Extract street/gali name** from question (e.g., "Gali 7" → "7")
- [ ] **Handle variations** ("Ward 45", "W-45", "Ward No. 45")

#### 3.3 Query Template Mapping
- [ ] **Map to backend endpoints**:
  - `WARD_SUMMARY` → `GET /wards/{ward_id}/assets`
  - `GALI_CHAIN` → Find asset by street → `GET /assets/{asset_id}/chain`
  - `SCHEME_GAPS` → `GET /wards/{ward_id}/gaps`
- [ ] **Return query metadata**:
  ```python
  {
    "query_type": "WARD_SUMMARY",
    "endpoint": "/wards/{ward_id}/assets",
    "params": {"ward_id": "REG_W45"},
    "cypher": "...",  # Optional: for direct Neo4j queries
  }
  ```

#### 3.4 Answer Formatting (Optional)
- [ ] **Format backend response** into natural language answer
- [ ] **OR use LLM** to generate explanation from query results

---

## 4. Backend Integration: ID Filling & Entity Resolution

### Current State
- ✅ `POST /ingest/entities` endpoint exists
- ❌ **Missing ID generation logic** - currently requires `entity.id` to be provided
- ❌ **Missing entity resolution** (fuzzy matching against existing graph)

### Pending Tasks

#### 4.1 ID Generation Logic
- [ ] **Add ID generation function** in `backend/app/routers/ingest.py`:
  ```python
  def generate_entity_id(entity: IngestEntity, existing_ids: set) -> str
  ```
- [ ] **Implement ID patterns**:
  - Region: `REG_{WARD_NUMBER}` or `STREET_{WARD}_{STREET_NAME}`
  - Asset: `ASSET_{WARD}_{LOCATION}_{TYPE}_{YEAR}`
  - Scheme: `SCHEME_{SCHEME_NAME}_{YEAR}`
  - Actor: `ACTOR_{NAME_HASH}` or match existing
  - Evidence: `EVID_{ASSET_ID}_{BEFORE_AFTER}_{DATE}`
- [ ] **Handle missing IDs** in `ingest_entities()`:
  - If `entity.id` is empty/missing, generate using pattern
  - Check for duplicates before generating

#### 4.2 Entity Resolution (Fuzzy Matching)
- [ ] **Add RapidFuzz integration** (already in requirements.txt)
- [ ] **Implement entity resolution function**:
  ```python
  def resolve_entity(entity: IngestEntity, graph_session) -> Optional[str]
  ```
  - Query graph for existing entities of same type
  - Fuzzy match entity name against existing names
  - Return existing ID if match found (confidence > 85%)
- [ ] **Update `ingest_entities()`** to:
  - Try entity resolution first
  - If no match, generate new ID
  - Log resolution decisions

#### 4.3 Validation Before Ingestion
- [ ] **Validate entity properties** match 7-table schema:
  - Required fields per entity type
  - Valid enum values (e.g., asset.type must be drain/road/toilet/etc.)
- [ ] **Validate relationships**:
  - Check `from_id` and `to_id` exist (or will be created)
  - Validate relationship type is allowed
- [ ] **Return validation errors** in response if any

---

## 5. Frontend Integration: Live Ingestion Screen

### Current State
- ✅ File exists: `frontend/pages/04_⚡_Live_Ingestion.py`
- ❌ **Completely stub** - just shows placeholder text
- ❌ No UI components
- ❌ No API integration

### Pending Tasks

#### 5.1 UI Components
- [ ] **Text input area** (Streamlit `st.text_area`) for pasting PIB/news text
- [ ] **"Extract" button** that calls `ai_extraction.py`
- [ ] **JSON preview section** showing extracted entities and relations
- [ ] **"Ingest" button** that sends JSON to `POST /ingest/entities`
- [ ] **Success/error feedback** (Streamlit `st.success` / `st.error`)
- [ ] **Loading indicators** during extraction and ingestion

#### 5.2 Integration with AI Module
- [ ] **Import `ai.ai_extraction`** module
- [ ] **Call extraction function** on button click:
  ```python
  result = extract_entities_and_relations(text)
  ```
- [ ] **Display results** in formatted tables or JSON viewer
- [ ] **Store extracted JSON** in `st.session_state` for ingestion

#### 5.3 Integration with Backend
- [ ] **Use `httpx` or `requests`** to call FastAPI backend
- [ ] **Transform extracted JSON** to `IngestPayload` format
- [ ] **Handle API errors** gracefully
- [ ] **Show ingestion results** (entities_created, relations_created)

#### 5.4 Refresh After Ingestion
- [ ] **Trigger refresh** of ward/asset views after successful ingestion
- [ ] **Navigate to Ward Map** page to show new data
- [ ] **OR reload current page** data

---

## 6. Testing & Validation

### Pending Tasks
- [ ] **Unit tests for `ai_extraction.py`**:
  - Test with sample PIB text
  - Verify JSON structure
  - Test entity mapping
  - Test caching
- [ ] **Unit tests for `nl_query.py`**:
  - Test 3 fixed question patterns
  - Test parameter extraction
- [ ] **Integration test**:
  - End-to-end: text → extract → ingest → query
- [ ] **Test offline mode** (cached responses)
- [ ] **Test error handling** (LLM API failures, invalid JSON)

---

## 7. Documentation

### Pending Tasks
- [ ] **Document LLM API setup** in README
- [ ] **Document environment variables** needed (API keys)
- [ ] **Add example prompts** to `ai/` directory
- [ ] **Document caching strategy** for offline demo
- [ ] **Add troubleshooting guide** for common LLM issues

---

## Priority Order (Recommended Implementation Sequence)

1. **Dependencies & Config** (30 min)
   - Add LLM SDK to requirements.txt
   - Add config to `config.py`
   - Create `.env.example`

2. **Basic LLM Integration** (2-3 hours)
   - Implement `call_llm()` function
   - Build basic prompt
   - Test with sample text

3. **Entity Extraction Core** (3-4 hours)
   - Implement `extract_entities_and_relations()`
   - Add JSON parsing and validation
   - Test entity mapping

4. **Backend ID Filling** (2-3 hours)
   - Add ID generation logic
   - Update `ingest_entities()` endpoint
   - Test with missing IDs

5. **Frontend Live Ingestion** (2-3 hours)
   - Build UI components
   - Integrate with AI module
   - Integrate with backend

6. **Caching & Offline Mode** (1-2 hours)
   - Implement cache functions
   - Pre-generate demo cache
   - Test offline mode

7. **NL Query (Simplified)** (1-2 hours)
   - Implement pattern matching
   - Map to backend endpoints
   - Test 3 fixed questions

**Total Estimated Time: 12-18 hours**

---

## Quick Start Checklist

To get AI working quickly:

1. [ ] Choose LLM provider (recommend: OpenAI GPT-4o-mini for cost/quality balance)
2. [ ] Add SDK to `requirements.txt`
3. [ ] Add API key to `.env`
4. [ ] Implement basic `extract_entities_and_relations()` with LLM call
5. [ ] Test with one sample PIB text
6. [ ] Build Live Ingestion UI
7. [ ] Test end-to-end flow
8. [ ] Add caching for demo

---

**Owner**: Sreenu (AI & Frontend Lead)  
**Timeline**: Before March 10, 2026 MVP submission
