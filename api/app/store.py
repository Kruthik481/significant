"""Reports in Postgres. Only the computed report is stored, never the uploaded rows."""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

ID_LENGTH = 10
ID_ATTEMPTS = 5

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id text PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    name text NOT NULL,
    source text NOT NULL,
    report jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_created_at ON reports (created_at);
"""

RETENTION = timedelta(days=90)


@dataclass(frozen=True)
class StoredReport:
    id: str
    name: str
    source: str
    created_at: datetime
    report: dict[str, Any]


class Store:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    @classmethod
    async def open(cls, dsn: str, schema: str | None = None) -> "Store":
        kwargs = {"options": f"-c search_path={schema}"} if schema else {}
        pool = AsyncConnectionPool(
            dsn,
            min_size=1,
            max_size=5,
            kwargs=kwargs,
            open=False,
            check=AsyncConnectionPool.check_connection,  # Neon drops idle connections
        )
        await pool.open(wait=True, timeout=15)
        return cls(pool)

    async def close(self) -> None:
        await self.pool.close()

    async def migrate(self) -> None:
        async with self.pool.connection() as conn:
            await conn.execute(SCHEMA)

    async def ping(self) -> None:
        async with self.pool.connection() as conn:
            await conn.execute("SELECT 1")

    async def save(self, name: str, source: str, report: dict[str, Any]) -> str:
        for _ in range(ID_ATTEMPTS):
            rid = secrets.token_urlsafe(8)[:ID_LENGTH]
            try:
                async with self.pool.connection() as conn:
                    await conn.execute(
                        "INSERT INTO reports (id, name, source, report) VALUES (%s, %s, %s, %s)",
                        (rid, name, source, Jsonb(report)),
                    )
                return rid
            except errors.UniqueViolation:
                continue
        raise RuntimeError("could not allocate a unique report id")

    async def get(self, rid: str) -> StoredReport | None:
        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT id, name, source, created_at, report FROM reports"
                " WHERE id = %s AND created_at >= now() - %s",
                (rid, RETENTION),
            )
            row = await cur.fetchone()
        return None if row is None else StoredReport(**row)

    async def purge(self, older_than: timedelta) -> int:
        async with self.pool.connection() as conn:
            cur = await conn.execute("DELETE FROM reports WHERE created_at < now() - %s", (older_than,))
            return cur.rowcount
