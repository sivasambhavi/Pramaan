"""
PRAMAAN — Neo4j Seed Loader
Loads the 7 formalized CSVs into Neo4j with row-level validation.
Every row is validated before insert. Errors abort the load — no silent skips.
"""

import sys
import pandas as pd
from pathlib import Path
from app.config import settings
from app.neo4j_client import get_driver

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "resources" / "final_formalized"


# ── Row-level validators ──────────────────────────────────────────────────────

def _require(row: dict, *fields: str, source: str):
    """Raise if any required field is missing or empty."""
    for f in fields:
        if not row.get(f):
            raise ValueError(f"[{source}] Missing required field '{f}' in row: {dict(list(row.items())[:4])}")


def _validate_region(row: dict):
    _require(row, "region_id", "name", "type", source="regions")
    if row["type"] not in ("state", "city", "zone", "ward", "street"):
        raise ValueError(f"[regions] Invalid type '{row['type']}' for region_id={row['region_id']}")


def _validate_scheme(row: dict):
    _require(row, "scheme_id", "name", source="schemes")


def _validate_actor(row: dict):
    _require(row, "actor_id", "name", "type", source="actors")
    if row["type"] not in ("government", "elected_rep", "contractor"):
        raise ValueError(f"[actors] Invalid type '{row['type']}' for actor_id={row['actor_id']}")


def _validate_asset(row: dict):
    _require(row, "asset_id", "name", "type", source="assets")
    valid_types = ("drain", "road", "toilet", "housing", "streetlight", "water_body", "park", "other")
    if row["type"] not in valid_types:
        raise ValueError(f"[assets] Invalid type '{row['type']}' for asset_id={row['asset_id']}")
    if row.get("lat") and row.get("lon"):
        lat, lon = float(row["lat"]), float(row["lon"])
        if not (28.4 <= lat <= 28.9 and 76.8 <= lon <= 77.4):
            raise ValueError(f"[assets] Coordinates ({lat},{lon}) outside Delhi bbox for asset_id={row['asset_id']}")


def _validate_beneficiary(row: dict):
    _require(row, "beneficiary_id", source="beneficiaries")
    if row.get("count"):
        try:
            c = int(float(row["count"]))
            if c <= 0:
                raise ValueError(f"[beneficiaries] count must be > 0 for beneficiary_id={row['beneficiary_id']}")
        except (ValueError, TypeError):
            raise ValueError(f"[beneficiaries] Invalid count '{row['count']}' for beneficiary_id={row['beneficiary_id']}")


def _validate_evidence(row: dict):
    _require(row, "evidence_id", source="evidence")
    if row.get("type") and row["type"] not in ("image", "document", "certificate", "news"):
        raise ValueError(f"[evidence] Invalid type '{row['type']}' for evidence_id={row['evidence_id']}")


def _validate_event(row: dict):
    _require(row, "event_id", "name", source="events")


# ── Loader helpers ────────────────────────────────────────────────────────────

