"""Spending summary/aggregation endpoint."""

from fastapi import APIRouter, Query

from ..client import USASpendingClient
from ..config import DEFAULT_NAICS_CODES

router = APIRouter()
client = USASpendingClient()


@router.get("/api/spending-summary")
def spending_summary(
    group_by: str = Query("psc", description="Group by: psc, recipient, or awarding_agency"),
    agency: str | None = Query(None, description="Comma-separated federal agency names"),
    psc: str | None = Query(None, description="Comma-separated PSC codes"),
    naics: str | None = Query(None, description="Comma-separated NAICS codes, or omit for the default set"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
):
    agency_names = [a.strip() for a in agency.split(",")] if agency else None
    psc_codes = [p.strip() for p in psc.split(",")] if psc else None
    naics_codes = [n.strip() for n in naics.split(",")] if naics else DEFAULT_NAICS_CODES

    data = client.spending_by_category(
        category=group_by,
        psc_codes=psc_codes,
        naics_codes=naics_codes,
        agencies=agency_names,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return {
        "group_by": group_by,
        "results": data.get("results", []),
        "total": data.get("total", 0),
    }
