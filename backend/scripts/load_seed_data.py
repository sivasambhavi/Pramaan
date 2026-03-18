"""
Ingestion script for Pramaan - Global Ontology Engine.
Loads the 7 formalized CSV files into Neo4j with correct relationships.
"""

import pandas as pd
from pathlib import Path
from app.config import settings
from app.neo4j_client import get_driver

# Config
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "resources" / "data" / "final_formalized"

def run_cypher(session, query, parameters=None):
    try:
        session.run(query, parameters)
    except Exception as e:
        print(f"Error executing query: {e}")

def main() -> None:
    if not DATA_DIR.exists():
        print(f"ERROR: Data directory not found at {DATA_DIR}")
        return

    driver = get_driver()
    with driver.session() as session:
        # --- 1. LOAD REGIONS ---
        print("Loading Regions...")
        df_reg = pd.read_csv(DATA_DIR / "regions.csv").fillna("")
        for _, row in df_reg.iterrows():
            session.run("""
                MERGE (r:Region {region_id: $region_id})
                SET r.name = $name, r.type = $type,
                    r.source_type = 'official_csv', r.confidence = 1.0, r.ingested_by = 'seed_script'
            """, row.to_dict())
            if row['parent_region_id']:
                session.run("""
                    MATCH (child:Region {region_id: $region_id})
                    MATCH (parent:Region {region_id: $parent_region_id})
                    MERGE (child)-[:LOCATED_IN]->(parent)
                """, row.to_dict())

        # --- 3. LOAD SCHEMES ---
        print("Loading Schemes...")
        df_schemes = pd.read_csv(DATA_DIR / "schemes.csv").fillna("")
        for _, row in df_schemes.iterrows():
            session.run("""
                MERGE (s:Scheme {scheme_id: $scheme_id})
                SET s.name = $name, s.ministry = $ministry, s.category = $category,
                    s.source_type = 'official_csv', s.confidence = 1.0, s.ingested_by = 'seed_script'
            """, row.to_dict())

        # --- 3B. LOAD SCHEME ALLOCATIONS ---
        allocations_path = DATA_DIR / "scheme_allocations.csv"
        if allocations_path.exists():
            print("Loading Scheme Allocations...")
            df_alloc = pd.read_csv(allocations_path).fillna("")
            for _, row in df_alloc.iterrows():
                # Ensure region via name
                session.run("""
                    MERGE (r:Region {name: $region_name})
                    ON CREATE SET r.region_id = 'reg_' + toLower(replace($region_name, ' ', '_')), r.type = 'state'
                """, {"region_name": row['region_name']})
                
                session.run("""
                    MERGE (sa:SchemeAllocation {allocation_id: $allocation_id})
                    SET sa.total_allocated = $total_allocated, sa.total_completed = $total_completed, sa.unit = $unit
                    WITH sa
                    MATCH (s:Scheme {scheme_id: $scheme_id})
                    MERGE (s)-[:ALLOCATED]->(sa)
                    WITH sa
                    MATCH (r:Region {name: $region_name})
                    MERGE (sa)-[:FOR_REGION]->(r)
                """, row.to_dict())

        # --- 4. LOAD ACTORS ---
        print("Loading Actors...")
        df_actors = pd.read_csv(DATA_DIR / "actors.csv").fillna("")
        for _, row in df_actors.iterrows():
            session.run("""
                MERGE (a:Actor {actor_id: $actor_id})
                SET a.name = $name, a.type = $type,
                    a.source_type = 'official_csv', a.confidence = 1.0, a.ingested_by = 'seed_script'
            """, row.to_dict())
            if row['region_id']:
                session.run("""
                    MATCH (a:Actor {actor_id: $actor_id})
                    MATCH (r:Region {region_id: $region_id})
                    MERGE (a)-[:REPRESENTS]->(r)
                """, row.to_dict())

        # --- 4B. LOAD ENRICHED ACTORS ---
        actors_env_path = DATA_DIR / "actors_enriched.csv"
        if actors_env_path.exists():
            print("Loading Enriched Actors (Tenders)...")
            df_actors_en = pd.read_csv(actors_env_path).fillna("")
            for _, row in df_actors_en.iterrows():
                session.run("""
                    MERGE (a:Actor {actor_id: $actor_id})
                    SET a.name = $name, a.type = $type, a.total_tenders = $total_tenders, a.budget_lakhs = $budget_lakhs
                """, row.to_dict())
                if row['region_id']:
                    session.run("""
                        MATCH (a:Actor {actor_id: $actor_id})
                        MATCH (r:Region {region_id: $region_id})
                        MERGE (a)-[:REPRESENTS]->(r)
                    """, row.to_dict())

        # --- 5. LOAD ASSETS ---
        print("Loading Assets...")
        df_assets = pd.read_csv(DATA_DIR / "assets.csv").fillna("")
        for _, row in df_assets.iterrows():
            session.run("""
                MERGE (a:Asset {asset_id: $asset_id})
                SET a.name = $name, a.type = $type,
                    a.cost = $cost, a.status = $status, a.lat = $lat, a.lon = $lon,
                    a.source_type = $source_type, a.confidence = $confidence,
                    a.ingested_by = 'seed_script'
            """, {**row.to_dict(),
                  "source_type": row.get("source_type", "official_csv"),
                  "confidence": float(row.get("confidence", 1.0))})
            # Relationships
            if row['region_id']:
                session.run("MATCH (a:Asset {asset_id: $id}) MATCH (r:Region {region_id: $rid}) MERGE (a)-[:LOCATED_IN]->(r)", {"id": row['asset_id'], "rid": row['region_id']})
            if row['scheme_id']:
                session.run("MATCH (a:Asset {asset_id: $id}) MATCH (s:Scheme {scheme_id: $sid}) MERGE (s)-[:FUNDS]->(a)", {"id": row['asset_id'], "sid": row['scheme_id']})
            if row['actor_id']:
                session.run("MATCH (a:Asset {asset_id: $id}) MATCH (act:Actor {actor_id: $aid}) MERGE (a)-[:BUILT_BY]->(act)", {"id": row['asset_id'], "aid": row['actor_id']})

        # --- 6. LOAD BENEFICIARIES ---
        print("Loading Beneficiaries...")
        df_ben = pd.read_csv(DATA_DIR / "beneficiaries.csv").fillna("")
        for _, row in df_ben.iterrows():
            session.run("""
                MERGE (b:Beneficiary {beneficiary_id: $beneficiary_id})
                SET b.count = $count, b.description = $description, b.scheme_id = $scheme_id, b.region_id = $region_id
            """, row.to_dict())
            if row['scheme_id']:
                session.run("MATCH (b:Beneficiary {beneficiary_id: $id}) MATCH (s:Scheme {scheme_id: $sid}) MERGE (s)-[:BENEFITS]->(b)", {"id": row['beneficiary_id'], "sid": row['scheme_id']})
            if row['region_id']:
                session.run("MATCH (b:Beneficiary {beneficiary_id: $id}) MATCH (r:Region {region_id: $rid}) MERGE (b)-[:LIVES_IN]->(r)", {"id": row['beneficiary_id'], "rid": row['region_id']})

        # --- 7. LOAD EVIDENCE ---
        print("Loading Evidence...")
        df_ev = pd.read_csv(DATA_DIR / "evidence.csv").fillna("")
        for _, row in df_ev.iterrows():
            session.run("""
                MERGE (e:Evidence {evidence_id: $evidence_id})
                SET e.type = $type, e.url = $url, e.before_or_after = $before_or_after, e.capture_date = $capture_date
            """, row.to_dict())
            if row['asset_id']:
                session.run("MATCH (e:Evidence {evidence_id: $id}) MATCH (a:Asset {asset_id: $aid}) MERGE (e)-[:PROVES]->(a)", {"id": row['evidence_id'], "aid": row['asset_id']})
            if row['region_id']:
                session.run("MATCH (e:Evidence {evidence_id: $id}) MATCH (r:Region {region_id: $rid}) MERGE (e)-[:CAPTURED_AT]->(r)", {"id": row['evidence_id'], "rid": row['region_id']})

        # --- 8. LOAD EVENTS ---
        print("Loading Events...")
        df_events = pd.read_csv(DATA_DIR / "events.csv").fillna("")
        for _, row in df_events.iterrows():
            session.run("""
                MERGE (e:Event {event_id: $event_id})
                SET e.name = $name, e.event_type = $event_type, e.date = $date
            """, row.to_dict())
            if row['asset_id']:
                session.run("MATCH (e:Event {event_id: $id}) MATCH (a:Asset {asset_id: $aid}) MERGE (e)-[:RELATED_TO]->(a)", {"id": row['event_id'], "aid": row['asset_id']})

    print("\nSUCCESS: Governance Knowledge Graph Ingested.")

if __name__ == "__main__":
    main()

