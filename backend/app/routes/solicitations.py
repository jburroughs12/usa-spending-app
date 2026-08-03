"""SAM.gov solicitations (open opportunities) endpoint.

Cached for 24h in the SAM client since this only needs a daily refresh —
keeps well under SAM.gov's strict per-key rate limit. Defaults to Grainger's
NAICS code set; results are enriched with reseller partner recommendations.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from ..config import DEFAULT_NAICS_CODES
from ..reseller_match import normalize_set_aside, score_resellers
from ..sam_client import SAMClient

logger = logging.getLogger(__name__)
"""SAM.gov solicitations (open opportunities) endpoint.

Reads from a snapshot file refreshed once daily by a scheduled GitHub
Action (see backend/scripts/refresh_solicitations.py and
.github/workflows/refresh-solicitations.yml), instead of calling SAM.gov's
Opportunities API live. That API has a much stricter daily quota than
Contract Awards — as low as 10 requests/day for individual accounts
without an entity role — and a live-per-request pattern kept burning
through it just from normal use and redeploys. Since the snapshot is
committed to the repo, this endpoint is effectively free to call as often
as needed; the daily Action is the only thing that ever talks to SAM.gov.
Defaults to Grainger's NAICS code set; results are enriched with reseller
partner recommendations.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..config import DEFAULT_NAICS_CODES
from ..reseller_match import normalize_set_aside, score_resellers

logger = logging.getLogger(__name__)

router = APIRouter()

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "solicitations_snapshot.json"


def _first_contact(contacts) -> str | None:
    if not contacts or not isinstance(contacts, list):
        return None
    primary = contacts[0]
    name = primary.get("fullName")
    email = primary.get("email")
    if name and email:
        return f"{name} <{email}>"
    return name or email


def _load_snapshot() -> dict:
    try:
        return json.loads(SNAPSHOT_PATH.read_text())
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="No solicitations snapshot yet. The daily SAM.gov refresh hasn't run — "
                   "trigger it manually from the repo's Actions tab, or wait for the next scheduled run.",
        )
    except Exception:
        logger.exception("Failed to read solicitations snapshot")
        raise HTTPException(status_code=500, detail="Solicitations snapshot is corrupted")


@router.get("/api/solicitations")
def list_solicitations(
    naics: str | None = Query(None, description="Comma-separated NAICS codes, or omit for Grainger default set"),
    set_aside: str | None = Query(None, description="Set-aside filter, e.g. SDVOSB"),
    keyword: str | None = Query(None, description="Keyword search in solicitation title"),
    posted_from: str | None = Query(None, description="Posted-after date YYYY-MM-DD"),
    posted_to: str | None = Query(None, description="Posted-before date YYYY-MM-DD"),
    active_only: bool = Query(True, description="Only show currently active solicitations"),
    limit: int = Query(50, ge=1, le=200),
):
    naics_filter = {n.strip() for n in naics.split(",")} if naics else set(DEFAULT_NAICS_CODES)

    snapshot = _load_snapshot()

    today = datetime.today()
    to_dt = datetime.strptime(posted_to, "%Y-%m-%d") if posted_to else today
    from_dt = datetime.strptime(posted_from, "%Y-%m-%d") if posted_from else today - timedelta(days=30)

    set_aside_code = set_aside.upper() if set_aside else None
    keyword_lower = keyword.lower() if keyword else None

    results = []
    for raw in snapshot.get("opportunitiesData", []):
        posted_raw = raw.get("postedDate")
        if posted_raw:
            try:
                posted_dt = datetime.strptime(posted_raw[:10], "%Y-%m-%d")
                if posted_dt < from_dt or posted_dt > to_dt:
                    continue
            except ValueError:
                pass

        opp_naics = str(raw.get("naicsCode") or "").strip()
        if naics_filter and opp_naics not in naics_filter:
            continue
        if active_only and str(raw.get("active", "")).strip().lower() == "no":
            continue

        title = raw.get("title") or ""
        if keyword_lower and keyword_lower not in title.lower():
            continue

        opp_set_aside_raw = raw.get("typeOfSetAsideDescription") or raw.get("typeOfSetAside")
        opp_set_aside_norm = normalize_set_aside(opp_set_aside_raw)
        if set_aside_code and opp_set_aside_norm != set_aside_code:
            continue

        agency_name = raw.get("fullParentPathName")

        recommended = score_resellers(
            naics_code=opp_naics or None,
            set_aside_code=opp_set_aside_norm,
            agency_name=agency_name,
        )

        results.append({
            "notice_id": raw.get("noticeId"),
            "title": title,
            "solicitation_number": raw.get("solicitationNumber"),
            "agency": agency_name,
            "posted_date": raw.get("postedDate"),
            "response_deadline": raw.get("responseDeadLine"),
            "naics_code": opp_naics or None,
            "psc_code": raw.get("classificationCode"),
            "set_aside": opp_set_aside_raw,
            "active": raw.get("active"),
            "point_of_contact": _first_contact(raw.get("pointOfContact")),
            "sam_url": raw.get("uiLink"),
            "recommended_resellers": recommended,
        })

        if len(results) >= limit:
            break

    return {
        "results": results,
        "count": len(results),
        "posted_from": from_dt.strftime("%Y-%m-%d"),
        "posted_to": to_dt.strftime("%Y-%m-%d"),
        "snapshot_fetched_at": snapshot.get("fetched_at"),
    }

