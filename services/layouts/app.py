import logging
import os
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request
from flask_cors import CORS

import repository
from db import get_db
from migrate import run_migrations
from validation import ValidationError, validate_attempt_payload, validate_layout_payload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("layouts")

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
            conn.close()
            if row is None:
                raise RuntimeError("health round-trip returned no row")
            return jsonify({"status": "ok", "db": "ok", "version": GIT_SHA}), 200
        except Exception:
            logger.exception("health check failed")
            return jsonify({"status": "error", "db": "error", "version": GIT_SHA}), 503

    @app.post("/layouts")
    def create_layout():
        data = request.get_json(silent=True)
        try:
            cue, balls = validate_layout_payload(data)
        except ValidationError as error:
            return jsonify({"error": str(error)}), 400
        layout_id = repository.create_layout(cue, balls)
        return jsonify({"id": layout_id}), 201

    @app.get("/layouts/<int:layout_id>")
    def get_layout(layout_id):
        layout = repository.get_layout(layout_id)
        if layout is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(layout)

    @app.get("/layouts")
    def list_recent_layouts():
        return jsonify(repository.list_recent_layouts())

    @app.post("/layouts/<int:layout_id>/attempts")
    def log_attempt(layout_id):
        data = request.get_json(silent=True)
        try:
            succeeded, notes = validate_attempt_payload(data)
        except ValidationError as error:
            return jsonify({"error": str(error)}), 400
        if not repository.layout_exists(layout_id):
            return jsonify({"error": "not found"}), 404
        repository.log_attempt(layout_id, succeeded, notes)
        return jsonify({"ok": True}), 201

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
