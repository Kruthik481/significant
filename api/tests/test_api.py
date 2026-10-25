import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings

ORIGIN = "http://localhost:3300"
CSV = b"user_id,variant,metric\n" + b"".join(
    f"u{i},{'control' if i % 2 else 'treatment'},{1 if i % 7 == 0 else 0}\n".encode() for i in range(400)
)


@pytest.fixture
def client(pg_schema):
    dsn, schema = pg_schema
    settings = Settings(
        database_url=dsn,
        web_origin=ORIGIN,
        rate_limit_per_hour=5,
        max_upload_bytes=64 * 1024,
        db_schema=schema,
    )
    with TestClient(create_app(settings)) as c:
        yield c


def error(resp):
    return resp.json()["error"]["code"]


def test_sample_analysis_round_trips_through_the_share_link(client):
    r = client.post("/analyses/samples/checkout_win")
    assert r.status_code == 201
    body = r.json()
    assert body["report"]["verdict"] == "significant_win"
    got = client.get(f"/analyses/{body['id']}")
    assert got.status_code == 200
    assert got.json()["report"] == body["report"]
    assert got.json()["source"] == "sample:checkout_win"


def test_upload_analysis_uses_form_options(client):
    r = client.post(
        "/analyses",
        files={"file": ("exp.csv", CSV, "text/csv")},
        data={"alpha": "0.1", "name": "Banner test"},
    )
    assert r.status_code == 201
    assert r.json()["report"]["alpha"] == 0.1
    assert client.get(f"/analyses/{r.json()['id']}").json()["name"] == "Banner test"


def test_ingest_errors_use_the_envelope(client):
    r = client.post("/analyses", files={"file": ("x.csv", b"user_id,metric\n1,1\n", "text/csv")})
    assert r.status_code == 400 and error(r) == "missing_column"


def test_oversized_upload_is_413(client):
    big = CSV + b"x" * (70 * 1024)
    r = client.post("/analyses", files={"file": ("big.csv", big, "text/csv")})
    assert r.status_code == 413 and error(r) == "too_large"


def test_bad_options_are_422(client):
    r = client.post("/analyses", files={"file": ("e.csv", CSV, "text/csv")}, data={"alpha": "0.5"})
    assert r.status_code == 422 and error(r) == "bad_option"
    assert error(client.post("/power", json={"baseline": 2, "mde": 0.1})) == "bad_option"


def test_unknown_sample_and_unknown_report_are_404(client):
    assert error(client.post("/analyses/samples/nope")) == "unknown_sample"
    assert client.get("/analyses/doesnotexist").status_code == 404


def test_unknown_report_is_404(client):
    r = client.get("/analyses/abcdefghij")
    assert r.status_code == 404 and error(r) == "not_found"


def test_rate_limit_counts_analyses_per_client(client):
    for _ in range(5):
        assert client.post("/analyses/samples/broken_split").status_code == 201
    r = client.post("/analyses/samples/broken_split")
    assert r.status_code == 429 and error(r) == "rate_limited"
    assert int(r.headers["Retry-After"]) > 0
    other = client.post("/analyses/samples/broken_split", headers={"X-Forwarded-For": "9.9.9.9"})
    assert other.status_code == 201


def test_samples_listing_and_download(client):
    names = [s["name"] for s in client.get("/samples").json()]
    assert names == ["checkout_win", "pricing_null", "broken_split"]
    r = client.get("/samples/pricing_null.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert r.text.startswith("user_id,variant,metric")


def test_power_endpoint(client):
    r = client.post("/power", json={"baseline": 0.1, "mde": 0.01})
    assert r.status_code == 200 and r.json()["total"] == 2 * r.json()["n_per_arm"]


def test_cors_allows_only_the_dashboard(client):
    ok = client.get("/samples", headers={"Origin": ORIGIN})
    assert ok.headers.get("access-control-allow-origin") == ORIGIN
    bad = client.get("/samples", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_health_checks(client):
    assert client.get("/healthz").json() == {"ok": True}
    assert client.get("/readyz").json() == {"ok": True, "postgres": True}
