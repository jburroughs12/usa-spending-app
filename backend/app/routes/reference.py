"""Reference data endpoint for populating filter dropdowns."""

from fastapi import APIRouter

from ..client import USASpendingClient
from ..config import SET_ASIDE_TYPES

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

    return {
        "agencies": agencies,
        "set_aside_types": SET_ASIDE_TYPES,
    }
