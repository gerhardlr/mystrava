import pytest
from unittest.mock import patch

from strava.cli import main


def test_main_reads_credentials_from_env(monkeypatch):
    monkeypatch.setenv("STRAVA_CLIENT_ID", "env_id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "env_secret")
    with patch("strava.cli.load_dotenv"), \
         patch("strava.cli.get_valid_token", return_value="token") as mock_token, \
         patch("strava.cli.fetch_all_activities", return_value=[]), \
         patch("strava.cli.save_csv"):
        main()
    mock_token.assert_called_once_with("env_id", "env_secret")


def test_main_exits_when_credentials_missing(monkeypatch):
    monkeypatch.delenv("STRAVA_CLIENT_ID", raising=False)
    monkeypatch.delenv("STRAVA_CLIENT_SECRET", raising=False)
    with patch("strava.cli.load_dotenv"), \
         pytest.raises(SystemExit, match="STRAVA_CLIENT_ID"):
        main()


def test_main_exits_when_client_id_missing(monkeypatch):
    monkeypatch.delenv("STRAVA_CLIENT_ID", raising=False)
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    with patch("strava.cli.load_dotenv"), \
         pytest.raises(SystemExit):
        main()


def test_main_uses_saved_session(monkeypatch, capsys):
    monkeypatch.setenv("STRAVA_CLIENT_ID", "id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    with patch("strava.cli.load_dotenv"), \
         patch("strava.cli.get_valid_token", return_value="saved_token"), \
         patch("strava.cli.fetch_all_activities", return_value=[{"id": 1}]) as mock_fetch, \
         patch("strava.cli.save_csv") as mock_save:
        main()
    mock_fetch.assert_called_once_with("saved_token")
    mock_save.assert_called_once()
    assert "Using saved session" in capsys.readouterr().out


def test_main_runs_oauth_when_no_token(monkeypatch, capsys):
    monkeypatch.setenv("STRAVA_CLIENT_ID", "id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    new_tokens = {"access_token": "oauth_token"}
    with patch("strava.cli.load_dotenv"), \
         patch("strava.cli.get_valid_token", return_value=None), \
         patch("strava.cli.run_oauth", return_value=new_tokens) as mock_oauth, \
         patch("strava.cli.save_tokens") as mock_save_tokens, \
         patch("strava.cli.fetch_all_activities", return_value=[]) as mock_fetch, \
         patch("strava.cli.save_csv"):
        main()
    mock_oauth.assert_called_once_with("id", "secret")
    mock_save_tokens.assert_called_once_with(new_tokens)
    mock_fetch.assert_called_once_with("oauth_token")
    assert "Authorised successfully" in capsys.readouterr().out
