"""
Pydantic models for Pramaan.

Node models reflect the exact Neo4j schema — property names here
are the source of truth for both the loader and the API layer.

API models (request/response) are kept separate at the bottom.

Changelog:
  v2 — Added lat/lon to RegionNode and AssetNode.
       Added proof_status, verified to AssetNode.
       Added AuditFields mixin: all live-ingested nodes carry lineage stamps.
       Fixed AssetChainResponse: funded_by -> built_by; added people_served, beneficiary_desc.
       Added ValidationEntry typed model for ingest audit log.
       source_type on IngestPayload now uses Literal for strict validation.
       Added ScrapeNewsResponse typed model.
  v5 — Models support 5-layer proof chain (Event → Response → Scheme → Asset → Evidence).
       /stats returns v5 governance metrics: funds_tracked, verified_assets, evidence, events.
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Audit-stamp mixin
#   Every node created via Live Ingestion carries these fields.
#   Seeded nodes may have these as None / default.
# ---------------------------------------------------------------------------

class AuditFields(BaseModel):
    """Lineage metadata written by the ingest pipeline on every AI-sourced node."""
    confidence:   Optional[float] = Field(None, ge=0.0, le=1.0,
                                          description="AI confidence score (0-1) at extraction time")
    source:       Optional[str]   = None   # "live_ingestion" | "seed"
    source_type:  Optional[str]   = None   # "unstructured_llm" | "unstructured_rss" | "csv_seed"
    ingested_at:  Optional[str]   = None   # ISO-8601 UTC timestamp
    ingested_by:  Optional[str]   = None   # "pramaan_live_ingestion" | "load_seed_data"


# ---------------------------------------------------------------------------
# Node models (match Neo4j properties exactly)
# ---------------------------------------------------------------------------

class RegionNode(AuditFields):
    region_id:        str                    # PK
    name:             str
    type:             str                    # country | state | district | city | zone | ward | street
    parent_region_id: Optional[str] = None  # FK -> Region.region_id
    lat:              Optional[float] = None  # geographic centroid written by load_seed_data
    lon:              Optional[float] = None


class SchemeNode(AuditFields):
    scheme_id: str                           # PK
    name:      str
    ministry:  Optional[str] = None
    category:  Optional[str] = None


class ActorNode(AuditFields):
    actor_id:  str                           # PK
    name:      str
    type:      str                           # government | elected_rep | contractor
    region_id: Optional[str] = None         # FK -> Region.region_id


class AssetNode(AuditFields):
    asset_id:     str                        # PK
    name:         str
    type:         str                        # drain | road | toilet | housing | streetlight | water_body
    region_id:    Optional[str]   = None     # FK -> Region.region_id
    scheme_id:    Optional[str]   = None     # FK -> Scheme.scheme_id
    actor_id:     Optional[str]   = None     # FK -> Actor.actor_id
    cost:         Optional[float] = None     # value in INR
    status:       Optional[str]   = None     # completed | in_progress | planned
    proof_status: Optional[str]   = None     # fully_verified | partially_verified | news_only | data_only | unverified
    verified:     Optional[bool]  = None     # True once manually marked verified
    lat:          Optional[float] = None     # map pin latitude
    lon:          Optional[float] = None     # map pin longitude


class BeneficiaryNode(AuditFields):
    beneficiary_id: str                      # PK
    scheme_id:      Optional[str] = None     # FK -> Scheme.scheme_id
    region_id:      Optional[str] = None     # FK -> Region.region_id
    count:          Optional[int] = None
    description:    Optional[str] = None


class EvidenceNode(AuditFields):
    evidence_id:     str                     # PK
    asset_id:        Optional[str] = None    # FK -> Asset.asset_id
    region_id:       Optional[str] = None    # FK -> Region.region_id
    type:            Optional[str] = None    # image | document | certificate
    url:             Optional[str] = None
    before_or_after: Optional[str] = None    # before | after
    capture_date:    Optional[str] = None


class EventNode(AuditFields):
    event_id:   str                          # PK
    name:       str
    event_type: Optional[str] = None        # completion | inauguration | handover
    date:       Optional[str] = None
    asset_id:   Optional[str] = None        # FK -> Asset.asset_id


# ---------------------------------------------------------------------------
# Relationship reference (documents all edges in one place)
#
#  Source Label      Relationship      Target Label      Driven by
#  -------------     ----------------  --------------    ------------------
#  Region            LOCATED_IN        Region            parent_region_id
#  Actor             REPRESENTS        Region            actor.region_id
#  Asset             LOCATED_IN        Region            asset.region_id
#  Scheme            FUNDS             Asset             asset.scheme_id
#  Asset             BUILT_BY          Actor             asset.actor_id
#  Scheme            BENEFITS          Beneficiary       beneficiary.scheme_id
#  Beneficiary       LIVES_IN          Region            beneficiary.region_id
#  Evidence          PROVES            Asset             evidence.asset_id
#  Evidence          CAPTURED_AT       Region            evidence.region_id
#  Event             RELATED_TO        Asset             event.asset_id
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class WardSummary(BaseModel):
    region_id: str
    name:      str
    type:      str
    lat:       Optional[float] = None   # geographic centroid for map rendering
    lon:       Optional[float] = None


class AssetSummary(BaseModel):
    asset_id:     str
    name:         str
    type:         Optional[str]   = None
    status:       Optional[str]   = None
    proof_status: Optional[str]   = None
    lat:          Optional[float] = None
    lon:          Optional[float] = None


class WardAssetsResponse(BaseModel):
    ward_id: str
    assets:  list[AssetSummary]


class GapItem(BaseModel):
    scheme_id:     str
    scheme_name:   str
    gap_type:      str
    linked_assets: int


class WardGapsResponse(BaseModel):
    ward_id: str
    gaps:    list[GapItem]


# ---------------------------------------------------------------------------
# Ward score response — full shape returned by GET /wards/{ward_id}/score
# ---------------------------------------------------------------------------

class AssetBreakdownItem(BaseModel):
    """One row in the ward-score asset_breakdown list."""
    asset_id:     Optional[str]   = None
    name:         Optional[str]   = None
    type:         Optional[str]   = None
    status:       Optional[str]   = None
    cost:         Optional[float] = None
    scheme_name:  Optional[str]   = None
    actor_name:   Optional[str]   = None
    proof_status: Optional[str]   = None  # fully_verified | partially_verified | news_only | data_only | unverified
    lat:          Optional[float] = None
    lon:          Optional[float] = None


class ProofStatusCounts(BaseModel):
    fully_verified:     int = 0
    partially_verified: int = 0
    news_only:          int = 0
    data_only:          int = 0
    unverified:         int = 0


class WardScoreResponse(BaseModel):
    """Full response from GET /wards/{ward_id}/score."""
    ward_id:          str
    total_assets:     int
    proven_assets:    int
    delivery_score:   float                        # 0-100
    counts:           ProofStatusCounts = Field(default_factory=ProofStatusCounts)
    scheme_breakdown: dict[str, int]    = {}       # scheme_name -> asset count
    asset_breakdown:  list[AssetBreakdownItem] = []


# Backward-compat alias — code that imported DeliveryScoreResponse still works
DeliveryScoreResponse = WardScoreResponse


# ---------------------------------------------------------------------------
# Asset proof chain
# ---------------------------------------------------------------------------

class AssetChainResponse(BaseModel):
    """Response from GET /assets/{asset_id}/chain."""
    asset_id:         str
    asset:            dict
    scheme:           Optional[dict] = None
    built_by:         Optional[dict] = None    # renamed from funded_by to match router
    region:           Optional[dict] = None
    ward:             Optional[dict] = None
    evidence:         list[dict]     = []
    beneficiaries:    list[dict]     = []
    people_served:    Optional[int]  = None
    beneficiary_desc: Optional[str]  = None


# ---------------------------------------------------------------------------
# Ingest API models
# ---------------------------------------------------------------------------

class IngestEntity(BaseModel):
    id:    str
    label: str                               # must be in ALLOWED_LABELS
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Free-form node properties. "
            "Expected keys: name (str), confidence (float 0-1). "
            "Asset nodes may include: cost (float INR), status (str), lat, lon."
        ),
    )


class IngestRelation(BaseModel):
    from_id:    str
    from_label: str
    to_id:      str
    to_label:   str
    type:       str                          # must be in ALLOWED_REL_TYPES
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Optional relation properties. "
            "May include: relevance (Direct Match|Zone Context|National Context|Unrelated), "
            "confidence (float 0-1), source_type (str)."
        ),
    )


class IngestPayload(BaseModel):
    entities:    list[IngestEntity]   = []
    relations:   list[IngestRelation] = []
    source_type: Literal["unstructured_llm", "unstructured_rss"] = "unstructured_llm"
    source_text: Optional[str] = None
    ai_model: Optional[str] = None
    ai_prompt_version: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation entry — typed audit record for ingest pipeline
# ---------------------------------------------------------------------------

class ValidationEntry(BaseModel):
    """Per-entity decision record returned in IngestResponse.validation_summary."""
    id:          str
    label:       str
    name:        str
    confidence:  float
    decision:    Literal[
        "ACCEPTED",
        "REJECTED_LOW_CONFIDENCE",
        "REJECTED_HALLUCINATION",
        "SKIPPED_DUPLICATE",
        "ERROR",
    ]
    reason:      Optional[str] = None    # populated when not ACCEPTED
    resolved_id: Optional[str] = None   # canonical Neo4j ID after resolution


class ValidationSummary(BaseModel):
    total_submitted: int
    accepted:        int
    rejected:        int
    log:             list[ValidationEntry] = []


class IngestResponse(BaseModel):
    entities_created:            int
    relations_created:           int
    delivery_chain:              Optional[dict]               = None
    # Validation telemetry
    skipped_low_confidence:      int                          = 0
    skipped_duplicates:          int                          = 0
    skipped_hallucinations:      int                          = 0
    skipped_unrelated_relations: int                          = 0
    validation_summary:          Optional[ValidationSummary] = None


# ---------------------------------------------------------------------------
# Scrape API models
# ---------------------------------------------------------------------------

class ArticleItem(BaseModel):
    """One news article returned by GET /scrape/news."""
    title:      str
    summary:    Optional[str]   = None
    published:  Optional[str]   = None
    link:       Optional[str]   = None
    relevance:  Optional[str]   = None    # Direct Match | Zone Context | National Context
    confidence: Optional[float] = None   # score_evidence confidence for this article


class ScrapeNewsResponse(BaseModel):
    """Response from GET /scrape/news."""
    entities:         list[IngestEntity]   = []
    relations:        list[IngestRelation] = []
    articles:         list[ArticleItem]    = []
    articles_dropped: int                  = 0    # filtered out as Unrelated
    source_type:      str                  = "unstructured_rss"
    message:          Optional[str]        = None  # set when all articles were Unrelated
