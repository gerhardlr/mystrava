import csv
import math

import pandas as pd
import pytest

from strava.export import (
    CSV_FIELDS,
    CAPE_TOWN_LAT,
    CAPE_TOWN_LON,
    KM_TO_NM,
    activity_to_row,
    extract_sailing_logbook,
    format_date,
    hours_after_sunset,
    save_csv,
    save_sailing_logbook_xlsx,
    to_dataframe,
)


# ── format_date ────────────────────────────────────────────────────────────────

def test_format_date_utc_z():
    assert format_date("2024-06-01T08:30:00Z") == "2024-06-01 08:30"


def test_format_date_local_no_tz():
    assert format_date("2024-06-01T08:30:00") == "2024-06-01 08:30"


def test_format_date_invalid_returns_original():
    assert format_date("not-a-date") == "not-a-date"


def test_format_date_empty_returns_empty():
    assert format_date("") == ""


# ── activity_to_row ────────────────────────────────────────────────────────────

def test_activity_to_row_full():
    activity = {
        "id": 42,
        "name": "Morning Run",
        "sport_type": "Run",
        "start_date_local": "2024-06-01T08:00:00",
        "start_latlng": [-33.9249, 18.4241],
        "distance": 10000,
        "moving_time": 3600,
        "elapsed_time": 3700,
    }
    row = activity_to_row(activity)
    assert row["id"] == 42
    assert row["name"] == "Morning Run"
    assert row["sport_type"] == "Run"
    assert row["start_lat"] == -33.9249
    assert row["start_lon"] == 18.4241
    assert row["distance_km"] == 10.0
    assert row["moving_time_min"] == 60.0
    assert row["elapsed_time_min"] == pytest.approx(61.7, abs=0.1)


def test_activity_to_row_falls_back_to_type_field():
    activity = {"sport_type": None, "type": "Ride"}
    row = activity_to_row(activity)
    assert row["sport_type"] == "Ride"


def test_activity_to_row_missing_fields_use_defaults():
    row = activity_to_row({})
    assert row["id"] == ""
    assert row["name"] == ""
    assert row["start_lat"] is None
    assert row["start_lon"] is None
    assert row["distance_km"] == 0.0
    assert row["moving_time_min"] == 0.0
    assert row["elapsed_time_min"] == 0.0


def test_activity_to_row_distance_rounded():
    row = activity_to_row({"distance": 10123})
    assert row["distance_km"] == 10.12


def test_activity_to_row_no_latlng_gives_none():
    row = activity_to_row({"start_latlng": None})
    assert row["start_lat"] is None
    assert row["start_lon"] is None


# ── save_csv ───────────────────────────────────────────────────────────────────

def test_save_csv_writes_correct_headers(tmp_path):
    path = str(tmp_path / "out.csv")
    save_csv([{"id": 1, "name": "Run", "sport_type": "Run",
               "start_date_local": "2024-01-01T07:00:00",
               "distance": 5000, "moving_time": 1800, "elapsed_time": 1900}], path)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_FIELDS


def test_save_csv_empty_activities(tmp_path):
    path = str(tmp_path / "out.csv")
    save_csv([], path)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_FIELDS
        assert list(reader) == []


def test_save_csv_row_values(tmp_path):
    path = str(tmp_path / "out.csv")
    activity = {
        "id": 99, "name": "Bike", "sport_type": "Ride",
        "start_date_local": "2024-03-15T06:00:00",
        "distance": 20000, "moving_time": 3600, "elapsed_time": 3660,
    }
    save_csv([activity], path)
    with open(path, newline="") as f:
        row = list(csv.DictReader(f))[0]
    assert row["id"] == "99"
    assert row["distance_km"] == "20.0"
    assert row["name"] == "Bike"


# ── to_dataframe ───────────────────────────────────────────────────────────────

def test_to_dataframe_columns():
    df = to_dataframe([])
    assert list(df.columns) == CSV_FIELDS


def test_to_dataframe_row_values():
    activity = {
        "id": 1, "name": "Run", "sport_type": "Run",
        "start_date_local": "2024-06-01T08:00:00",
        "distance": 5000, "moving_time": 1800, "elapsed_time": 1900,
    }
    df = to_dataframe([activity])
    assert len(df) == 1
    assert df.iloc[0]["distance_km"] == 5.0
    assert df.iloc[0]["moving_time_min"] == 30.0


def test_to_dataframe_date_parsed_as_datetime():
    activity = {"start_date_local": "2024-06-01T08:00:00"}
    df = to_dataframe([activity])
    assert pd.api.types.is_datetime64_any_dtype(df["start_date_local"])
    assert df.iloc[0]["start_date_local"] == pd.Timestamp("2024-06-01 08:00")


