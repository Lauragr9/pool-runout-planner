import glob
import os
import re
from datetime import datetime, timezone

from db import get_db

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

# T-SQL scripts use GO as a batch separator; the driver can't execute GO
# itself, so each migration file is split on a line that is only GO before
# being sent to the server one batch at a time.
_BATCH_SEPARATOR = re.compile(r"(?im)^\s*GO\s*$")


def _ensure_migrations_table(conn):
    cur = conn.cursor()
    cur.execute(
        "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'schema_migrations') "
        "CREATE TABLE schema_migrations ("
        "    filename NVARCHAR(255) PRIMARY KEY,"
        "    applied_at NVARCHAR(32) NOT NULL"
        ")"
    )
    conn.commit()


def _already_applied(conn):
    cur = conn.cursor()
    cur.execute("SELECT filename FROM schema_migrations")
    return {row["filename"] for row in cur.fetchall()}


def run_migrations():
    conn = get_db()
    _ensure_migrations_table(conn)
    applied = _already_applied(conn)

    paths = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    for path in paths:
        filename = os.path.basename(path)
        if filename in applied:
            continue

        with open(path) as f:
            script = f.read()

        cur = conn.cursor()
        for batch in _BATCH_SEPARATOR.split(script):
            if batch.strip():
                cur.execute(batch)
        cur.execute(
            "INSERT INTO schema_migrations (filename, applied_at) VALUES (%s, %s)",
            (filename, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        print(f"applied migration {filename}", flush=True)

    conn.close()
