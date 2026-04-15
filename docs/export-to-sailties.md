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

## Step 2 — Import into Sailties (mobile app only)

> **Note:** GPX import is only available in the Sailties mobile app (iOS / Android),
> added in app version 2.10.0. The website (sailties.net) is read-only and does
> not have an import button.

### Copy GPX files to your phone

Transfer the exported `.gpx` files from your computer to your phone — via
AirDrop, Google Drive, iCloud, USB, or any file sharing method you prefer.

### Import steps (iOS / Android)

1. Open the **Sailties** app
2. Go to the **My Sailing** tab
3. Tap **+** (Add Voyage)
4. When prompted how to add the voyage, select **Import a GPX file**
5. Navigate to the `.gpx` file on your device and select it
6. The app imports the track and creates a voyage entry
7. Repeat for each activity

---

## Notes

- Each `.gpx` file includes the full GPS track with timestamps and speed data
- Activities are exported with the original Strava activity name
- Only activities with sport type **Sail** are exported — runs, rides, and other
  activities are ignored
- If an activity has no GPS data recorded it will be skipped automatically
- Strava's API rate limit is 100 requests per 15 minutes; a small delay is
  added between requests automatically if you have many activities

---

## Bulk Import Limitations

**Sailties does not support bulk import or a public API.** Each GPX file must be
imported manually, one at a time, through the app. There is no way to script or
automate uploads into Sailties.

If you have a large backlog of activities, the options are:

- **Import manually one by one** using the steps above
- **Contact Sailties support** at [sailties.net](https://sailties.net) and ask
  about a data migration service — they have done this for sailing schools
  onboarding large archives
- **Use an alternative platform** that supports bulk GPX import, such as
  [Navionics](https://www.navionics.com) or [OpenCPN](https://opencpn.org)
