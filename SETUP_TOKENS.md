# Setting Up Strava API Tokens

## 1. Create a Strava API Application

1. Go to [https://www.strava.com/settings/api](https://www.strava.com/settings/api) and log in.
2. Fill in the application form:
   - **Application Name** — any name, e.g. `My CSV Exporter`
   - **Category** — choose the closest match, e.g. `Data Importer`
   - **Club** — leave blank
   - **Website** — any valid URL, e.g. `http://localhost`
   - **Authorization Callback Domain** — must be exactly `localhost`
   - **Icon** — Strava requires an image upload. Any square image works (minimum 124×124 px). An `icon.png` is included in this repo if you need one.
3. Click **Create** and note down your **Client ID** and **Client Secret**.

---

## 2. Configure Your `.env` File

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
STRAVA_CLIENT_ID=12345
STRAVA_CLIENT_SECRET=abc123...
```

The exporter reads these automatically on startup. It will exit with an error if either value is missing.

---

## 3. First Run — Browser Login

Run the exporter:

```bash
poetry run strava-export
```

A browser window will open asking you to authorise the app. Click **Authorize** and the tab will show:

```
Authorised! You can close this tab.
```

The OAuth tokens are saved locally to `.strava_tokens.json` — **do not commit this file**.

---

## 4. Subsequent Runs

On every run after the first, the saved tokens are reused automatically:

```
Using saved session.
```

If the access token has expired (they last 6 hours), it is refreshed silently using the stored refresh token. You will not need to log in again.

---

## 5. Revoking Access

To revoke the app's access to your Strava account:

1. Go to [https://www.strava.com/settings/apps](https://www.strava.com/settings/apps).
2. Find your app and click **Revoke Access**.

To force a fresh login locally, delete the token file:

```bash
rm .strava_tokens.json
```

---

## 6. Security Notes

Add both files to `.gitignore` to avoid committing secrets:

```
.env
.strava_tokens.json
```

- `.env` contains your Client ID and Client Secret.
- `.strava_tokens.json` contains your OAuth access and refresh tokens.

Neither should ever be committed to version control.
