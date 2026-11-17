import os
import time
from urllib.parse import urlparse

import pymssql

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "mssql://solver_user:solver_pw@sqlserver:1433/solver"
)
CONNECT_RETRIES = int(os.environ.get("DB_CONNECT_RETRIES", 5))
CONNECT_RETRY_DELAY_S = float(os.environ.get("DB_CONNECT_RETRY_DELAY_S", 2))


def _connection_params():
    parsed = urlparse(DATABASE_URL)
    return {
        "server": parsed.hostname,
        "port": parsed.port or 1433,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
    }


def get_db():
    params = _connection_params()
    last_error = None
    for attempt in range(CONNECT_RETRIES):
        try:
            return pymssql.connect(as_dict=True, **params)
        except (pymssql.OperationalError, pymssql.InterfaceError) as error:
            last_error = error
            if attempt < CONNECT_RETRIES - 1:
                time.sleep(CONNECT_RETRY_DELAY_S * (attempt + 1))
    raise last_error
