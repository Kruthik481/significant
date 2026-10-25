// verdict.test.ts
import { describe, expect, it } from 'vitest';
import { verdictCopy } from './verdict';
import type { Report } from './types';

const base = {
  alpha: 0.05, primary: 'raw', expected_split: 0.5, cuped: null, sequential: null,
  summary: { control: 'control', treatment: 'treatment', kind: 'binary', control_n: 100, treatment_n: 100,
    control_mean: 0.1, treatment_mean: 0.11, has_pre_metric: false, has_timestamp: false },
  raw: { control_mean: 0.1, treatment_mean: 0.11, abs_lift: 0.01, abs_ci: [0.002, 0.018], rel_lift: 0.1,
    rel_ci: [0.02, 0.18], p_value: 0.01, stat: 2.5, se: 0.004 },
  srm: { control_n: 100, treatment_n: 100, expected_split: 0.5, observed_split: 0.5, chi2: 0, p_value: 1, flagged: false },
} as unknown as Report;

describe('verdictCopy', () => {
  it('names the winner with lift and p-value', () => {
    const c = verdictCopy('significant_win', { ...base, verdict: 'significant_win' });
    expect(c.tone).toBe('win');
    expect(c.title).toBe('Treatment wins');
    expect(c.body).toContain('+10.0%');
    expect(c.body).toContain('0.01');
  });
  it('warns that an SRM result cannot be trusted', () => {
    const c = verdictCopy('srm_invalid', { ...base, verdict: 'srm_invalid' });
    expect(c.tone).toBe('invalid');
    expect(c.body).toMatch(/sample ratio/i);
  });
  it('explains a null result without claiming no effect', () => {
    const c = verdictCopy('not_significant', { ...base, verdict: 'not_significant' });
    expect(c.tone).toBe('neutral');
    expect(c.body).toMatch(/not enough evidence/i);
  });
});
