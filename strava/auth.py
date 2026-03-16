"""
Authentication helpers for the Strava API.

Handles OAuth2 token storage, refresh, and the browser-based authorisation
flow. Tokens are persisted locally in a JSON file so that subsequent runs
can reuse a valid session without prompting the user again.
"""

import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

TOKEN_FILE = ".strava_tokens.json"
REDIRECT_URI = "http://localhost:8765/callback"
AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"

_auth_code: str | None = None


def save_tokens(tokens: dict):
    """Persist the token payload returned by Strava to TOKEN_FILE."""
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)


def load_tokens() -> dict | None:
    """Load tokens from TOKEN_FILE, or return None if the file does not exist."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token via the Strava token endpoint.

    Args:
        client_id: Strava application client ID.
        client_secret: Strava application client secret.
        refresh_token: The current refresh token.

    Returns:
        The full token payload from Strava (includes new access_token, expires_at, etc.).

    Raises:
        requests.HTTPError: If Strava returns a non-2xx response.
    """
    resp = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })
    resp.raise_for_status()
    return resp.json()


def get_valid_token(client_id: str, client_secret: str) -> str | None:
    """Return a valid access token, refreshing it automatically if it has expired.

    Args:
        client_id: Strava application client ID.
        client_secret: Strava application client secret.

    Returns:
        A valid access token string, or None if no saved session exists.
    """
    tokens = load_tokens()
    if tokens:
        if tokens["expires_at"] <= time.time() + 60:
            print("Access token expired — refreshing...")
            tokens = refresh_access_token(client_id, client_secret, tokens["refresh_token"])
            save_tokens(tokens)
        return tokens["access_token"]
    return None


class _CallbackHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that captures the OAuth authorisation code."""

    def do_GET(self):
        global _auth_code
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Authorised! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Error: no code received.</h2>")

    def log_message(self, *args):
        pass  # silence server logs


def run_oauth(client_id: str, client_secret: str) -> dict:
    """Run the browser-based OAuth2 authorisation flow.

    Opens the Strava authorisation page in the user's default browser, spins up
    a temporary local HTTP server to receive the callback, then exchanges the
    authorisation code for an access/refresh token pair.

    Args:
        client_id: Strava application client ID.
        client_secret: Strava application client secret.

    Returns:
        The full token payload from Strava.

    Raises:
        RuntimeError: If no authorisation code is received within 120 seconds.
        requests.HTTPError: If the token exchange request fails.
    """
    global _auth_code
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "activity:read_all",
    })
    url = f"{AUTH_URL}?{params}"

    server = HTTPServer(("localhost", 8765), _CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    print(f"\nOpening Strava in your browser...\nIf it doesn't open, visit:\n  {url}\n")
    webbrowser.open(url)
    thread.join(timeout=120)
    server.server_close()

    if not _auth_code:
        raise RuntimeError("OAuth timed out — no authorisation code received.")

    resp = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": _auth_code,
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    return resp.json()
