"""Always-valid sequential testing: the normal-mixture mSPRT (Johari et al., 2017).

Peeking at a fixed-horizon p-value inflates false positives; the mixture likelihood ratio below stays
valid at every look, so an experiment can be stopped as soon as its p-value drops under alpha.
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

MIN_PER_ARM = 100
MAX_CHECKPOINTS = 50
DEFAULT_POWER = 0.8


@dataclass(frozen=True)
class Checkpoint:
    n: int
    p_value: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True)
class SequentialResult:
    tau: float
    points: list[Checkpoint]
    stopped_at: int | None


def mixture_p_value(delta: float, v: float, tau2: float) -> float:
    """1 / Lambda for a N(0, tau2) mixture over the effect, given the estimate delta with variance v."""
    log_lr = 0.5 * math.log(v / (v + tau2)) + delta**2 * tau2 / (2 * v * (v + tau2))
    return 1.0 if log_lr <= 0 else min(1.0, math.exp(-log_lr))


def cs_halfwidth(v: float, tau2: float, alpha: float) -> float:
    """Half-width of the confidence sequence: the effects whose mixture ratio stays below 1/alpha."""
    return math.sqrt((v * (v + tau2) / tau2) * (2 * math.log(1 / alpha) + math.log((v + tau2) / v)))


def _prefix_sizes(total: int, checkpoints: int) -> list[int]:
    return sorted({math.ceil(total * i / checkpoints) for i in range(1, checkpoints + 1)})


def _prefix_stats(values: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Running count, mean and sample variance of one arm along the ordered stream."""
    count = np.cumsum(mask)
    total = np.cumsum(np.where(mask, values, 0.0))
    total_sq = np.cumsum(np.where(mask, values**2, 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = total / count
        var = np.maximum(total_sq - count * mean**2, 0.0) / (count - 1)
    return count, mean, var


def msprt(
    values: np.ndarray,
    treated: np.ndarray,
    order: np.ndarray,
    alpha: float,
    tau: float | None = None,
    checkpoints: int = MAX_CHECKPOINTS,
) -> SequentialResult | None:
    idx = np.argsort(order, kind="stable")
    v, t = values[idx].astype(float), treated[idx].astype(bool)
    v = (
        v - v.mean()
    )  # running sums of squares cancel catastrophically at a large mean; shifts leave delta alone
    n_t, mean_t, var_t = _prefix_stats(v, t)
    n_c, mean_c, var_c = _prefix_stats(v, ~t)
    sizes = [k for k in _prefix_sizes(v.size, checkpoints) if min(n_t[k - 1], n_c[k - 1]) >= MIN_PER_ARM]
    if not sizes or sizes[-1] != v.size:
        return None

    def variance(k: int) -> float:
        i = k - 1
        return float(var_t[i] / n_t[i] + var_c[i] / n_c[i])

    if tau is None:
        v_final = variance(v.size)
        if v_final == 0:
            return None
        z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(DEFAULT_POWER)
        tau = float(z * math.sqrt(v_final))
    tau2 = tau**2

    points: list[Checkpoint] = []
    best_p, low, high = 1.0, -math.inf, math.inf
    stopped_at: int | None = None
    for k in sizes:
        delta = float(mean_t[k - 1] - mean_c[k - 1])
        var = variance(k)
        if var == 0:
            p, half = (1.0 if delta == 0 else 0.0), 0.0
        else:
            p, half = mixture_p_value(delta, var, tau2), cs_halfwidth(var, tau2, alpha)
        best_p = min(best_p, p)
        low, high = max(low, delta - half), min(high, delta + half)
        points.append(Checkpoint(k, best_p, low, high))
        if stopped_at is None and best_p < alpha:
            stopped_at = k
    return SequentialResult(tau, points, stopped_at)
