import db
import results_repository as results_repo


def test_get_latest_solve_returns_none_when_never_solved(clean_db):
    assert results_repo.get_latest_solve(42) is None


def test_save_and_get_a_possible_solve_roundtrip(clean_db):
    layout_id = 42
    result = {
        "possible": True,
        "failed_at": None,
        "order": [
            {
                "ball": 1,
                "pocket": {"x": 0, "y": 0},
                "cut_angle": 5.0,
                "cue_rest_position": {"x": 10.0, "y": 10.0},
            }
        ],
    }

    results_repo.save_solve(layout_id, result, duration_ms=1.5)
    saved = results_repo.get_latest_solve(layout_id)

    assert saved == {**result, "game_mode": "freeform", "my_group": None, "duration_ms": 1.5}


def test_save_and_get_an_impossible_solve(clean_db):
    layout_id = 42
    result = {"possible": False, "failed_at": 3, "order": None}

    results_repo.save_solve(layout_id, result, game_mode="eight_ball", my_group="solids")
    saved = results_repo.get_latest_solve(layout_id)

    assert saved == {**result, "game_mode": "eight_ball", "my_group": "solids", "duration_ms": None}


def test_get_latest_solve_falls_back_to_freeform_for_a_legacy_row(clean_db):
    # simulates a row saved before the game_mode column existed: inserted
    # directly via SQL instead of through save_solve (which always sets a
    # value), leaving game_mode as a real SQL NULL
    layout_id = 42
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO solves (layout_id, computed_at, possible, failed_at, order_json) "
        "VALUES (%s, %s, %s, %s, %s)",
        (layout_id, "2026-01-01T00:00:00+00:00", True, None, "[]"),
    )
    conn.commit()
    conn.close()

    saved = results_repo.get_latest_solve(layout_id)

    assert saved["game_mode"] == "freeform"
    assert saved["my_group"] is None
    assert saved["possible"] is True
    assert saved["order"] == []
    assert saved["duration_ms"] is None


def test_get_latest_solve_returns_the_most_recent_one(clean_db):
    layout_id = 42
    first = {"possible": False, "failed_at": 2, "order": None}
    second = {"possible": True, "failed_at": None, "order": []}

    results_repo.save_solve(layout_id, first, game_mode="freeform")
    results_repo.save_solve(layout_id, second, game_mode="nine_ball")

    assert results_repo.get_latest_solve(layout_id) == {
        **second, "game_mode": "nine_ball", "my_group": None, "duration_ms": None
    }
