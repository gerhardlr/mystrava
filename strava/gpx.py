"""
GPX 1.1 export for Strava sailing activities.

Produces standard GPX tracks with timestamps and optional speed/elevation,
compatible with Sailties and other sailing logbook platforms.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def _iso_to_dt(iso: str) -> datetime:
    """Parse an ISO 8601 string (with or without Z/offset) to a UTC datetime."""
    iso = iso.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        # Fallback: assume local time, attach UTC
        return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


def write_gpx(
    name: str,
    start_date_local: str,
    latlng: list[list[float]],
    times_s: list[float],
    velocities_ms: list[float] | None = None,
    elevations_m: list[float] | None = None,
) -> str:
    """
    Build a GPX 1.1 XML string for a single activity.

    Args:
        name:              Activity name (used as <trk><name>).
        start_date_local:  ISO 8601 start time of the activity.
        latlng:            List of [lat, lon] pairs.
        times_s:           Elapsed seconds from activity start (same length as latlng).
        velocities_ms:     Optional speed in m/s per point (written as <speed> in m/s).
        elevations_m:      Optional elevation in metres per point (written as <ele>).

    Returns:
        UTF-8 encoded GPX XML string.
    """
    assert len(latlng) == len(times_s), "latlng and times_s must have the same length"
    if velocities_ms is not None:
        assert len(velocities_ms) == len(latlng)
    if elevations_m is not None:
        assert len(elevations_m) == len(latlng)

    start_dt = _iso_to_dt(start_date_local)

    root = ET.Element("gpx", {
        "version": "1.1",
        "creator": "MySailing Logbook",
        "xmlns": "http://www.topografix.com/GPX/1/1",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": (
            "http://www.topografix.com/GPX/1/1 "
            "http://www.topografix.com/GPX/1/1/gpx.xsd"
        ),
    })

    trk = ET.SubElement(root, "trk")
    ET.SubElement(trk, "name").text = name
    ET.SubElement(trk, "type").text = "sailing"

    seg = ET.SubElement(trk, "trkseg")

    for idx, (latlon, t_s) in enumerate(zip(latlng, times_s)):
        lat, lon = latlon
        pt = ET.SubElement(seg, "trkpt", {"lat": str(lat), "lon": str(lon)})

        # Elevation
        ele_val = elevations_m[idx] if elevations_m else 0.0
        ET.SubElement(pt, "ele").text = str(round(ele_val, 1))

        # Timestamp = start + elapsed seconds
        point_dt = start_dt.replace(microsecond=0)
        from datetime import timedelta
        point_dt = start_dt + timedelta(seconds=t_s)
        ET.SubElement(pt, "time").text = point_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Speed as GPX extension (speed in m/s — standard GPX extension)
        if velocities_ms is not None and velocities_ms[idx] is not None:
            extensions = ET.SubElement(pt, "extensions")
            ET.SubElement(extensions, "speed").text = str(round(velocities_ms[idx], 3))

    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")
