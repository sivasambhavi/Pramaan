import pandas as pd
import os
import random

# Base Directory
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 1. GENERATE REGIONS (Real Wards + Mocked Streets)
def generate_regions():
    regions = [
        {"id": "region_w45", "name": "Ward 45 Shahdara", "type": "ward"},
        {"id": "region_w45_g7", "name": "Gali 7 Shahdara", "type": "street"},
        {"id": "region_w45_g12", "name": "Gali 12 Shahdara", "type": "street"},
        {"id": "region_w45_mblk", "name": "M-Block Park Shahdara", "type": "park_area"},
        {"id": "region_w45_mrd", "name": "Main Road Shahdara", "type": "street"}
    ]
    df = pd.DataFrame(regions)
    df.to_csv(os.path.join(DATA_DIR, 'regions.csv'), index=False)
    print("Created regions.csv")

# 2. GENERATE SCHEMES (Real Schemes from API Data)
def generate_schemes():
    schemes = [
        {"id": "scheme_sfc", "name": "SFC Grant", "ministry": "Urban Development"},
        {"id": "scheme_sbm", "name": "Swachh Bharat Mission (Urban)", "ministry": "Housing and Urban Affairs"},
        {"id": "scheme_amrut", "name": "AMRUT", "ministry": "Housing and Urban Affairs"},
        {"id": "scheme_pmay", "name": "PMAY (Urban)", "ministry": "Housing and Urban Affairs"},
        {"id": "scheme_mcd", "name": "MCD Ward Development Fund", "ministry": "MCD"}
    ]
    df = pd.DataFrame(schemes)
    df.to_csv(os.path.join(DATA_DIR, 'schemes.csv'), index=False)
    print("Created schemes.csv")

# 3. GENERATE ACTORS (Real Actors from MDC Duty Roster + Mock Contractors)
def generate_actors():
    actors = [
        {"id": "actor_mcd_ez", "name": "MCD East Zone", "type": "agency", "role": "Funder/Approver"},
        {"id": "actor_c_sharma", "name": "Sharma Constructions", "type": "contractor", "role": "Executor"},
        {"id": "actor_c_gupta", "name": "Gupta Infra", "type": "contractor", "role": "Executor"},
        {"id": "actor_m_ram", "name": "Ram Singh (Mali ID: 1045)", "type": "employee", "role": "Maintainer"},
        {"id": "actor_i_kumar", "name": "Ajay Kumar (Inspector)", "type": "employee", "role": "Inspector"}
    ]
    df = pd.DataFrame(actors)
    df.to_csv(os.path.join(DATA_DIR, 'actors.csv'), index=False)
    print("Created actors.csv")

# 4. GENERATE ASSETS (Hyper-local mocked assets linked to Regions)
def generate_assets():
    assets = [
        {"id": "asset_001", "name": "Drain Gali 7", "type": "drain", "ward_id": "region_w45_g7", "cost": 1200000, "status": "completed"},
        {"id": "asset_002", "name": "Public Toilet Main Market", "type": "toilet", "ward_id": "region_w45_mrd", "cost": 850000, "status": "completed"},
        {"id": "asset_003", "name": "LED Streetlights Gali 12", "type": "streetlight", "ward_id": "region_w45_g12", "cost": 450000, "status": "completed"},
        {"id": "asset_004", "name": "PMAY House Beneficiary 402", "type": "housing", "ward_id": "region_w45_g7", "cost": 250000, "status": "completed"},
        {"id": "asset_005", "name": "M-Block Road Repair", "type": "road", "ward_id": "region_w45_mblk", "cost": 3200000, "status": "in_progress"}
    ]
    df = pd.DataFrame(assets)
    df.to_csv(os.path.join(DATA_DIR, 'assets.csv'), index=False)
    print("Created assets.csv")

# 5. GENERATE EVIDENCE (Mocked Proof Links)
def generate_evidence():
    evidence = [
        {"id": "evid_001", "asset_id": "asset_001", "type": "photo", "before_after": "after", "url": "https://example.com/shahdara_drain_after.jpg"},
        {"id": "evid_002", "asset_id": "asset_002", "type": "photo", "before_after": "after", "url": "https://example.com/shahdara_toilet_after.jpg"},
        {"id": "evid_003", "asset_id": "asset_003", "type": "document", "before_after": "after", "url": "https://example.com/streetlight_invoice.pdf"},
        {"id": "evid_004", "asset_id": "asset_004", "type": "photo", "before_after": "before", "url": "https://example.com/pmay_house_before.jpg"},
        {"id": "evid_005", "asset_id": "asset_005", "type": "photo", "before_after": "in_progress", "url": "https://example.com/road_repair_progress.jpg"}
    ]
    df = pd.DataFrame(evidence)
    df.to_csv(os.path.join(DATA_DIR, 'evidence.csv'), index=False)
    print("Created evidence.csv")

# 6. GENERATE BENEFICIARIES (Mocked Citizens)
def generate_beneficiaries():
    beneficiaries = [
        {"id": "ben_001", "name": "Ramesh Kumar", "asset_linked": "asset_001", "address": "Gali 7, Shahdara"},
        {"id": "ben_002", "name": "Sunita Devi", "asset_linked": "asset_004", "address": "House 402, Gali 7, Shahdara"},
        {"id": "ben_003", "name": "Amit Sharma", "asset_linked": "asset_003", "address": "Gali 12, Shahdara"},
        {"id": "ben_004", "name": "Meera Verma", "asset_linked": "asset_002", "address": "Main Market, Shahdara"}
    ]
    df = pd.DataFrame(beneficiaries)
    df.to_csv(os.path.join(DATA_DIR, 'beneficiaries.csv'), index=False)
    print("Created beneficiaries.csv")


if __name__ == "__main__":
    generate_regions()
    generate_schemes()
    generate_actors()
    generate_assets()
    generate_evidence()
    generate_beneficiaries()
    print("\nAll seed data CSVs successfully generated in the /data folder!")
