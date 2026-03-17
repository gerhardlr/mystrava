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

import requests
import pandas as pd
from strava.api import fetch_all_activities
from strava.export import activity_to_row, to_dataframe, hours_after_sunset
from strava.navigation import compute_track

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
            params={"keys": "latlng,time", "key_by_type": "true"},
        )
        resp.raise_for_status()
        data = resp.json()
        latlng = data["latlng"]["data"]
        times  = data["time"]["data"]
        points = compute_track(latlng, times)
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
                }
                for p in points
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
