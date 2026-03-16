"""
CSV export utilities for Strava activities.

Converts raw Strava API activity dicts into flat rows and writes them to a
CSV file with a fixed set of human-readable columns.
"""

import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from astral import LocationInfo
from astral.sun import sun as astral_sun
from timezonefinder import TimezoneFinder

CSV_FIELDS = [
    "id", "name", "sport_type", "start_date_local",
    "start_lat", "start_lon",
    "distance_km", "moving_time_min", "elapsed_time_min",
]

KM_TO_NM = 1 / 1.852  # 1 nautical mile = 1.852 km

CAPE_TOWN_LAT = -33.9249
CAPE_TOWN_LON = 18.4241

# Module-level instance — expensive to construct, reuse across calls
_tf = TimezoneFinder()


def format_date(iso_str: str) -> str:
    """Convert an ISO 8601 date string to ``YYYY-MM-DD HH:MM`` format.

    Args:
        iso_str: ISO 8601 date string, e.g. ``"2024-06-01T08:30:00Z"``.

    Returns:
        Formatted date string, or the original value if parsing fails.
    """
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str


def activity_to_row(a: dict) -> dict:
    """Convert a raw Strava activity dict to a flat CSV row dict.

    Distances are converted from metres to kilometres, times from seconds to
    minutes. All values are rounded to two decimal places or one decimal place
    respectively. ``start_latlng`` is unpacked into ``start_lat`` / ``start_lon``.

    Args:
        a: A single activity dict as returned by the Strava API.

    Returns:
        A dict whose keys match CSV_FIELDS.
    """
    latlng = a.get("start_latlng") or []
    return {
        "id": a.get("id", ""),
        "name": a.get("name", ""),
        "sport_type": a.get("sport_type") or a.get("type", ""),
        "start_date_local": format_date(a.get("start_date_local", "")),
        "start_lat": latlng[0] if len(latlng) >= 2 else None,
        "start_lon": latlng[1] if len(latlng) >= 2 else None,
        "distance_km": round(a.get("distance", 0) / 1000, 2),
        "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
        "elapsed_time_min": round(a.get("elapsed_time", 0) / 60, 1),
    }


def to_dataframe(activities: list[dict]) -> pd.DataFrame:
    """Convert a list of Strava activities to a pandas DataFrame.

    Applies the same field selection and unit conversions as ``save_csv``.
    The ``start_date_local`` column is parsed as a datetime.

    Args:
        activities: Raw activity dicts as returned by the Strava API.

    Returns:
        A DataFrame with columns matching CSV_FIELDS.
    """
    rows = [activity_to_row(a) for a in activities]
    df = pd.DataFrame(rows, columns=CSV_FIELDS)
    df["start_date_local"] = pd.to_datetime(df["start_date_local"], format="%Y-%m-%d %H:%M", errors="coerce")
    return df


def extract_sailing_logbook(df: pd.DataFrame) -> pd.DataFrame:
    """Filter a activities DataFrame down to sailing entries with logbook fields.

    Keeps only rows where ``sport_type`` is ``"Sail"``, adds ``from`` and ``to``
    datetime columns derived from the start time and elapsed duration, and
    expresses distance in nautical miles instead of kilometres.

    Args:
        df: DataFrame as returned by :func:`to_dataframe`.

    Returns:
        A new DataFrame with columns:
        ``from``, ``to``, ``name``, ``distance_nm``, ``moving_time_min``, ``elapsed_time_min``.
    """
    sailing = df[df["sport_type"] == "Sail"].copy()

    sailing["from"] = sailing["start_date_local"]
    sailing["to"] = sailing["start_date_local"] + pd.to_timedelta(sailing["elapsed_time_min"], unit="min")
    sailing["distance_nm"] = (sailing["distance_km"] * KM_TO_NM).round(2)

    return sailing[["from", "to", "name", "distance_nm", "moving_time_min", "elapsed_time_min"]].reset_index(drop=True)


def _after_sunset_minutes(
    start: datetime,
    end: datetime,
    lat: float,
    lon: float,
) -> float:
    """Return the number of minutes of the interval [start, end] that fall after sunset.

    Times are naive datetimes in local wall-clock time at the given coordinates.
    The timezone is derived automatically from the lat/lon using timezonefinder.

    Args:
        start: Activity start as a naive local datetime.
        end: Activity end as a naive local datetime.
        lat: Latitude of the activity location.
        lon: Longitude of the activity location.

    Returns:
        Minutes of the interval that occurred after sunset (and before next sunrise).
    """
    tz_name = _tf.timezone_at(lat=lat, lng=lon) or "UTC"
    tz = ZoneInfo(tz_name)
    location = LocationInfo(latitude=lat, longitude=lon, timezone=tz_name)

    def _get_sunset_sunrise(date):
        try:
            s = astral_sun(location.observer, date=date, tzinfo=tz)
            sunset = s["sunset"].astimezone(tz).replace(tzinfo=None)
            next_s = astral_sun(location.observer, date=date + timedelta(days=1), tzinfo=tz)
            sunrise_next = next_s["sunrise"].astimezone(tz).replace(tzinfo=None)
            return sunset, sunrise_next
        except ValueError:
            # Polar night: sun never rises — entire day is dark
            # Polar day: sun never sets — no darkness
            # Distinguish by checking if it's summer (polar day) or winter (polar night)
            # astral raises ValueError with message indicating which case
            return None, None

    try:
        s = astral_sun(location.observer, date=start.date(), tzinfo=tz)
        sunset_local = s["sunset"].astimezone(tz).replace(tzinfo=None)
    except ValueError:
        # Polar day (sun never sets) → no darkness
        # Polar night (sun never rises) → all dark; treat entire interval as after "sunset"
        # We distinguish by checking for sunrise on this date
        try:
            astral_sun(location.observer, date=start.date(), tzinfo=tz)
        except ValueError:
            pass
        # If we can't get a sunset, assume full darkness (conservative/safe for sailing)
        return (end - start).total_seconds() / 60

    try:
        next_s = astral_sun(location.observer, date=start.date() + timedelta(days=1), tzinfo=tz)
        sunrise_next = next_s["sunrise"].astimezone(tz).replace(tzinfo=None)
    except ValueError:
        # Polar day on the next day — sunrise is effectively at midnight
        sunrise_next = datetime.combine(start.date() + timedelta(days=1), datetime.min.time())

    # Overlap between [start, end] and the dark window [sunset, sunrise_next]
    dark_start = max(start, sunset_local)
    dark_end = min(end, sunrise_next)
    dark_minutes = max(0.0, (dark_end - dark_start).total_seconds() / 60)

    # Recurse if the activity continues past the next sunrise (spans multiple nights)
    if end > sunrise_next:
        dark_minutes += _after_sunset_minutes(sunrise_next, end, lat, lon)

    return dark_minutes


