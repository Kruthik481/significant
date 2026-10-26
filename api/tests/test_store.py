from datetime import timedelta

from app.store import Store


async def test_save_get_round_trip_and_unknown_id(pg_schema):
    dsn, schema = pg_schema
    store = await Store.open(dsn, schema)
    try:
        await store.migrate()
        await store.migrate()  # idempotent
        report = {"verdict": "significant_win", "x": [1, 2]}
        rid = await store.save("Checkout test", "sample:checkout_win", report)
        assert len(rid) == 10
        got = await store.get(rid)
        assert got is not None
        assert (got.name, got.source, got.report) == ("Checkout test", "sample:checkout_win", report)
        assert await store.get("missing000") is None
        await store.ping()
    finally:
        await store.close()


async def test_purge_removes_only_old_reports(pg_schema):
    dsn, schema = pg_schema
    store = await Store.open(dsn, schema)
    try:
        await store.migrate()
        old = await store.save("old", "upload", {})
        new = await store.save("new", "upload", {})
        async with store.pool.connection() as conn:
            await conn.execute(
                "UPDATE reports SET created_at = now() - interval '91 days' WHERE id = %s", (old,)
            )
        assert await store.purge(timedelta(days=90)) == 1
        assert await store.get(old) is None
        assert await store.get(new) is not None
    finally:
        await store.close()


async def test_expired_reports_are_hidden_before_the_purge_runs(pg_schema):
    dsn, schema = pg_schema
    store = await Store.open(dsn, schema)
    try:
        await store.migrate()
        old = await store.save("old", "upload", {})
        async with store.pool.connection() as conn:
            await conn.execute(
                "UPDATE reports SET created_at = now() - interval '91 days' WHERE id = %s", (old,)
            )
        assert await store.get(old) is None
    finally:
        await store.close()
