from app.neo4j_client import get_session
import sys
sys.path.insert(0, ".")
from app.queries import WARD_ASSET_DETAIL

with get_session() as session:
    res2 = session.run(WARD_ASSET_DETAIL, ward_id="WARD45_SHAHDARA")
    for r in res2:
        print(r['name'], "-", r['proof_status'], "-", r['scheme_name'])
