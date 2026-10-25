"""Parse and validate an experiment CSV into per-arm numpy arrays."""

import io
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

MAX_ROWS = 1_000_000
REQUIRED = ("user_id", "variant", "metric")
CONTROL_NAMES = ("control", "a", "baseline")
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")

Kind = Literal["binary", "continuous"]


class IngestError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Arm:
    metric: np.ndarray
    pre: np.ndarray | None
    ts: np.ndarray | None


@dataclass(frozen=True)
class Experiment:
    control: str
    treatment: str
    kind: Kind
    c: Arm
    t: Arm

    @property
    def has_pre(self) -> bool:
        return self.c.pre is not None

    @property
    def has_ts(self) -> bool:
        return self.c.ts is not None


def _read(data: bytes, max_bytes: int) -> pd.DataFrame:
    if len(data) > max_bytes:
        raise IngestError("too_large", f"The file is larger than {max_bytes // (1024 * 1024)} MB.")
    if not data.strip():
        raise IngestError("empty", "The file is empty.")
    try:
        df = pd.read_csv(
            io.BytesIO(data), dtype=str, encoding="utf-8-sig", skipinitialspace=True, keep_default_na=False
        )
    except pd.errors.EmptyDataError as e:
        raise IngestError("empty", "The file is empty.") from e
    except (pd.errors.ParserError, UnicodeDecodeError) as e:
        raise IngestError("bad_value", f"The file could not be read as CSV: {e}") from e
    df.columns = [str(c).strip().lower() for c in df.columns]
    if df.empty:
        raise IngestError("empty", "The file has a header but no rows.")
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise IngestError("missing_column", f"Missing required column(s): {', '.join(missing)}.")
    if len(df) > MAX_ROWS:
        raise IngestError("too_large", f"The file has more than {MAX_ROWS:,} rows.")
    return df


def _numbers(df: pd.DataFrame, column: str) -> np.ndarray:
    values = pd.to_numeric(df[column].str.strip(), errors="coerce").to_numpy(dtype=np.float64)
    bad = ~np.isfinite(values)
    if bad.any():
        row = int(np.argmax(bad)) + 1
        raise IngestError("bad_value", f"row {row}: column '{column}' must be a finite number.")
    return values


def _timestamps(df: pd.DataFrame) -> np.ndarray:
    raw = df["timestamp"].str.strip()
    epoch = pd.to_numeric(raw, errors="coerce")
    if epoch.notna().all():
        return epoch.to_numpy(dtype=np.float64)
    parsed = pd.to_datetime(raw, utc=True, format="ISO8601", errors="coerce")
    if parsed.isna().any():
        row = int(np.argmax(parsed.isna().to_numpy())) + 1
        raise IngestError("bad_value", f"row {row}: column 'timestamp' must be ISO-8601 or epoch seconds.")
    return ((parsed - EPOCH) / pd.Timedelta(seconds=1)).to_numpy(dtype=np.float64)


def _variants(labels: pd.Series, control: str | None) -> tuple[pd.Series, str, str, str, str]:
    """Returns per-row keys, then (control key, control name, treatment key, treatment name)."""
    stripped = labels.str.strip()
    keys = stripped.str.lower()
    names: dict[str, str] = {}
    for key, name in zip(keys, stripped, strict=True):
        names.setdefault(key, name)
    if len(names) != 2:
        raise IngestError("variant_count", f"Expected exactly 2 variants, found {len(names)}.")
    if control is not None:
        c_key = control.strip().lower()
        if c_key not in names:
            raise IngestError("bad_value", f"control '{control}' is not one of: {', '.join(names.values())}.")
    else:
        named = [k for k in names if k in CONTROL_NAMES]
        c_key = named[0] if named else sorted(names)[0]
    t_key = next(k for k in names if k != c_key)
    return keys, c_key, names[c_key], t_key, names[t_key]


def parse_csv(data: bytes, control: str | None = None, max_bytes: int = 20 * 1024 * 1024) -> Experiment:
    df = _read(data, max_bytes)
    keys, c_key, c_name, t_key, t_name = _variants(df["variant"], control)
    users = df["user_id"].str.strip()
    duplicates = len(users) - users.nunique()
    if duplicates:
        raise IngestError("duplicate_user", f"{duplicates} user_id value(s) appear more than once.")
    metric = _numbers(df, "metric")
    pre = _numbers(df, "pre_metric") if "pre_metric" in df.columns else None
    ts = _timestamps(df) if "timestamp" in df.columns else None
    in_control = (keys == c_key).to_numpy()

    def arm(mask: np.ndarray) -> Arm:
        return Arm(metric[mask], None if pre is None else pre[mask], None if ts is None else ts[mask])

    kind: Kind = "binary" if np.isin(metric, (0.0, 1.0)).all() else "continuous"
    return Experiment(c_name, t_name, kind, arm(in_control), arm(~in_control))
