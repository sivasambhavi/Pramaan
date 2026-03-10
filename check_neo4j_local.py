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
    # Check Ward 45 node
    result = tx.run("MATCH (w:Region {region_id: 'WARD45_SHAHDARA'}) RETURN w")
    if not result.peek():
        print("ERROR: Ward 45 node NOT FOUND!")
        return
    print("Ward 45 node found.")

    # Count assets directly in Ward 45
    result = tx.run("MATCH (a:Asset)-[:LOCATED_IN]->(:Region {region_id: 'WARD45_SHAHDARA'}) RETURN count(a) as count")
    print(f"Direct assets in Ward 45: {result.single()['count']}")

    # Count all assets in Ward 45 including hierarchy
    query = """
    MATCH (w:Region {region_id: 'WARD45_SHAHDARA'})
    MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)
    WHERE r.region_id = 'WARD45_SHAHDARA'
       OR (r)-[:PART_OF*1..3]->(w)
    RETURN count(DISTINCT a) as count
    """
    result = tx.run(query)
    print(f"Hierarchical assets in Ward 45: {result.single()['count']}")

    # Inspect streets
    print("\n--- Street Hierarchy Check ---")
    query = """
    MATCH (s:Region {type: 'street'})-[rel:PART_OF*1..3]->(w:Region {region_id: 'WARD45_SHAHDARA'})
    RETURN s.region_id as street, s.name as name, length(rel) as hops
    """
    result = tx.run(query)
    for record in result:
        print(f"Street {record['street']} ({record['name']}) -> Ward 45 in {record['hops']} hops")

with driver.session() as session:
    session.execute_read(run_diagnostic)

driver.close()
