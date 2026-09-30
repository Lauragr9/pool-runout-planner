import json
from datetime import datetime, timezone

from db import get_db


def save_solve(layout_id, result):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    order_json = json.dumps(result["order"]) if result["possible"] else None
    conn.execute(
        "INSERT INTO solves (layout_id, computed_at, possible, failed_at, order_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (layout_id, now, int(result["possible"]), result["failed_at"], order_json),
    )
    conn.commit()
    conn.close()


def get_latest_solve(layout_id):
    conn = get_db()
    row = conn.execute(
        "SELECT possible, failed_at, order_json FROM solves "
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
    }
