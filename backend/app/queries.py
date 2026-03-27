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
MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)<-[:CONTAINS*0..3]-(w)
RETURN DISTINCT a.asset_id  AS asset_id,
       a.name      AS name,
       a.type      AS type,
       a.status    AS status,
       a.cost      AS cost,
       a.lat       AS lat,
       a.lon       AS lon
ORDER BY a.name
"""

WARD_GAPS = """
MATCH (s:Scheme)-[:FUNDS]->(a:Asset)-[:LOCATED_IN]->(w:Region {region_id: $ward_id})
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
  WHERE e.url_or_path IS NOT NULL AND trim(e.url_or_path) <> '' AND e.url_or_path <> 'N/A'
OPTIONAL MATCH (a)-[:MENTIONED_IN]->(n:NewsArticle)
WITH s,
     count(DISTINCT a) AS asset_count,
     count(DISTINCT CASE WHEN (e IS NOT NULL OR n IS NOT NULL) THEN a END) AS proven_count
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

LIST_WARD_ASSETS = """
MATCH (w:Region {region_id: $ward_id})
MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)<-[:CONTAINS*0..3]-(w)
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
RETURN a.asset_id AS id, a.name AS name, a.type AS type, collect(s.name) AS schemes, count(e) > 0 AS verified, a.status AS status
"""

LIST_ALL_ASSETS = """
MATCH (w:Region {region_id: $ward_region_id})
MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)<-[:CONTAINS*0..3]-(w)
RETURN DISTINCT a.asset_id AS asset_id, a.name AS name, a.type AS type, a.status AS status, a.cost AS cost,
       a.proof_status AS proof_status, r.region_id as region_id, r.name as region_name
ORDER BY a.type, a.name
"""


# ---------------------------------------------------------------------------
# Mapping of Labels to their Primary Key property names
# ---------------------------------------------------------------------------
PK_MAP = {
    "Region":      "region_id",
    "Scheme":      "scheme_id",
    "Actor":       "actor_id",
    "Asset":       "asset_id",
    "Beneficiary": "beneficiary_id",
    "Evidence":    "evidence_id",
    "Event":       "event_id",
    "Domain":      "domain_id",
    "Policy":      "policy_id",
    "Impact":      "impact_id",
}

WARD_ASSET_DETAIL = """
MATCH (w:Region {region_id: $ward_id})
MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)<-[:CONTAINS*0..3]-(w)
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
OPTIONAL MATCH (a)-[:BUILT_BY]->(act:Actor)
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
  WHERE e.url_or_path IS NOT NULL AND trim(e.url_or_path) <> '' AND e.url_or_path <> 'N/A'
OPTIONAL MATCH (a)-[:MENTIONED_IN]->(n:NewsArticle)
WITH a,
     collect(DISTINCT s.name)      AS scheme_names,
     collect(DISTINCT s.scheme_id) AS scheme_ids,
     collect(DISTINCT act.name)    AS actor_names,
     count(DISTINCT e)             AS ev_count,
     count(DISTINCT n)             AS news_count
RETURN
  a.asset_id  AS asset_id,
  a.name      AS name,
  a.type      AS type,
  a.status    AS status,
  a.cost      AS cost,
  CASE
       WHEN (news_count > 0 OR ev_count >= 2) THEN 'fully_verified'
       WHEN (ev_count = 1)                    THEN 'partially_verified'
       ELSE 'unverified'
  END AS proof_status,
  a.lat        AS lat,
  a.lon        AS lon,
  scheme_names[0]  AS scheme_name,
  scheme_ids[0]    AS scheme_id,
  actor_names[0]   AS actor_name
ORDER BY a.name
"""

# ---------------------------------------------------------------------------
# Asset queries
# ---------------------------------------------------------------------------

