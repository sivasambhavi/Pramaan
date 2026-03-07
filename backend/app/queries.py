# Cypher query strings and helper functions

LIST_WARDS = """
MATCH (w:Ward)
RETURN w.id AS id, w.name AS name, w.region AS region
ORDER BY w.name
"""

WARD_GAPS = """
MATCH (w:Ward {id: $ward_id})-[:HAS_SCHEME]->(s:Scheme)
OPTIONAL MATCH (s)-[:HAS_GAP]->(g:Gap)
RETURN s.id AS scheme_id, s.name AS scheme_name,
       g.type AS gap_type, g.detail AS detail
"""

ASSET_CHAIN = """
MATCH path = (a:Asset {id: $asset_id})-[*0..5]-(n)
RETURN path
"""

MERGE_ENTITY = """
MERGE (n {id: $id})
SET n:$label
SET n += $properties
RETURN n
"""

MERGE_RELATION = """
MATCH (a {id: $from_id}), (b {id: $to_id})
MERGE (a)-[r:$type]->(b)
SET r += $properties
RETURN r
"""


def build_merge_entity_query(label: str) -> str:
    return f"""
    MERGE (n:{label} {{id: $id}})
    SET n += $properties
    RETURN n
    """


def build_merge_relation_query(rel_type: str) -> str:
    return f"""
    MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    SET r += $properties
    RETURN r
    """
