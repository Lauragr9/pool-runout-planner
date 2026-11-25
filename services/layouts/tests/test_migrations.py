import db
import migrate


def test_adding_source_preserves_existing_layout_rows(_migrated):
    conn = db.get_db()
    cur = conn.cursor()
    # roll the table back to its pre-003 shape and seed a row under it, to
    # prove the migration below doesn't lose data that was already there.
    # The DEFAULT constraint SQL Server auto-names when the column was
    # added must be dropped by name before the column itself can go.
    cur.execute(
        "IF EXISTS (SELECT 1 FROM sys.default_constraints dc "
        "JOIN sys.columns c ON dc.parent_object_id = c.object_id "
        "AND dc.parent_column_id = c.column_id "
        "WHERE dc.parent_object_id = OBJECT_ID('layouts') AND c.name = 'source') "
        "BEGIN "
        "DECLARE @cname NVARCHAR(128); "
        "SELECT @cname = dc.name FROM sys.default_constraints dc "
        "JOIN sys.columns c ON dc.parent_object_id = c.object_id "
        "AND dc.parent_column_id = c.column_id "
        "WHERE dc.parent_object_id = OBJECT_ID('layouts') AND c.name = 'source'; "
        "EXEC('ALTER TABLE layouts DROP CONSTRAINT ' + @cname); "
        "END"
    )
    cur.execute(
        "IF COL_LENGTH('layouts', 'source') IS NOT NULL "
        "ALTER TABLE layouts DROP COLUMN source"
    )
    cur.execute(
        "DELETE FROM schema_migrations WHERE filename = %s",
        ("003_add_layout_source.sql",),
    )
    cur.execute(
        "INSERT INTO layouts (created_at, cue_x, cue_y) OUTPUT INSERTED.id "
        "VALUES (%s, %s, %s)",
        ("2026-01-01T00:00:00+00:00", 10.0, 20.0),
    )
    layout_id = cur.fetchone()["id"]
    conn.commit()
    conn.close()

    migrate.run_migrations()

    conn = db.get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT cue_x, cue_y, source FROM layouts WHERE id = %s",
        (layout_id,),
    )
    row = cur.fetchone()
    conn.close()

    assert row["cue_x"] == 10.0
    assert row["cue_y"] == 20.0
    assert row["source"] == "ui"
