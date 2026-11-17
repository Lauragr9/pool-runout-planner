import pytest

import db
import migrate


@pytest.fixture(scope="session", autouse=True)
def _migrated():
    migrate.run_migrations()


@pytest.fixture(autouse=True)
def _clean_tables():
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM attempts")
    cur.execute("DELETE FROM layout_balls")
    cur.execute("DELETE FROM layouts")
    conn.commit()
    conn.close()
    yield
