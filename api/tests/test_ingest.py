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
        )
    )
    assert exp.kind == "continuous"
    assert exp.control == "A"
    assert exp.has_pre and exp.has_ts
    assert exp.t.ts is not None and exp.c.ts is not None
    assert exp.t.ts[0] - exp.c.ts[0] == pytest.approx(3600)


def test_epoch_timestamps_are_accepted():
    exp = parse_csv(csv("user_id,variant,metric,timestamp", "1,a,1,1700000000", "2,b,0,1700000060"))
    assert exp.c.ts is not None and exp.c.ts.tolist() == [1_700_000_000.0]


def test_parses_bom_crlf_quotes_and_extra_columns():
    raw = '﻿user_id,variant,metric,country\r\n"u1","control","1","IN"\r\n"u2","treatment","0","US"\r\n'
    exp = parse_csv(raw.encode())
    assert exp.c.metric.tolist() == [1.0]


def test_variant_labels_are_trimmed():
    exp = parse_csv(csv("user_id,variant,metric", "1,Control ,1", "2,control,0", "3,new,1"))
    assert exp.control == "Control"
    assert exp.c.metric.size == 2


def test_explicit_control_wins_and_falls_back_to_alphabetical():
    data = csv("user_id,variant,metric", "1,zeta,1", "2,beta,0")
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
