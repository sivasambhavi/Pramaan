from typing import Any, Optional
from pydantic import BaseModel


# --- Ward models ---

class WardSummary(BaseModel):
    id: str
    name: str
    region: Optional[str] = None


class GapItem(BaseModel):
    scheme_id: str
    scheme_name: str
    gap_type: str
    detail: Optional[str] = None


class WardGapsResponse(BaseModel):
    ward_id: str
    gaps: list[GapItem]


# --- Asset models ---

class ChainNode(BaseModel):
    node_id: str
    label: str
    properties: dict[str, Any]


class ChainEdge(BaseModel):
    from_id: str
    to_id: str
    relation: str


class AssetChainResponse(BaseModel):
    asset_id: str
    nodes: list[ChainNode]
    edges: list[ChainEdge]


# --- Ingest models ---

class Entity(BaseModel):
    id: str
    label: str
    properties: dict[str, Any] = {}


class Relation(BaseModel):
    from_id: str
    to_id: str
    type: str
    properties: dict[str, Any] = {}


class IngestPayload(BaseModel):
    entities: list[Entity] = []
    relations: list[Relation] = []


class IngestResponse(BaseModel):
    entities_created: int
    relations_created: int