def test_to_dataframe_multiple_rows():
    activities = [{"id": i, "distance": i * 1000} for i in range(5)]
    df = to_dataframe(activities)
    assert len(df) == 5
    assert list(df["distance_km"]) == [0.0, 1.0, 2.0, 3.0, 4.0]


# ── extract_sailing_logbook ────────────────────────────────────────────────────

def _make_df(activities):
    return to_dataframe(activities)


def test_sailing_logbook_filters_to_sail_only():
    activities = [
        {"sport_type": "Sail", "start_date_local": "2024-06-01T09:00:00", "distance": 10000, "moving_time": 3600, "elapsed_time": 3900},
        {"sport_type": "Run",  "start_date_local": "2024-06-02T07:00:00", "distance": 5000,  "moving_time": 1800, "elapsed_time": 1800},
        {"sport_type": "Sail", "start_date_local": "2024-06-03T10:00:00", "distance": 20000, "moving_time": 7200, "elapsed_time": 7500},
    ]
    result = extract_sailing_logbook(_make_df(activities))
    assert len(result) == 2
    assert set(result.columns) >= {"from", "to", "name", "distance_nm"}


def test_sailing_logbook_distance_in_nautical_miles():
    activities = [{"sport_type": "Sail", "start_date_local": "2024-06-01T09:00:00",
                   "distance": 1852, "moving_time": 3600, "elapsed_time": 3600}]
    result = extract_sailing_logbook(_make_df(activities))
    assert result.iloc[0]["distance_nm"] == pytest.approx(1.0, abs=0.01)


def test_sailing_logbook_from_to_datetimes():
    activities = [{"sport_type": "Sail", "start_date_local": "2024-06-01T09:00:00",
                   "distance": 5000, "moving_time": 3600, "elapsed_time": 7200}]
    result = extract_sailing_logbook(_make_df(activities))
    assert result.iloc[0]["from"] == pd.Timestamp("2024-06-01 09:00")
    assert result.iloc[0]["to"] == pd.Timestamp("2024-06-01 11:00")


def test_sailing_logbook_empty_when_no_sail():
    activities = [{"sport_type": "Run", "start_date_local": "2024-06-01T07:00:00",
                   "distance": 5000, "moving_time": 1800, "elapsed_time": 1800}]
    result = extract_sailing_logbook(_make_df(activities))
    assert len(result) == 0


def test_sailing_logbook_index_reset():
    activities = [
        {"sport_type": "Run",  "start_date_local": "2024-06-01T07:00:00", "distance": 5000, "moving_time": 1800, "elapsed_time": 1800},
        {"sport_type": "Sail", "start_date_local": "2024-06-02T09:00:00", "distance": 10000, "moving_time": 3600, "elapsed_time": 3600},
    ]
    result = extract_sailing_logbook(_make_df(activities))
    assert list(result.index) == [0]


# ── hours_after_sunset ─────────────────────────────────────────────────────────
# All tests use Cape Town coordinates (lat=-33.9249, lon=18.4241).
# December sunset in Cape Town is approximately 19:50 local time (SAST, UTC+2).

def _ct_activity(start_iso, elapsed_seconds, latlng=None):
    """Helper: build a single-row DataFrame with optional GPS coords."""
    a = {
        "sport_type": "Sail",
        "start_date_local": start_iso,
        "elapsed_time": elapsed_seconds,
        "moving_time": elapsed_seconds,
    }
    if latlng:
        a["start_latlng"] = latlng
    return to_dataframe([a])


def test_after_sunset_daytime_activity_returns_zero():
    # 08:00–09:00, well before sunset (~19:50)
    df = _ct_activity("2024-12-01T08:00:00", 3600, [CAPE_TOWN_LAT, CAPE_TOWN_LON])
    result = hours_after_sunset(df)
    assert result.iloc[0] == pytest.approx(0.0)


def test_after_sunset_fully_nocturnal_returns_full_duration():
    # 21:00–23:00, entirely after sunset
    df = _ct_activity("2024-12-01T21:00:00", 7200, [CAPE_TOWN_LAT, CAPE_TOWN_LON])
    result = hours_after_sunset(df)
    assert result.iloc[0] == pytest.approx(120.0, abs=1.0)


def test_after_sunset_straddles_sunset():
    # 19:00–21:00; sunset ~19:50 → roughly 70 minutes after sunset
    df = _ct_activity("2024-12-01T19:00:00", 7200, [CAPE_TOWN_LAT, CAPE_TOWN_LON])
    result = hours_after_sunset(df)
    assert 50.0 < result.iloc[0] < 90.0


def test_after_sunset_spans_midnight():
    # 22:00 + 3 h → ends 01:00; all after sunset, before sunrise
    df = _ct_activity("2024-12-01T22:00:00", 10800, [CAPE_TOWN_LAT, CAPE_TOWN_LON])
    result = hours_after_sunset(df)
    assert result.iloc[0] == pytest.approx(180.0, abs=1.0)