def load_csv(filename: str, validator, required: bool = True) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required file missing: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path).fillna("")
    errors = []
    for i, row in df.iterrows():
        try:
            validator(row.to_dict())
        except ValueError as e:
            errors.append(f"  Row {i+2}: {e}")
    if errors:
        print(f"\n❌ Validation failed for {filename} — {len(errors)} error(s):")
        for e in errors:
            print(e)
        raise SystemExit(1)
    print(f"  ✅ {filename} — {len(df)} rows validated")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not DATA_DIR.exists():
        print(f"❌ Staging directory not found: {DATA_DIR}")
        print("   Run transform_to_7_table_schema.py first.")
        sys.exit(1)

    # ── Validate all CSVs before touching Neo4j ───────────────────────────────
    print("\n── Validating staging CSVs ──────────────────────────────────────────")
    df_reg    = load_csv("regions.csv",           _validate_region)
    df_sch    = load_csv("schemes.csv",            _validate_scheme)
    df_act    = load_csv("actors.csv",             _validate_actor)
    df_act_en = load_csv("actors_enriched.csv",    _validate_actor,      required=False)
    df_alloc  = load_csv("scheme_allocations.csv", lambda r: None,       required=False)
    df_assets = load_csv("assets.csv",             _validate_asset)
    df_ben    = load_csv("beneficiaries.csv",      _validate_beneficiary)
    df_ev     = load_csv("evidence.csv",           _validate_evidence)
    df_events = load_csv("events.csv",             _validate_event)

    # ── Load into Neo4j ───────────────────────────────────────────────────────
    print("\n── Loading into Neo4j ───────────────────────────────────────────────")
    driver = get_driver()
    with driver.session() as session:
        print("Loading Regions...")
        for _, row in df_reg.iterrows():
            r = row.to_dict()
            _lat = float(r["lat"]) if str(r.get("lat", "")).strip() else None
            _lon = float(r["lon"]) if str(r.get("lon", "")).strip() else None
            session.run("""
                MERGE (n:Region {region_id: $region_id})
                SET n.name = $name, n.type = $type,
                    n.lat  = $lat,  n.lon  = $lon,
                    n.population = $population,
                    n.source_type = 'structured_csv', n.confidence = 1.0, n.ingested_by = 'seed_script'
            """, {**r, "population": r.get("population", ""), "lat": _lat, "lon": _lon})
            if r["parent_region_id"]:
                session.run("""
                    MATCH (parent:Region {region_id: $parent_region_id})
                    MATCH (child:Region  {region_id: $region_id})
                    MERGE (parent)-[:CONTAINS]->(child)
                """, r)

        print("Loading Schemes...")
        for _, row in df_sch.iterrows():
            r = row.to_dict()
            session.run("""
                MERGE (s:Scheme {scheme_id: $scheme_id})
                SET s.name = $name, s.ministry = $ministry, s.category = $category,
                    s.source_type = 'structured_csv', s.confidence = 1.0, s.ingested_by = 'seed_script'
            """, r)

        if not df_alloc.empty:
            print("Loading Scheme Allocations...")
            for _, row in df_alloc.iterrows():
                r = row.to_dict()
                session.run("""
                    MERGE (reg:Region {name: $region_name})
                    ON CREATE SET reg.region_id = 'reg_' + toLower(replace($region_name, ' ', '_')), reg.type = 'state'
                """, {"region_name": r["region_name"]})
                session.run("""
                    MERGE (sa:SchemeAllocation {allocation_id: $allocation_id})
                    SET sa.total_allocated = $total_allocated, sa.total_completed = $total_completed, sa.unit = $unit
                    WITH sa
                    MATCH (s:Scheme {scheme_id: $scheme_id})
                    MERGE (s)-[:ALLOCATED]->(sa)
                    WITH sa
                    MATCH (reg:Region {name: $region_name})
                    MERGE (sa)-[:FOR_REGION]->(reg)
                """, r)

        print("Loading Actors...")
        for _, row in df_act.iterrows():
            r = row.to_dict()
            session.run("""
                MERGE (a:Actor {actor_id: $actor_id})
                SET a.name = $name, a.type = $type,
                    a.source_type = 'structured_csv', a.confidence = 1.0, a.ingested_by = 'seed_script'
            """, r)
            if r["region_id"]:
                session.run("""
                    MATCH (a:Actor {actor_id: $actor_id})
                    MATCH (reg:Region {region_id: $region_id})
                    MERGE (a)-[:REPRESENTS]->(reg)
                """, r)

        if not df_act_en.empty:
            print("Loading Enriched Actors (Tenders)...")
            for _, row in df_act_en.iterrows():
                r = row.to_dict()
                session.run("""
                    MERGE (a:Actor {actor_id: $actor_id})
                    SET a.name = $name, a.type = $type,
                        a.total_tenders = $total_tenders, a.budget_lakhs = $budget_lakhs
                """, r)
                if r["region_id"]:
                    session.run("""
                        MATCH (a:Actor {actor_id: $actor_id})
                        MATCH (reg:Region {region_id: $region_id})
                        MERGE (a)-[:REPRESENTS]->(reg)
                    """, r)

        print("Loading Assets...")
        for _, row in df_assets.iterrows():
            r = row.to_dict()
            session.run("""
                MERGE (a:Asset {asset_id: $asset_id})
                SET a.name = $name, a.type = $type,
                    a.cost = $cost, a.status = $status, a.lat = $lat, a.lon = $lon,
                    a.encroached = $encroached, a.nature = $nature,
                    a.ownership = $ownership, a.image_url = $image_url,
                    a.source_type = $source_type, a.confidence = $confidence,
                    a.ingested_by = 'seed_script'
            """, {**r,
                  "source_type": r.get("source_type", "structured_csv"),
                  "confidence":  float(r["confidence"]) if r.get("confidence") not in ("", None) else 1.0,
                  "encroached":  r.get("encroached", ""),
                  "nature":      r.get("nature", ""),
                  "ownership":   r.get("ownership", ""),
                  "image_url":   r.get("image_url", "")})
            if r["region_id"]:
                session.run("MATCH (a:Asset {asset_id: $id}) MATCH (reg:Region {region_id: $rid}) MERGE (a)-[:LOCATED_IN]->(reg)",
                            {"id": r["asset_id"], "rid": r["region_id"]})
            if r["scheme_id"]:
                session.run("MATCH (a:Asset {asset_id: $id}) MATCH (s:Scheme {scheme_id: $sid}) MERGE (s)-[:FUNDS]->(a)",
                            {"id": r["asset_id"], "sid": r["scheme_id"]})
            if r["actor_id"]:
                session.run("MATCH (a:Asset {asset_id: $id}) MATCH (act:Actor {actor_id: $aid}) MERGE (a)-[:BUILT_BY]->(act)",
                            {"id": r["asset_id"], "aid": r["actor_id"]})

        print("Loading Beneficiaries...")
        for _, row in df_ben.iterrows():
            r = row.to_dict()
            session.run("""
                MERGE (b:Beneficiary {beneficiary_id: $beneficiary_id})
                SET b.count = $count, b.description = $description,
                    b.scheme_id = $scheme_id, b.region_id = $region_id
            """, r)
            if r["scheme_id"]:
                session.run("MATCH (b:Beneficiary {beneficiary_id: $id}) MATCH (s:Scheme {scheme_id: $sid}) MERGE (s)-[:BENEFITS]->(b)",
                            {"id": r["beneficiary_id"], "sid": r["scheme_id"]})
            if r["region_id"]:
                session.run("MATCH (b:Beneficiary {beneficiary_id: $id}) MATCH (reg:Region {region_id: $rid}) MERGE (b)-[:LIVES_IN]->(reg)",
                            {"id": r["beneficiary_id"], "rid": r["region_id"]})

        print("Loading Evidence...")
        for _, row in df_ev.iterrows():
            r = row.to_dict()
            session.run("""
                MERGE (e:Evidence {evidence_id: $evidence_id})
                SET e.type = $type, e.url = $url,
                    e.before_or_after = $before_or_after, e.capture_date = $capture_date
            """, r)
            if r["asset_id"]:
                session.run("MATCH (e:Evidence {evidence_id: $id}) MATCH (a:Asset {asset_id: $aid}) MERGE (e)-[:PROVES]->(a)",
                            {"id": r["evidence_id"], "aid": r["asset_id"]})
            if r["region_id"]:
                session.run("MATCH (e:Evidence {evidence_id: $id}) MATCH (reg:Region {region_id: $rid}) MERGE (e)-[:CAPTURED_AT]->(reg)",
                            {"id": r["evidence_id"], "rid": r["region_id"]})

        print("Loading Events...")
        for _, row in df_events.iterrows():
            r = row.to_dict()
            session.run("""
                MERGE (e:Event {event_id: $event_id})
                SET e.name = $name, e.event_type = $event_type, e.date = $date
            """, r)
            if r["asset_id"]:
                session.run("MATCH (e:Event {event_id: $id}) MATCH (a:Asset {asset_id: $aid}) MERGE (e)-[:RELATED_TO]->(a)",
                            {"id": r["event_id"], "aid": r["asset_id"]})

    print("\nSUCCESS: Governance Knowledge Graph Ingested.")

    # ── Cleanup staging CSVs ──────────────────────────────────────────────────
    cleaned = []
    for csv_file in DATA_DIR.glob("*.csv"):
        try:
            csv_file.unlink()
            cleaned.append(csv_file.name)
        except Exception as e:
            print(f"  Could not delete {csv_file.name}: {e}")
    if cleaned:
        print(f"Cleaned up {len(cleaned)} staging CSVs: {', '.join(cleaned)}")


if __name__ == "__main__":
    main()
