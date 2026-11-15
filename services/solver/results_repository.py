import json
from datetime import datetime, timezone

from db import get_db


def save_solve(layout_id, result, game_mode="freeform", my_group=None):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    order_json = json.dumps(result["order"]) if result["possible"] else None
    conn.execute(
        "INSERT INTO solves (layout_id, computed_at, possible, failed_at, order_json, game_mode, my_group) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (layout_id, now, int(result["possible"]), result["failed_at"], order_json, game_mode, my_group),
    )
    conn.commit()
    conn.close()


def get_latest_solve(layout_id):
    conn = get_db()
    row = conn.execute(
        "SELECT possible, failed_at, order_json, game_mode, my_group FROM solves "
        "WHERE layout_id = ? ORDER BY id DESC LIMIT 1",
        (layout_id,),
    ).fetchone()
    conn.close()
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
    }
