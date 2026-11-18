import json
from datetime import datetime, timezone

from db import get_db


def save_solve(layout_id, result, game_mode="freeform", my_group=None, duration_ms=None):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        order_json = json.dumps(result["order"]) if result["possible"] else None
        cur.execute(
            "INSERT INTO solves (layout_id, computed_at, possible, failed_at, order_json, "
            "game_mode, my_group, duration_ms) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                layout_id,
                now,
                bool(result["possible"]),
                result["failed_at"],
                order_json,
                game_mode,
                my_group,
                duration_ms,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_latest_solve(layout_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT TOP (1) possible, failed_at, order_json, game_mode, my_group, duration_ms "
            "FROM solves WHERE layout_id = %s ORDER BY id DESC",
            (layout_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "possible": bool(row["possible"]),
            "failed_at": row["failed_at"],
            "order": json.loads(row["order_json"]) if row["order_json"] else None,
            # same idea: NULL only for rows saved before game_mode existed
            "game_mode": row["game_mode"] or "freeform",
            # None here is a real value, not a missing-column fallback: it means
            # no group was chosen, so the sequence covers the whole table
            "my_group": row["my_group"],
            # NULL for rows saved before this column existed, or before the
            # route started timing the solve
            "duration_ms": row["duration_ms"],
        }
    finally:
        conn.close()
