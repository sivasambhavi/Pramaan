"""
load_ontology.py — PRAMAAN Global Ontology Engine Seed Loader
Reads data/resources/ontology/seed_graph.json and loads all nodes + edges
into Neo4j.

Node types: Domain, Region, Actor, Scheme, Policy, Event, Impact, Evidence
Edge types: OCCURRED_IN, BELONGS_TO, ALSO_IN, MANAGED_BY, FUNDED_BY,
            CAUSED, TRIGGERED, CONNECTED_TO, PART_OF, PROVEN_BY

Usage:
    cd /path/to/Pramaan
    python3 -m backend.scripts.load_ontology
    # or
    python3 backend/scripts/load_ontology.py
"""

import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.neo4j_client import get_driver

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "resources" / "ontology" / "seed_graph.json"


# ── Constraints & Indexes ─────────────────────────────────────────────────────

def setup_schema(session):
    constraints = [
        ("Domain",   "domain_id"),
        ("Region",   "region_id"),
        ("Actor",    "actor_id"),
        ("Scheme",   "scheme_id"),
        ("Policy",   "policy_id"),
        ("Event",    "event_id"),
        ("Impact",   "impact_id"),
        ("Evidence", "evidence_id"),
    ]
    for label, prop in constraints:
        session.run(
            f"CREATE CONSTRAINT constraint_{label.lower()}_{prop} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        )
    indexes = [
        ("Event",  "domain"),
        ("Event",  "date"),
        ("Region", "type"),
        ("Impact", "type"),
    ]
    for label, prop in indexes:
        session.run(
            f"CREATE INDEX index_{label.lower()}_{prop} IF NOT EXISTS "
            f"FOR (n:{label}) ON (n.{prop})"
        )
    logger.info("Schema constraints and indexes ready.")


# ── Node loaders ──────────────────────────────────────────────────────────────

def load_domains(session, domains):
    for d in domains:
        session.run("""
            MERGE (n:Domain {domain_id: $domain_id})
            SET n.name = $name, n.description = $description
        """, {**d, "description": d.get("description", "")})
    logger.info("  Loaded %d Domain nodes.", len(domains))


def load_regions(session, regions):
    for r in regions:
        session.run("""
            MERGE (n:Region {region_id: $region_id})
            SET n.name = $name, n.type = $type,
                n.lat  = $lat,  n.lon  = $lon
        """, {**r, "lat": r.get("lat"), "lon": r.get("lon")})
    logger.info("  Loaded %d Region nodes.", len(regions))


def load_actors(session, actors):
    for a in actors:
        session.run("""
            MERGE (n:Actor {actor_id: $actor_id})
            SET n.name = $name, n.type = $type
        """, a)
    logger.info("  Loaded %d Actor nodes.", len(actors))


def load_schemes(session, schemes):
    for s in schemes:
        session.run("""
            MERGE (n:Scheme {scheme_id: $scheme_id})
            SET n.name = $name, n.ministry = $ministry,
                n.budget_crore = $budget_crore, n.source_url = $source_url
        """, {**s,
              "ministry":     s.get("ministry", ""),
              "budget_crore": s.get("budget_crore"),
              "source_url":   s.get("source_url", "")})
    logger.info("  Loaded %d Scheme nodes.", len(schemes))


def load_policies(session, policies):
    for p in policies:
        session.run("""
            MERGE (n:Policy {policy_id: $policy_id})
            SET n.name = $name, n.date = $date,
                n.description = $description, n.source_url = $source_url
        """, {**p,
              "date":        p.get("date", ""),
              "description": p.get("description", ""),
              "source_url":  p.get("source_url", "")})
    logger.info("  Loaded %d Policy nodes.", len(policies))


def load_events(session, events):
    for e in events:
        session.run("""
            MERGE (n:Event {event_id: $event_id})
            SET n.name = $name, n.date = $date,
                n.domain = $domain, n.description = $description,
                n.severity = $severity, n.source_url = $source_url,
                n.confidence = $confidence
        """, {**e,
              "description": e.get("description", ""),
              "severity":    e.get("severity", "medium"),
              "source_url":  e.get("source_url", ""),
              "confidence":  e.get("confidence", 1.0)})
    logger.info("  Loaded %d Event nodes.", len(events))


def load_impacts(session, impacts):
    for i in impacts:
        session.run("""
            MERGE (n:Impact {impact_id: $impact_id})
            SET n.type = $type, n.value = $value,
                n.unit = $unit, n.description = $description
        """, {**i,
              "unit":        i.get("unit", ""),
              "description": i.get("description", "")})
    logger.info("  Loaded %d Impact nodes.", len(impacts))


def load_evidence(session, evidence):
    for e in evidence:
        session.run("""
            MERGE (n:Evidence {evidence_id: $evidence_id})
            SET n.type = $type, n.url = $url,
                n.title = $title, n.date = $date, n.source = $source
        """, {**e,
              "title":  e.get("title", ""),
              "date":   e.get("date", ""),
              "source": e.get("source", "")})
    logger.info("  Loaded %d Evidence nodes.", len(evidence))


# ── Edge loader ───────────────────────────────────────────────────────────────

# Map edge type → (from_label, from_id, to_label, to_id)
EDGE_CONFIG = {
    "OCCURRED_IN":  ("Event",   "event_id",   "Region",  "region_id"),
    "BELONGS_TO":   ("Event",   "event_id",   "Domain",  "domain_id"),
    "ALSO_IN":      ("Event",   "event_id",   "Domain",  "domain_id"),
    "MANAGED_BY":   ("Event",   "event_id",   "Actor",   "actor_id"),
    "FUNDED_BY":    ("Event",   "event_id",   "Scheme",  "scheme_id"),
    "CAUSED":       ("Event",   "event_id",   "Impact",  "impact_id"),
    "TRIGGERED":    ("Event",   "event_id",   "Policy",  "policy_id"),
    "PROVEN_BY":    ("Event",   "event_id",   "Evidence","evidence_id"),
    "CONNECTED_TO": ("Event",   "event_id",   "Event",   "event_id"),
    "PART_OF":      ("Actor",   "actor_id",   "Actor",   "actor_id"),
}

def load_edges(session, edges):
    ok = skipped = 0
    for edge in edges:
        etype = edge["type"]
        cfg   = EDGE_CONFIG.get(etype)
        if not cfg:
            logger.warning("  Unknown edge type: %s — skipped.", etype)
            skipped += 1
            continue

        from_label, from_id_field, to_label, to_id_field = cfg
        reason = edge.get("reason", "")

        result = session.run(f"""
            MATCH (a:{from_label} {{{from_id_field}: $from_id}})
            MATCH (b:{to_label}   {{{to_id_field}:  $to_id}})
            MERGE (a)-[r:{etype}]->(b)
            SET r.reason = $reason
            RETURN r
        """, {
            "from_id": edge["from"],
            "to_id":   edge["to"],
            "reason":  reason,
        })

        if result.single():
            ok += 1
        else:
            logger.warning("  Edge %s -[%s]-> %s: one or both nodes not found.",
                           edge["from"], etype, edge["to"])
            skipped += 1

    logger.info("  Edges: %d created, %d skipped.", ok, skipped)


# ── Main ──────────────────────────────────────────────────────────────────────

def wipe_neo4j(session):
    """Delete all nodes and relationships from Neo4j."""
    result = session.run("MATCH (n) DETACH DELETE n")
    logger.info("  Neo4j wiped — all nodes and relationships deleted.")


def main():
    clean = "--clean" in sys.argv

    if not SEED_PATH.exists():
        logger.error("Seed file not found: %s", SEED_PATH)
        sys.exit(1)

    with open(SEED_PATH) as f:
        graph = json.load(f)

    logger.info("Seed file loaded: %s", SEED_PATH.name)
    logger.info("  Domains:  %d", len(graph["domains"]))
    logger.info("  Regions:  %d", len(graph["regions"]))
    logger.info("  Actors:   %d", len(graph["actors"]))
    logger.info("  Schemes:  %d", len(graph["schemes"]))
    logger.info("  Policies: %d", len(graph["policies"]))
    logger.info("  Events:   %d", len(graph["events"]))
    logger.info("  Impacts:  %d", len(graph["impacts"]))
    logger.info("  Evidence: %d", len(graph["evidence"]))
    logger.info("  Edges:    %d", len(graph["edges"]))

    driver = get_driver()
    with driver.session() as session:
        if clean:
            logger.info("\n── Wiping Neo4j ───────────────────────────────────")
            wipe_neo4j(session)

        logger.info("\n── Setting up schema ──────────────────────────────")
        setup_schema(session)

        logger.info("\n── Loading nodes ──────────────────────────────────")
        load_domains(session,  graph["domains"])
        load_regions(session,  graph["regions"])
        load_actors(session,   graph["actors"])
        load_schemes(session,  graph["schemes"])
        load_policies(session, graph["policies"])
        load_events(session,   graph["events"])
        load_impacts(session,  graph["impacts"])
        load_evidence(session, graph["evidence"])

        logger.info("\n── Loading edges ──────────────────────────────────")
        load_edges(session, graph["edges"])

    logger.info("\nSUCCESS: Global Ontology Graph loaded into Neo4j.")
    logger.info("Total nodes: %d | Total edges: %d",
                sum(len(graph[k]) for k in ["domains","regions","actors","schemes","policies","events","impacts","evidence"]),
                len(graph["edges"]))


if __name__ == "__main__":
    main()
