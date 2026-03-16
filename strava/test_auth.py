import json
import time
from unittest.mock import MagicMock, mock_open, patch

import pytest

import strava.auth as auth
from strava.auth import (
    get_valid_token,
    load_tokens,
    refresh_access_token,
    save_tokens,
)


# ── save_tokens / load_tokens ──────────────────────────────────────────────────

def test_save_tokens_writes_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tokens = {"access_token": "abc", "expires_at": 9999}
    save_tokens(tokens)
    with open(auth.TOKEN_FILE) as f:
        assert json.load(f) == tokens


def test_load_tokens_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_tokens() is None


def test_load_tokens_returns_dict(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tokens = {"access_token": "abc", "expires_at": 9999}
    save_tokens(tokens)
    assert load_tokens() == tokens


# ── refresh_access_token ───────────────────────────────────────────────────────

def test_refresh_access_token_posts_and_returns_json():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "new_token", "expires_at": 9999}
    with patch("strava.auth.requests.post", return_value=mock_resp) as mock_post:
        result = refresh_access_token("id", "secret", "old_refresh")
    mock_post.assert_called_once()
    call_data = mock_post.call_args.kwargs["data"]
    assert call_data["grant_type"] == "refresh_token"
    assert call_data["refresh_token"] == "old_refresh"
    assert result["access_token"] == "new_token"


def test_refresh_access_token_raises_on_http_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("401")
    with patch("strava.auth.requests.post", return_value=mock_resp):
        with pytest.raises(Exception, match="401"):
            refresh_access_token("id", "secret", "bad_token")


# ── get_valid_token ────────────────────────────────────────────────────────────

def test_get_valid_token_returns_none_with_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_valid_token("id", "secret") is None


def test_get_valid_token_returns_token_when_fresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tokens = {"access_token": "fresh", "expires_at": time.time() + 3600, "refresh_token": "r"}
    save_tokens(tokens)
    assert get_valid_token("id", "secret") == "fresh"


def test_get_valid_token_refreshes_when_expired(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tokens = {"access_token": "old", "expires_at": time.time() - 1, "refresh_token": "r"}
    save_tokens(tokens)

    new_tokens = {"access_token": "new", "expires_at": time.time() + 3600, "refresh_token": "r2"}
    with patch("strava.auth.refresh_access_token", return_value=new_tokens):
        result = get_valid_token("id", "secret")

    assert result == "new"
    assert load_tokens()["access_token"] == "new"
