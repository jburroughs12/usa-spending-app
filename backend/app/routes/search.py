"""Award search endpoint."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from ..client import USASpendingClient
from ..config import DEFAULT_NAICS_CODES, SET_ASIDE_RECIPIENT_TYPES
from ..reseller_match import match_competitor

router = APIRouter()
client = USASpendingClient()


@router.get("/api/search")
def search_awards(
    agency: str | None = Query(None, description="Comma-separated federal agency names, or omit for all"),
    psc: str | None = Query(None, description="Comma-separated PSC codes, or omit for all"),
    naics: str | None = Query(None, description="Comma-separated NAICS codes, or omit for the default set"),
    recipient: str | None = Query(None, description="Recipient/vendor name search text"),
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    set_aside: str | None = Query(None, description="Set-aside filter, e.g. SDVOSB"),
    expiring_within_days: int | None = Query(
        None, description="Only show contracts whose End Date falls within the next N days"
    ),
    expiring_from_days: int | None = Query(
        None, description="Only show contracts whose End Date is at least N days out"
    ),
    sort: str = Query("Start Date", description="Sort field"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    agency_names = [a.strip() for a in agency.split(",")] if agency else None
    psc_codes = [p.strip() for p in psc.split(",")] if psc else None
    naics_codes = [n.strip() for n in naics.split(",")] if naics else DEFAULT_NAICS_CODES
    set_aside_types = SET_ASIDE_RECIPIENT_TYPES.get(set_aside.upper()) if set_aside else None

    data = client.search_awards(
        psc_codes=psc_codes,
        naics_codes=naics_codes,
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

    # Expiration-range filter: applied to the fetched page, since USASpending's
    # search API doesn't support filtering by period-of-performance end date
    # directly. Sort by "End Date" ascending when using this for best results.
    if expiring_within_days is not None or expiring_from_days is not None:
        today = datetime.today().date()
        min_date = today + timedelta(days=expiring_from_days) if expiring_from_days is not None else None
        max_date = today + timedelta(days=expiring_within_days) if expiring_within_days is not None else None

        def _in_range(row):
            raw = row.get("End Date")
            if not raw:
                return False
            try:
                end = datetime.strptime(raw[:10], "%Y-%m-%d").date()
            except ValueError:
                return False
            if min_date and end < min_date:
                return False
            if max_date and end > max_date:
                return False
            return True

        results = [r for r in results if _in_range(r)]

    for row in results:
        row["reseller_partner_match"] = match_competitor(row.get("Recipient Name"))

    page_meta = data.get("page_metadata", {})
    has_next = page_meta.get("hasNext", False)

    return {
        "results": results,
        "count": len(results),
        "has_next": has_next,
        "page": page,
        "limit": limit,
    }