ASSET_CHAIN = """
MATCH (a:Asset {asset_id: $asset_id})
OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
OPTIONAL MATCH (a)-[:BUILT_BY]->(act:Actor)
OPTIONAL MATCH (a)-[:LOCATED_IN]->(street:Region {type: 'street'})
OPTIONAL MATCH (a)-[:LOCATED_IN]->(ward:Region {type: 'ward'})
OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
OPTIONAL MATCH (b:Beneficiary) WHERE b.asset_id = a.asset_id
WITH a, s, act, street, ward, e, b
OPTIONAL MATCH (s)-[:BENEFITS]->(b2:Beneficiary)-[:LIVES_IN]->(ward) WHERE b IS NULL
WITH a, s, act, street, ward, collect(DISTINCT e) AS evidence_list, b, b2
RETURN a, s, act, street, ward,
       evidence_list,
       COALESCE(b.count, b2.count) AS people_served,
       COALESCE(b.description, b2.description) AS beneficiary_desc
"""

GET_WARDS_WITH_ASSETS = """
MATCH (a:Asset)-[:LOCATED_IN]->(r:Region {type: 'ward'})
RETURN DISTINCT r.region_id AS region_id, r.name AS name, count(a) AS asset_count
ORDER BY asset_count DESC
"""

DISTRICT_COMPARISON = """
MATCH (r:Region {type:'ward'})
OPTIONAL MATCH (a:Asset)-[:LOCATED_IN]->(r)
RETURN r.name AS ward_name, count(a) AS assets
ORDER BY assets DESC
"""

# ---------------------------------------------------------------------------
# Blast score — dynamic event risk scoring from graph topology
# ---------------------------------------------------------------------------
#
# Weights (sum = 10.0 max):
#   3.0  — Impact density      (CAUSED edges, capped at 5 impacts = full)
#   2.0  — Evidence volume     (PROVEN_BY edges, capped at 5)
#   1.5  — Evidence velocity   (PROVEN_BY edges ingested in last 24 h, capped at 3)
#   2.0  — Cross-domain spread (CONNECTED_TO edges to other events, capped at 4)
#   0.5  — Domain breadth      (ALSO_IN secondary domains, capped at 3)
#   1.0  — Source credibility  (avg confidence of connected Evidence nodes)
#
# Thresholds: >= 8.5 → critical  |  >= 6.5 → high  |  >= 4.0 → medium  |  else → low
#
# The query also writes e.blast_score back to each Event node so the value is
# persistent and readable by list_events() without re-running the full calc.
# Pass $since_24h as an ISO-8601 string (datetime - 24h) for velocity window.

BLAST_SCORE_CYPHER = """
MATCH (e:Event)
WHERE e.confidence IS NOT NULL
OPTIONAL MATCH (e)-[:CAUSED]->(i:Impact)
OPTIONAL MATCH (e)-[:PROVEN_BY]->(ev:Evidence)
OPTIONAL MATCH (e)-[:CONNECTED_TO]-(other:Event)
OPTIONAL MATCH (e)-[:ALSO_IN]->(d2:Domain)
WITH e,
     count(DISTINCT i)     AS impact_count,
     count(DISTINCT ev)    AS evidence_count,
     count(DISTINCT other) AS connection_count,
     count(DISTINCT d2)    AS cross_domain_count,
     avg(COALESCE(toFloat(ev.confidence), 0.7)) AS avg_src_confidence
OPTIONAL MATCH (e)-[:PROVEN_BY]->(ev2:Evidence)
WHERE ev2.ingested_at IS NOT NULL
  AND ev2.ingested_at >= $since_24h
WITH e, impact_count, evidence_count, connection_count,
     cross_domain_count, avg_src_confidence,
     count(DISTINCT ev2) AS recent_evidence
WITH e,
     (CASE WHEN impact_count     >= 5 THEN 3.0 ELSE toFloat(impact_count)     / 5.0 * 3.0 END
    + CASE WHEN evidence_count   >= 5 THEN 2.0 ELSE toFloat(evidence_count)   / 5.0 * 2.0 END
    + CASE WHEN recent_evidence  >= 3 THEN 1.5 ELSE toFloat(recent_evidence)  / 3.0 * 1.5 END
    + CASE WHEN connection_count >= 4 THEN 2.0 ELSE toFloat(connection_count) / 4.0 * 2.0 END
    + CASE WHEN cross_domain_count >= 3 THEN 0.5 ELSE toFloat(cross_domain_count) / 3.0 * 0.5 END
    + COALESCE(avg_src_confidence, 0.7) * 1.0) AS raw_score,
     impact_count, evidence_count, connection_count,
     cross_domain_count, recent_evidence
WITH e,
     CASE WHEN raw_score > 10.0 THEN 10.0 ELSE raw_score END AS blast_score,
     impact_count, evidence_count, connection_count,
     cross_domain_count, recent_evidence
SET e.blast_score = round(blast_score * 10) / 10.0
RETURN e.event_id AS event_id,
       e.name     AS name,
       round(blast_score * 10) / 10.0 AS blast_score,
       CASE
         WHEN blast_score >= 8.5 THEN 'critical'
         WHEN blast_score >= 6.5 THEN 'high'
         WHEN blast_score >= 4.0 THEN 'medium'
         ELSE 'low'
       END AS computed_severity,
       impact_count, evidence_count, connection_count,
       cross_domain_count, recent_evidence
ORDER BY blast_score DESC
"""

