"""Two-sample tests: a two-proportion z-test and Welch's t-test, with delta-method relative lift."""

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

MIN_PER_ARM = 2


@dataclass(frozen=True)
class TestResult:
    __test__ = False  # not a pytest test class

    control_mean: float
    treatment_mean: float
    abs_lift: float
    abs_ci: tuple[float, float]
    rel_lift: float | None
    rel_ci: tuple[float, float] | None
    p_value: float
    stat: float
    se: float


def _check_sizes(control: np.ndarray, treatment: np.ndarray) -> None:
    if control.size < MIN_PER_ARM or treatment.size < MIN_PER_ARM:
        raise ValueError(f"each arm needs at least {MIN_PER_ARM} values")


def _relative(
    mc: float, mt: float, var_mean_c: float, var_mean_t: float, z: float
) -> tuple[float | None, tuple[float, float] | None]:
    """Relative lift mt/mc - 1 with a delta-method interval; undefined when the control mean is 0."""
    if mc == 0:
        return None, None
    rel = mt / mc - 1
    se = math.sqrt(var_mean_t / mc**2 + mt**2 * var_mean_c / mc**4)
    return rel, (rel - z * se, rel + z * se)


def proportion_test(control: np.ndarray, treatment: np.ndarray, alpha: float) -> TestResult:
    """Pooled standard error for the test, unpooled for the interval."""
    _check_sizes(control, treatment)
    nc, nt = control.size, treatment.size
    pc, pt = float(control.mean()), float(treatment.mean())
    diff = pt - pc
    pooled = float(control.sum() + treatment.sum()) / (nc + nt)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / nc + 1 / nt))
    if se_pooled == 0:
        z_stat, p = 0.0, 1.0
    else:
        z_stat = diff / se_pooled
        p = float(2 * stats.norm.sf(abs(z_stat)))
    var_c, var_t = pc * (1 - pc) / nc, pt * (1 - pt) / nt
    se = math.sqrt(var_c + var_t)
    z = float(stats.norm.ppf(1 - alpha / 2))
    rel, rel_ci = _relative(pc, pt, var_c, var_t, z)
    return TestResult(pc, pt, diff, (diff - z * se, diff + z * se), rel, rel_ci, p, z_stat, se)


def welch_test(control: np.ndarray, treatment: np.ndarray, alpha: float) -> TestResult:
    _check_sizes(control, treatment)
    nc, nt = control.size, treatment.size
    mc, mt = float(control.mean()), float(treatment.mean())
    var_c, var_t = float(control.var(ddof=1)) / nc, float(treatment.var(ddof=1)) / nt
    diff = mt - mc
    se = math.sqrt(var_c + var_t)
    if se == 0:
        stat = 0.0 if diff == 0 else math.copysign(math.inf, diff)
        p = 1.0 if diff == 0 else 0.0
        ci = (diff, diff)
    else:
        df = (var_c + var_t) ** 2 / (var_c**2 / (nc - 1) + var_t**2 / (nt - 1))
        stat = diff / se
        p = float(2 * stats.t.sf(abs(stat), df))
        q = float(stats.t.ppf(1 - alpha / 2, df))
        ci = (diff - q * se, diff + q * se)
    z = float(stats.norm.ppf(1 - alpha / 2))
    rel, rel_ci = _relative(mc, mt, var_c, var_t, z)
    return TestResult(mc, mt, diff, ci, rel, rel_ci, p, stat, se)
