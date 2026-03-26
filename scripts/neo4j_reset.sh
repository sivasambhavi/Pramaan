#!/usr/bin/env bash
# neo4j_reset.sh — Wipe Neo4j and reload from seed_graph.json
# Usage:
#   ./scripts/neo4j_reset.sh          # clean wipe + reload
#   ./scripts/neo4j_reset.sh --reload # reload without wipe (MERGE, no delete)

set -e
cd "$(dirname "$0")/.."

VENV_PYTHON="./venv/bin/python3"

if [[ ! -f "$VENV_PYTHON" ]]; then
  echo "ERROR: venv not found at ./venv — activate your virtual environment first."
  exit 1
fi

if [[ "$1" == "--reload" ]]; then
  echo ">> Reloading seed data (no wipe)..."
  $VENV_PYTHON -m backend.scripts.load_ontology
else
  echo ">> Wiping Neo4j and reloading from seed_graph.json..."
  $VENV_PYTHON -m backend.scripts.load_ontology --clean
fi

echo ""
echo ">> Verifying node counts..."
$VENV_PYTHON -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as s:
    rows = s.run('MATCH (n) RETURN labels(n)[0] as label, count(n) as cnt ORDER BY cnt DESC').data()
    total_n = s.run('MATCH (n) RETURN count(n) as c').single()['c']
    total_r = s.run('MATCH ()-[r]->() RETURN count(r) as c').single()['c']
    for r in rows:
        print(f'  {r[\"label\"]:<12} {r[\"cnt\"]}')
    print(f'  {\"─\"*18}')
    print(f'  Total nodes  {total_n}')
    print(f'  Total edges  {total_r}')
driver.close()
"
