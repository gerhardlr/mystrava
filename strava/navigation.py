"""
Navigation calculations derived from GPS streams.

All bearing values use the meteorological/nautical convention:
  0° / 360° = North, 90° = East, 180° = South, 270° = West
"""

import math
from dataclasses import dataclass

M_S_TO_KN = 1.94384  # metres per second → knots


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


def _circular_mean(angles_deg: list[float]) -> float:
    """Mean of a list of bearings, correctly handling the 0/360 wrap-around."""
    sin_sum = sum(math.sin(math.radians(a)) for a in angles_deg)
    cos_sum = sum(math.cos(math.radians(a)) for a in angles_deg)
    return (math.degrees(math.atan2(sin_sum, cos_sum)) + 360) % 360


def _smooth_bearings(bearings: list[float | None], window: int = 5) -> list[float | None]:
    """
    Circular-mean smoothing over a rolling window.
    Uses atan2(mean(sin), mean(cos)) to handle the 0/360 wrap correctly.
    """
    half = window // 2
    n = len(bearings)
    result: list[float | None] = []
    for i in range(n):
        neighbours = [
            bearings[j]
            for j in range(max(0, i - half), min(n, i + half + 1))
            if bearings[j] is not None
        ]
        result.append(_circular_mean(neighbours) if neighbours else None)
    return result


@dataclass
class TrackPoint:
    index: int
    lat: float
    lon: float
    time_s: float                       # seconds from activity start
    bearing_deg: float | None           # direction of travel to next point
    rotation_deg: float | None          # heading change at this point
    rot_speed_deg_s: float | None       # rate of turn in °/s (positive = starboard)
    speed_kn: float | None              # vessel speed in knots

    @property
    def rot_speed_deg_min(self) -> float | None:
        """Rate of turn in °/min — the standard nautical ROT unit."""
        if self.rot_speed_deg_s is None:
            return None
        return self.rot_speed_deg_s * 60


@dataclass
class Tack:
    index: int                          # 1-based sequential number
    start_time_s: float
    end_time_s: float
    duration_s: float
    angle_deg: float                    # absolute total bearing change
    direction: str                      # "port" | "starboard"
    start_bearing_deg: float | None
    end_bearing_deg: float | None
    avg_speed_kn: float | None
    start_speed_kn: float | None
    end_speed_kn: float | None


def compute_track(
    latlng: list[list[float]],
    times: list[float],
    velocities: list[float] | None = None,
) -> list[TrackPoint]:
    """
    Compute bearing, rotation, rate-of-turn, and speed for each point in a GPS track.

    Args:
        latlng:     List of [lat, lon] pairs from the Strava latlng stream.
        times:      List of elapsed seconds from the Strava time stream (same length).
        velocities: Optional list of speeds in m/s from the Strava velocity_smooth
                    stream (same length). Converted to knots internally.

    Returns:
        List of TrackPoint objects, one per GPS fix.
        - First point has no bearing/rotation (no prior segment).
        - Second point has a bearing but no rotation (no prior bearing to diff against).
        - Points 3+ have all fields populated.
    """
    n = len(latlng)
    assert len(times) == n, "latlng and times must have the same length"
    if velocities is not None:
        assert len(velocities) == n, "velocities and latlng must have the same length"

    bearings: list[float | None] = [None] * n

    # Bearing for segment i→i+1 is stored on point i
    for i in range(n - 1):
        lat1, lon1 = latlng[i]
        lat2, lon2 = latlng[i + 1]
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

        speed = None
        if velocities is not None and velocities[i] is not None:
            speed = velocities[i] * M_S_TO_KN

        points.append(TrackPoint(
            index=i,
            lat=latlng[i][0],
            lon=latlng[i][1],
            time_s=times[i],
            bearing_deg=bearings[i],
            rotation_deg=rotation,
            rot_speed_deg_s=rot_speed,
            speed_kn=speed,
        ))

    return points


