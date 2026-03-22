import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load API keys and DB URI
load_dotenv()

uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
user = os.environ.get("NEO4J_USER", "neo4j")
password = os.environ.get("NEO4J_PASSWORD", "password")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # Modern Neo4j 5+ syntax for ACID unique constraints
    constraints = [
        "CREATE CONSTRAINT asset_id_unique IF NOT EXISTS FOR (a:Asset) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT ward_id_unique IF NOT EXISTS FOR (w:Ward) REQUIRE w.id IS UNIQUE",
        "CREATE CONSTRAINT scheme_id_unique IF NOT EXISTS FOR (s:Scheme) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT dept_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE"
    ]
    
    print(f"Connecting to Neo4j at {uri}...")
    with driver.session() as session:
        for c in constraints:
            try:
                session.run(c)
                print(f"[SUCCESS] Applied Constraint: {c.split(' FOR ')[1]}")
            except Exception as e:
                print(f"[ERROR] Failed applying {c}: {e}")
                
    driver.close()
    print("\n--- Neo4j database successfully locked with strict constraints! ---")

except Exception as err:
    print(f"Driver connection failed: {err}")
