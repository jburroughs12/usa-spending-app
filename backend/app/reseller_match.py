"""Reseller partner matching.

Scores the authorized reseller network (config.RESELLER_PARTNERS) against a
solicitation's NAICS code, set-aside requirement, and awarding agency, using
each reseller's historical USASpending.gov award profile (set-aside
certifications are static, from config; NAICS/agency history is fetched live
and cached).
"""

import logging
import time

from .client import USASpendingClient
from .config import RESELLER_PARTNERS

logger = logging.getLogger(__name__)

_client = USASpendingClient()

_PROFILE_CACHE_TTL = 86400  # 24 hours
_profile_cache: dict[str, tuple[float, dict]] = {}

# Ordered (most-specific-first) keyword rules for normalizing raw set-aside
# labels — from the reseller directory (short codes) or SAM.gov (verbose
# descriptions like "Total Small Business Set-Aside (FAR 19.5)") — into a
# common vocabulary for matching. Checked in order so e.g. "SDVOSB" wins over
# a later generic "small business" match.
_SET_ASIDE_KEYWORD_RULES = [
    ("SDVOSB", ["SDVOSB", "SERVICE-DISABLED VETERAN", "SERVICE DISABLED VETERAN"]),
    ("HUBZONE", ["HUBZONE"]),
    ("8A", ["8(A)", "8A PROGRAM", " 8A ", "8A-"]),
    ("WOSB", ["WOSB", "WOMEN-OWNED", "WOMEN OWNED"]),
    ("DBE", ["DBE", "DISADVANTAGED BUSINESS"]),
    ("SB", ["SMALL BUSINESS", "SB SET-ASIDE", " SB "]),
]


def normalize_set_aside(raw: str | None) -> str | None:
    if not raw:
        return None
    upper = f" {raw.strip().upper()} "
    for code, keywords in _SET_ASIDE_KEYWORD_RULES:
        if any(kw in upper for kw in keywords):
            return code
    return None


def _get_profile(recipient_name: str) -> dict:
    """Cached lookup of a reseller's historical NAICS codes and awarding agencies."""
    cached = _profile_cache.get(recipient_name)
    if cached and time.time() - cached[0] < _PROFILE_CACHE_TTL:
        return cached[1]

    naics_codes: set[str] = set()
    agencies: set[str] = set()
    try:
        data = _client.get_recipient_profile(recipient_name)
        for row in data.get("results", []):
            naics = row.get("NAICS Code")
            if naics:
                naics_codes.add(str(naics).strip())
            agency = row.get("Awarding Agency")
            if agency:
                agencies.add(agency)
    except Exception:
        logger.exception("Failed to build reseller profile for %s", recipient_name)

    profile = {"naics_codes": naics_codes, "agencies": agencies}
    _profile_cache[recipient_name] = (time.time(), profile)
    return profile


def score_resellers(
    naics_code: str | None = None,
    set_aside_code: str | None = None,
    agency_name: str | None = None,
    top_n: int = 3,
) -> list[dict]:
    """Rank the reseller partner network against a solicitation's requirements."""
    scored = []
    for partner in RESELLER_PARTNERS:
        score = 0
        reasons = []

        if set_aside_code and set_aside_code in partner["set_asides"]:
            score += 2
            reasons.append(f"Certified {set_aside_code}")

        profile = _get_profile(partner["name"])
        if naics_code and naics_code in profile["naics_codes"]:
            score += 2
            reasons.append(f"Prior awards under NAICS {naics_code}")
        if agency_name and agency_name in profile["agencies"]:
            score += 1
            reasons.append(f"Prior awards with {agency_name}")

        if score > 0:
            scored.append({
                "name": partner["name"],
                "website": partner["website"],
                "set_asides": partner["set_asides"],
                "score": score,
                "reasons": reasons,
            })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_n]


def match_competitor(recipient_name: str | None) -> str | None:
    """Return the reseller partner name if recipient_name matches one, else None."""
    if not recipient_name:
        return None
    normalized = recipient_name.strip().upper()
    for partner in RESELLER_PARTNERS:
        if partner["name"].strip().upper() in normalized or normalized in partner["name"].strip().upper():
            return partner["name"]
    return None
