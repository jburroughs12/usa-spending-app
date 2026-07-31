"""USASpending.gov API client with TTL caching."""

import hashlib
import json
import time
from datetime import datetime

import requests

BASE_URL = "https://api.usaspending.gov/api/v2"
CACHE_TTL = 3600  # 1 hour
MAX_CACHE_SIZE = 500


def _psc_require(codes: list) -> list:
    """Convert flat PSC code list to the API's required hierarchical format."""
    result = []
    seen = set()
    for code in codes:
        key = code.strip().upper()
        if key not in seen:
            seen.add(key)
            result.append(["Product", key[:2], key])
    return result


def _fy_start(year: int = None) -> str:
    today = datetime.today()
    fy_year = year or (today.year if today.month >= 10 else today.year - 1)
    return f"{fy_year}-10-01"


# Simple in-memory cache: {hash: (timestamp, data)}
_cache: dict[str, tuple[float, dict]] = {}


def _cache_key(endpoint: str, payload: dict) -> str:
    raw = f"{endpoint}:{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(key: str) -> dict | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _set_cache(key: str, data: dict):
    if len(_cache) >= MAX_CACHE_SIZE:
        oldest = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest]
    _cache[key] = (time.time(), data)


class USASpendingClient:
    """Thin wrapper around the USASpending.gov REST API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "BBS-SpendingSearch/1.0",
        })

    def _post(self, endpoint: str, payload: dict) -> dict:
        key = _cache_key(endpoint, payload)
        cached = _get_cached(key)
        if cached is not None:
            return cached

        url = f"{BASE_URL}{endpoint}"
        r = self.session.post(url, json=payload, timeout=45)
        r.raise_for_status()
        data = r.json()
        _set_cache(key, data)
        return data

    def _get(self, endpoint: str) -> dict:
        key = _cache_key(endpoint, {})
        cached = _get_cached(key)
        if cached is not None:
            return cached

        url = f"{BASE_URL}{endpoint}"
        r = self.session.get(url, timeout=45)
        r.raise_for_status()
        data = r.json()
        _set_cache(key, data)
        return data

    def get_award(self, award_id: str) -> dict:
        """Fetch full award detail via GET /awards/<id>/. No API key or rate limit."""
        return self._get(f"/awards/{award_id}/")

    def search_awards(
        self,
        psc_codes: list[str] | None = None,
        agencies: list[str] | None = None,
        recipient_text: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        set_aside_types: list[str] | None = None,
        limit: int = 100,
        page: int = 1,
        sort: str = "Award Amount",
        order: str = "desc",
    ) -> dict:
        """Search contracts via POST /search/spending_by_award/."""
        # Always enforce 5-year lookback window
        five_years_ago = (datetime.today().replace(year=datetime.today().year - 5)).strftime("%Y-%m-%d")
        if not start_date or start_date < five_years_ago:
            start_date = five_years_ago
        if not end_date:
            end_date = datetime.today().strftime("%Y-%m-%d")

        filters = {
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{"start_date": start_date, "end_date": end_date}],
        }

        if psc_codes:
            filters["psc_codes"] = {"require": _psc_require(psc_codes)}
        if agencies:
            filters["agencies"] = [
                {"type": "awarding", "tier": "toptier", "name": name}
                for name in agencies
            ]
        if recipient_text:
            filters["recipient_search_text"] = [recipient_text]
        if set_aside_types:
            filters["recipient_type_names"] = set_aside_types

        payload = {
            "filters": filters,
            "fields": [
                "Award ID",
                "Recipient Name",
                "Recipient UEI",
                "Awarding Agency",
                "Awarding Sub Agency",
                "Awarding Office Name",
                "Award Amount",
                "Description",
                "Start Date",
                "End Date",
                "Contract Award Type",
                "Type of Set Aside",
                "Place of Performance State Code",
            ],
            "sort": sort,
            "order": order,
            "limit": limit,
            "page": page,
        }

        return self._post("/search/spending_by_award/", payload)

    def spending_by_category(
        self,
        category: str,
        psc_codes: list[str] | None = None,
        agencies: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 25,
    ) -> dict:
        """Aggregate spending by category: 'recipient', 'psc', or 'awarding_agency'."""
        if not start_date:
            start_date = _fy_start()
        if not end_date:
            end_date = datetime.today().strftime("%Y-%m-%d")

        filters = {
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{"start_date": start_date, "end_date": end_date}],
        }

        if psc_codes:
            filters["psc_codes"] = {"require": _psc_require(psc_codes)}
        if agencies:
            filters["agencies"] = [
                {"type": "awarding", "tier": "toptier", "name": name}
                for name in agencies
            ]

        payload = {
            "category": category,
            "filters": filters,
            "limit": limit,
            "page": 1,
        }

        return self._post(f"/search/spending_by_category/{category}/", payload)