def hours_after_sunset(
    df: pd.DataFrame,
    fallback_lat: float = CAPE_TOWN_LAT,
    fallback_lon: float = CAPE_TOWN_LON,
) -> pd.Series:
    """Calculate how many minutes of each activity took place after sunset.

    Uses the ``start_lat`` / ``start_lon`` columns from the DataFrame for
    per-activity location. Falls back to ``fallback_lat`` / ``fallback_lon``
    (default: Cape Town) when GPS data is absent.

    The timezone for sunrise/sunset calculation is derived automatically from
    the coordinates using ``timezonefinder``. Activity times are assumed to be
    naive datetimes in the local wall-clock time at that location, as Strava
    stores them in ``start_date_local``.

    Args:
        df: DataFrame as returned by :func:`to_dataframe`.
        fallback_lat: Latitude to use when ``start_lat`` is missing. Defaults to Cape Town.
        fallback_lon: Longitude to use when ``start_lon`` is missing. Defaults to Cape Town.

    Returns:
        A Series named ``"after_sunset_min"`` with one float per row (minutes after sunset).
        Rows with a missing ``start_date_local`` produce ``NaN``.
    """
    end_times = df["start_date_local"] + pd.to_timedelta(df["elapsed_time_min"], unit="min")
    results = []

    for start, end, row_lat, row_lon in zip(
        df["start_date_local"], end_times, df["start_lat"], df["start_lon"]
    ):
        if pd.isna(start):
            results.append(float("nan"))
            continue

        lat = row_lat if pd.notna(row_lat) else fallback_lat
        lon = row_lon if pd.notna(row_lon) else fallback_lon

        results.append(_after_sunset_minutes(start.to_pydatetime(), end.to_pydatetime(), lat, lon))

    return pd.Series(results, index=df.index, name="after_sunset_min")


def save_sailing_logbook_xlsx(df: pd.DataFrame, path: str):
    """Build the sailing logbook and write it to an Excel (.xlsx) file.

    Filters ``df`` to sailing activities, adds ``after_sunset_min`` using
    per-activity GPS coordinates (falling back to Cape Town), and writes the
    result to ``path``.

    Columns in the output workbook:
    ``from``, ``to``, ``name``, ``distance_nm``, ``moving_time_hr``,
    ``elapsed_time_hr``, ``after_sunset_hr``.

    Args:
        df: DataFrame as returned by :func:`to_dataframe`.
        path: Destination ``.xlsx`` file path. Created or overwritten.
    """
    # Compute after_sunset_min on the full df (preserves original index)
    after_sunset = hours_after_sunset(df)

    # Filter to sailing rows keeping the original index for alignment
    sailing_mask = df["sport_type"] == "Sail"
    sailing = df[sailing_mask].copy()

    sailing["from"] = sailing["start_date_local"]
    sailing["to"] = sailing["start_date_local"] + pd.to_timedelta(sailing["elapsed_time_min"], unit="min")
    sailing["distance_nm"] = (sailing["distance_km"] * KM_TO_NM).round(2)
    sailing["moving_time_hr"] = (sailing["moving_time_min"] / 60).round(2)
    sailing["elapsed_time_hr"] = (sailing["elapsed_time_min"] / 60).round(2)
    sailing["after_sunset_hr"] = (after_sunset[sailing_mask].values / 60).round(2)

    logbook = sailing[[
        "from", "to", "name", "distance_nm",
        "moving_time_hr", "elapsed_time_hr", "after_sunset_hr",
    ]].reset_index(drop=True)

    logbook.to_excel(path, index=False, engine="openpyxl")
    print(f"Saved {len(logbook)} sailing activities to {path}")


def save_csv(activities: list[dict], path: str):
    """Write a list of Strava activities to a CSV file.

    Args:
        activities: Raw activity dicts as returned by the Strava API.
        path: Destination file path. Created or overwritten.
    """
    rows = [activity_to_row(a) for a in activities]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} activities to {path}")
