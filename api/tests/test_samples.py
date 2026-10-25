import pytest

from app.analysis import AnalysisOptions, analyze
from app.ingest import parse_csv
from app.samples import SAMPLES, sample_csv


def test_samples_are_listed_with_their_truth():
    assert list(SAMPLES) == ["checkout_win", "pricing_null", "broken_split"]
    assert SAMPLES["broken_split"].truth == "srm_invalid"


def test_samples_are_deterministic():
    assert sample_csv("pricing_null") == sample_csv("pricing_null")


@pytest.mark.parametrize("name", ["checkout_win", "pricing_null", "broken_split"])
def test_each_sample_reproduces_its_ground_truth(name):
    report = analyze(parse_csv(sample_csv(name)), AnalysisOptions())
    assert report.verdict == SAMPLES[name].truth


def test_checkout_win_stops_early_and_pricing_null_benefits_from_cuped():
    win = analyze(parse_csv(sample_csv("checkout_win")), AnalysisOptions())
    assert win.sequential is not None and win.sequential.stopped_at is not None
    null = analyze(parse_csv(sample_csv("pricing_null")), AnalysisOptions())
    assert null.cuped is not None and null.cuped.variance_reduction is not None
    assert null.cuped.variance_reduction > 0.3


def test_unknown_sample_raises():
    with pytest.raises(KeyError):
        sample_csv("nope")
