import pytest

from app import app as flask_app


@pytest.fixture
def client():
    return flask_app.test_client()


def test_create_layout_rejects_missing_cue(client):
    response = client.post("/layouts", json={"balls": []})
    assert response.status_code == 400


def test_create_layout_rejects_missing_balls(client):
    response = client.post("/layouts", json={"cue": {"x": 10, "y": 5}})
    assert response.status_code == 400


def test_create_layout_rejects_non_numeric_coordinate(client):
    response = client.post("/layouts", json={"cue": {"x": "abc", "y": 5}, "balls": []})
    assert response.status_code == 400


def test_create_layout_rejects_ball_without_coordinates(client):
    response = client.post(
        "/layouts", json={"cue": {"x": 10, "y": 5}, "balls": [{"number": 1}]}
    )
    assert response.status_code == 400


def test_create_layout_rejects_off_table_cue(client):
    response = client.post(
        "/layouts", json={"cue": {"x": 1000, "y": 5}, "balls": []}
    )
    assert response.status_code == 400


def test_create_layout_accepts_a_valid_payload(client):
    response = client.post(
        "/layouts",
        json={"cue": {"x": 10, "y": 5}, "balls": [{"number": 1, "x": 20, "y": 10}]},
    )
    assert response.status_code == 201
    assert "id" in response.get_json()


def test_log_attempt_rejects_non_boolean_succeeded(client):
    create = client.post("/layouts", json={"cue": {"x": 0, "y": 0}, "balls": []})
    layout_id = create.get_json()["id"]

    response = client.post(f"/layouts/{layout_id}/attempts", json={"succeeded": "no"})
    assert response.status_code == 400


def test_log_attempt_rejects_an_unknown_layout(client):
    response = client.post("/layouts/999999/attempts", json={"succeeded": True})
    assert response.status_code == 404


def test_log_attempt_accepts_a_valid_payload(client):
    create = client.post("/layouts", json={"cue": {"x": 0, "y": 0}, "balls": []})
    layout_id = create.get_json()["id"]

    response = client.post(
        f"/layouts/{layout_id}/attempts", json={"succeeded": True, "notes": "clean run"}
    )
    assert response.status_code == 201
