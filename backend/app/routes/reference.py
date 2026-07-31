"""Reference data endpoint for populating filter dropdowns."""

from fastapi import APIRouter

from ..client import USASpendingClient
from ..config import NAICS_DESCRIPTIONS, SET_ASIDE_TYPES

router = APIRouter()
client = USASpendingClient()


@router.get("/api/reference-data")
def reference_data():
    raw = client.get_toptier_agencies()
    agencies = sorted(
        (
            {"name": a.get("agency_name"), "abbreviation": a.get("abbreviation")}
            for a in raw.get("results", [])
            if a.get("agency_name")
        ),
        key=lambda a: a["name"],
    )

    naics_codes = [
        {"code": code, "description": description}
        for code, description in NAICS_DESCRIPTIONS.items()
    ]

    return {
        "agencies": agencies,
        "set_aside_types": SET_ASIDE_TYPES,
        "naics_codes": naics_codes,
    }
