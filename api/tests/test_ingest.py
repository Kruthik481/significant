import numpy as np
import pytest

from app.ingest import MAX_ROWS, IngestError, parse_csv


def csv(*rows: str) -> bytes:
    return ("\n".join(rows) + "\n").encode()


BASIC = csv("user_id,variant,metric", "u1,control,0", "u2,control,1", "u3,treatment,1", "u4,treatment,1")


def code_of(data: bytes, **kw) -> str:
    with pytest.raises(IngestError) as e:
        parse_csv(data, **kw)
    return e.value.code


def test_parses_a_binary_experiment():
    exp = parse_csv(BASIC)
    assert (exp.control, exp.treatment, exp.kind) == ("control", "treatment", "binary")
    assert exp.c.metric.tolist() == [0.0, 1.0]
    assert exp.t.metric.tolist() == [1.0, 1.0]
    assert not exp.has_pre and not exp.has_ts


def test_detects_continuous_metrics_and_optional_columns():
    exp = parse_csv(
        csv(
            "user_id,variant,metric,pre_metric,timestamp",
            "1,A,12.5,10,2026-10-01T00:00:00Z",
            "2,B,3.0,2,2026-10-01T01:00:00Z",
            "3,A,7.5,6,2026-10-01T02:00:00Z",
            "4,B,4.0,5,2026-10-01T03:00:00Z",
        )
    )
    assert exp.kind == "continuous"
    assert exp.control == "A"
    assert exp.has_pre and exp.has_ts
    assert exp.t.ts is not None and exp.c.ts is not None
    assert exp.t.ts[0] - exp.c.ts[0] == pytest.approx(3600)


def test_epoch_timestamps_are_accepted():
    exp = parse_csv(
        csv(
            "user_id,variant,metric,timestamp",
            "1,a,1,1700000000",
            "2,b,0,1700000060",
            "3,a,0,1700000001",
            "4,b,1,1700000061",
        )
    )
    assert exp.c.ts is not None and exp.c.ts.tolist() == [1_700_000_000.0, 1_700_000_001.0]


def test_parses_bom_crlf_quotes_and_extra_columns():
    raw = '﻿user_id,variant,metric,country\r\n"u1","control","1","IN"\r\n"u2","treatment","0","US"\r\n'
    raw += '"u3","control","0","IN"\r\n"u4","treatment","1","US"\r\n'
    exp = parse_csv(raw.encode())
    assert exp.c.metric.tolist() == [1.0, 0.0]


def test_variant_labels_are_trimmed():
    exp = parse_csv(csv("user_id,variant,metric", "1,Control ,1", "2,control,0", "3,new,1", "4,new,0"))
    assert exp.control == "Control"
    assert exp.c.metric.size == 2


def test_explicit_control_wins_and_falls_back_to_alphabetical():
    data = csv("user_id,variant,metric", "1,zeta,1", "2,beta,0", "3,zeta,0", "4,beta,1")
    assert parse_csv(data).control == "beta"
    assert parse_csv(data, control="ZETA").control == "zeta"
    assert code_of(data, control="gamma") == "bad_value"


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"", "empty"),
        (csv("user_id,variant,metric"), "empty"),
        (csv("user_id,metric", "1,1"), "missing_column"),
        (csv("user_id,variant,metric", "1,a,1", "2,a,0"), "variant_count"),
        (csv("user_id,variant,metric", "1,a,1", "2,b,0", "3,c,1"), "variant_count"),
        (csv("user_id,variant,metric", "1,a,1", "1,b,0"), "duplicate_user"),
        (csv("user_id,variant,metric", "1,a,1", "2,b,yes"), "bad_value"),
        (csv("user_id,variant,metric", "1,a,1", "2,b,inf"), "bad_value"),
        (csv("user_id,variant,metric,pre_metric", "1,a,1,", "2,b,0,3"), "bad_value"),
        (csv("user_id,variant,metric,timestamp", "1,a,1,soon", "2,b,0,2026-01-01"), "bad_value"),
    ],
)
def test_rejects_invalid_files(data, code):
    assert code_of(data) == code


def test_bad_value_message_names_row_and_column():
    with pytest.raises(IngestError) as e:
        parse_csv(csv("user_id,variant,metric", "1,a,1", "2,b,oops"))
    assert "row 2" in e.value.message and "metric" in e.value.message


def test_size_and_row_caps(monkeypatch):
    assert code_of(BASIC, max_bytes=10) == "too_large"
    monkeypatch.setattr("app.ingest.MAX_ROWS", 3)
    assert code_of(BASIC) == "too_large"
    assert MAX_ROWS == 1_000_000


def test_arrays_are_float64():
    exp = parse_csv(BASIC)
    assert exp.c.metric.dtype == np.float64


def test_each_variant_needs_two_users():
    data = csv("user_id,variant,metric", "1,a,1", "2,b,0", "3,b,1")
    with pytest.raises(IngestError) as e:
        parse_csv(data)
    assert e.value.code == "bad_value" and "at least 2 users" in e.value.message


def test_a_million_rows_fit_in_a_small_container():
    import tracemalloc

    from app.analysis import AnalysisOptions, analyze

    rng = np.random.default_rng(0)
    rows = [
        f"user_{i:07d},{'control' if i % 2 else 'treatment'},{m:.4f},{p:.4f},{1760000000 + i}"
        for i, m, p in zip(
            range(MAX_ROWS), rng.normal(10, 2, MAX_ROWS), rng.normal(10, 2, MAX_ROWS), strict=True
        )
    ]
    data = csv("user_id,variant,metric,pre_metric,timestamp", *rows)
    del rows
    tracemalloc.start()
    try:
        analyze(parse_csv(data, max_bytes=len(data)), AnalysisOptions())
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    # Render's free plan has 512 MB for the whole process; this traced peak measured ~330 MB RSS in Docker
    assert peak < 200 * 1024 * 1024
