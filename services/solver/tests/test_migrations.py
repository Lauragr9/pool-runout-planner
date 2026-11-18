import db
import migrate


def test_adding_duration_ms_preserves_existing_solve_rows(_migrated):
    conn = db.get_db()
    cur = conn.cursor()
    # roll the table back to its pre-002 shape and seed a row under it, to
    # prove the migration below doesn't lose data that was already there
    cur.execute("IF OBJECT_ID('solves', 'U') IS NOT NULL DROP TABLE solves")
    cur.execute(
        "CREATE TABLE solves ("
        "    id INT IDENTITY(1,1) PRIMARY KEY,"
        "    layout_id INT NOT NULL,"
        "    computed_at NVARCHAR(32) NOT NULL,"
        "    possible BIT NOT NULL,"
        "    failed_at INT,"
        "    order_json NVARCHAR(MAX),"
        "    game_mode NVARCHAR(32),"
        "    my_group NVARCHAR(16)"
        ")"
    )
    cur.execute(
        "DELETE FROM schema_migrations WHERE filename = %s",
        ("002_add_solve_duration.sql",),
    )
    cur.execute(
        "INSERT INTO solves (layout_id, computed_at, possible, failed_at, order_json, "
        "game_mode, my_group) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (42, "2026-01-01T00:00:00+00:00", True, None, "[]", "freeform", None),
    )
    conn.commit()
    conn.close()

    migrate.run_migrations()

    conn = db.get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT layout_id, possible, game_mode, duration_ms FROM solves WHERE layout_id = %s",
        (42,),
    )
    row = cur.fetchone()
    conn.close()

    assert row["layout_id"] == 42
    assert row["possible"] is True
    assert row["game_mode"] == "freeform"
    assert row["duration_ms"] is None
