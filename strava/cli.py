"""
Command-line entry point for the Strava CSV exporter.

Credentials are read from a ``.env`` file (or environment variables) using
python-dotenv. ``STRAVA_CLIENT_ID`` and ``STRAVA_CLIENT_SECRET`` must be set.
Handles authentication (reusing a saved session where possible), fetches all
activities, and writes them to a CSV file.
"""

import os

from dotenv import load_dotenv

from strava.api import fetch_all_activities
from strava.auth import get_valid_token, run_oauth, save_tokens
from strava.export import save_csv, save_sailing_logbook_xlsx, to_dataframe

OUTPUT_FILE = "strava_activities.csv"
SAILING_LOGBOOK_FILE = "sailing_logbook.xlsx"


def main():
    """Run the Strava → CSV export workflow.

    Loads ``STRAVA_CLIENT_ID`` and ``STRAVA_CLIENT_SECRET`` from a ``.env``
    file or the environment. Exits with an error message if either is missing.
    Fetches all activities and writes them to ``strava_activities.csv`` in the
    current working directory.
    """
    load_dotenv()

    print("=== Strava → CSV Exporter ===\n")

    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit(
            "Error: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in your .env file.\n"
            "See .env.example for reference."
        )

    access_token = get_valid_token(client_id, client_secret)

    if not access_token:
        print("\nNo saved session — starting OAuth login...")
        tokens = run_oauth(client_id, client_secret)
        save_tokens(tokens)
        access_token = tokens["access_token"]
        print("Authorised successfully!\n")
    else:
        print("Using saved session.\n")

    print("Fetching activities from Strava...")
    activities = fetch_all_activities(access_token)

    save_csv(activities, OUTPUT_FILE)

    df = to_dataframe(activities)
    print(f"\n{df.to_string(index=False)}")


def sailing_logbook():
    """Export the sailing logbook to an Excel file.

    Loads ``STRAVA_CLIENT_ID`` and ``STRAVA_CLIENT_SECRET`` from a ``.env``
    file or the environment. Fetches all activities, filters to sailing entries,
    annotates each with minutes after sunset, and writes ``sailing_logbook.xlsx``
    to the current working directory.
    """
    load_dotenv()

    print("=== Strava Sailing Logbook Exporter ===\n")

    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit(
            "Error: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in your .env file.\n"
            "See .env.example for reference."
        )

    access_token = get_valid_token(client_id, client_secret)

    if not access_token:
        print("\nNo saved session — starting OAuth login...")
        tokens = run_oauth(client_id, client_secret)
        save_tokens(tokens)
        access_token = tokens["access_token"]
        print("Authorised successfully!\n")
    else:
        print("Using saved session.\n")

    print("Fetching activities from Strava...")
    activities = fetch_all_activities(access_token)

    df = to_dataframe(activities)
    save_sailing_logbook_xlsx(df, SAILING_LOGBOOK_FILE)
