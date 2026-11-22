"""Integration test for the one required server-side cross-seam flow
(solver calling layouts over real HTTP, per ADR-6 and ADR-9).

Run against the real compose stack, not a stub: `docker compose up --build -d`
first, then `python -m pytest tests/integration`. Both services and SQL
Server must already be healthy; this test does not start or stop compose
itself.
"""

import os
import time

import pytest
import requests

LAYOUTS_URL = os.environ.get("LAYOUTS_BASE_URL", "http://localhost:8100")
SOLVER_URL = os.environ.get("SOLVER_BASE_URL", "http://localhost:8101")


def _wait_for_health(base_url, timeout=30):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                return
        except requests.RequestException as error:
            last_error = error
        time.sleep(1)
    raise RuntimeError(f"{base_url}/health never returned 200: {last_error}")


@pytest.fixture(scope="module", autouse=True)
def _stack_is_up():
    _wait_for_health(LAYOUTS_URL)
    _wait_for_health(SOLVER_URL)


def test_solver_fetches_a_real_layout_over_http_and_persists_the_result():
    create = requests.post(
        f"{LAYOUTS_URL}/layouts",
        json={"cue": {"x": 20, "y": 25}, "balls": [{"number": 1, "x": 70, "y": 25}]},
        timeout=5,
    )
    assert create.status_code == 201
    layout_id = create.json()["id"]

    solve = requests.post(
        f"{SOLVER_URL}/layouts/{layout_id}/solve",
        json={"game_mode": "freeform"},
        timeout=5,
    )
    assert solve.status_code == 200
    result = solve.json()
    assert result["possible"] is True
    assert [step["ball"] for step in result["order"]] == [1]

    stored = requests.get(f"{SOLVER_URL}/solves/{layout_id}", timeout=5)
    assert stored.status_code == 200
    assert stored.json()["order"] == result["order"]


def test_solve_reports_a_clean_404_for_a_layout_layouts_does_not_have():
    response = requests.post(
        f"{SOLVER_URL}/layouts/999999999/solve",
        json={"game_mode": "freeform"},
        timeout=5,
    )
    assert response.status_code == 404
