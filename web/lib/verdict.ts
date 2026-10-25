import { pValue, pct, signedDiff, signedPct } from './format';
import type { Report, TestOut, Verdict } from './types';

export type Tone = 'win' | 'loss' | 'neutral' | 'invalid';
export type VerdictCopy = { title: string; body: string; tone: Tone };

export function primaryResult(r: Report): TestOut {
  return r.primary === 'cuped' && r.cuped ? r.cuped.result : r.raw;
}

function lift(r: Report, t: TestOut): string {
  return t.rel_lift !== null ? signedPct(t.rel_lift) : signedDiff(t.abs_lift, r.summary.kind);
}

export function verdictCopy(v: Verdict, r: Report): VerdictCopy {
  const t = primaryResult(r);
  const { control, treatment } = r.summary;
  const adjusted = r.primary === 'cuped' ? ' after CUPED adjustment' : '';
  switch (v) {
    case 'significant_win':
      return {
        tone: 'win',
        title: 'Treatment wins',
        body: `${treatment} beats ${control} by ${lift(r, t)}${adjusted} (p = ${pValue(t.p_value)}).`,
      };
    case 'significant_loss':
      return {
        tone: 'loss',
        title: 'Treatment loses',
        body: `${treatment} trails ${control} by ${lift(r, t)}${adjusted} (p = ${pValue(t.p_value)}).`,
      };
    case 'srm_invalid':
      return {
        tone: 'invalid',
        title: "Don't trust this result",
        body: `The sample ratio is off: ${pct(r.srm.expected_split)} of users were meant to be in ${control}, but ${pct(r.srm.observed_split)} were (p = ${pValue(r.srm.p_value)}). Something dropped or duplicated users; fix assignment or logging before reading any lift.`,
      };
    case 'not_significant':
      return {
        tone: 'neutral',
        title: 'No significant difference',
        body: `There is not enough evidence at α = ${r.alpha} to say the variants differ (p = ${pValue(t.p_value)}). That is not proof of no effect: the interval shows which effects are still plausible.`,
      };
  }
}
