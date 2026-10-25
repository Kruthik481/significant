"""Sample-ratio mismatch: a chi-square check that the observed split matches the designed one."""

from dataclasses import dataclass

from scipy import stats

SRM_THRESHOLD = 0.001  # the conventional bar; a broken split is usually far below it


@dataclass(frozen=True)
class SrmResult:
    control_n: int
    treatment_n: int
    expected_split: float
    observed_split: float
    chi2: float
    p_value: float
    flagged: bool


def srm(control_n: int, treatment_n: int, expected_split: float = 0.5) -> SrmResult:
    if not 0 < expected_split < 1:
        raise ValueError("expected_split must be between 0 and 1")
    total = control_n + treatment_n
    expected = [total * expected_split, total * (1 - expected_split)]
    chi2, p = stats.chisquare([control_n, treatment_n], expected)
    return SrmResult(
        control_n=control_n,
        treatment_n=treatment_n,
        expected_split=expected_split,
        observed_split=control_n / total if total else 0.0,
        chi2=float(chi2),
        p_value=float(p),
        flagged=bool(p < SRM_THRESHOLD),
    )
