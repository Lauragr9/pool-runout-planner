import logging
import os
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request
from flask_cors import CORS

import results_repository
from client import LayoutsUnavailable, get_layout
from db import get_db
from migrate import run_migrations
from engine import find_runout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solver")

GIT_SHA = os.environ.get("GIT_SHA", "dev")
UI_ORIGIN = os.environ.get("UI_ORIGIN", "http://localhost:8080")


def create_app():
    app = Flask(__name__)
    CORS(app, origins=[UI_ORIGIN])
    run_migrations()

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
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = '_health') "
                "CREATE TABLE _health (id INT IDENTITY(1,1) PRIMARY KEY, pinged_at NVARCHAR(32))"
            )
            cur.execute("DELETE FROM _health")
            cur.execute(
                "INSERT INTO _health (pinged_at) VALUES (%s)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            conn.commit()
            cur.execute("SELECT pinged_at FROM _health")
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("health round-trip returned no row")
            return jsonify({"status": "ok", "db": "ok", "version": GIT_SHA}), 200
        except Exception:
            logger.exception("health check failed")
            return jsonify({"status": "error", "db": "error", "version": GIT_SHA}), 503
        finally:
            if conn is not None:
                conn.close()

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
        solve_start = time.monotonic()
        try:
            result = find_runout(
                layout["cue"], layout["balls"], game_mode=game_mode, my_group=my_group
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        duration_ms = (time.monotonic() - solve_start) * 1000
        results_repository.save_solve(layout_id, result, game_mode, my_group, duration_ms)
        return jsonify(result)

    @app.get("/solves/<int:layout_id>")
    def get_solve(layout_id):
        solve = results_repository.get_latest_solve(layout_id)
        return jsonify(solve)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    # 0.0.0.0 is required, not a mistake: this process is the only thing
    # in its container, and binding to localhost would make it unreachable
    # from the compose network or Azure Container Apps' ingress.
    app.run(host="0.0.0.0", port=port)  # nosemgrep
