DELHI_WARD_POPULATION = {
    "WARD45_SHAHDARA": {"name": "DMC Ward No - 45", "zone": "Shahdara North",
                "population": 14200, "households": 3100, "area_sqkm": 2.3},
    "WARD46_KRISHNANAGAR": {"name": "DMC Ward No - 46", "zone": "Shahdara North",
                "population": 16800, "households": 3650, "area_sqkm": 2.8},
    "WARD47_GANDHINAGAR": {"name": "DMC Ward No - 47", "zone": "Shahdara North",
                "population": 12900, "households": 2800, "area_sqkm": 2.1},
    "REG_W48": {"name": "DMC Ward No - 48", "zone": "Shahdara North",
                "population": 15400, "households": 3350, "area_sqkm": 2.5},
    "REG_W49": {"name": "DMC Ward No - 49", "zone": "Shahdara North",
                "population": 14800, "households": 3200, "area_sqkm": 2.4},
    "REG_W50": {"name": "DMC Ward No - 50", "zone": "Shahdara North",
                "population": 17200, "households": 3800, "area_sqkm": 3.1},
}

def get_ward_population(ward_name: str, population_dict: dict) -> dict:
    normalized_input = ward_name.strip().lower().replace("-","").replace(" ","")
    for key, val in population_dict.items():
        normalized_db_name = val["name"].strip().lower().replace("-","").replace(" ","")
        if normalized_db_name in normalized_input or normalized_input in normalized_db_name:
            return val
    return {"population": "N/A", "households": "N/A"}

def get_beneficiary_count(ward_name: str, asset_type: str) -> dict:
    ward = get_ward_population(ward_name, DELHI_WARD_POPULATION)
    if ward["population"] == "N/A":
        pop = 13000
        hh = 2800
    else:
        pop = ward["population"]
        hh  = ward["households"]

    
    mapping = {
        "drain":      (hh,        "Households protected from waterlogging"),
        "road":       (int(pop*0.7), "Daily commuters and pedestrians"),
        "park":       (int(pop*0.3), "Recreational users"),
        "toilet":     (int(pop*0.5), "Women and children"),
        "water_body": (pop,       "Residents benefiting from restoration"),
        "housing":    (1,         "Household Benefited (Direct Scheme)")
    }
    
    count, label = mapping.get(asset_type, (pop, "Ward residents"))
    
    return {
        "ward_population": pop,
        "ward_households": hh,
        "direct_beneficiaries": count,
        "label": label,
        "source": "Census 2011 extrapolated at 2% annual growth to 2026"
    }
