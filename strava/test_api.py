from unittest.mock import MagicMock, call, patch

import pytest

from strava.api import fetch_all_activities


def _mock_response(data):
    resp = MagicMock()
    resp.json.return_value = data
    return resp


def test_fetch_all_activities_single_page():
    batch = [{"id": 1}, {"id": 2}]
    responses = [_mock_response(batch), _mock_response([])]
    with patch("strava.api.requests.get", side_effect=responses), \
         patch("strava.api.time.sleep"):
        result = fetch_all_activities("token")
    assert result == batch


def test_fetch_all_activities_multiple_pages():
    page1 = [{"id": i} for i in range(200)]
    page2 = [{"id": i} for i in range(200, 250)]
    responses = [_mock_response(page1), _mock_response(page2), _mock_response([])]
    with patch("strava.api.requests.get", side_effect=responses), \
         patch("strava.api.time.sleep"):
        result = fetch_all_activities("token")
    assert len(result) == 250


def test_fetch_all_activities_empty():
    with patch("strava.api.requests.get", return_value=_mock_response([])), \
         patch("strava.api.time.sleep"):
        result = fetch_all_activities("token")
    assert result == []


def test_fetch_all_activities_sends_auth_header():
    with patch("strava.api.requests.get", return_value=_mock_response([])) as mock_get, \
         patch("strava.api.time.sleep"):
        fetch_all_activities("my_token")
    headers = mock_get.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer my_token"


def test_fetch_all_activities_raises_on_http_error():
    resp = MagicMock()
    resp.raise_for_status.side_effect = Exception("403 Forbidden")
    with patch("strava.api.requests.get", return_value=resp), \
         patch("strava.api.time.sleep"):
        with pytest.raises(Exception, match="403"):
            fetch_all_activities("bad_token")
