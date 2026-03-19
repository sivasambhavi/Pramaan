"""
Run ONCE before reseeding to delete water body assets that were incorrectly
tagged to REG_W45 but belong to South/West Delhi localities.

Usage:
    cd backend
    python scripts/cleanup_mistagged_assets.py
"""
from neo4j import GraphDatabase

URI      = "neo4j://localhost:7687"
AUTH     = ("neo4j", "password")

# Asset IDs removed from assets.csv because their coordinates place them
# in South/West Delhi, not Shahdara (Ward 45).
MISTAGGED_IDS = [
    "ASSET_WB_272052", "ASSET_WB_272053", "ASSET_WB_272054", "ASSET_WB_272055",  # BAGROLA
    "ASSET_WB_272056",                                                             # NANGAL RAYA
    "ASSET_WB_272057",                                                             # NARAINA
    "ASSET_WB_272058", "ASSET_WB_272059", "ASSET_WB_272060",
    "ASSET_WB_272061", "ASSET_WB_272062",                                         # SHAHBAD MOHD. PUR
    "ASSET_WB_272063", "ASSET_WB_272064", "ASSET_WB_272065",                      # TODAPUR
    "ASSET_WB_272066",                                                             # BASANT NAGAR
    "ASSET_WB_272067",                                                             # GHATORNI
    "ASSET_WB_272068", "ASSET_WB_272069", "ASSET_WB_272070",
    "ASSET_WB_272071", "ASSET_WB_272072",                                         # MAHIPALPUR
    "ASSET_WB_272073",                                                             # MASOOD PUR
    "ASSET_WB_272074", "ASSET_WB_272075", "ASSET_WB_272076",                      # MOHD. PUR MUNIRKA
    "ASSET_WB_272077",                                                             # NANGAL DEVAT
]


def main() -> None:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        result = session.run(
            """
            MATCH (a:Asset) WHERE a.asset_id IN $ids
            DETACH DELETE a
            RETURN count(a) AS deleted
            """,
            ids=MISTAGGED_IDS,
        )
        deleted = result.single()["deleted"]
        print(f"Deleted {deleted} mis-tagged asset node(s).")

    driver.close()
    print("Done. Now run: python scripts/load_seed_data.py")


if __name__ == "__main__":
    main()
