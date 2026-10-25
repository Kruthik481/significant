// format.test.ts
import { describe, expect, it } from 'vitest';
import { ciText, pValue, pct, signedPct } from './format';

describe('format', () => {
  it('formats percentages and nulls', () => {
    expect(pct(0.1234)).toBe('12.3%');
    expect(pct(null)).toBe('—');
    expect(signedPct(0.05)).toBe('+5.0%');
    expect(signedPct(-0.05)).toBe('−5.0%');
  });
  it('formats p-values', () => {
    expect(pValue(0.0004)).toBe('< 0.001');
    expect(pValue(0.04567)).toBe('0.0457');
    expect(pValue(null)).toBe('—');
  });
  it('formats intervals by metric kind', () => {
    expect(ciText([0.004, 0.016], 'binary')).toBe('[+0.40 pp, +1.60 pp]');
    expect(ciText([-1.5, 2.25], 'continuous')).toBe('[−1.50, +2.25]');
  });
});
