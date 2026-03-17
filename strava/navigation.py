"""
Navigation calculations derived from GPS streams.

All bearing values use the meteorological/nautical convention:
  0° / 360° = North, 90° = East, 180° = South, 270° = West
"""

import math
from dataclasses import dataclass


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Initial bearing from (lat1, lon1) to (lat2, lon2) in degrees [0, 360).
    Uses the forward azimuth formula on a sphere.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def delta_bearing(b1: float, b2: float) -> float:
    """
    Signed rotation from bearing b1 to bearing b2, in range (-180, 180].
    Positive = clockwise (starboard turn), negative = counter-clockwise (port turn).
    """
    return (b2 - b1 + 180) % 360 - 180


@dataclass
class TrackPoint:
    index: int
    lat: float
    lon: float
    time_s: float          # seconds from activity start
    bearing_deg: float | None       # direction of travel to next point
    rotation_deg: float | None      # heading change at this point
    rot_speed_deg_s: float | None   # rate of turn in °/s (positive = starboard)

    @property
    def rot_speed_deg_min(self) -> float | None:
        """Rate of turn in °/min — the standard nautical ROT unit."""
        if self.rot_speed_deg_s is None:
            return None
        return self.rot_speed_deg_s * 60


def compute_track(latlng: list[list[float]], times: list[float]) -> list[TrackPoint]:
    """
    Compute bearing, rotation, and rate-of-turn for each point in a GPS track.

    Args:
        latlng: List of [lat, lon] pairs from the Strava latlng stream.
        times:  List of elapsed seconds from the Strava time stream (same length).

    Returns:
        List of TrackPoint objects, one per GPS fix.
        - First point has no bearing/rotation (no prior segment).
        - Second point has a bearing but no rotation (no prior bearing to diff against).
        - Points 3+ have all fields populated.
    """
    n = len(latlng)
    assert len(times) == n, "latlng and times must have the same length"

    bearings: list[float | None] = [None] * n

    # Bearing for segment i→i+1 is stored on point i
    for i in range(n - 1):
        lat1, lon1 = latlng[i]
        lat2, lon2 = latlng[i + 1]
        # Skip duplicate positions (vessel stationary)
        if (lat1, lon1) != (lat2, lon2):
            bearings[i] = bearing(lat1, lon1, lat2, lon2)

    points: list[TrackPoint] = []
    for i in range(n):
        rotation = None
        rot_speed = None

        if i >= 1 and bearings[i] is not None and bearings[i - 1] is not None:
            rotation = delta_bearing(bearings[i - 1], bearings[i])
            dt = times[i] - times[i - 1]
            if dt > 0:
                rot_speed = rotation / dt

        points.append(TrackPoint(
            index=i,
            lat=latlng[i][0],
            lon=latlng[i][1],
            time_s=times[i],
            bearing_deg=bearings[i],
            rotation_deg=rotation,
            rot_speed_deg_s=rot_speed,
        ))

    return points
