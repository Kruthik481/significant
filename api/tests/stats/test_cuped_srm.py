import numpy as np
import pytest
from scipy import stats as sps

from app.stats.cuped import cuped
from app.stats.srm import srm
from app.stats.tests import welch_test


def test_cuped_theta_and_adjusted_means():
    xc, yc = np.array([1.0, 2.0, 3.0]), np.array([2.0, 4.1, 5.9])
    xt, yt = np.array([4.0, 5.0, 6.0]), np.array([8.2, 9.8, 12.1])
    x, y = np.concatenate([xc, xt]), np.concatenate([yc, yt])
    theta = np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1)
    res = cuped(yc, xc, yt, xt, alpha=0.05)
    assert res is not None
    assert res.theta == pytest.approx(theta)
    assert res.result.control_mean == pytest.approx((yc - theta * (xc - x.mean())).mean())
    assert res.result.treatment_mean == pytest.approx((yt - theta * (xt - x.mean())).mean())


def test_cuped_narrows_the_interval_with_a_correlated_covariate():
    rng = np.random.default_rng(3)
    xc, xt = rng.normal(50, 10, 2000), rng.normal(50, 10, 2000)
    yc = xc + rng.normal(0, 3, 2000)
    yt = xt + 1 + rng.normal(0, 3, 2000)
    res = cuped(yc, xc, yt, xt, alpha=0.05)
    raw = welch_test(yc, yt, alpha=0.05)
    assert res is not None
    assert res.variance_reduction > 0.8
    assert (res.result.abs_ci[1] - res.result.abs_ci[0]) < (raw.abs_ci[1] - raw.abs_ci[0]) / 2
    assert res.result.abs_lift == pytest.approx(1, abs=0.2)


def test_cuped_is_skipped_for_a_constant_covariate():
    assert cuped(np.array([1.0, 2.0]), np.ones(2), np.array([2.0, 3.0]), np.ones(2), 0.05) is None


def test_srm_matches_scipy_and_flags_a_broken_split():
    r = srm(5000, 4600)
    assert r.p_value == pytest.approx(sps.chisquare([5000, 4600]).pvalue)
    assert r.flagged
    assert r.observed_split == pytest.approx(5000 / 9600)


def test_srm_passes_a_healthy_split_and_respects_the_expected_ratio():
    assert not srm(5010, 4990).flagged
    assert not srm(6000, 4000, expected_split=0.6).flagged


@pytest.mark.parametrize("split", [0.0, 1.0, -0.2, 1.5])
def test_srm_rejects_impossible_splits(split):
    with pytest.raises(ValueError):
        srm(10, 10, expected_split=split)
