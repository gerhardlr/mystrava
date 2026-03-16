"""
Strava API client.

Thin wrapper around the Strava v3 REST API. Currently supports paginated
retrieval of all activities for the authenticated athlete.
"""

import time

import requests

API_BASE = "https://www.strava.com/api/v3"


def fetch_all_activities(access_token: str) -> list[dict]:
    """Fetch every activity for the authenticated athlete.

    Iterates through all pages of the ``/athlete/activities`` endpoint,
    collecting results until an empty page is returned.

    Args:
        access_token: A valid Strava OAuth2 access token.

    Returns:
        A list of raw activity dicts as returned by the Strava API.

    Raises:
        requests.HTTPError: If any paginated request returns a non-2xx status.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    activities = []
    page = 1
    per_page = 200

    while True:
        print(f"  Fetching page {page}...", end="\r")
        resp = requests.get(
            f"{API_BASE}/athlete/activities",
            headers=headers,
            params={"per_page": per_page, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
        time.sleep(0.3)  # be polite to the API

    print(f"\n  Total activities fetched: {len(activities)}")
    return activities
