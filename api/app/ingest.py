"""Parse and validate an experiment CSV into per-arm numpy arrays."""

import io
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

MAX_ROWS = 1_000_000
REQUIRED = ("user_id", "variant", "metric")
COLUMNS = (*REQUIRED, "pre_metric", "timestamp")
TEXT = {"user_id": "str", "variant": "category"}
MIN_ARM = 2
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
        header = pd.read_csv(io.BytesIO(data), nrows=0, encoding="utf-8-sig", skipinitialspace=True).columns
        names = {raw: str(raw).strip().lower() for raw in header}
        # only the columns we use, with numbers read natively: all-string frames blow past 512 MB at 1M rows
        df = pd.read_csv(
            io.BytesIO(data),
            usecols=[raw for raw, name in names.items() if name in COLUMNS],
            dtype={raw: TEXT[name] for raw, name in names.items() if name in TEXT},
            index_col=False,
            encoding="utf-8-sig",
            skipinitialspace=True,
            keep_default_na=False,
        )
    except pd.errors.EmptyDataError as e:
        raise IngestError("empty", "The file is empty.") from e
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as e:
        raise IngestError("bad_value", f"The file could not be read as CSV: {e}") from e
    df.columns = [names[c] for c in df.columns]
    if df.empty:
        raise IngestError("empty", "The file has a header but no rows.")
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise IngestError("missing_column", f"Missing required column(s): {', '.join(missing)}.")
    if len(df) > MAX_ROWS:
        raise IngestError("too_large", f"The file has more than {MAX_ROWS:,} rows.")
    return df


def _native(column: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(column) and not pd.api.types.is_bool_dtype(column)


def _numbers(df: pd.DataFrame, column: str) -> np.ndarray:
    raw = df[column]
    if _native(raw):
        values = raw.to_numpy(dtype=np.float64)
    else:
        values = pd.to_numeric(raw.astype(str).str.strip(), errors="coerce").to_numpy(dtype=np.float64)
    bad = ~np.isfinite(values)
    if bad.any():
        row = int(np.argmax(bad)) + 1
        raise IngestError("bad_value", f"row {row}: column '{column}' must be a finite number.")
    return values


def _timestamps(df: pd.DataFrame) -> np.ndarray:
    if _native(df["timestamp"]):
        return df["timestamp"].to_numpy(dtype=np.float64)
    raw = df["timestamp"].astype(str).str.strip()
    epoch = pd.to_numeric(raw, errors="coerce")
    if epoch.notna().all():
        return epoch.to_numpy(dtype=np.float64)
    parsed = pd.to_datetime(raw, utc=True, format="ISO8601", errors="coerce")
    if parsed.isna().any():
        row = int(np.argmax(parsed.isna().to_numpy())) + 1
        raise IngestError("bad_value", f"row {row}: column 'timestamp' must be ISO-8601 or epoch seconds.")
    return ((parsed - EPOCH) / pd.Timedelta(seconds=1)).to_numpy(dtype=np.float64)


def _variants(labels: pd.Series, control: str | None) -> tuple[np.ndarray, str, str]:
    """Returns the per-row control mask, then the control and treatment names."""
    stripped = [str(c).strip() for c in labels.cat.categories]
    keys = [c.lower() for c in stripped]
    codes = labels.cat.codes.to_numpy()
    names: dict[str, str] = {}
    for code in map(int, pd.unique(codes)):  # first-seen order, so the first spelling of a label names it
        names.setdefault(keys[code], stripped[code])
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
    in_control = np.isin(codes, [i for i, k in enumerate(keys) if k == c_key])
    return in_control, names[c_key], names[t_key]


def parse_csv(data: bytes, control: str | None = None, max_bytes: int = 20 * 1024 * 1024) -> Experiment:
    df = _read(data, max_bytes)
    in_control, c_name, t_name = _variants(df["variant"], control)
    users = df["user_id"].str.strip()
    duplicates = len(users) - users.nunique()
    if duplicates:
        raise IngestError("duplicate_user", f"{duplicates} user_id value(s) appear more than once.")
    metric = _numbers(df, "metric")
    pre = _numbers(df, "pre_metric") if "pre_metric" in df.columns else None
    ts = _timestamps(df) if "timestamp" in df.columns else None
    if min(in_control.sum(), (~in_control).sum()) < MIN_ARM:
        raise IngestError("bad_value", f"Each variant needs at least {MIN_ARM} users.")

    def arm(mask: np.ndarray) -> Arm:
        return Arm(metric[mask], None if pre is None else pre[mask], None if ts is None else ts[mask])

    kind: Kind = "binary" if np.isin(metric, (0.0, 1.0)).all() else "continuous"
    return Experiment(c_name, t_name, kind, arm(in_control), arm(~in_control))
