import sys, os
sys.path.insert(0, r'E:\INDIA_INNOVATES\Pramaan\backend')
from app.neo4j_client import get_session

cypher = """
MATCH (ag:Actor {name: 'MCD Shahdara South Works Dept'})
SET ag.name = 'MCD Shahdara North Works Dept',
    ag.zone = 'Shahdara North',
    ag.city = 'Delhi',
    ag.ulb = 'MCD'
RETURN ag.name, count(ag)
"""

with get_session() as session:
    result = session.run(cypher)
    for r in result:
        print(dict(r))