def detect_tacks(
    points: list[TrackPoint],
    min_angle: float = 90.0,
    max_duration_s: float = 120.0,
    smooth_window: int = 5,
    reversal_tolerance: float = 30.0,
) -> list[Tack]:
    """
    Detect tacks as periods of sustained large bearing change.

    A tack is identified when:
    - Total bearing change across a window exceeds ``min_angle``
    - The window duration is within ``max_duration_s``
    - The rotation stays consistently in one direction (reversals > ``reversal_tolerance``
      degrees invalidate the candidate — this filters out zig-zag corrections)

    Bearings are pre-smoothed with a circular-mean rolling window to suppress
    single-sample GPS noise before any rotation is accumulated.

    Args:
        points:              TrackPoint list from compute_track().
        min_angle:           Minimum total bearing change to count as a tack (default 90°).
        max_duration_s:      Maximum duration for a single tack (default 120 s).
        smooth_window:       Rolling window size for circular-mean bearing smoothing.
        reversal_tolerance:  Maximum counter-rotation allowed within a tack (default 30°).

    Returns:
        List of Tack objects in chronological order, numbered from 1.
    """
    n = len(points)
    raw_bearings = [p.bearing_deg for p in points]
    smooth = _smooth_bearings(raw_bearings, smooth_window)

    # Pre-compute per-step rotations from smoothed bearings
    smooth_rot: list[float | None] = [None]
    for k in range(1, n):
        if smooth[k] is not None and smooth[k - 1] is not None:
            smooth_rot.append(delta_bearing(smooth[k - 1], smooth[k]))
        else:
            smooth_rot.append(None)

    tacks: list[Tack] = []
    i = 0
    skip_until = 0

    while i < n:
        # Only start a tack candidate where a significant rotation is already happening
        if (
            i < skip_until
            or smooth[i] is None
            or smooth_rot[i] is None
            or abs(smooth_rot[i]) < 2.0
        ):
            i += 1
            continue

        # The direction of this tack is set by the first significant step
        direction_sign = 1 if smooth_rot[i] > 0 else -1

        best_j: int | None = None
        cumulative = abs(smooth_rot[i])
        valid = True

        j = i + 1
        while j < n:
            if smooth[j] is None or smooth_rot[j] is None:
                j += 1
                continue

            dt = points[j].time_s - points[i].time_s
            if dt > max_duration_s:
                break

            projected = smooth_rot[j] * direction_sign
            if projected >= 0:
                cumulative += projected
            elif abs(projected) > reversal_tolerance:
                valid = False
                break

            if cumulative >= min_angle and valid:
                best_j = j
                break  # stop at first crossing — pre/post windows measure stable headings

            j += 1

        if valid and best_j is not None and cumulative >= min_angle:
            si, ei = i, best_j
            net_angle = abs(delta_bearing(smooth[si] or 0, smooth[ei] or 0))
            if net_angle < min_angle:
                # Cumulative noise exceeded threshold but net bearing change did not
                i += 1
                continue

            # Average bearing over the 10 s window before and after the tack
            # for a stable, noise-free start/end heading.
            pre_bearings = [
                smooth[k] for k in range(n)
                if smooth[k] is not None
                and points[si].time_s - 10.0 <= points[k].time_s < points[si].time_s
            ]
            post_bearings = [
                smooth[k] for k in range(n)
                if smooth[k] is not None
                and points[ei].time_s < points[k].time_s <= points[ei].time_s + 10.0
            ]
            pre_bearing  = round(_circular_mean(pre_bearings), 1)  if pre_bearings  else (round(smooth[si], 1) if smooth[si] is not None else None)
            post_bearing = round(_circular_mean(post_bearings), 1) if post_bearings else (round(smooth[ei], 1) if smooth[ei] is not None else None)

            # Recompute angle_deg from the stable pre/post windows
            if pre_bearing is not None and post_bearing is not None:
                stable_angle = round(abs(delta_bearing(pre_bearing, post_bearing)), 1)
            else:
                stable_angle = round(net_angle, 1)

            if stable_angle < min_angle:
                i += 1
                continue

            speed_values = [p.speed_kn for p in points[si:ei + 1] if p.speed_kn is not None]
            avg_speed = sum(speed_values) / len(speed_values) if speed_values else None

            tacks.append(Tack(
                index=len(tacks) + 1,
                start_time_s=points[si].time_s,
                end_time_s=points[ei].time_s,
                duration_s=round(points[ei].time_s - points[si].time_s, 1),
                angle_deg=stable_angle,
                direction="starboard" if direction_sign == 1 else "port",
                start_bearing_deg=pre_bearing,
                end_bearing_deg=post_bearing,
                avg_speed_kn=round(avg_speed, 2) if avg_speed is not None else None,
                start_speed_kn=round(points[si].speed_kn, 2) if points[si].speed_kn is not None else None,
                end_speed_kn=round(points[ei].speed_kn, 2) if points[ei].speed_kn is not None else None,
            ))
            skip_until = best_j + 1
            i = best_j + 1
        else:
            i += 1

    return tacks
