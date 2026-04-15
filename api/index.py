"""FastAPI application wrapping the Strava library for Vercel deployment.

Routes:
  GET /api/health              - health check
  GET /api/activities          - all activities for the authenticated user
  GET /api/activities/sailing  - sailing activities with logbook data
"""
from __future__ import annotations

import os
import sys
from typing import Optional

# Ensure the repo root (which contains the `strava` package) is on the path
# when running as a Vercel serverless function.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

import requests
import pandas as pd
from strava.api import fetch_all_activities
from strava.export import activity_to_row, to_dataframe, hours_after_sunset
from strava.navigation import compute_track, detect_tacks
from strava.gpx import write_gpx

KM_TO_NM = 1 / 1.852

app = FastAPI(title="Strava API", version="1.0.0")

# Allow the frontend origin; set ALLOWED_ORIGINS env var as comma-separated list
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
)


def _extract_token(authorization: Optional[str]) -> str:
    """Pull the Bearer token out of the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header (expected 'Bearer <token>')",
        )
    return authorization.split(" ", 1)[1]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    """Liveness check."""
    return {"status": "ok"}


@app.get("/api/activities")
async def get_activities(authorization: Optional[str] = Header(None)):
    """Return all Strava activities for the authenticated user as JSON rows."""
    token = _extract_token(authorization)
    try:
        activities = fetch_all_activities(token)
        rows = [activity_to_row(a) for a in activities]
        return {"activities": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def run_dev():
    import uvicorn
    uvicorn.run("api.index:app", reload=True, port=8000)


@app.get("/api/activities/sailing")
async def get_sailing_activities(authorization: Optional[str] = Header(None)):
    """Return sailing activities enriched with logbook data (distance in nm, sunset hours)."""
    token = _extract_token(authorization)
    try:
        activities = fetch_all_activities(token)
        df = to_dataframe(activities)

        after_sunset = hours_after_sunset(df)
        sailing_mask = df["sport_type"] == "Sail"
        sailing = df[sailing_mask].copy()

        sailing["from"] = sailing["start_date_local"]
        sailing["to"] = sailing["start_date_local"] + pd.to_timedelta(sailing["elapsed_time_min"], unit="min")
        sailing["distance_nm"] = (sailing["distance_km"] * KM_TO_NM).round(2)
        sailing["moving_time_hr"] = (sailing["moving_time_min"] / 60).round(2)
        sailing["elapsed_time_hr"] = (sailing["elapsed_time_min"] / 60).round(2)
        sailing["after_sunset_hr"] = (after_sunset[sailing_mask].values / 60).round(2)

        logbook = sailing[[
            "id", "start_date_local", "from", "to", "name",
            "distance_nm", "moving_time_hr", "elapsed_time_hr", "after_sunset_hr", "max_speed_kn", "avg_speed_kn",
        ]].reset_index(drop=True)

        return {
            "activities": logbook.to_dict(orient="records"),
            "count": len(logbook),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/activities/{activity_id}/track")
async def get_activity_track(activity_id: int, authorization: Optional[str] = Header(None)):
    """Return GPS track with bearing, rotation, and rate-of-turn for a single activity."""
    token = _extract_token(authorization)
    try:
        resp = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            headers={"Authorization": f"Bearer {token}"},
            params={"keys": "latlng,time,velocity_smooth", "key_by_type": "true"},
        )
        resp.raise_for_status()
        data = resp.json()
        latlng     = data["latlng"]["data"]
        times      = data["time"]["data"]
        velocities = data.get("velocity_smooth", {}).get("data")
        points     = compute_track(latlng, times, velocities)
        tacks      = detect_tacks(points)
        return {
            "activity_id": activity_id,
            "points": [
                {
                    "index":             p.index,
                    "lat":               p.lat,
                    "lon":               p.lon,
                    "time_s":            p.time_s,
                    "bearing_deg":       round(p.bearing_deg, 1)       if p.bearing_deg       is not None else None,
                    "rotation_deg":      round(p.rotation_deg, 1)      if p.rotation_deg      is not None else None,
                    "rot_speed_deg_min": round(p.rot_speed_deg_min, 2) if p.rot_speed_deg_min is not None else None,
                    "speed_kn":          round(p.speed_kn, 2)          if p.speed_kn          is not None else None,
                }
                for p in points
            ],
            "tacks": [
                {
                    "index":             t.index,
                    "start_time_s":      t.start_time_s,
                    "end_time_s":        t.end_time_s,
                    "duration_s":        t.duration_s,
                    "angle_deg":         t.angle_deg,
                    "direction":         t.direction,
                    "start_bearing_deg": t.start_bearing_deg,
                    "end_bearing_deg":   t.end_bearing_deg,
                    "avg_speed_kn":      t.avg_speed_kn,
                    "start_speed_kn":    t.start_speed_kn,
                    "end_speed_kn":      t.end_speed_kn,
                }
                for t in tacks
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/activities/{activity_id}/gpx")
async def get_activity_gpx(activity_id: int, authorization: Optional[str] = Header(None)):
    """Return a GPX file for a single activity, ready for download."""
    token = _extract_token(authorization)
    try:
        headers = {"Authorization": f"Bearer {token}"}

        act_resp = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}",
            headers=headers,
        )
        act_resp.raise_for_status()
        act = act_resp.json()
        name  = act.get("name", f"activity_{activity_id}")
        start = act.get("start_date_local") or act.get("start_date", "")

        streams_resp = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            headers=headers,
            params={"keys": "latlng,time,velocity_smooth,altitude", "key_by_type": "true"},
        )
        streams_resp.raise_for_status()
        streams = streams_resp.json()

        latlng     = streams.get("latlng", {}).get("data", [])
        times_s    = streams.get("time", {}).get("data", [])
        velocities = streams.get("velocity_smooth", {}).get("data")
        elevations = streams.get("altitude", {}).get("data")

        if not latlng or not times_s:
            raise HTTPException(status_code=404, detail="No GPS data for this activity")

        gpx_xml = write_gpx(
            name=name,
            start_date_local=start,
            latlng=latlng,
            times_s=times_s,
            velocities_ms=velocities,
            elevations_m=elevations,
        )

        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        filename  = f"{start[:10]}_{safe_name}_{activity_id}.gpx"

        return Response(
            content=gpx_xml,
            media_type="application/gpx+xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
