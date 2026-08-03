#!/usr/bin/env python3
"""Fetch SAM.gov Opportunities data once and write a snapshot file.

Run on a schedule via .github/workflows/refresh-solicitations.yml (once a
day) so the live app never calls SAM.gov's Opportunities API directly from
a user request. That API has a much stricter daily quota than Contract
Awards — as low as 10 requests/day for individual accounts without an
entity role — so a single controlled fetch per day keeps well under it
regardless of how often the app itself is used or redeployed.

On failure, this leaves the previously committed snapshot untouched rather
than overwriting it with nothing — a day-old snapshot is better than none.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.sam_client import SAMClient  # noqa: E402

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "solicitations_snapshot.json"

# Fetch a slightly wider window than the app's 30-day default display range,
# so a missed day or two of the schedule doesn't immediately leave gaps.
FETCH_WINDOW_DAYS = 35


def main() -> int:
    client = SAMClient()
    if not client.api_key:
        print("SAM_API_KEY is not set", file=sys.stderr)
        return 1

    today = datetime.today()
    posted_from = (today - timedelta(days=FETCH_WINDOW_DAYS)).strftime("%m/%d/%Y")
    posted_to = today.strftime("%m/%d/%Y")

    try:
        data = client.search_opportunities(posted_from=posted_from, posted_to=posted_to, limit=1000)
    except Exception as e:
        print(f"Fetch failed, leaving existing snapshot in place: {e}", file=sys.stderr)
        return 1

    opportunities = data.get("opportunitiesData", [])

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "fetched_at": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "posted_from": posted_from,
        "posted_to": posted_to,
        "opportunitiesData": opportunities,
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2))
    print(f"Wrote {len(opportunities)} opportunities to {SNAPSHOT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
