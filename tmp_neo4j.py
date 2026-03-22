from neo4j import GraphDatabase

def main():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "pramaa2026"))
    with driver.session() as session, open("neo4j_output.txt", "w") as f:
        f.write("--- ASSET LOCATIONS ---\n")
        res = session.run("MATCH (a:Asset)-[:LOCATED_IN]->(r:Region) RETURN r.region_id as region_id, count(a) AS count LIMIT 5")
        for rec in res:
            f.write(f"Region: {rec['region_id']}, Assets: {rec['count']}\n")
            
        f.write("\n--- DESCENDANT QUERY REG_W45 ---\n")
        res2 = session.run("MATCH (a:Asset)-[:LOCATED_IN]->(r:Region)<-[:CONTAINS*0..3]-(w:Region {region_id: 'REG_W45'}) RETURN count(a) as total")
        for rec in res2:
            f.write(f"Total descendant assets found: {rec['total']}\n")

        f.write("\n--- PARENT QUERY REG_W45 ---\n")
        res3 = session.run("MATCH (w:Region {region_id: 'REG_W45'})-[:CONTAINS]->(child) RETURN child.region_id as crid LIMIT 5")
        for rec in res3:
            f.write(f"Contains child: {rec['crid']}\n")
            
        f.write("\n--- WARD METADATA ---\n")
        res4 = session.run("MATCH (r:Region {region_id: 'REG_W45'}) RETURN r.name as name")
        for rec in res4:
            f.write(f"Ward Name: {rec['name']}\n")

if __name__ == '__main__':
    main()
