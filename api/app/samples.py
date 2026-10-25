"""Three synthetic experiments with known ground truth, so visitors can try the tool without data."""

from dataclasses import dataclass
from functools import cache

import numpy as np
import pandas as pd

START = pd.Timestamp("2026-09-01T00:00:00Z")
DAYS = 14


@dataclass(frozen=True)
class SampleInfo:
    name: str
    title: str
    description: str
    truth: str


SAMPLES: dict[str, SampleInfo] = {
    s.name: s
    for s in (
        SampleInfo(
            "checkout_win",
            "Checkout redesign",
            "Conversion rate, 40,000 users. The new checkout lifts conversion by about 10% relative.",
            "significant_win",
        ),
        SampleInfo(
            "pricing_null",
            "Pricing page copy",
            "Revenue per user, 20,000 users, with last month's revenue as a covariate. No real effect.",
            "not_significant",
        ),
        SampleInfo(
            "broken_split",
            "Onboarding email",
            "Conversion rate. A logging bug silently dropped about 6% of treatment users.",
            "srm_invalid",
        ),
    )
}


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return np.asarray(1 / (1 + np.exp(-x)))


def _frame(
    rng: np.random.Generator, variant: np.ndarray, metric: np.ndarray, pre: np.ndarray | None
) -> bytes:
    seconds = rng.uniform(0, DAYS * 86_400, variant.size)
    columns: dict[str, object] = {"variant": variant, "metric": metric}
    if pre is not None:
        columns["pre_metric"] = pre
    df = pd.DataFrame(columns)
    df["timestamp"] = (START + pd.to_timedelta(seconds, unit="s")).strftime("%Y-%m-%dT%H:%M:%SZ")
    df = df.iloc[np.argsort(seconds, kind="stable")].reset_index(drop=True)
    df.insert(0, "user_id", [f"u{i:06d}" for i in range(len(df))])
    return df.to_csv(index=False).encode()


def _checkout_win(rng: np.random.Generator) -> bytes:
    n = 20_000
    variant = np.repeat(np.array(["control", "treatment"]), n)
    z = rng.normal(0, 1, 2 * n)
    p = _sigmoid(np.log(0.10 / 0.90) + 0.9 * z)
    p = np.where(variant == "treatment", np.minimum(p * 1.10, 1.0), p)
    metric = (rng.random(2 * n) < p).astype(int)
    pre = rng.poisson(np.exp(0.3 + 0.6 * z))
    return _frame(rng, variant, metric, pre)


def _pricing_null(rng: np.random.Generator) -> bytes:
    n = 10_000
    variant = np.repeat(np.array(["control", "treatment"]), n)
    z = rng.normal(0, 1, 2 * n)
    metric = np.round(np.exp(3 + 0.8 * z + rng.normal(0, 0.45, 2 * n)), 2)
    pre = np.round(np.exp(3 + 0.8 * z + rng.normal(0, 0.45, 2 * n)), 2)
    return _frame(rng, variant, metric, pre)


def _broken_split(rng: np.random.Generator) -> bytes:
    n = 10_000
    variant = np.repeat(np.array(["control", "treatment"]), n)
    metric = (rng.random(2 * n) < 0.10).astype(int)
    kept = (variant == "control") | (rng.random(2 * n) >= 0.06)
    return _frame(rng, variant[kept], metric[kept], None)


_BUILDERS = {
    "checkout_win": (_checkout_win, 11),
    "pricing_null": (_pricing_null, 12),
    "broken_split": (_broken_split, 13),
}


@cache
def sample_csv(name: str) -> bytes:
    builder, seed = _BUILDERS[name]
    return builder(np.random.default_rng(seed))
