"""SAM.gov Contract Awards API client with TTL caching."""

import hashlib
import json
import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

SAM_BASE_URL = "https://api.sam.gov/contract-awards/v1/search"
SAM_OPPORTUNITIES_URL = "https://api.sam.gov/opportunities/v2/search"
CACHE_TTL = 3600  # 1 hour
OPPORTUNITIES_CACHE_TTL = 86400  # 24 hours — solicitations only need a daily refresh
MAX_CACHE_SIZE = 500

# Persisted to disk so a Render free-tier idle restart (which wipes the process
# but keeps the local disk within the same deploy) doesn't throw away results
# we already paid for out of SAM.gov's tight daily quota.
_CACHE_FILE = Path(__file__).resolve().parent / ".cache" / "sam_cache.json"

_cache: dict[str, tuple[float, dict]] = {}


def _load_cache_from_disk():
    try:
        raw = json.loads(_CACHE_FILE.read_text())
        for key, (ts, data) in raw.items():
            _cache[key] = (ts, data)
    except FileNotFoundError:
        pass
    except Exception:
        logger.exception("Failed to load SAM.gov cache from disk")


def _persist_cache_to_disk():
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(_cache))
        tmp.replace(_CACHE_FILE)
    except Exception:
        logger.exception("Failed to persist SAM.gov cache to disk")


_load_cache_from_disk()


def _cache_key(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(key: str, ttl: int = CACHE_TTL) -> dict | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < ttl:
            return data
    return None


def _get_stale(key: str) -> dict | None:
    """Return cached data regardless of age — used as a 429 fallback."""
    entry = _cache.get(key)
    return entry[1] if entry else None


def _set_cache(key: str, data: dict):
    if len(_cache) >= MAX_CACHE_SIZE and key not in _cache:
        oldest = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest]
    _cache[key] = (time.time(), data)
    _persist_cache_to_disk()


