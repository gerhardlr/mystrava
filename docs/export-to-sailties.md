# Exporting Sailing Activities to Sailties

This guide walks through exporting your Strava sailing activities as GPX files
and importing them into [Sailties](https://sailties.net).

---

## Prerequisites

- Python environment set up (`poetry install`)
- `.env` file in the repo root with your Strava API credentials:
  ```
  STRAVA_CLIENT_ID=your_client_id
  STRAVA_CLIENT_SECRET=your_client_secret
  ```
- A valid Strava session (the first run will open a browser to authorise if needed)

---

## Step 1 — Export GPX files from Strava

Run the following command from the repo root:

```bash
poetry run strava-api-client export-gpx --out-dir .exports/sailties_import
```

This will:
1. Authenticate with your Strava account
2. Fetch all sailing activities from your Strava history
3. Download the GPS track for each activity
4. Write one `.gpx` file per activity to `.exports/sailties_import/`

Files are named: `YYYY-MM-DD_ActivityName_ActivityID.gpx`

**Example output:**
```
Found 12 sailing activities
  [1/12] Afternoon Sail (17655997816) ... saved → 2026-03-08_Afternoon_Sail_17655997816.gpx
  [2/12] Morning Sail (17612345678) ... saved → 2026-02-14_Morning_Sail_17612345678.gpx
  ...
Done — 12 file(s) written to .exports/sailties_import/
```

---

## Step 2 — Import into Sailties

### On iOS / Android

1. Open the **Sailties** app
2. Tap **+** to add a new log entry
3. Select **Import GPX**
4. Navigate to the folder where the `.gpx` files were saved
5. Select one file at a time and confirm the import
6. Repeat for each activity

### On the Sailties website (sailties.net)

1. Log in to [sailties.net](https://sailties.net)
2. Go to **My Logs** → **Import**
3. Click **Choose File** and select a `.gpx` file
4. Review the activity details and save
5. Repeat for each file

---

## Notes

- Each `.gpx` file includes the full GPS track with timestamps and speed data
- Activities are exported with the original Strava activity name
- Only activities with sport type **Sail** are exported — runs, rides, and other
  activities are ignored
- If an activity has no GPS data recorded it will be skipped automatically
- Strava's API rate limit is 100 requests per 15 minutes; a small delay is
  added between requests automatically if you have many activities
