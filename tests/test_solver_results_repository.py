import db
import domains.layouts.repository as layouts_repo
import domains.solver.results_repository as results_repo


def _use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()


def test_get_latest_solve_returns_none_when_never_solved(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    layout_id = layouts_repo.create_layout({"x": 0, "y": 0}, [])

    assert results_repo.get_latest_solve(layout_id) is None


def test_save_and_get_a_possible_solve_roundtrip(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    layout_id = layouts_repo.create_layout({"x": 0, "y": 0}, [])
    result = {
        "possible": True,
        "failed_at": None,
        "order": [{"ball": 1, "pocket": {"x": 0, "y": 0}, "cut_angle": 5.0,
                    "cue_rest_position": {"x": 10.0, "y": 10.0}}],
    }

    results_repo.save_solve(layout_id, result)
    saved = results_repo.get_latest_solve(layout_id)

    assert saved == {**result, "game_mode": "freeform", "my_group": None}


def test_save_and_get_an_impossible_solve(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    layout_id = layouts_repo.create_layout({"x": 0, "y": 0}, [])
    result = {"possible": False, "failed_at": 3, "order": None}

    results_repo.save_solve(layout_id, result, game_mode="eight_ball", my_group="solids")
    saved = results_repo.get_latest_solve(layout_id)

    assert saved == {**result, "game_mode": "eight_ball", "my_group": "solids"}


def test_get_latest_solve_returns_the_most_recent_one(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    layout_id = layouts_repo.create_layout({"x": 0, "y": 0}, [])
    first = {"possible": False, "failed_at": 2, "order": None}
    second = {"possible": True, "failed_at": None, "order": []}

    results_repo.save_solve(layout_id, first, game_mode="freeform")
    results_repo.save_solve(layout_id, second, game_mode="nine_ball")

    assert results_repo.get_latest_solve(layout_id) == {**second, "game_mode": "nine_ball", "my_group": None}