class SAMClient:
    """Thin wrapper around the SAM.gov Contract Awards API."""

    def __init__(self):
        self.api_key = os.environ.get("SAM_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FederalSpendingSearch/1.0",
            "Accept": "application/json",
        })

    def _get(self, params: dict) -> dict:
        key = _cache_key(params)
        cached = _get_cached(key)
        if cached is not None:
            return cached

        query = {**params, "api_key": self.api_key}
        r = self.session.get(SAM_BASE_URL, params=query, timeout=20)
        if r.status_code == 429:
            stale = _get_stale(key)
            if stale is not None:
                logger.warning("SAM.gov rate limited; serving stale cached contract award data")
                return stale
            raise RuntimeError("SAM.gov rate limit reached. Try again later.")
        r.raise_for_status()
        data = r.json()
        _set_cache(key, data)
        return data

    def search_opportunities(self, posted_from: str, posted_to: str, limit: int = 100, offset: int = 0) -> dict:
        """Fetch federal solicitations posted in a date range (MM/dd/yyyy).

        Cached for 24h since solicitation listings only need a daily refresh —
        keeps this well under SAM.gov's strict per-key rate limit. If a fresh
        fetch gets rate limited, falls back to whatever we last fetched
        successfully (even if stale) rather than erroring out entirely.
        """
        params = {"postedFrom": posted_from, "postedTo": posted_to, "limit": limit, "offset": offset}
        key = _cache_key({"opportunities": params})
        # The date range shifts daily (rolling window), so exact-key hits are
        # rare across days — keep a fixed "last known good" slot too, so we
        # always have *something* to fall back to once any fetch has ever
        # succeeded, even after the quota resets mid-window tomorrow.
        latest_key = _cache_key({"opportunities_latest": True})
        cached = _get_cached(key, ttl=OPPORTUNITIES_CACHE_TTL)
        if cached is not None:
            return cached

        query = {**params, "api_key": self.api_key}
        r = self.session.get(SAM_OPPORTUNITIES_URL, params=query, timeout=30)
        if r.status_code == 429:
            stale = _get_stale(key) or _get_stale(latest_key)
            if stale is not None:
                logger.warning("SAM.gov rate limited; serving stale cached opportunities data")
                return stale
            raise RuntimeError(
                "SAM.gov rate limit reached for the Opportunities API. This is a separate, much "
                "stricter daily quota than the Contract Awards API — individual SAM.gov accounts "
                "without an entity/system-account role are limited to 10 requests/day. It resets "
                "daily; results are cached for 24h once a fetch succeeds."
            )
        r.raise_for_status()
        data = r.json()
        _set_cache(key, data)
        _set_cache(latest_key, data)
        return data

    def search_by_piid(self, piid: str) -> dict | None:
        """Look up a contract by its PIID (Award ID).

        Tries the base award (mod 0) first, falls back to latest modification.
        """
        # Try base award first
        base = self._get({
            "piid": piid,
            "modificationNumber": "0",
            "limit": 1,
        })
        base_records = base.get("awardSummary", [])
        if base_records:
            return self._extract(base_records[0])

        # Fall back to latest modification
        data = self._get({
            "piid": piid,
            "limit": 1,
        })
        records = data.get("awardSummary", [])
        if not records:
            return None

        return self._extract(records[0])

    @staticmethod
    def _code_name(obj) -> str | None:
        """Extract display string from {code, name} objects."""
        if not obj or not isinstance(obj, dict):
            return None
        name = obj.get("name", "").strip()
        return name if name else obj.get("code")

    def _extract(self, record: dict) -> dict:
        """Pull the fields we care about from a SAM.gov record."""
        contract_id = record.get("contractId", {})
        core = record.get("coreData", {})
        fed_org = core.get("federalOrganization", {})
        contracting_info = fed_org.get("contractingInformation", {})
        award_details = record.get("awardDetails", {})
        awardee_data = award_details.get("awardeeData", {})
        awardee_header = awardee_data.get("awardeeHeader", {})
        awardee_location = awardee_data.get("awardeeLocation", {})
        awardee_uei = awardee_data.get("awardeeUEIInformation", {})
        dollars = award_details.get("dollars", {})
        total_dollars = award_details.get("totalContractDollars", {})
        competition = core.get("competitionInformation", {})
        product_info = core.get("productOrServiceInformation", {})
        product_svc = product_info.get("productOrService", {})
        naics_list = product_info.get("principalNaics", [])
        naics = naics_list[0] if naics_list else {}
        dates = award_details.get("dates", {})
        transaction = award_details.get("transactionData", {})
        description_info = award_details.get("productOrServiceInformation", {})

        dept = contracting_info.get("contractingDepartment", {})
        subtier = contracting_info.get("contractingSubtier", {})
        office = contracting_info.get("contractingOffice", {})

        # State can be a string or {code, name} object
        state_raw = awardee_location.get("state", {})
        awardee_state = state_raw.get("code", "").strip() if isinstance(state_raw, dict) else state_raw

        return {
            # Contract ID
            "piid": contract_id.get("piid"),
            "modification_number": contract_id.get("modificationNumber"),

            # Contracting organization
            "department_name": dept.get("name"),
            "department_code": dept.get("code", "").strip(),
            "subtier_name": subtier.get("name"),
            "subtier_code": subtier.get("code"),
            "office_name": office.get("name"),
            "office_code": office.get("code"),
            "office_country": office.get("country"),

            # Contracting officer info (from transaction data)
            "created_by": transaction.get("createdBy"),
            "approved_by": transaction.get("approvedBy"),
            "last_modified_by": transaction.get("lastModifiedBy"),

            # Awardee
            "awardee_name": awardee_header.get("awardeeName"),
            "awardee_legal_name": awardee_header.get("awardeeNameFromContract"),
            "awardee_uei": awardee_uei.get("uniqueEntityId"),
            "awardee_cage": awardee_uei.get("cageCode"),
            "awardee_parent_name": awardee_uei.get("awardeeUltimateParentName"),
            "awardee_address": awardee_location.get("streetAddress1"),
            "awardee_city": awardee_location.get("city"),
            "awardee_state": awardee_state,
            "awardee_zip": awardee_location.get("zip"),
            "awardee_phone": awardee_location.get("phoneNumber"),
            "awardee_fax": awardee_location.get("faxNumber"),

            # Dollars
            "action_obligation": dollars.get("actionObligation"),
            "base_and_options_value": dollars.get("baseAndAllOptionsValue"),
            "total_obligation": total_dollars.get("totalActionObligation"),
            "total_base_and_options": total_dollars.get("totalBaseAndAllOptionsValue"),

            # Product/Service
            "psc_code": product_svc.get("code"),
            "psc_description": product_svc.get("name"),
            "naics_code": naics.get("code"),
            "naics_description": naics.get("name"),
            "description": description_info.get("descriptionOfContractRequirement"),

            # Competition
            "set_aside_type": self._code_name(competition.get("typeOfSetAside")),
            "solicitation_procedures": self._code_name(competition.get("solicitationProcedures")),
            "extent_competed": self._code_name(competition.get("extentCompeted")),

            # Dates
            "effective_date": dates.get("periodOfPerformanceStartDate"),
            "completion_date": dates.get("ultimateCompletionDate"),
            "signed_date": dates.get("dateSigned"),

            # Place of performance
            "pop_city": core.get("principalPlaceOfPerformance", {}).get("city", {}).get("name"),
            "pop_state": self._code_name(core.get("principalPlaceOfPerformance", {}).get("state", {})),
        }
