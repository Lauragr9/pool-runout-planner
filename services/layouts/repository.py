from datetime import datetime, timezone

from db import get_db


def create_layout(cue, balls):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO layouts (created_at, cue_x, cue_y) OUTPUT INSERTED.id VALUES (%s, %s, %s)",
            (now, cue["x"], cue["y"]),
        )
        layout_id = cur.fetchone()["id"]
        if balls:
            cur.executemany(
                "INSERT INTO layout_balls (layout_id, ball_number, x, y) VALUES (%s, %s, %s, %s)",
                [(layout_id, b["number"], b["x"], b["y"]) for b in balls],
            )
        conn.commit()
        return layout_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def layout_exists(layout_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM layouts WHERE id = %s", (layout_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def get_layout(layout_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM layouts WHERE id = %s", (layout_id,))
        layout_row = cur.fetchone()
        if layout_row is None:
            return None
        cur.execute(
            "SELECT ball_number, x, y FROM layout_balls WHERE layout_id = %s ORDER BY ball_number",
            (layout_id,),
        )
        ball_rows = cur.fetchall()
        return {
            "id": layout_row["id"],
            "cue": {"x": layout_row["cue_x"], "y": layout_row["cue_y"]},
            "balls": [
                {"number": r["ball_number"], "x": r["x"], "y": r["y"]} for r in ball_rows
            ],
        }
    finally:
        conn.close()


def log_attempt(layout_id, succeeded, notes):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO attempts (layout_id, created_at, succeeded, notes) "
            "VALUES (%s, %s, %s, %s)",
            (layout_id, now, succeeded, notes),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_recent_layouts(limit=20):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT TOP (%s) id, created_at, cue_x, cue_y FROM layouts ORDER BY id DESC",
            (limit,),
        )
        layout_rows = cur.fetchall()

        layouts = []
        for row in layout_rows:
            cur.execute(
                "SELECT ball_number, x, y FROM layout_balls "
                "WHERE layout_id = %s ORDER BY ball_number",
                (row["id"],),
            )
            ball_rows = cur.fetchall()
            cur.execute(
                "SELECT succeeded, notes, created_at FROM attempts "
                "WHERE layout_id = %s ORDER BY id",
                (row["id"],),
            )
            attempt_rows = cur.fetchall()
            layouts.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "cue": {"x": row["cue_x"], "y": row["cue_y"]},
                    "balls": [
                        {"number": b["ball_number"], "x": b["x"], "y": b["y"]} for b in ball_rows
                    ],
                    "attempts": [
                        {
                            "succeeded": bool(a["succeeded"]),
                            "notes": a["notes"],
                            "created_at": a["created_at"],
                        }
                        for a in attempt_rows
                    ],
                }
            )
        return layouts
    finally:
        conn.close()
