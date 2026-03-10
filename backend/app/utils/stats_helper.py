from app.neo4j_client import get_session

def get_verified_asset_count(ward_id: str):
    """
    Unified logic to count verified assets for a ward.
    An asset is verified if it has at least one Evidence node or PROVES relationship.
    """
    query = """
    MATCH (w:Region {region_id: $ward_id})
    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)-[:PART_OF*0..3]->(w)
    OPTIONAL MATCH (e:Evidence)-[:PROVES]->(a)
    OPTIONAL MATCH (a)-[:MENTIONED_IN]->(n:NewsArticle)
    WITH a, count(DISTINCT e) AS ev_count, count(DISTINCT n) AS news_count
    WHERE news_count > 0 OR ev_count >= 2
    RETURN count(DISTINCT a) AS verified_count
    """
    with get_session() as session:
        result = session.run(query, ward_id=ward_id)
        record = result.single()
        return record["verified_count"] if record else 0
