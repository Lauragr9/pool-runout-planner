import os
import sqlite3

DATA_DIR = os.environ.get("DATA_DIR", "data")
DB_PATH = os.path.join(DATA_DIR, "runout.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS layouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    cue_x REAL NOT NULL,
    cue_y REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS layout_balls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_id INTEGER NOT NULL REFERENCES layouts(id),
    ball_number INTEGER NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_id INTEGER NOT NULL REFERENCES layouts(id),
    created_at TEXT NOT NULL,
    succeeded INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS solves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_id INTEGER NOT NULL REFERENCES layouts(id),
    computed_at TEXT NOT NULL,
    possible INTEGER NOT NULL,
    failed_at INTEGER,
    order_json TEXT,
    game_mode TEXT
);
"""


def get_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
