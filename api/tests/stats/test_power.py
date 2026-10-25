import math

import pytest
from scipy.stats import norm
from statsmodels.stats.power import NormalIndPower

from app.stats.power import mde_for, sample_size


def test_continuous_matches_statsmodels():
    ref = NormalIndPower().solve_power(effect_size=0.5 / 2, alpha=0.05, power=0.8, ratio=1)
    assert sample_size(10, 0.5, kind="continuous", sd=2) == math.ceil(ref)


def test_binary_closed_form():
    p1, p2 = 0.10, 0.11
    pb = (p1 + p2) / 2
    za, zb = norm.ppf(0.975), norm.ppf(0.8)
    expected = math.ceil(
        (za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / 0.01**2
    )
    assert sample_size(0.10, 0.01) == expected


@pytest.mark.parametrize(
    ("kind", "baseline", "mde", "sd"), [("binary", 0.1, 0.01, None), ("continuous", 10, 0.5, 2.0)]
)
def test_mde_for_inverts_sample_size(kind, baseline, mde, sd):
    n = sample_size(baseline, mde, kind=kind, sd=sd)
    found = mde_for(n, baseline, kind=kind, sd=sd)
    assert found <= mde
    assert found == pytest.approx(mde, rel=0.02)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"baseline": 0.1, "mde": 0},
        {"baseline": 1.2, "mde": 0.01},
        {"baseline": 0.95, "mde": 0.1},
        {"baseline": 0.1, "mde": 0.01, "alpha": 0.7},
        {"baseline": 0.1, "mde": 0.01, "power": 1.0},
        {"baseline": 10, "mde": 1, "kind": "continuous"},
    ],
)
def test_rejects_bad_inputs(kwargs):
    with pytest.raises(ValueError):
        sample_size(**kwargs)


def test_mde_for_needs_at_least_two_per_arm():
    with pytest.raises(ValueError):
        mde_for(1, 0.1)
