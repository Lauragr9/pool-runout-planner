import db
import domains.layouts.repository as repo


def _use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()


def test_create_and_get_layout_roundtrip(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    cue = {"x": 10, "y": 5}
    balls = [{"number": 1, "x": 20, "y": 10}, {"number": 2, "x": 30, "y": 15}]

    layout_id = repo.create_layout(cue, balls)
    layout = repo.get_layout(layout_id)

    assert layout["id"] == layout_id
    assert layout["cue"] == cue
    assert layout["balls"] == balls


def test_get_layout_returns_none_for_unknown_id(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    assert repo.get_layout(999) is None


def test_get_layout_orders_balls_by_number(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    cue = {"x": 0, "y": 0}
    balls = [
        {"number": 3, "x": 1, "y": 1},
        {"number": 1, "x": 2, "y": 2},
        {"number": 2, "x": 3, "y": 3},
    ]

    layout_id = repo.create_layout(cue, balls)
    layout = repo.get_layout(layout_id)

    assert [b["number"] for b in layout["balls"]] == [1, 2, 3]


def test_log_attempt_persists_success_flag_and_notes(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    layout_id = repo.create_layout({"x": 0, "y": 0}, [])

    repo.log_attempt(layout_id, True, "clean run")

    conn = db.get_db()
    row = conn.execute(
        "SELECT succeeded, notes FROM attempts WHERE layout_id = ?", (layout_id,)
    ).fetchone()
    conn.close()

    assert row["succeeded"] == 1
    assert row["notes"] == "clean run"


def test_log_attempt_stores_false_as_zero(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    layout_id = repo.create_layout({"x": 0, "y": 0}, [])

    repo.log_attempt(layout_id, False, "missed the cut")

    conn = db.get_db()
    row = conn.execute(
        "SELECT succeeded FROM attempts WHERE layout_id = ?", (layout_id,)
    ).fetchone()
    conn.close()

    assert row["succeeded"] == 0


def test_list_recent_layouts_includes_positions_and_attempts(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    cue = {"x": 0, "y": 0}
    balls = [{"number": 1, "x": 1, "y": 1}, {"number": 2, "x": 2, "y": 2}]
    layout_id = repo.create_layout(cue, balls)
    repo.log_attempt(layout_id, True, "worked")
    repo.log_attempt(layout_id, False, "missed second ball")

    layouts = repo.list_recent_layouts()

    assert len(layouts) == 1
    assert layouts[0]["id"] == layout_id
    assert layouts[0]["cue"] == cue
    assert layouts[0]["balls"] == balls
    assert [a["succeeded"] for a in layouts[0]["attempts"]] == [True, False]
    assert layouts[0]["attempts"][1]["notes"] == "missed second ball"


def test_list_recent_layouts_newest_first(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    first_id = repo.create_layout({"x": 0, "y": 0}, [])
    second_id = repo.create_layout({"x": 1, "y": 1}, [])

    layouts = repo.list_recent_layouts()

    assert [layout["id"] for layout in layouts] == [second_id, first_id]