# ---------------------------------------------------------------------------
# Ingest helpers
# ---------------------------------------------------------------------------

ALLOWED_LABELS = {
    "Region", "Scheme", "Actor",
    "Asset", "Beneficiary", "Evidence", "Event",
    "Domain", "Policy", "Impact",
}

ALLOWED_REL_TYPES = {
    "LOCATED_IN", "REPRESENTS", "FUNDS", "BUILT_BY",
    "BENEFITS", "LIVES_IN", "PROVES", "CAPTURED_AT", "RELATED_TO",
    "SANCTIONS", "PROVIDES", "IMPLEMENTS", "MANAGES", "OPERATES",
    "SERVES", "MONITORS", "APPROVES",
    # Event-graph edge types
    "OCCURRED_IN", "BELONGS_TO", "ALSO_IN", "MANAGED_BY", "FUNDED_BY",
    "CAUSED", "TRIGGERED", "PROVEN_BY", "CONNECTED_TO", "PART_OF", "HAS_EVIDENCE",
}

# Map AI-generated relation types -> canonical types for consistency
REL_TYPE_NORMALIZER = {
    "SANCTIONS": "FUNDS",
    "PROVIDES": "BENEFITS",
    "IMPLEMENTS": "BUILT_BY",
    "MANAGES": "BUILT_BY",
    "OPERATES": "BUILT_BY",
    "SERVES": "BENEFITS",
    "MONITORS": "RELATED_TO",
    "APPROVES": "FUNDS",
}


def validate_extracted(
    entities: list[dict],
    relations: list[dict],
) -> tuple[list[dict], list[dict], int]:
    """
    Validate LLM-extracted entities and relations before Neo4j write.

    Checks:
      - Entity has non-empty 'id' and 'label'
      - Entity label is in ALLOWED_LABELS
      - Entity 'properties' is a dict (defaults to {} if missing)
      - Relation has non-empty from_id, from_label, to_id, to_label, type
      - Relation labels are in ALLOWED_LABELS
      - Relation type is in ALLOWED_REL_TYPES (after normalization)

    Returns (valid_entities, valid_relations, skipped_count).
    """
    import logging
    log = logging.getLogger("pramaan.validation")

    valid_ents: list[dict] = []
    valid_rels: list[dict] = []
    skipped = 0

    for ent in entities:
        eid   = str(ent.get("id",    "")).strip()
        label = str(ent.get("label", "")).strip()
        if not eid:
            log.warning("[validate] entity dropped — missing id: %r", ent)
            skipped += 1
            continue
        if not label or label not in ALLOWED_LABELS:
            log.warning("[validate] entity dropped — invalid label %r (id=%s)", label, eid)
            skipped += 1
            continue
        if not isinstance(ent.get("properties"), dict):
            ent = {**ent, "properties": {}}
        valid_ents.append(ent)

    for rel in relations:
        fid   = str(rel.get("from_id",    "")).strip()
        fl    = str(rel.get("from_label", "")).strip()
        tid   = str(rel.get("to_id",      "")).strip()
        tl    = str(rel.get("to_label",   "")).strip()
        rtype = str(rel.get("type",       "")).strip()
        rtype_norm = REL_TYPE_NORMALIZER.get(rtype, rtype)

        if not all([fid, fl, tid, tl, rtype]):
            log.warning("[validate] relation dropped — missing fields: %r", rel)
            skipped += 1
            continue
        if fl not in ALLOWED_LABELS or tl not in ALLOWED_LABELS:
            log.warning("[validate] relation dropped — invalid label(s) %r→%r", fl, tl)
            skipped += 1
            continue
        if rtype_norm not in ALLOWED_REL_TYPES:
            log.warning("[validate] relation dropped — unknown type %r", rtype)
            skipped += 1
            continue
        valid_rels.append(rel)

    if skipped:
        log.info("[validate] %d entity/relation(s) dropped by schema validation", skipped)

    return valid_ents, valid_rels, skipped


