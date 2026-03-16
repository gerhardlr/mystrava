"""CLI client for end-to-end testing and inspection of the Strava FastAPI.

Usage:
  strava-api-client health
  strava-api-client activities [--limit N]
  strava-api-client sailing
  strava-api-client --base-url https://your-api.vercel.app sailing
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

from strava.auth import get_valid_token, run_oauth, save_tokens

load_dotenv()

DEFAULT_BASE_URL = "http://localhost:8000"


class StravaApiClient:
    """HTTP client for the Strava FastAPI backend.

    Loads and refreshes OAuth tokens on construction so all subsequent
    calls are authenticated without any extra setup.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._token = self._load_token()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _load_token(self) -> str:
        client_id = os.getenv("STRAVA_CLIENT_ID")
        client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        if not client_id or not client_secret:
            sys.exit("ERROR: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env")

        token = get_valid_token(client_id, client_secret)
        if not token:
            print("No saved session — starting OAuth flow...")
            tokens = run_oauth(client_id, client_secret)
            save_tokens(tokens)
            token = tokens["access_token"]
        return token

    # ------------------------------------------------------------------
    # Low-level request
    # ------------------------------------------------------------------

    def _get(self, path: str, auth: bool = True) -> dict:
        headers = {"Authorization": f"Bearer {self._token}"} if auth else {}
        resp = requests.get(f"{self.base_url}{path}", headers=headers)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # API methods
    # ------------------------------------------------------------------

    def health(self) -> dict:
        return self._get("/api/health", auth=False)

    def activities(self) -> dict:
        return self._get("/api/activities")

    def sailing(self) -> dict:
        return self._get("/api/activities/sailing")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Strava API CLI client")
    parser.add_argument(
        "--base-url", default=os.getenv("NEXT_PUBLIC_API_URL", DEFAULT_BASE_URL),
        help="API base URL (default: http://localhost:8000)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health", help="Check API liveness")

    p_act = sub.add_parser("activities", help="List activities")
    p_act.add_argument("--limit", type=int, default=10, metavar="N",
                       help="Max activities to show (default: 10, 0 = all)")

    sub.add_parser("sailing", help="List sailing logbook")

    args = parser.parse_args()
    client = StravaApiClient(base_url=args.base_url)

    if args.command == "health":
        print(json.dumps(client.health(), indent=2))
    elif args.command == "activities":
        data = client.activities()
        activities = data["activities"][:args.limit] if args.limit else data["activities"]
        print(json.dumps({"count": data["count"], "activities": activities}, indent=2))
    elif args.command == "sailing":
        print(json.dumps(client.sailing(), indent=2))


if __name__ == "__main__":
    main()
