"""
Run once to set up Neo4j constraints and indexes for Pramaan.

Constraints use domain-specific PK property names to match the CSV schema
(region_id, scheme_id, asset_id, etc.) — NOT a generic 'id' field.

Usage (from project root):
    PYTHONPATH=backend .venv/bin/python3 backend/scripts/setup_constraints.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.neo4j_client import get_driver

# (label, pk_property)
CONSTRAINTS = [
    ("Region",      "region_id"),
    ("Scheme",      "scheme_id"),
    ("Actor",       "actor_id"),
    ("Asset",       "asset_id"),
    ("Beneficiary", "beneficiary_id"),
    ("Evidence",    "evidence_id"),
    ("Event",       "event_id"),
]

# (label, property) — for fast lookups beyond the PK
INDEXES = [
    ("Region", "name"),
    ("Region", "type"),
    ("Asset",  "name"),
    ("Asset",  "status"),
    ("Asset",  "type"),
    ("Scheme", "name"),
]


def run():
    driver = get_driver()
    with driver.session() as session:

        print("Dropping old generic 'id' constraints if they exist...")
        old = [
            "unique_ward_id", "unique_region_id", "unique_scheme_id",
            "unique_actor_id", "unique_asset_id", "unique_beneficiary_id",
            "unique_evidence_id", "unique_event_id",
        ]
        for name in old:
            session.run(f"DROP CONSTRAINT {name} IF EXISTS")
        print("  Done.")

        print("\nCreating uniqueness constraints (domain-specific PKs)...")
        for label, prop in CONSTRAINTS:
            name = f"unique_{label.lower()}_{prop}"
            cypher = (
                f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            session.run(cypher)
            print(f"  OK  {label}.{prop}")

        print("\nCreating indexes...")
        for label, prop in INDEXES:
            name = f"idx_{label.lower()}_{prop}"
            cypher = (
                f"CREATE INDEX {name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )
            session.run(cypher)
            print(f"  OK  {label}.{prop}")

        print("\nVerifying...")
        result = session.run("SHOW CONSTRAINTS")
        constraints = [r["name"] for r in result]
        print(f"  {len(constraints)} constraint(s) active")

        result = session.run("SHOW INDEXES")
        indexes = [r["name"] for r in result]
        print(f"  {len(indexes)} index(es) active")

    print("\nDone.")


if __name__ == "__main__":
    run()
