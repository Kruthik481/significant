"""CUPED: remove the part of the metric explained by a pre-experiment covariate (Deng et al., 2013)."""

from dataclasses import dataclass

import numpy as np

from app.stats.tests import TestResult, welch_test


@dataclass(frozen=True)
class CupedResult:
    theta: float
    variance_reduction: float
    result: TestResult


def cuped(yc: np.ndarray, xc: np.ndarray, yt: np.ndarray, xt: np.ndarray, alpha: float) -> CupedResult | None:
    """Adjust with one pooled theta so both arms shift by the same rule; None when x carries no signal."""
    x = np.concatenate([xc, xt])
    y = np.concatenate([yc, yt])
    var_x = float(x.var(ddof=1))
    if var_x == 0:
        return None
    theta = float(np.cov(x, y, ddof=1)[0, 1]) / var_x
    x_mean = float(x.mean())
    adj_c = yc - theta * (xc - x_mean)
    adj_t = yt - theta * (xt - x_mean)
    var_y = float(y.var(ddof=1))
    var_adj = float(np.concatenate([adj_c, adj_t]).var(ddof=1))
    reduction = 1 - var_adj / var_y if var_y > 0 else 0.0
    return CupedResult(theta, reduction, welch_test(adj_c, adj_t, alpha))
