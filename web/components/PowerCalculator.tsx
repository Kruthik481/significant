'use client';

import { useState } from 'react';
import { ApiError, power } from '@/lib/api';
import type { Report } from '@/lib/types';

// Pre-fills from this experiment: the control mean as baseline and, for continuous metrics, a pooled sd
// recovered from the standard error.
function defaults(r: Report) {
  const { control_n: nc, treatment_n: nt, control_mean } = r.summary;
  const sd = r.raw.se !== null ? r.raw.se * Math.sqrt((nc * nt) / (nc + nt)) : 1;
  return { baseline: String(Number((control_mean ?? 0.1).toPrecision(4))), lift: '5', sd: String(Number(sd.toPrecision(4))) };
}

export function PowerCalculator({ report }: { report: Report }) {
  const kind = report.summary.kind;
  const [form, setForm] = useState(() => defaults(report));
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const baseline = Number(form.baseline);
    const mde = baseline * (Number(form.lift) / 100);
    try {
      const r = await power({ baseline, mde, alpha: report.alpha, kind, sd: kind === 'continuous' ? Number(form.sd) : undefined });
      setResult(`${r.n_per_arm.toLocaleString()} users per variant (${r.total.toLocaleString()} total) to detect a ${form.lift}% relative change with 80% power.`);
    } catch (err) {
      setResult('');
      setError(err instanceof ApiError ? err.message : 'Could not compute the sample size.');
    }
  };

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [key]: e.target.value });
  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="field">{kind === 'binary' ? 'Baseline rate' : 'Baseline mean'}<input value={form.baseline} onChange={set('baseline')} inputMode="decimal" /></label>
        <label className="field">Smallest change worth detecting (%)<input value={form.lift} onChange={set('lift')} inputMode="decimal" /></label>
        {kind === 'continuous' && <label className="field">Standard deviation<input value={form.sd} onChange={set('sd')} inputMode="decimal" /></label>}
      </div>
      <button type="submit" className="btn">Size the next test</button>
      {result && <p className="text-[var(--ink)]" aria-live="polite">{result}</p>}
      {error && <p role="alert" className="alert">{error}</p>}
    </form>
  );
}
