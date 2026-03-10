import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "pramaa2026")

driver = GraphDatabase.driver(uri, auth=(user, password))

print(f"Connecting to {uri}...")

def run_diagnostic(tx):
    # Check hierarchy for STREET_W45_GALI7
    print("\n--- Hierarchy for STREET_W45_GALI7 ---")
    query = """
    MATCH (s:Region {region_id: 'STREET_W45_GALI7'})
    OPTIONAL MATCH p = (s)-[:PART_OF*1..3]->(w:Region {region_id: 'WARD45_SHAHDARA'})
    RETURN s.region_id, w.region_id, length(p) as hops
    """
    result = tx.run(query)
    for record in result:
        print(f"Path from {record['s.region_id']} to {record['w.region_id']}: {record['hops']} hops")

    # Check ALL PART_OF relations
    print("\n--- All PART_OF ---")
    query = "MATCH (a)-[r:PART_OF]->(b) RETURN a.region_id, b.region_id"
    result = tx.run(query)
    for record in result:
        print(f"{record['a.region_id']} -> {record['b.region_id']}")

    # Check assets in sub-regions
    print("\n--- Assets in sub-regions of Ward 45 ---")
    query = """
    MATCH (w:Region {region_id: 'WARD45_SHAHDARA'})
    MATCH (r:Region)-[:PART_OF*1..3]->(w)
    MATCH (a:Asset)-[:LOCATED_IN]->(r)
    RETURN a.asset_id, r.region_id
    """
    result = tx.run(query)
    for record in result:
        print(f"Asset {record['a.asset_id']} is in {record['r.region_id']}")

with driver.session() as session:
    session.execute_read(run_diagnostic)

driver.close()
