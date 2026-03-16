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

from strava.api import fetch_all_activities
from strava.export import activity_to_row, to_dataframe, extract_sailing_logbook

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


@app.get("/api/activities/sailing")
async def get_sailing_activities(authorization: Optional[str] = Header(None)):
    """Return sailing activities enriched with logbook data (distance in nm, sunset hours)."""
    token = _extract_token(authorization)
    try:
        activities = fetch_all_activities(token)
        df = to_dataframe(activities)
        sailing_df = extract_sailing_logbook(df)
        return {
            "activities": sailing_df.to_dict(orient="records"),
            "count": len(sailing_df),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
