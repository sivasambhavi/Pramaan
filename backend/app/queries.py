# Cypher query strings and builder helpers for Pramaan.
#
# Schema conventions (match models.py and CSVs exactly):
#   - Region nodes use region_id as PK. Wards are Region{type:'ward'}
#   - Scheme nodes use scheme_id as PK
#   - Actor  nodes use actor_id  as PK
#   - Asset  nodes use asset_id  as PK
#   - Beneficiary nodes use beneficiary_id as PK
#   - Evidence    nodes use evidence_id    as PK
#   - Event       nodes use event_id       as PK
#
# Rules:
#   - Never interpolate user input into Cypher strings.
#   - Labels and rel types are whitelisted — only internal code builds them.
#   - All runtime values are passed as named $params.

# ---------------------------------------------------------------------------
# Ward (Region{type:'ward'}) queries
# ---------------------------------------------------------------------------

LIST_WARDS = """
MATCH (w:Region {type: 'ward'})
RETURN w.region_id AS region_id, w.name AS name, w.type AS type
ORDER BY w.name
"""

WARD_ASSETS = """
MATCH (w:Region {region_id: $ward_id})
MATCH (a:Asset)-[:LOCATED_IN]->(w)
RETURN a.asset_id  AS asset_id,
       a.name      AS name,
       a.type      AS type,
       a.status    AS status,
       a.cost      AS cost
ORDER BY a.name
"""

WARD_GAPS = """
MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(w:Region {region_id: $ward_id})
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
WITH s,
     count(DISTINCT a) AS asset_count,
     count(DISTINCT CASE WHEN e IS NOT NULL THEN a END) AS proven_count
RETURN s.scheme_id   AS scheme_id,
       s.name        AS scheme_name,
       CASE
           WHEN asset_count = 0              THEN 'no_assets'
           WHEN proven_count = asset_count   THEN 'complete'
           WHEN proven_count > 0             THEN 'partial'
           ELSE 'no_evidence'
       END            AS gap_type,
       asset_count    AS linked_assets,
       proven_count   AS proven_assets
ORDER BY proven_count ASC
"""

WARD_DELIVERY_SCORE = """
MATCH (w:Region {region_id: $ward_id})
OPTIONAL MATCH (a:Asset)-[:LOCATED_IN]->(w)
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
WITH count(DISTINCT a) AS total_assets,
     count(DISTINCT CASE WHEN e IS NOT NULL THEN a END) AS proven_assets
RETURN total_assets,
       proven_assets,
       CASE WHEN total_assets = 0 THEN 0.0
            ELSE round(100.0 * proven_assets / total_assets, 1)
       END AS delivery_score
"""

# ---------------------------------------------------------------------------
# Asset queries
# ---------------------------------------------------------------------------

ASSET_CHAIN = """
MATCH (a:Asset {asset_id: $asset_id})
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
OPTIONAL MATCH (a)-[:BUILT_BY]->(act:Actor)
OPTIONAL MATCH (a)-[:LOCATED_IN]->(r:Region {type: 'street'})
OPTIONAL MATCH (a)-[:LOCATED_IN]->(w:Region {type: 'ward'})
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
OPTIONAL MATCH (b:Beneficiary)-[:LIVES_IN]->(:Region)<-[:LOCATED_IN]-(a)
RETURN a, s, act, r, w,
       collect(DISTINCT e) AS evidence_list,
       collect(DISTINCT b) AS beneficiaries
"""

# ---------------------------------------------------------------------------
# Ingest helpers
# ---------------------------------------------------------------------------

ALLOWED_LABELS = {
    "Region", "Scheme", "Actor",
    "Asset", "Beneficiary", "Evidence", "Event",
}

ALLOWED_REL_TYPES = {
    "LOCATED_IN", "REPRESENTS", "FUNDS", "BUILT_BY",
    "BENEFITS", "LIVES_IN", "PROVES", "CAPTURED_AT", "RELATED_TO",
}


def build_merge_entity_query(label: str) -> str:
    """Return a MERGE query for a whitelisted node label."""
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unknown entity label: {label!r}")
    return f"""
    MERGE (n:{label} {{id: $id}})
    SET n += $properties
    RETURN n
    """


def build_merge_relation_query(rel_type: str) -> str:
    """Return a MERGE query for a whitelisted relationship type."""
    if rel_type not in ALLOWED_REL_TYPES:
        raise ValueError(f"Unknown relationship type: {rel_type!r}")
    return f"""
    MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    SET r += $properties
    RETURN r
    """