def test_after_sunset_empty_dataframe():
    df = to_dataframe([])
    result = hours_after_sunset(df)
    assert len(result) == 0


def test_after_sunset_multiple_rows():
    activities = [
        {"start_date_local": "2024-12-01T08:00:00", "elapsed_time": 3600,
         "moving_time": 3600, "start_latlng": [CAPE_TOWN_LAT, CAPE_TOWN_LON]},
        {"start_date_local": "2024-12-01T21:00:00", "elapsed_time": 3600,
         "moving_time": 3600, "start_latlng": [CAPE_TOWN_LAT, CAPE_TOWN_LON]},
    ]
    df = to_dataframe(activities)
    result = hours_after_sunset(df)
    assert result.iloc[0] == pytest.approx(0.0)
    assert result.iloc[1] == pytest.approx(60.0, abs=1.0)


def test_after_sunset_nat_start_date_returns_nan():
    activities = [{"start_date_local": "not-a-date", "elapsed_time": 3600,
                   "start_latlng": [CAPE_TOWN_LAT, CAPE_TOWN_LON]}]
    df = to_dataframe(activities)
    result = hours_after_sunset(df)
    assert math.isnan(result.iloc[0])


def test_after_sunset_returns_series_with_correct_metadata():
    df = _ct_activity("2024-12-01T21:00:00", 3600, [CAPE_TOWN_LAT, CAPE_TOWN_LON])
    result = hours_after_sunset(df)
    assert isinstance(result, pd.Series)
    assert list(result.index) == list(df.index)
    assert result.name == "after_sunset_min"


def test_after_sunset_falls_back_to_cape_town_when_no_gps():
    # No GPS in activity; fallback = Cape Town; 21:00 → after sunset
    df = _ct_activity("2024-12-01T21:00:00", 3600)  # no latlng
    result = hours_after_sunset(df)  # uses default fallback
    assert result.iloc[0] == pytest.approx(60.0, abs=1.0)


# ── save_sailing_logbook_xlsx ──────────────────────────────────────────────────

def test_sailing_logbook_xlsx_columns(tmp_path):
    activities = [
        {"sport_type": "Sail", "start_date_local": "2024-12-01T21:00:00",
         "elapsed_time": 7200, "moving_time": 7200, "distance": 10000,
         "start_latlng": [CAPE_TOWN_LAT, CAPE_TOWN_LON]},
    ]
    path = str(tmp_path / "logbook.xlsx")
    save_sailing_logbook_xlsx(to_dataframe(activities), path)
    result = pd.read_excel(path)
    assert list(result.columns) == ["from", "to", "name", "distance_nm",
                                    "moving_time_hr", "elapsed_time_hr", "after_sunset_hr"]


def test_sailing_logbook_xlsx_filters_non_sail(tmp_path):
    activities = [
        {"sport_type": "Sail", "start_date_local": "2024-12-01T21:00:00",
         "elapsed_time": 3600, "moving_time": 3600, "distance": 5000},
        {"sport_type": "Run",  "start_date_local": "2024-12-01T08:00:00",
         "elapsed_time": 1800, "moving_time": 1800, "distance": 3000},
    ]
    path = str(tmp_path / "logbook.xlsx")
    save_sailing_logbook_xlsx(to_dataframe(activities), path)
    result = pd.read_excel(path)
    assert len(result) == 1


def test_sailing_logbook_xlsx_after_sunset_populated(tmp_path):
    # Night sail after 21:00 → after_sunset_min should be > 0
    activities = [
        {"sport_type": "Sail", "start_date_local": "2024-12-01T21:00:00",
         "elapsed_time": 3600, "moving_time": 3600, "distance": 5000,
         "start_latlng": [CAPE_TOWN_LAT, CAPE_TOWN_LON]},
    ]
    path = str(tmp_path / "logbook.xlsx")
    save_sailing_logbook_xlsx(to_dataframe(activities), path)
    result = pd.read_excel(path)
    assert result.iloc[0]["after_sunset_hr"] > 0


def test_sailing_logbook_xlsx_empty_when_no_sail(tmp_path):
    activities = [{"sport_type": "Run", "start_date_local": "2024-12-01T08:00:00",
                   "elapsed_time": 1800, "moving_time": 1800}]
    path = str(tmp_path / "logbook.xlsx")
    save_sailing_logbook_xlsx(to_dataframe(activities), path)
    result = pd.read_excel(path)
    assert len(result) == 0


def test_after_sunset_uses_row_lat_lon():
    # London in December: sunset ~15:55 local.
    # A 15:00–16:30 activity: 0 in Cape Town (sunset ~19:50), ~35 min in London.
    df = _ct_activity("2024-12-01T15:00:00", 5400, [51.5074, -0.1278])
    result = hours_after_sunset(df)
    assert result.iloc[0] > 0.0  # London sunset already passed by 15:55
