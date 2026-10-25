import pytest

from app.settings import Settings


def test_defaults_applied():
    s = Settings.from_env({"DATABASE_URL": "postgresql://x", "WEB_ORIGIN": "http://localhost:3300"})
    assert s.port == 8300
    assert s.rate_limit_per_hour == 20
    assert s.max_upload_bytes == 20 * 1024 * 1024
    assert s.db_schema is None


def test_missing_required_variables_are_all_named():
    with pytest.raises(ValueError) as e:
        Settings.from_env({})
    assert "DATABASE_URL" in str(e.value)
    assert "WEB_ORIGIN" in str(e.value)


@pytest.mark.parametrize("name", ["PORT", "RATE_LIMIT_PER_HOUR", "MAX_UPLOAD_BYTES"])
def test_numbers_must_be_positive_integers(name):
    env = {"DATABASE_URL": "postgresql://x", "WEB_ORIGIN": "http://w", name: "0"}
    with pytest.raises(ValueError, match=name):
        Settings.from_env(env)
