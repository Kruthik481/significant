import json

import numpy as np
import pytest

from app.analysis import AnalysisOptions, analyze
from app.ingest import Arm, Experiment


def exp(c, t, kind="continuous", pre=None, ts=None):
    pc, pt = pre if pre is not None else (None, None)
    tc, tt = ts if ts is not None else (None, None)
    c_arm = Arm(np.asarray(c, float), pc, tc)
    t_arm = Arm(np.asarray(t, float), pt, tt)
    return Experiment("control", "treatment", kind, c_arm, t_arm)


def test_win_loss_and_null_verdicts():
    rng = np.random.default_rng(5)
    base = rng.normal(10, 1, 3000)
    assert analyze(exp(base, base + 0.5), AnalysisOptions()).verdict == "significant_win"
    assert analyze(exp(base, base - 0.5), AnalysisOptions()).verdict == "significant_loss"
    assert analyze(exp(base, rng.permutation(base)), AnalysisOptions()).verdict == "not_significant"


def test_srm_overrides_a_significant_result():
    rng = np.random.default_rng(6)
    r = analyze(exp(rng.normal(10, 1, 5000), rng.normal(11, 1, 4400)), AnalysisOptions())
    assert r.srm.flagged
    assert r.verdict == "srm_invalid"


def test_cuped_becomes_primary_when_pre_metric_is_present():
    rng = np.random.default_rng(7)
    xc, xt = rng.normal(50, 10, 2000), rng.normal(50, 10, 2000)
    yc, yt = xc + rng.normal(0, 2, 2000), xt + rng.normal(0, 2, 2000)
    r = analyze(exp(yc, yt, pre=(xc, xt)), AnalysisOptions())
    assert r.primary == "cuped"
    assert r.cuped is not None
    assert r.cuped.variance_reduction is not None and r.cuped.variance_reduction > 0.9


def test_binary_without_extras_uses_proportions_and_skips_optional_parts():
    c = [1.0] * 100 + [0.0] * 900
    t = [1.0] * 130 + [0.0] * 870
    r = analyze(exp(c, t, kind="binary"), AnalysisOptions())
    assert r.primary == "raw" and r.cuped is None and r.sequential is None
    assert r.summary.control_mean == pytest.approx(0.1)


def test_small_experiment_skips_sequential():
    ts = (np.arange(20, dtype=float), np.arange(20, dtype=float))
    r = analyze(exp(np.arange(20.0), np.arange(20.0) + 1, ts=ts), AnalysisOptions())
    assert r.sequential is None
    assert r.raw.p_value is not None


def test_degenerate_data_serialises_without_nan():
    r = analyze(exp(np.zeros(10), np.ones(10)), AnalysisOptions())
    payload = json.dumps(r.model_dump(mode="json"), allow_nan=False)
    assert '"rel_lift": null' in payload


@pytest.mark.parametrize(
    "kwargs",
    [
        {"alpha": 0.5},
        {"alpha": 0.0001},
        {"expected_split": 1.0},
        {"tau": -1.0},
        {"tau": 1e-200},
        {"tau": 1e200},
        {"tau": float("inf")},
        {"tau": float("nan")},
    ],
)
def test_options_are_validated(kwargs):
    with pytest.raises(ValueError):
        AnalysisOptions(**kwargs)


def test_sequential_discloses_whether_tau_came_from_the_data():
    from app.ingest import parse_csv
    from app.samples import sample_csv

    exp = parse_csv(sample_csv("checkout_win"))
    default = analyze(exp, AnalysisOptions()).sequential
    fixed = analyze(exp, AnalysisOptions(tau=0.01)).sequential
    assert default is not None and default.tau_from_data
    assert fixed is not None and not fixed.tau_from_data
