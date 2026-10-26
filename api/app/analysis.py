"""Turn a validated experiment into a report: the raw test, CUPED, SRM, sequential view and a verdict."""

import math
from dataclasses import dataclass

import numpy as np

from app.ingest import Experiment
from app.report import CupedOut, Report, SequentialOut, SrmOut, Summary, TestOut, Verdict, finite
from app.stats.cuped import cuped
from app.stats.sequential import msprt
from app.stats.srm import srm
from app.stats.tests import TestResult, proportion_test, welch_test

ALPHA_RANGE = (0.001, 0.2)


@dataclass(frozen=True)
class AnalysisOptions:
    alpha: float = 0.05
    expected_split: float = 0.5
    tau: float | None = None

    def __post_init__(self) -> None:
        low, high = ALPHA_RANGE
        if not low <= self.alpha <= high:
            raise ValueError(f"alpha must be between {low} and {high}")
        if not 0 < self.expected_split < 1:
            raise ValueError("expected_split must be between 0 and 1")
        # tau is squared downstream, so it must stay finite and non-zero once squared
        if self.tau is not None and not (self.tau > 0 and 0 < self.tau * self.tau < math.inf):
            raise ValueError("tau must be a positive, finite number")


def _verdict(primary: TestResult, srm_flagged: bool, alpha: float) -> Verdict:
    if srm_flagged:
        return "srm_invalid"
    if primary.p_value < alpha:
        return "significant_win" if primary.abs_lift > 0 else "significant_loss"
    return "not_significant"


def analyze(exp: Experiment, opts: AnalysisOptions) -> Report:
    test = proportion_test if exp.kind == "binary" else welch_test
    raw = test(exp.c.metric, exp.t.metric, opts.alpha)
    adjusted = None
    if exp.c.pre is not None and exp.t.pre is not None:
        adjusted = cuped(exp.c.metric, exp.c.pre, exp.t.metric, exp.t.pre, opts.alpha)
    primary = adjusted.result if adjusted is not None else raw
    ratio = srm(exp.c.metric.size, exp.t.metric.size, opts.expected_split)
    sequential = None
    if exp.c.ts is not None and exp.t.ts is not None:
        values = np.concatenate([exp.c.metric, exp.t.metric])
        treated = np.concatenate([np.zeros(exp.c.metric.size, bool), np.ones(exp.t.metric.size, bool)])
        sequential = msprt(values, treated, np.concatenate([exp.c.ts, exp.t.ts]), opts.alpha, opts.tau)
    return Report(
        summary=Summary(
            control=exp.control,
            treatment=exp.treatment,
            kind=exp.kind,
            control_n=int(exp.c.metric.size),
            treatment_n=int(exp.t.metric.size),
            control_mean=finite(raw.control_mean),
            treatment_mean=finite(raw.treatment_mean),
            has_pre_metric=exp.has_pre,
            has_timestamp=exp.has_ts,
        ),
        alpha=opts.alpha,
        expected_split=opts.expected_split,
        primary="cuped" if adjusted is not None else "raw",
        verdict=_verdict(primary, ratio.flagged, opts.alpha),
        raw=TestOut.of(raw),
        cuped=None if adjusted is None else CupedOut.of(adjusted),
        srm=SrmOut.of(ratio),
        sequential=None if sequential is None else SequentialOut.of(sequential),
    )
