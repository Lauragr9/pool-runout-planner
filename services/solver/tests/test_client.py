from unittest.mock import Mock, patch

import pytest
import requests

import client


def test_get_layout_returns_the_parsed_json_on_success():
    fake_response = Mock(status_code=200)
    fake_response.json.return_value = {"id": 7, "cue": {"x": 1, "y": 2}, "balls": []}
    with patch("client.requests.get", return_value=fake_response) as mock_get:
        layout = client.get_layout(7)

    assert layout == {"id": 7, "cue": {"x": 1, "y": 2}, "balls": []}
    mock_get.assert_called_once()


def test_get_layout_returns_none_for_a_404():
    fake_response = Mock(status_code=404)
    with patch("client.requests.get", return_value=fake_response):
        assert client.get_layout(999) is None


def test_get_layout_retries_then_raises_when_layouts_is_unreachable(monkeypatch):
    # keep the test fast: no real sleeping, and only one retry to check for
    monkeypatch.setattr(client, "LAYOUTS_RETRIES", 1)
    monkeypatch.setattr(client.time, "sleep", lambda seconds: None)
    with patch("client.requests.get", side_effect=requests.ConnectionError("refused")) as mock_get:
        with pytest.raises(client.LayoutsUnavailable):
            client.get_layout(7)

    # one initial attempt plus one retry = 2 calls
    assert mock_get.call_count == 2
