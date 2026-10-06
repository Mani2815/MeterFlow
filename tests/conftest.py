"""
tests/conftest.py
-----------------
Shared pytest fixtures for all test modules.
"""

import os
import pytest
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load .env before any test runs."""
    load_dotenv()


@pytest.fixture(scope="session")
def db_conn():
    """
    Session-scoped PostgreSQL connection.
    Uses DATABASE_URL from .env or the environment.
    The connection is read-only (autocommit off, no DML in tests).
    """
    dsn = os.getenv(
        "DATABASE_URL",
        "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash",
    )
    conn = psycopg2.connect(dsn)
    conn.autocommit = True  # read-only; no explicit transactions needed
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def cursor(db_conn):
    """Named server-side cursor for efficient large result sets."""
    with db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        yield cur
