"""
PRAMAAN — Ward population lookup.
Reads population from Neo4j Region nodes (stored from census data).
No hardcoded values — fails loudly if Neo4j is unreachable.
"""
from app.neo4j_client import get_session


def get_ward_population(ward_name: str) -> dict:
    """Fetch population for a ward by name from Neo4j."""
    with get_session() as session:
        result = session.run("""
            MATCH (r:Region {type: 'ward'})
            WHERE toLower(r.name) CONTAINS toLower($ward_name)
               OR toLower($ward_name) CONTAINS toLower(r.name)
            RETURN r.population AS population, r.name AS name, r.region_id AS region_id
            LIMIT 1
        """, ward_name=ward_name.strip())
        record = result.single()

    if not record or not record["population"]:
        return {"population": None, "households": None, "name": ward_name}

    pop = int(record["population"])
    return {
        "population":  pop,
        "households":  pop // 4,   # avg 4 persons/household (Delhi Census 2011)
        "name":        record["name"],
        "region_id":   record["region_id"],
    }


def get_beneficiary_count(ward_name: str, asset_type: str) -> dict:
    """
    Derive beneficiary count for an asset type based on real ward population from Neo4j.
    Returns a dict with ward_population, ward_households, direct_beneficiaries, label, source.
    """
    ward = get_ward_population(ward_name)
    pop = ward["population"]
    hh  = ward["households"]

    if not pop:
        raise RuntimeError(f"Population not found in Neo4j for ward: {ward_name!r}. Run pipeline first.")

    mapping = {
        "drain":      (hh,           "Households protected from waterlogging"),
        "road":       (int(pop*0.7), "Daily commuters and pedestrians"),
        "park":       (int(pop*0.3), "Recreational users"),
        "toilet":     (int(pop*0.5), "Women and children"),
        "water_body": (pop,          "Residents benefiting from restoration"),
        "housing":    (1,            "Household benefited (direct scheme)"),
    }

    count, label = mapping.get(asset_type, (pop, "Ward residents"))

    return {
        "ward_population":      pop,
        "ward_households":      hh,
        "direct_beneficiaries": count,
        "label":                label,
        "source":               f"Census 2011 — Neo4j Region node ({ward.get('region_id', ward_name)})",
    }


# Kept for any import that references DELHI_WARD_POPULATION directly.
# Empty dict forces callers to use get_ward_population() instead.
DELHI_WARD_POPULATION = {}
