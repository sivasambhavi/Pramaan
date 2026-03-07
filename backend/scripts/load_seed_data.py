"""
Stub script to load seed CSV data into Neo4j.

This is a placeholder; extend it to parse CSVs from the `data/` directory
and create nodes/relationships as needed.
"""

from pathlib import Path

from app.config import settings  # type: ignore[attr-defined]
from app.neo4j_client import get_driver


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main() -> None:
    print("Seed loader stub")
    print(f"Expected CSV directory: {DATA_DIR}")

    driver = get_driver()
    with driver.session() as session:
        result = session.run("RETURN 1 AS ok")
        print("Neo4j connectivity check:", result.single())

    print("Implement CSV → Neo4j loading logic here.")


if __name__ == "__main__":
    main()

