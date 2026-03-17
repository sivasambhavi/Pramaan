"""
Static government data endpoint for PRAMAAN.
Serves JSON files from data/resources/ as structured API responses.
Source: data.gov.in (official Indian Government Open Data)
"""
import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/data", tags=["govdata"])

DATA_DIR = os.path.join(
    os.path.dirname(__file__),          # .../backend/app/routers/
    "..", "..", "..",                   # -> .../Pramaan/
    "data", "resources"
)
DATA_DIR = os.path.abspath(DATA_DIR)


def _load(filename: str) -> dict:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Data file '{filename}' not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/amrut-drainage")
def amrut_drainage():
    """
    State/UT-wise Status of AMRUT Storm-Water Drainage Projects (Dec 2021).
    Source: Rajya Sabha Starred Question via data.gov.in
    """
    raw = _load("amrut_storm_water_drainage.json")
    records = raw.get("records", [])

    # Separate Delhi row
    delhi = next((r for r in records if "Delhi" in str(r.get("state_ut",""))), None)
    grand_total = next((r for r in records if r.get("state_ut") == "Grand Total"), None)

    # States data (exclude Grand Total)
    states = [r for r in records if r.get("state_ut") != "Grand Total"]

    return {
        "title": raw.get("title", ""),
        "source": "data.gov.in — Rajya Sabha Starred Question, 20 Dec 2021",
        "source_url": "https://data.gov.in/catalog/stateut-wise-status-progress-storm-water-drainage-projects-taken-under-amrut",
        "delhi": delhi,
        "grand_total": grand_total,
        "states": states,
    }


@router.get("/pmay-housing")
def pmay_housing():
    """
    State/UT-wise PMAY-U completed & occupied houses (as on 31-Dec-2024).
    Source: data.gov.in — MoHUA
    """
    raw = _load("pmay_housing_data.json")
    records = raw.get("records", [])

    # Separate Delhi row and totals
    delhi = next((r for r in records if str(r.get("state_ut", "")).strip() == "Delhi"), None)
    total = next(
        (r for r in records if "total" in str(r.get("state_ut", "")).lower()),
        None
    )
    states = [r for r in records if "total" not in str(r.get("state_ut", "")).lower()]

    # Compute national totals from numeric fields if no explicit total row
    if not total and states:
        def _sum(field):
            return sum(int(r.get(field, 0) or 0) for r in states)
        total = {
            "state_ut": "All India Total",
            "houses_as_on_31_03_2024___completed": _sum("houses_as_on_31_03_2024___completed"),
            "houses_as_on_31_03_2024___occupied": _sum("houses_as_on_31_03_2024___occupied"),
            "houses_as_on_31_12_2024___completed": _sum("houses_as_on_31_12_2024___completed"),
            "houses_as_on_31_12_2024___occupied": _sum("houses_as_on_31_12_2024___occupied"),
        }

    return {
        "title": raw.get("title", "PMAY-U Housing Data"),
        "source": "data.gov.in — MoHUA PMAY-U State/UT-wise data",
        "source_url": "https://data.gov.in/catalog/statut-wise-total-number-completed-and-occupied-houses-under-pradhan-mantri-awas-yojana",
        "delhi": delhi,
        "national_total": total,
        "states": states,
    }
