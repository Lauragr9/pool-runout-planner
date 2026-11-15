import logging
import os
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request
from flask_cors import CORS

import results_repository
from client import LayoutsUnavailable, get_layout
from db import get_db, init_db
from engine import find_runout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solver")

GIT_SHA = os.environ.get("GIT_SHA", "dev")
UI_ORIGIN = os.environ.get("UI_ORIGIN", "http://localhost:8080")


def create_app():
    app = Flask(__name__)
    CORS(app, origins=[UI_ORIGIN])
    init_db()

    @app.before_request
    def _start_timer():
        g.start_time = time.monotonic()

    @app.after_request
    def _log_request(response):
        duration_ms = (time.monotonic() - g.start_time) * 1000
        logger.info(
            "%s %s %s %.1fms", request.method, request.path, response.status_code, duration_ms
        )
        return response

    @app.get("/health")
    def health():
        try:
            conn = get_db()
            conn.execute("CREATE TABLE IF NOT EXISTS _health (id INTEGER PRIMARY KEY, pinged_at TEXT)")
            conn.execute("DELETE FROM _health")
            conn.execute(
                "INSERT INTO _health (pinged_at) VALUES (?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            conn.commit()
            row = conn.execute("SELECT pinged_at FROM _health").fetchone()
            conn.close()
            if row is None:
                raise RuntimeError("health round-trip returned no row")
            return jsonify({"status": "ok", "db": "ok", "version": GIT_SHA}), 200
        except Exception:
            logger.exception("health check failed")
            return jsonify({"status": "error", "db": "error", "version": GIT_SHA}), 503

    @app.post("/layouts/<int:layout_id>/solve")
    def solve_layout(layout_id):
        try:
            layout = get_layout(layout_id)
        except LayoutsUnavailable as error:
            logger.warning("layouts service unavailable: %s", error)
            return jsonify({"error": "layouts service unavailable"}), 503
        if layout is None:
            return jsonify({"error": "not found"}), 404

        data = request.get_json(silent=True) or {}
        game_mode = data.get("game_mode", "freeform")
        my_group = data.get("my_group")
        try:
            result = find_runout(layout["cue"], layout["balls"], game_mode=game_mode, my_group=my_group)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        results_repository.save_solve(layout_id, result, game_mode, my_group)
        return jsonify(result)

    @app.get("/solves/<int:layout_id>")
    def get_solve(layout_id):
        solve = results_repository.get_latest_solve(layout_id)
        return jsonify(solve)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    app.run(host="0.0.0.0", port=port)
