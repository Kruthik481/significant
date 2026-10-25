import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest

DEFAULT_TEST_DB = "postgresql://ab:ab@localhost:5436/ab_test"


@pytest.fixture
def pg_schema() -> Iterator[tuple[str, str]]:
    """A fresh Postgres schema per test, dropped afterwards."""
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB)
    schema = f"t_{uuid.uuid4().hex[:12]}"
    try:
        admin = psycopg.connect(url, autocommit=True)
    except psycopg.OperationalError as e:
        pytest.fail(f"postgres unavailable (run `docker compose up -d --wait`): {e}")
    with admin:
        admin.execute(f"CREATE SCHEMA {schema}")
        try:
            yield url, schema
        finally:
            admin.execute(f"DROP SCHEMA {schema} CASCADE")
