"""
Pydantic models for Pramaan.

Node models reflect the exact Neo4j schema — property names here
are the source of truth for both the loader and the API layer.

API models (request/response) are kept separate at the bottom.
"""

from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Node models (match Neo4j properties exactly)
# ---------------------------------------------------------------------------

class RegionNode(BaseModel):
    region_id: str                       # PK
    name: str
    type: str                            # city | zone | ward | street
    parent_region_id: Optional[str] = None  # FK → Region.region_id


class SchemeNode(BaseModel):
    scheme_id: str                       # PK
    name: str
    ministry: Optional[str] = None
    category: Optional[str] = None


class ActorNode(BaseModel):
    actor_id: str                        # PK
    name: str
    type: str                            # government | elected_rep | contractor
    region_id: Optional[str] = None     # FK → Region.region_id


class AssetNode(BaseModel):
    asset_id: str                        # PK
    name: str
    type: str                            # drain | road | toilet | housing | streetlight | water_body
    region_id: Optional[str] = None     # FK → Region.region_id
    scheme_id: Optional[str] = None     # FK → Scheme.scheme_id
    actor_id: Optional[str] = None      # FK → Actor.actor_id
    cost: Optional[float] = None
    status: Optional[str] = None        # completed | in_progress | planned


class BeneficiaryNode(BaseModel):
    beneficiary_id: str                  # PK
    scheme_id: Optional[str] = None     # FK → Scheme.scheme_id
    region_id: Optional[str] = None     # FK → Region.region_id
    count: Optional[int] = None
    description: Optional[str] = None


class EvidenceNode(BaseModel):
    evidence_id: str                     # PK
    asset_id: Optional[str] = None      # FK → Asset.asset_id
    region_id: Optional[str] = None     # FK → Region.region_id
    type: Optional[str] = None          # image | document | certificate
    url: Optional[str] = None
    before_or_after: Optional[str] = None   # before | after
    capture_date: Optional[str] = None


class EventNode(BaseModel):
    event_id: str                        # PK
    name: str
    event_type: Optional[str] = None    # completion | inauguration | handover
    date: Optional[str] = None
    asset_id: Optional[str] = None      # FK → Asset.asset_id


# ---------------------------------------------------------------------------
# Relationship reference (documents all edges in one place)
#
#  Source Label      Relationship      Target Label      Driven by
#  ─────────────     ────────────────  ──────────────    ──────────────────
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
    name: str
    type: str


class AssetSummary(BaseModel):
    asset_id: str
    name: str
    type: Optional[str] = None
    status: Optional[str] = None


class WardAssetsResponse(BaseModel):
    ward_id: str
    assets: list[AssetSummary]


class GapItem(BaseModel):
    scheme_id: str
    scheme_name: str
    gap_type: str
    linked_assets: int


class WardGapsResponse(BaseModel):
    ward_id: str
    gaps: list[GapItem]


class DeliveryScoreResponse(BaseModel):
    ward_id: str
    total_assets: int
    proven_assets: int
    delivery_score: float


class AssetChainResponse(BaseModel):
    asset_id: str
    asset: dict
    scheme: Optional[dict] = None
    funded_by: Optional[dict] = None
    region: Optional[dict] = None
    ward: Optional[dict] = None
    evidence: list[dict] = []
    beneficiaries: list[dict] = []


# ---------------------------------------------------------------------------
# Ingest API models
# ---------------------------------------------------------------------------

class IngestEntity(BaseModel):
    id: str
    label: str                           # must be in ALLOWED_LABELS
    properties: dict = {}


class IngestRelation(BaseModel):
    from_id: str
    to_id: str
    type: str                            # must be in ALLOWED_REL_TYPES
    properties: dict = {}


class IngestPayload(BaseModel):
    entities: list[IngestEntity] = []
    relations: list[IngestRelation] = []


class IngestResponse(BaseModel):
    entities_created: int
    relations_created: int
