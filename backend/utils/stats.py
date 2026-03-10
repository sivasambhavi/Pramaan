def get_scheme_breakdown(ward_id: str, session) -> dict:
    # Use the hierarchical pattern to catch all 8+ assets (Direct + Street/Booth rollup)
    result = session.run("""
        MATCH (w:Region {region_id: $ward_id})
        MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)-[:PART_OF*0..3]->(w)
        OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
        RETURN coalesce(s.name, 'Other MCD Schemes') AS scheme, count(DISTINCT a) AS count
        ORDER BY count DESC
    """, ward_id=ward_id)
    return {r["scheme"]: r["count"] for r in result}
