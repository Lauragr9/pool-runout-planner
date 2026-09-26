from datetime import datetime, timezone

from db import get_db


def create_layout(cue, balls):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO layouts (created_at, cue_x, cue_y) VALUES (?, ?, ?)",
        (now, cue["x"], cue["y"]),
    )
    layout_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO layout_balls (layout_id, ball_number, x, y) VALUES (?, ?, ?, ?)",
        [(layout_id, b["number"], b["x"], b["y"]) for b in balls],
    )
    conn.commit()
    conn.close()
    return layout_id


def get_layout(layout_id):
    conn = get_db()
    layout_row = conn.execute(
        "SELECT * FROM layouts WHERE id = ?", (layout_id,)
    ).fetchone()
    if layout_row is None:
        conn.close()
        return None
    ball_rows = conn.execute(
        "SELECT ball_number, x, y FROM layout_balls WHERE layout_id = ? ORDER BY ball_number",
        (layout_id,),
    ).fetchall()
    conn.close()
    return {
        "id": layout_row["id"],
        "cue": {"x": layout_row["cue_x"], "y": layout_row["cue_y"]},
        "balls": [
            {"number": r["ball_number"], "x": r["x"], "y": r["y"]} for r in ball_rows
        ],
    }


def log_attempt(layout_id, succeeded, notes):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO attempts (layout_id, created_at, succeeded, notes) VALUES (?, ?, ?, ?)",
        (layout_id, now, int(bool(succeeded)), notes),
    )
    conn.commit()
    conn.close()
