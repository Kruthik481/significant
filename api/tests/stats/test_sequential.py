import math

import numpy as np
import pytest

from app.stats.sequential import MIN_PER_ARM, cs_halfwidth, mixture_p_value, msprt


def test_mixture_p_value_closed_form():
    delta, v, tau2 = 0.3, 0.01, 0.04
    lam = math.sqrt(v / (v + tau2)) * math.exp(delta**2 * tau2 / (2 * v * (v + tau2)))
    assert mixture_p_value(delta, v, tau2) == pytest.approx(min(1.0, 1 / lam))
    assert mixture_p_value(0.0, v, tau2) == 1.0


def test_confidence_sequence_widens_as_alpha_shrinks():
    assert cs_halfwidth(0.01, 0.04, 0.01) > cs_halfwidth(0.01, 0.04, 0.05) > 0


def _stream(rng, n, effect):
    treated = rng.random(n) < 0.5
    values = rng.normal(0, 1, n) + effect * treated
    return values, treated, np.arange(n, dtype=float)


def test_checkpoints_are_increasing_bounded_and_end_at_n():
    rng = np.random.default_rng(1)
    v, tr, order = _stream(rng, 10_000, 0.0)
    res = msprt(v, tr, order, alpha=0.05)
    assert res is not None
    ns = [p.n for p in res.points]
    assert len(ns) <= 50
    assert ns == sorted(set(ns))
    assert ns[-1] == 10_000


def test_p_values_never_increase_and_intervals_only_narrow():
    rng = np.random.default_rng(2)
    v, tr, order = _stream(rng, 6000, 0.05)
    res = msprt(v, tr, order, alpha=0.05)
    assert res is not None
    ps = [p.p_value for p in res.points]
    assert all(b <= a for a, b in zip(ps, ps[1:], strict=False))
    lows = [p.ci_low for p in res.points]
    highs = [p.ci_high for p in res.points]
    assert all(b >= a for a, b in zip(lows, lows[1:], strict=False))
    assert all(b <= a for a, b in zip(highs, highs[1:], strict=False))


def test_detects_a_real_effect_and_reports_where_it_stopped():
    rng = np.random.default_rng(3)
    n = 40_000
    treated = rng.random(n) < 0.5
    values = (rng.random(n) < np.where(treated, 0.13, 0.10)).astype(float)
    res = msprt(values, treated, np.arange(n, dtype=float), alpha=0.05)
    assert res is not None
    assert res.stopped_at is not None and res.stopped_at < n
    assert res.points[-1].p_value < 0.05


def test_order_column_controls_the_sequence():
    treated = np.array([True, False] * 300)
    values = np.where(treated, 1.0, 0.0) + np.linspace(0, 1, 600)
    shuffled = np.random.default_rng(4).permutation(600).astype(float)
    a = msprt(values, treated, np.arange(600, dtype=float), alpha=0.05)
    b = msprt(values, treated, shuffled, alpha=0.05)
    assert a is not None and b is not None
    assert a.points[0].ci_low != b.points[0].ci_low


def test_too_few_units_per_arm_skips_the_test():
    treated = np.array([True] * (MIN_PER_ARM - 1) + [False] * 500)
    ramp = np.arange(treated.size, dtype=float)
    assert msprt(ramp, treated, ramp, 0.05) is None


@pytest.mark.slow
def test_peeking_at_every_checkpoint_keeps_the_false_positive_rate():
    rng = np.random.default_rng(2027)
    hits = 0
    for _ in range(500):
        v, tr, order = _stream(rng, 4000, 0.0)
        res = msprt(v, tr, order, alpha=0.05)
        assert res is not None
        hits += res.stopped_at is not None
    assert hits / 500 <= 0.07


def test_a_huge_mean_offset_does_not_change_the_result():
    rng = np.random.default_rng(5)
    n = 20_000
    treated = rng.random(n) < 0.5
    values = rng.normal(np.where(treated, 10.1, 10.0), 2.0)
    order = np.arange(n, dtype=float)
    base = msprt(values, treated, order, alpha=0.05)
    shifted = msprt(values + 1e9, treated, order, alpha=0.05)
    assert base is not None and shifted is not None
    assert shifted.tau == pytest.approx(base.tau, rel=1e-6)
    assert [p.p_value for p in shifted.points] == pytest.approx([p.p_value for p in base.points], rel=1e-6)
