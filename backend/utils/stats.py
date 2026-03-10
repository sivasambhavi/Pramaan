def get_scheme_breakdown(ward_name: str, session) -> dict:
    # Use the schema relationship to find assets in the ward
    result = session.run("""
        MATCH (a:Asset)-[:LOCATED_IN]->(r:Region {name: $ward})
        OPTIONAL MATCH (s:Scheme)-[:FUNDS]->(a)
        RETURN coalesce(s.name, a.scheme, 'Unknown') AS scheme, count(a) AS count
        ORDER BY count DESC
    """, ward=ward_name)
    return {r["scheme"]: r["count"] for r in result}