def build_merge_entity_query(label: str) -> str:
    """Return a MERGE query for a whitelisted node label with its specific PK."""
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unknown entity label: {label!r}")
    
    pk_field = PK_MAP.get(label, "id")
    return f"""
    MERGE (n:{label} {{{pk_field}: $id}})
    SET n += $properties
    RETURN n
    """


# Base confidence per source type — used for relationship scoring
SOURCE_CONFIDENCE = {
    "structured_csv":      1.0,
    "semi_structured_kml": 0.95,
    "semi_structured_xlsx": 0.9,
    "unstructured_llm":    0.7,
    "unstructured_rss":    0.6,
    "scheduler":           0.6,
}


def build_merge_relation_query(rel_type: str, from_label: str, to_label: str) -> str:
    """Return a scored MERGE query for a whitelisted relationship type.

    Callers must supply params: from_id, to_id, properties, source_type, now, base_confidence.

    ON CREATE: stamps confidence, first_seen, source_types.
    ON MATCH:  increments asserted_count, boosts confidence by +0.1 per corroboration (cap 1.0),
               appends new source_type to source_types list.
    """
    rel_type = REL_TYPE_NORMALIZER.get(rel_type, rel_type)
    if rel_type not in ALLOWED_REL_TYPES:
        raise ValueError(f"Unknown relationship type: {rel_type!r}")

    from_pk = PK_MAP.get(from_label, "id")
    to_pk   = PK_MAP.get(to_label,   "id")

    return f"""
    MATCH (a:{from_label} {{{from_pk}: $from_id}}), (b:{to_label} {{{to_pk}: $to_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    ON CREATE SET
        r.asserted_count = 1,
        r.confidence     = $base_confidence,
        r.first_seen     = $now,
        r.last_seen      = $now,
        r.source_types   = [$source_type]
    ON MATCH SET
        r.asserted_count = coalesce(r.asserted_count, 0) + 1,
        r.confidence     = CASE
            WHEN r.confidence IS NULL THEN $base_confidence
            ELSE min(1.0, r.confidence + 0.1)
        END,
        r.last_seen      = $now,
        r.source_types   = CASE
            WHEN $source_type IN coalesce(r.source_types, []) THEN coalesce(r.source_types, [])
            ELSE coalesce(r.source_types, []) + [$source_type]
        END
    SET r += $properties
    RETURN r
    """


# Detect relationship conflicts:
# An asset with 2+ distinct BUILT_BY actors or 2+ funding schemes signals a conflict.
DETECT_CONFLICTS = """
MATCH (a:Asset)-[r:BUILT_BY]->(act:Actor)
WITH a, collect({actor_id: act.actor_id, name: act.name,
                 confidence: r.confidence, sources: r.source_types,
                 asserted: r.asserted_count}) AS builders
WHERE size(builders) > 1
RETURN a.asset_id   AS asset_id,
       a.name       AS asset_name,
       'BUILT_BY'   AS conflict_type,
       builders     AS conflicting_parties

UNION

MATCH (s:Scheme)-[r:FUNDS]->(a:Asset)
WITH a, collect({scheme_id: s.scheme_id, name: s.name,
                 confidence: r.confidence, sources: r.source_types,
                 asserted: r.asserted_count}) AS funders
WHERE size(funders) > 1
RETURN a.asset_id   AS asset_id,
       a.name       AS asset_name,
       'FUNDS'      AS conflict_type,
       funders      AS conflicting_parties
ORDER BY asset_id
"""
