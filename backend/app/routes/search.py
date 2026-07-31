"""Award search endpoint."""

from fastapi import APIRouter, Query

from ..client import USASpendingClient
from ..config import SET_ASIDE_RECIPIENT_TYPES

router = APIRouter()
client = USASpendingClient()


@router.get("/api/search")
def search_awards(
    agency: str | None = Query(None, description="Comma-separated federal agency names, or omit for all"),
    psc: str | None = Query(None, description="Comma-separated PSC codes, or omit for all"),
    recipient: str | None = Query(None, description="Recipient/vendor name search text"),
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    set_aside: str | None = Query(None, description="Set-aside filter, e.g. SDVOSB"),
    sort: str = Query("Start Date", description="Sort field"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    agency_names = [a.strip() for a in agency.split(",")] if agency else None
    psc_codes = [p.strip() for p in psc.split(",")] if psc else None
    set_aside_types = SET_ASIDE_RECIPIENT_TYPES.get(set_aside.upper()) if set_aside else None

    data = client.search_awards(
        psc_codes=psc_codes,
        agencies=agency_names,
        recipient_text=recipient or None,
        start_date=start_date,
        end_date=end_date,
        set_aside_types=set_aside_types,
        limit=limit,
        page=page,
        sort=sort,
        order=order,
    )

    results = data.get("results", [])
    page_meta = data.get("page_metadata", {})
    has_next = page_meta.get("hasNext", False)

    return {
        "results": results,
        "count": len(results),
        "has_next": has_next,
        "page": page,
        "limit": limit,
    }
