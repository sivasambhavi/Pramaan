"""
setup_constraints.py — PRAMAAN Neo4j Schema Setup
Creates uniqueness constraints and indexes for all node labels.

Run ONCE before loading any data:
  python3 backend/scripts/setup_constraints.py

Safe to re-run — uses CREATE CONSTRAINT IF NOT EXISTS.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.neo4j_client import get_driver

CONSTRAINTS = [
    ("Region",      "region_id"),
    ("Scheme",      "scheme_id"),
    ("Actor",       "actor_id"),
    ("Asset",       "asset_id"),
    ("Beneficiary", "beneficiary_id"),
    ("Evidence",    "evidence_id"),
    ("Event",       "event_id"),
]

INDEXES = [
    # Region filtering by type (heavily used: type='ward', type='state', etc.)
    ("Region", "type"),
    # Asset filtering by type and status
    ("Asset",  "type"),
    ("Asset",  "status"),
    ("Asset",  "region_id"),
    # Region geo lookups
    ("Region", "lgd_code"),
]


def setup(driver):
    with driver.session() as session:
        print("\nCreating uniqueness constraints...")
        for label, prop in CONSTRAINTS:
            name = f"constraint_{label.lower()}_{prop}"
            cypher = (
                f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            session.run(cypher)
            print(f"  ✓ UNIQUE {label}.{prop}")

        print("\nCreating indexes...")
        for label, prop in INDEXES:
            name = f"index_{label.lower()}_{prop}"
            cypher = (
                f"CREATE INDEX {name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )
            session.run(cypher)
            print(f"  ✓ INDEX  {label}.{prop}")

        # Verify
        print("\nActive constraints:")
        result = session.run("SHOW CONSTRAINTS")
        for row in result:
            print(f"  {row['name']} — {row.get('type', '')}")

        print("\nActive indexes:")
        result = session.run("SHOW INDEXES WHERE type <> 'LOOKUP'")
        for row in result:
            print(f"  {row['name']} — {row.get('state', '')}")

    print("\nDone.")


if __name__ == "__main__":
    driver = get_driver()
    setup(driver)
