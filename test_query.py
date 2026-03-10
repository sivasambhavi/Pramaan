from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))

with driver.session() as s:
    # Debug: show all regions with PART_OF relationships
    print("=== PART_OF relationships ===")
    r = s.run("MATCH (r:Region)-[:PART_OF]->(w:Region) RETURN r.region_id, w.region_id as parent LIMIT 30").data()
    for x in r:
        print(f"  {x['r.region_id']} -> {x['parent']}")

    print("\n=== Test hierarchy traversal for WARD45_SHAHDARA ===")
    r2 = s.run("""
    MATCH (w:Region {region_id: 'WARD45_SHAHDARA'})
    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE r.region_id = 'WARD45_SHAHDARA'
       OR EXISTS {
           MATCH (r)-[:PART_OF*1..3]->(w)
       }
    RETURN DISTINCT a.asset_id, r.region_id
    ORDER BY a.asset_id
    """).data()
    print(f"  Found {len(r2)} assets:")
    for x in r2:
        print(f"  {x}")

driver.close()
