import type { Interval, Kind } from './types';

const DASH = '—';
const MINUS = '−';

const sign = (x: number) => (x > 0 ? '+' : x < 0 ? MINUS : '');

export function pct(x: number | null, digits = 1): string {
  return x === null ? DASH : `${(x * 100).toFixed(digits)}%`;
}

export function signedPct(x: number | null, digits = 1): string {
  return x === null ? DASH : `${sign(x)}${pct(Math.abs(x), digits)}`;
}

export function pValue(p: number | null): string {
  if (p === null) return DASH;
  if (p < 0.001) return '< 0.001';
  return String(Number(p.toPrecision(3)));
}

export function num(x: number | null, digits = 2): string {
  return x === null ? DASH : x.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

// Absolute difference with sign: percentage points for rates, raw units otherwise.
export function signedDiff(x: number | null, kind: Kind): string {
  if (x === null) return DASH;
  return kind === 'binary' ? `${sign(x)}${(Math.abs(x) * 100).toFixed(2)} pp` : `${sign(x)}${Math.abs(x).toFixed(2)}`;
}

export function ciText([lo, hi]: Interval, kind: Kind): string {
  return `[${signedDiff(lo, kind)}, ${signedDiff(hi, kind)}]`;
}
