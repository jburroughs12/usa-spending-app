"""Award detail endpoint — full contract detail sourced from USASpending.gov.

No API key, no rate limit. This is the primary data source for the Contract
Detail panel; SAM.gov (see contract_detail.py) is only used as an optional,
user-triggered lookup for contracting officer contact info.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from ..client import USASpendingClient

logger = logging.getLogger(__name__)

router = APIRouter()
client = USASpendingClient()


def _first(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return None


@router.get("/api/award-detail")
def award_detail(
    internal_id: str = Query(..., min_length=1, description="USASpending.gov internal award id"),
):
    try:
        record = client.get_award(internal_id)
    except Exception:
        logger.exception("USASpending award lookup failed for internal_id=%s", internal_id)
        raise HTTPException(status_code=502, detail="USASpending.gov API is temporarily unavailable")

    if not record or record.get("detail"):
        raise HTTPException(status_code=404, detail=f"No USASpending.gov record found for id: {internal_id}")

    awarding_agency = record.get("awarding_agency") or {}
    toptier = awarding_agency.get("toptier_agency") or {}
    subtier = awarding_agency.get("subtier_agency") or {}

    recipient = record.get("recipient") or {}
    recipient_location = recipient.get("location") or {}

    pop = record.get("place_of_performance") or {}

    pop_state = _first(pop, "state_code")
    txn = record.get("latest_transaction_contract_data") or {}

    period = record.get("period_of_performance") or {}

    return {
        "piid": record.get("piid"),

        "department_name": toptier.get("name"),
        "subtier_name": subtier.get("name"),
        "office_name": awarding_agency.get("office_agency_name"),

        "awardee_name": recipient.get("recipient_name"),
        "awardee_parent_name": recipient.get("parent_recipient_name"),
        "awardee_uei": recipient.get("recipient_uei"),
        "awardee_address": recipient_location.get("address_line1"),
        "awardee_city": recipient_location.get("city_name"),
        "awardee_state": recipient_location.get("state_code"),
        "awardee_zip": recipient_location.get("zip5"),

        "action_obligation": record.get("total_obligation"),
        "base_and_options_value": record.get("base_and_all_options_value"),
        "total_obligation": record.get("total_obligation"),
        "total_base_and_options": record.get("base_and_all_options_value"),

        "psc_code": _first(txn, "product_or_service_code"),
        "psc_description": _first(txn, "product_or_service_description", "product_or_service_co_description"),
        "naics_code": _first(txn, "naics"),
        "naics_description": _first(txn, "naics_description"),
        "description": record.get("description"),

        "set_aside_type": _first(txn, "type_set_aside_description", "type_set_aside"),
        "solicitation_procedures": _first(txn, "solicitation_procedures_description", "solicitation_procedures"),
        "extent_competed": _first(txn, "extent_competed_description", "extent_competed"),

        "effective_date": period.get("start_date"),
        "completion_date": period.get("end_date"),
        "signed_date": record.get("date_signed"),

        "pop_city": pop.get("city_name"),
        "pop_state": pop_state,
    }
