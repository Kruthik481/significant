import numpy as np
import pytest
from scipy import stats as sps
from statsmodels.stats.proportion import proportions_ztest

from app.stats.tests import proportion_test, welch_test

Z975 = 1.959963984540054


def test_proportion_test_matches_statsmodels():
    rng = np.random.default_rng(7)
    c = (rng.random(8000) < 0.10).astype(float)
    t = (rng.random(8200) < 0.11).astype(float)
    r = proportion_test(c, t, alpha=0.05)
    z, p = proportions_ztest([t.sum(), c.sum()], [t.size, c.size])
    assert r.stat == pytest.approx(z, rel=1e-9)
    assert r.p_value == pytest.approx(p, rel=1e-9)
    assert r.abs_lift == pytest.approx(t.mean() - c.mean())


def test_proportion_ci_uses_unpooled_standard_error():
    c = np.array([1.0] * 100 + [0.0] * 900)
    t = np.array([1.0] * 150 + [0.0] * 850)
    r = proportion_test(c, t, alpha=0.05)
    se = np.sqrt(0.1 * 0.9 / 1000 + 0.15 * 0.85 / 1000)
    assert r.abs_ci == pytest.approx((0.05 - Z975 * se, 0.05 + Z975 * se))
    assert r.se == pytest.approx(se)


def test_welch_matches_scipy():
    rng = np.random.default_rng(11)
    c = rng.normal(10, 3, 500)
    t = rng.normal(10.6, 4, 700)
    r = welch_test(c, t, alpha=0.05)
    ref = sps.ttest_ind(t, c, equal_var=False)
    ci = ref.confidence_interval(0.95)
    assert r.stat == pytest.approx(ref.statistic, rel=1e-9)
    assert r.p_value == pytest.approx(ref.pvalue, rel=1e-9)
    assert r.abs_ci == pytest.approx((ci.low, ci.high), rel=1e-9)


def test_relative_lift_uses_the_delta_method():
    c = np.array([8.0, 10.0, 12.0, 10.0])
    t = np.array([11.0, 13.0, 12.0, 12.0])
    r = welch_test(c, t, alpha=0.05)
    mc, mt = c.mean(), t.mean()
    var = t.var(ddof=1) / t.size / mc**2 + mt**2 * c.var(ddof=1) / c.size / mc**4
    assert r.rel_lift == pytest.approx(mt / mc - 1)
    assert r.rel_ci == pytest.approx((mt / mc - 1 - Z975 * np.sqrt(var), mt / mc - 1 + Z975 * np.sqrt(var)))


def test_relative_lift_is_undefined_when_control_mean_is_zero():
    r = welch_test(np.zeros(5), np.array([1.0, 2.0, 0.0, 1.0, 1.0]), alpha=0.05)
    assert r.rel_lift is None
    assert r.rel_ci is None


def test_identical_constant_arms_are_not_significant():
    r = welch_test(np.ones(10), np.ones(10), alpha=0.05)
    assert r.p_value == 1.0
    p = proportion_test(np.zeros(10), np.zeros(10), alpha=0.05)
    assert p.p_value == 1.0


def test_each_arm_needs_two_values():
    with pytest.raises(ValueError):
        welch_test(np.array([1.0]), np.array([1.0, 2.0]), alpha=0.05)


@pytest.mark.slow
def test_aa_false_positive_rate_is_close_to_alpha():
    rng = np.random.default_rng(2026)
    hits = 0
    for _ in range(2000):
        c = (rng.random(2000) < 0.1).astype(float)
        t = (rng.random(2000) < 0.1).astype(float)
        hits += proportion_test(c, t, 0.05).p_value < 0.05
    assert 0.035 <= hits / 2000 <= 0.065


@pytest.mark.slow
def test_confidence_intervals_cover_the_truth():
    rng = np.random.default_rng(99)
    abs_cover = rel_cover = 0
    for _ in range(2000):
        c = rng.normal(10, 2, 400)
        t = rng.normal(10.5, 2, 400)
        r = welch_test(c, t, 0.05)
        abs_cover += r.abs_ci[0] <= 0.5 <= r.abs_ci[1]
        assert r.rel_ci is not None
        rel_cover += r.rel_ci[0] <= 0.05 <= r.rel_ci[1]
    assert 0.93 <= abs_cover / 2000 <= 0.97
    assert 0.93 <= rel_cover / 2000 <= 0.97
