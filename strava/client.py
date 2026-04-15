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

import pathlib
import time as _time

from strava.auth import get_valid_token, run_oauth, save_tokens
from strava.navigation import compute_track
from strava.export import save_track_xlsx
from strava.gpx import write_gpx

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

    def _fetch_streams(self, activity_id: int, keys: str = "latlng,time,velocity_smooth,altitude") -> dict:
        resp = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            headers={"Authorization": f"Bearer {self._token}"},
            params={"keys": keys, "key_by_type": "true"},
        )
        resp.raise_for_status()
        return resp.json()

    def track(self, activity_id: int) -> list[dict]:
        """
        Fetch GPS + time streams for an activity directly from the Strava API
        and compute bearing, rotation, and rate-of-turn for each point.
        """
        data = self._fetch_streams(activity_id)
        latlng = data["latlng"]["data"]
        times = data["time"]["data"]
        velocities = data.get("velocity_smooth", {}).get("data")
        points = compute_track(latlng, times, velocities)
        return [
            {
                "index": p.index,
                "lat": p.lat,
                "lon": p.lon,
                "time_s": p.time_s,
                "bearing_deg": round(p.bearing_deg, 1) if p.bearing_deg is not None else None,
                "rotation_deg": round(p.rotation_deg, 1) if p.rotation_deg is not None else None,
                "rot_speed_deg_min": round(p.rot_speed_deg_min, 2) if p.rot_speed_deg_min is not None else None,
            }
            for p in points
        ]


    def export_gpx_all(self, out_dir: str = "gpx_exports") -> list[str]:
        """
        Export all sailing activities as individual GPX files.

        Fetches the sailing logbook, then downloads GPS streams for each
        activity and writes one .gpx file per activity to ``out_dir``.

        Returns the list of file paths written.
        """
        out_path = pathlib.Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        data = self.sailing()
        activities = data.get("activities", [])
        written: list[str] = []

        for idx, activity in enumerate(activities, 1):
            activity_id = activity.get("id")
            name = activity.get("name", f"activity_{activity_id}")
            start = activity.get("start_date_local", "")

            if not activity_id:
                print(f"  [{idx}/{len(activities)}] Skipping '{name}' — no id")
                continue

            print(f"  [{idx}/{len(activities)}] {name} ({activity_id}) ...", end=" ", flush=True)
            try:
                streams = self._fetch_streams(activity_id)
                latlng = streams.get("latlng", {}).get("data", [])
                times_s = streams.get("time", {}).get("data", [])
                velocities = streams.get("velocity_smooth", {}).get("data")
                elevations = streams.get("altitude", {}).get("data")

                if not latlng or not times_s:
                    print("no GPS data — skipped")
                    continue

                gpx_xml = write_gpx(
                    name=name,
                    start_date_local=start,
                    latlng=latlng,
                    times_s=times_s,
                    velocities_ms=velocities,
                    elevations_m=elevations,
                )

                # Safe filename: replace characters not valid in filenames
                safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
                filename = f"{start[:10]}_{safe_name}_{activity_id}.gpx"
                filepath = out_path / filename
                filepath.write_text(gpx_xml, encoding="utf-8")
                written.append(str(filepath))
                print(f"saved → {filename}")

            except Exception as exc:  # noqa: BLE001
                print(f"ERROR: {exc}")

            # Strava rate limit: 100 requests/15 min — small delay between calls
            if idx < len(activities):
                _time.sleep(0.5)

        return written


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

    p_track = sub.add_parser("track", help="Fetch GPS track with bearing/rotation/ROT")
    p_track.add_argument("activity_id", type=int, help="Strava activity ID")
    p_track.add_argument("--limit", type=int, default=20, metavar="N",
                         help="Max points to print (default: 20, 0 = all)")

    p_export = sub.add_parser("export-track", help="Export GPS track navigation data to Excel")
    p_export.add_argument("activity_id", type=int, help="Strava activity ID")
    p_export.add_argument("--out", default=None, metavar="FILE",
                          help="Output .xlsx path (default: track_<id>.xlsx)")

    p_gpx = sub.add_parser("export-gpx", help="Export all sailing activities as GPX files")
    p_gpx.add_argument("--out-dir", default="gpx_exports", metavar="DIR",
                       help="Output directory (default: gpx_exports/)")

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
    elif args.command == "track":
        points = client.track(args.activity_id)
        sample = points[:args.limit] if args.limit else points
        print(json.dumps({"total_points": len(points), "points": sample}, indent=2))
    elif args.command == "export-track":
        points = client.track(args.activity_id)
        out = args.out or f"track_{args.activity_id}.xlsx"
        save_track_xlsx(points, out)
    elif args.command == "export-gpx":
        print(f"Exporting sailing activities to {args.out_dir}/")
        files = client.export_gpx_all(out_dir=args.out_dir)
        print(f"\nDone — {len(files)} file(s) written to {args.out_dir}/")


if __name__ == "__main__":
    main()
