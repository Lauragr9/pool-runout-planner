import pytest

import db
import migrate


@pytest.fixture(scope="session")
def _migrated():
    migrate.run_migrations()


@pytest.fixture
def clean_db(_migrated):
    """Only tests that touch the database request this fixture, so the pure
    logic tests (engine, geometry, client) never need a live SQL Server."""
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM solves")
    conn.commit()
    conn.close()
    yield
