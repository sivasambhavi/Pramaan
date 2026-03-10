import os
import csv
import logging
from typing import List, Dict, Any
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "pramaa2026")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class PramaanDataSeeder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def wait_for_db(self):
        try:
             self.driver.verify_connectivity()
             logger.info("Successfully connected to Neo4j.")
        except Exception as e:
             logger.error(f"Failed to connect to Neo4j at {NEO4J_URI}: {e}")
             raise

    def setup_schema(self, tx):
        logger.info("Setting up constraints...")
        constraints = [
            "CREATE CONSTRAINT region_id_idx IF NOT EXISTS FOR (r:Region) REQUIRE r.region_id IS UNIQUE",
            "CREATE CONSTRAINT scheme_id_idx IF NOT EXISTS FOR (s:Scheme) REQUIRE s.scheme_id IS UNIQUE",
            "CREATE CONSTRAINT actor_id_idx IF NOT EXISTS FOR (a:Actor) REQUIRE a.actor_id IS UNIQUE",
            "CREATE CONSTRAINT asset_id_idx IF NOT EXISTS FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE",
            "CREATE CONSTRAINT beneficiary_id_idx IF NOT EXISTS FOR (b:Beneficiary) REQUIRE b.beneficiary_id IS UNIQUE",
            "CREATE CONSTRAINT evidence_id_idx IF NOT EXISTS FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE",
            "CREATE CONSTRAINT event_id_idx IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
            "CREATE CONSTRAINT resident_id_idx IF NOT EXISTS FOR (r:Resident) REQUIRE r.resident_id IS UNIQUE"
        ]
        for query in constraints:
            tx.run(query)

    def load_csv(self, filename: str) -> List[Dict[str, Any]]:
        path = DATA_DIR / filename
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return []
        
        data = []
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data

    def seed_regions(self, tx, data):
        logger.info(f"Seeding {len(data)} Regions...")
        query = """
        UNWIND $rows AS row
        MERGE (r:Region {region_id: trim(row.regionid)})
        SET r.name = row.name,
            r.type = row.type,
            r.ward_code = row.wardcode,
            r.lat = toFloat(row.lat),
            r.lon = toFloat(row.lon),
            r.population = toInteger(row.population),
            r.zone = row.zone
        WITH r, row
        WHERE row.parent_regionid IS NOT NULL AND trim(row.parent_regionid) <> ''
        MERGE (parent:Region {region_id: trim(row.parent_regionid)})
        MERGE (r)-[:PART_OF]->(parent)
        """
        tx.run(query, rows=data)

    def seed_schemes(self, tx, data):
        logger.info(f"Seeding {len(data)} Schemes...")
        query = """
        UNWIND $rows AS row
        MERGE (s:Scheme {scheme_id: row.schemeid})
        SET s.name = row.name,
            s.ministry = row.ministry,
            s.category = row.category,
            s.budget_allocated = toFloat(row.budget_allocated),
            s.budget_released = toFloat(row.budget_released),
            s.budget_utilized = toFloat(row.budget_utilized),
            s.target_beneficiaries = toInteger(row.target_beneficiaries),
            s.launch_date = row.launch_date,
            s.year = toInteger(row.year),
            s.status = row.status,
            s.description = row.description
        """
        tx.run(query, rows=data)

    def seed_actors(self, tx, data):
        logger.info(f"Seeding {len(data)} Actors...")
        query = """
        UNWIND $rows AS row
        MERGE (a:Actor {actor_id: row.actorid})
        SET a.name = row.name,
            a.type = row.type,
            a.designation = row.designation,
            a.contact_email = row.contact_email,
            a.contact_phone = row.contact_phone,
            a.party = row.party
        WITH a, row
        
        OPTIONAL MATCH (r:Region {region_id: trim(coalesce(row.regionid, ''))})
        FOREACH (_ IN CASE WHEN r IS NOT NULL AND trim(coalesce(row.regionid, '')) <> '' THEN [1] ELSE [] END |
            MERGE (a)-[:REPRESENTS]->(r)
        )
        WITH a, row
        
        WITH a, row, split(coalesce(row.scheme_ids, ''), '|') AS schemes
        UNWIND schemes AS scheme_id
        OPTIONAL MATCH (s:Scheme {scheme_id: trim(scheme_id)})
        FOREACH (_ IN CASE WHEN s IS NOT NULL AND trim(scheme_id) <> '' THEN [1] ELSE [] END |
            MERGE (a)-[:IMPLEMENTS]->(s)
        )
        """
        tx.run(query, rows=data)

    def seed_assets(self, tx, data):
        logger.info(f"Seeding {len(data)} Assets...")
        query = """
        UNWIND $rows AS row
        MERGE (a:Asset {asset_id: trim(row.assetid)})
        SET a.name = row.name,
            a.type = row.type,
            a.street_name = row.street_name,
            a.lat = toFloat(row.lat),
            a.lon = toFloat(row.lon),
            a.cost = toFloat(row.cost),
            a.construction_start = row.construction_start,
            a.construction_end = row.construction_end,
            a.status = row.status,
            a.source = row.source,
            a.verification_status = row.verification_status,
            a.chain_complete = toBoolean(row.chain_complete)
            
        WITH a, row
        
        OPTIONAL MATCH (r:Region {region_id: trim(coalesce(row.regionid, ''))})
        FOREACH (_ IN CASE WHEN r IS NOT NULL AND trim(coalesce(row.regionid, '')) <> '' THEN [1] ELSE [] END |
            MERGE (a)-[:LOCATED_IN]->(r)
        )
        WITH a, row
        
        OPTIONAL MATCH (act:Actor {actor_id: trim(coalesce(row.contractor_id, ''))})
        FOREACH (_ IN CASE WHEN act IS NOT NULL AND trim(coalesce(row.contractor_id, '')) <> '' THEN [1] ELSE [] END |
            MERGE (a)-[:BUILT_BY]->(act)
        )
        WITH a, row
        
        WITH a, row, split(coalesce(row.scheme_ids, ''), '|') AS schemes
        UNWIND schemes AS scheme_id
        OPTIONAL MATCH (s:Scheme {scheme_id: trim(scheme_id)})
        FOREACH (_ IN CASE WHEN s IS NOT NULL AND trim(scheme_id) <> '' THEN [1] ELSE [] END |
            MERGE (s)-[:FUNDS]->(a)
        )
        """
        tx.run(query, rows=data)

    def seed_beneficiaries(self, tx, data):
        logger.info(f"Seeding {len(data)} Beneficiaries...")
        query = """
        UNWIND $rows AS row
        MERGE (b:Beneficiary {beneficiary_id: trim(row.beneficiaryid)})
        SET b.name = row.name,
            b.type = row.type,
            b.count = toInteger(row.count),
            b.demographic_segment = row.demographic_segment,
            b.year = toInteger(row.year),
            b.ward_code = row.ward_code,
            b.ab_cards_issued = toInteger(row.ab_cards_issued),
            b.pmay_units = toInteger(row.pmay_units),
            b.sbm_toilets_accessed = toInteger(row.sbm_toilets_accessed),
            b.pmjdy_accounts = toInteger(row.pmjdy_accounts),
            b.source = row.source
            
        WITH b, row
        
        WITH b, row, split(coalesce(row.scheme_ids, ''), '|') AS schemes
        UNWIND schemes AS scheme_id
        OPTIONAL MATCH (s:Scheme {scheme_id: trim(scheme_id)})
        FOREACH (_ IN CASE WHEN s IS NOT NULL AND trim(scheme_id) <> '' THEN [1] ELSE [] END |
            MERGE (s)-[:BENEFITS]->(b)
        )
        WITH b, row
        
        OPTIONAL MATCH (r:Region {region_id: trim(coalesce(row.regionid, ''))})
        FOREACH (_ IN CASE WHEN r IS NOT NULL AND trim(coalesce(row.regionid, '')) <> '' THEN [1] ELSE [] END |
            MERGE (b)-[:LIVES_IN]->(r)
        )
        """
        tx.run(query, rows=data)

    def seed_evidence(self, tx, data):
        logger.info(f"Seeding {len(data)} Evidence items...")
        query = """
        UNWIND $rows AS row
        MERGE (e:Evidence {evidence_id: trim(row.evidenceid)})
        SET e.type = row.type,
            e.url_or_path = row.url_or_path,
            e.before_or_after = row.before_or_after,
            e.capture_date = row.capture_date,
            e.geo_lat = toFloat(row.geo_lat),
            e.geo_lon = toFloat(row.geo_lon),
            e.source = row.source,
            e.caption = row.caption,
            e.verified_by = row.verified_by,
            e.confidence_score = toFloat(row.confidence_score)
            
        WITH e, row
        
        OPTIONAL MATCH (a:Asset {asset_id: trim(coalesce(row.asset_id, ''))})
        FOREACH (_ IN CASE WHEN a IS NOT NULL AND trim(coalesce(row.asset_id, '')) <> '' THEN [1] ELSE [] END |
            MERGE (e)-[:PROVES]->(a)
        )
        WITH e, row
        
        OPTIONAL MATCH (r:Region {region_id: trim(coalesce(row.regionid, ''))})
        FOREACH (_ IN CASE WHEN r IS NOT NULL AND trim(coalesce(row.regionid, '')) <> '' THEN [1] ELSE [] END |
            MERGE (e)-[:CAPTURED_AT]->(r)
        )
        """
        tx.run(query, rows=data)

    def seed_residents(self, tx, data):
        logger.info(f"Seeding {len(data)} Residents for Notifications...")
        query = """
        UNWIND $rows AS row
        MERGE (res:Resident {resident_id: trim(row.residentid)})
        SET res.name = row.name,
            res.phone = row.phone,
            res.opt_in = toBoolean(row.opt_in)
            
        WITH res, row
        
        OPTIONAL MATCH (r:Region {region_id: trim(coalesce(row.regionid, ''))})
        FOREACH (_ IN CASE WHEN r IS NOT NULL AND trim(coalesce(row.regionid, '')) <> '' THEN [1] ELSE [] END |
            MERGE (res)-[:RESIDES_ON]->(r)
        )
        """
        tx.run(query, rows=data)

    def seed_events(self, tx, data):
        logger.info(f"Seeding {len(data)} Events...")
        query = """
        UNWIND $rows AS row
        MERGE (e:Event {event_id: row.eventid})
        SET e.name = row.name,
            e.type = row.type,
            e.date = row.date,
            e.description = row.description
            
        WITH e, row
        
        OPTIONAL MATCH (a:Asset {asset_id: coalesce(row.related_node_id, '')})
        FOREACH (_ IN CASE WHEN a IS NOT NULL AND coalesce(row.related_node_id, '') <> '' THEN [1] ELSE [] END | MERGE (e)-[:RELATED_TO]->(a) )
        WITH e, row
        
        OPTIONAL MATCH (s:Scheme {scheme_id: coalesce(row.related_node_id, '')})
        FOREACH (_ IN CASE WHEN s IS NOT NULL AND coalesce(row.related_node_id, '') <> '' THEN [1] ELSE [] END | MERGE (e)-[:RELATED_TO]->(s) )
        WITH e, row
        
        OPTIONAL MATCH (r:Region {region_id: coalesce(row.region_id, '')})
        FOREACH (_ IN CASE WHEN r IS NOT NULL AND coalesce(row.region_id, '') <> '' THEN [1] ELSE [] END |
            MERGE (e)-[:OCCURRED_AT]->(r)
        )
        """
        tx.run(query, rows=data)


    def clear_database(self, tx):
        logger.info("Clearing existing database...")
        tx.run("MATCH (n) DETACH DELETE n;")

    def run_all(self):
        try:
            self.wait_for_db()
            with self.driver.session() as session:
                session.execute_write(self.clear_database)
                session.execute_write(self.setup_schema)
                
                regions = self.load_csv("regions.csv")
                if regions: session.execute_write(self.seed_regions, regions)
                schemes = self.load_csv("schemes.csv")
                if schemes: session.execute_write(self.seed_schemes, schemes)
                actors = self.load_csv("actors.csv")
                if actors: session.execute_write(self.seed_actors, actors)
                assets = self.load_csv("assets.csv")
                if assets: session.execute_write(self.seed_assets, assets)
                beneficiaries = self.load_csv("beneficiaries.csv")
                if beneficiaries: session.execute_write(self.seed_beneficiaries, beneficiaries)
                evidence = self.load_csv("evidence.csv")
                if evidence: session.execute_write(self.seed_evidence, evidence)
                residents = self.load_csv("residents.csv")
                if residents: session.execute_write(self.seed_residents, residents)
                events = self.load_csv("events.csv")
                if events: session.execute_write(self.seed_events, events)
                
            logger.info("Database seeding completed gracefully.")
        except Exception as e:
            logger.error(f"Seeding failed: {e}")

if __name__ == "__main__":
    seeder = PramaanDataSeeder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        seeder.run_all()
    finally:
        seeder.close()
