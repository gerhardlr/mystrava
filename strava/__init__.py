"""
strava — Strava CSV exporter.

Fetches all activities for an authenticated athlete via the Strava v3 API
and exports them to a CSV file.

Modules:
    auth    — OAuth2 token management and browser-based login flow.
    api     — Paginated activity retrieval from the Strava REST API.
    export  — Conversion of raw activity data to CSV rows.
    cli     — Command-line entry point (``strava-export``).
"""
