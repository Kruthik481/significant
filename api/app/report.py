"""The analysis report returned by the API and stored as JSON. Non-finite numbers become null."""

import math
from typing import Literal

from pydantic import BaseModel

from app.stats.cuped import CupedResult
from app.stats.sequential import SequentialResult
from app.stats.srm import SrmResult
from app.stats.tests import TestResult

Verdict = Literal["significant_win", "significant_loss", "not_significant", "srm_invalid"]


def finite(x: float | None) -> float | None:
    return x if x is not None and math.isfinite(x) else None


class TestOut(BaseModel):
    __test__ = False  # not a pytest test class

    control_mean: float | None
    treatment_mean: float | None
    abs_lift: float | None
    abs_ci: list[float | None]
    rel_lift: float | None
    rel_ci: list[float | None] | None
    p_value: float | None
    stat: float | None
    se: float | None

    @classmethod
    def of(cls, r: TestResult) -> "TestOut":
        return cls(
            control_mean=finite(r.control_mean),
            treatment_mean=finite(r.treatment_mean),
            abs_lift=finite(r.abs_lift),
            abs_ci=[finite(v) for v in r.abs_ci],
            rel_lift=finite(r.rel_lift),
            rel_ci=None if r.rel_ci is None else [finite(v) for v in r.rel_ci],
            p_value=finite(r.p_value),
            stat=finite(r.stat),
            se=finite(r.se),
        )


class CupedOut(BaseModel):
    theta: float | None
    variance_reduction: float | None
    result: TestOut

    @classmethod
    def of(cls, c: CupedResult) -> "CupedOut":
        return cls(
            theta=finite(c.theta),
            variance_reduction=finite(c.variance_reduction),
            result=TestOut.of(c.result),
        )


class SrmOut(BaseModel):
    control_n: int
    treatment_n: int
    expected_split: float
    observed_split: float | None
    chi2: float | None
    p_value: float | None
    flagged: bool

    @classmethod
    def of(cls, s: SrmResult) -> "SrmOut":
        return cls(
            control_n=s.control_n,
            treatment_n=s.treatment_n,
            expected_split=s.expected_split,
            observed_split=finite(s.observed_split),
            chi2=finite(s.chi2),
            p_value=finite(s.p_value),
            flagged=s.flagged,
        )


class CheckpointOut(BaseModel):
    n: int
    p_value: float | None
    ci_low: float | None
    ci_high: float | None


class SequentialOut(BaseModel):
    tau: float | None
    points: list[CheckpointOut]
    stopped_at: int | None
    tau_from_data: bool  # the default tau uses the final variance, so the guarantee is only approximate

    @classmethod
    def of(cls, s: SequentialResult, tau_from_data: bool) -> "SequentialOut":
        points = [
            CheckpointOut(
                n=p.n, p_value=finite(p.p_value), ci_low=finite(p.ci_low), ci_high=finite(p.ci_high)
            )
            for p in s.points
        ]
        return cls(tau=finite(s.tau), points=points, stopped_at=s.stopped_at, tau_from_data=tau_from_data)


class Summary(BaseModel):
    control: str
    treatment: str
    kind: Literal["binary", "continuous"]
    control_n: int
    treatment_n: int
    control_mean: float | None
    treatment_mean: float | None
    has_pre_metric: bool
    has_timestamp: bool


class Report(BaseModel):
    summary: Summary
    alpha: float
    expected_split: float
    primary: Literal["raw", "cuped"]
    verdict: Verdict
    raw: TestOut
    cuped: CupedOut | None
    srm: SrmOut
    sequential: SequentialOut | None
