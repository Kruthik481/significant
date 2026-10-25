"""Sample size per arm for a two-sided test, and its inverse, the minimum detectable effect."""

import math
from typing import Literal

from scipy import optimize, stats

Kind = Literal["binary", "continuous"]
_EPS = 1e-9


def _check(baseline: float, alpha: float, power: float, kind: Kind, sd: float | None) -> None:
    if not 0 < alpha < 0.5:
        raise ValueError("alpha must be between 0 and 0.5")
    if not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")
    if kind == "binary" and not 0 < baseline < 1:
        raise ValueError("a binary baseline must be a rate between 0 and 1")
    if kind == "continuous" and (sd is None or sd <= 0):
        raise ValueError("a continuous metric needs a positive standard deviation (sd)")


def _raw_n(baseline: float, mde: float, alpha: float, power: float, kind: Kind, sd: float | None) -> float:
    za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    if kind == "continuous":
        assert sd is not None
        return float(2 * (za + zb) ** 2 * sd**2 / mde**2)
    p1, p2 = baseline, baseline + mde
    pbar = (p1 + p2) / 2
    spread = za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return float(spread**2 / mde**2)


def sample_size(
    baseline: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.8,
    kind: Kind = "binary",
    sd: float | None = None,
) -> int:
    """Users needed per arm to detect an absolute change of `mde` from `baseline`."""
    _check(baseline, alpha, power, kind, sd)
    if mde <= 0:
        raise ValueError("mde must be positive")
    if kind == "binary" and baseline + mde >= 1:
        raise ValueError("baseline + mde must stay below 1 for a rate")
    return math.ceil(_raw_n(baseline, mde, alpha, power, kind, sd))


def mde_for(
    n: int,
    baseline: float,
    alpha: float = 0.05,
    power: float = 0.8,
    kind: Kind = "binary",
    sd: float | None = None,
) -> float:
    """Smallest absolute effect detectable with `n` users per arm."""
    _check(baseline, alpha, power, kind, sd)
    if n < 2:
        raise ValueError("n must be at least 2 per arm")
    if kind == "continuous":
        assert sd is not None
        za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
        return float((za + zb) * sd * math.sqrt(2 / n))
    return float(
        optimize.brentq(lambda m: _raw_n(baseline, m, alpha, power, kind, sd) - n, _EPS, 1 - baseline - _EPS)
    )