router = APIRouter()
sam = SAMClient()


def _first_contact(contacts) -> str | None:
    if not contacts or not isinstance(contacts, list):
        return None
    primary = contacts[0]
    name = primary.get("fullName")
    email = primary.get("email")
    if name and email:
        return f"{name} <{email}>"
    return name or email


@router.get("/api/solicitations")
def list_solicitations(
    naics: str | None = Query(None, description="Comma-separated NAICS codes, or omit for Grainger default set"),
    set_aside: str | None = Query(None, description="Set-aside filter, e.g. SDVOSB"),
    keyword: str | None = Query(None, description="Keyword search in solicitation title"),
    posted_from: str | None = Query(None, description="Posted-after date YYYY-MM-DD"),
    posted_to: str | None = Query(None, description="Posted-before date YYYY-MM-DD"),
    active_only: bool = Query(True, description="Only show currently active solicitations"),
    limit: int = Query(50, ge=1, le=200),
):
    api_key = sam.api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="SAM_API_KEY not configured")

    naics_filter = {n.strip() for n in naics.split(",")} if naics else set(DEFAULT_NAICS_CODES)

    today = datetime.today()
    to_dt = datetime.strptime(posted_to, "%Y-%m-%d") if posted_to else today
    from_dt = datetime.strptime(posted_from, "%Y-%m-%d") if posted_from else today - timedelta(days=30)

    try:
        data = sam.search_opportunities(
            posted_from=from_dt.strftime("%m/%d/%Y"),
            posted_to=to_dt.strftime("%m/%d/%Y"),
            limit=min(limit * 5, 1000),  # over-fetch since NAICS/keyword/set-aside are filtered client-side
        )
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception:
        logger.exception("SAM.gov opportunities lookup failed")
        raise HTTPException(status_code=502, detail="SAM.gov API is temporarily unavailable")

    set_aside_code = set_aside.upper() if set_aside else None
    keyword_lower = keyword.lower() if keyword else None

    results = []
    for raw in data.get("opportunitiesData", []):
        opp_naics = str(raw.get("naicsCode") or "").strip()
        if naics_filter and opp_naics not in naics_filter:
            continue
        if active_only and str(raw.get("active", "")).strip().lower() == "no":
            continue

        title = raw.get("title") or ""
        if keyword_lower and keyword_lower not in title.lower():
            continue

        opp_set_aside_raw = raw.get("typeOfSetAsideDescription") or raw.get("typeOfSetAside")
        opp_set_aside_norm = normalize_set_aside(opp_set_aside_raw)
        if set_aside_code and opp_set_aside_norm != set_aside_code:
            continue

        agency_name = raw.get("fullParentPathName")

        recommended = score_resellers(
            naics_code=opp_naics or None,
            set_aside_code=opp_set_aside_norm,
            agency_name=agency_name,
        )

        results.append({
            "notice_id": raw.get("noticeId"),
            "title": title,
            "solicitation_number": raw.get("solicitationNumber"),
            "agency": agency_name,
            "posted_date": raw.get("postedDate"),
            "response_deadline": raw.get("responseDeadLine"),
            "naics_code": opp_naics or None,
            "psc_code": raw.get("classificationCode"),
            "set_aside": opp_set_aside_raw,
            "active": raw.get("active"),
            "point_of_contact": _first_contact(raw.get("pointOfContact")),
            "sam_url": raw.get("uiLink"),
            "recommended_resellers": recommended,
        })

        if len(results) >= limit:
            break

    return {
        "results": results,
        "count": len(results),
        "posted_from": from_dt.strftime("%Y-%m-%d"),
        "posted_to": to_dt.strftime("%Y-%m-%d"),
    }
