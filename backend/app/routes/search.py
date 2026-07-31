"""Award search endpoint."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from ..client import USASpendingClient
from ..config import DEFAULT_NAICS_CODES
from ..reseller_match import match_competitor, normalize_set_aside

logger = logging.getLogger(__name__)

router = APIRouter()
client = USASpendingClient()

# USASpending's search API has no native way to filter on the award-level
# "Type of Set Aside" text field (only on the recipient's own business
# classification, which is a different and unreliably-populated thing — see
# note below). So a set-aside filter has to scan real pages of results and
# classify them client-side with normalize_set_aside(). A single page isn't
# enough: sorted by recency, the most recent activity in a broad NAICS/agency
# search is often dominated by a handful of high-volume non-set-aside vendors,
# which can crowd out real matches entirely. Scan several pages instead.
SET_ASIDE_SCAN_PAGE_SIZE = 100
SET_ASIDE_SCAN_PAGES_PER_REQUEST = 5


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
    set_aside_code = set_aside.upper() if set_aside else None

    def _fetch_page(fetch_page: int, fetch_limit: int) -> dict:
        try:
            return client.search_awards(
                psc_codes=psc_codes,
                naics_codes=naics_codes,
                agencies=agency_names,
                recipient_text=recipient or None,
                start_date=start_date,
                end_date=end_date,
                limit=fetch_limit,
                page=fetch_page,
                sort=sort,
                order=order,
            )
        except Exception as e:
            logger.exception("USASpending search failed")
            raise HTTPException(status_code=502, detail=f"USASpending.gov API is temporarily unavailable: {e}")

    if set_aside_code:
        # Recipient's own SAM.gov business classification (USASpending's
        # "recipient_type_names" filter) isn't the same thing as the set-aside
        # actually used to compete THIS award, and is unreliably populated —
        # that mismatch is why this filter used to silently return nothing.
        # Scan several pages of real results and classify each award's own
        # "Type of Set Aside" field instead.
        results = []
        has_next = False
        start_page = (page - 1) * SET_ASIDE_SCAN_PAGES_PER_REQUEST + 1
        for underlying_page in range(start_page, start_page + SET_ASIDE_SCAN_PAGES_PER_REQUEST):
            data = _fetch_page(underlying_page, SET_ASIDE_SCAN_PAGE_SIZE)
            page_rows = data.get("results", [])
            results.extend(
                r for r in page_rows if normalize_set_aside(r.get("Type of Set Aside")) == set_aside_code
            )
            if not data.get("page_metadata", {}).get("hasNext", False):
                has_next = False
                break
            has_next = True
    else:
        data = _fetch_page(page, limit)
        results = data.get("results", [])
        has_next = data.get("page_metadata", {}).get("hasNext", False)

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

    if set_aside_code:
        results = results[:limit]

    for row in results:
        row["reseller_partner_match"] = match_competitor(row.get("Recipient Name"))

    return {
        "results": results,
        "count": len(results),
        "has_next": has_next,
        "page": page,
        "limit": limit,
    }
