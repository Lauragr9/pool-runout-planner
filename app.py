import os

from flask import Flask, jsonify, render_template, request

from db import init_db
from domains.layouts import repository as layouts_repo
from domains.solver.engine import find_runout


def create_app():
    app = Flask(__name__)
    init_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/layouts")
    def create_layout():
        data = request.get_json()
        layout_id = layouts_repo.create_layout(data["cue"], data["balls"])
        return jsonify({"id": layout_id}), 201

    @app.get("/api/layouts/<int:layout_id>")
    def get_layout(layout_id):
        layout = layouts_repo.get_layout(layout_id)
        if layout is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(layout)

    @app.post("/api/layouts/<int:layout_id>/solve")
    def solve_layout(layout_id):
        layout = layouts_repo.get_layout(layout_id)
        if layout is None:
            return jsonify({"error": "not found"}), 404
        result = find_runout(layout["cue"], layout["balls"])
        return jsonify(result)

    @app.post("/api/layouts/<int:layout_id>/attempts")
    def log_attempt(layout_id):
        data = request.get_json()
        layouts_repo.log_attempt(layout_id, data.get("succeeded"), data.get("notes", ""))
        return jsonify({"ok": True}), 201

    @app.get("/api/history")
    def history():
        layouts = layouts_repo.list_recent_layouts()
        for layout in layouts:
            layout["solution"] = find_runout(layout["cue"], layout["balls"])
        return jsonify(layouts)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
