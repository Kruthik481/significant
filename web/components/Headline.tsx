import { ciText, num, pValue, pct, signedDiff, signedPct } from '@/lib/format';
import type { Report } from '@/lib/types';
import { primaryResult } from '@/lib/verdict';

export function Headline({ report }: { report: Report }) {
  const { summary: s } = report;
  const t = primaryResult(report);
  const mean = (x: number | null) => (s.kind === 'binary' ? pct(x, 2) : num(x));
  const level = `${Math.round((1 - report.alpha) * 100)}%`;
  const stats = [
    [s.control, mean(s.control_mean), `control · ${s.control_n.toLocaleString()} users`],
    [s.treatment, mean(s.treatment_mean), `treatment · ${s.treatment_n.toLocaleString()} users`],
    ['Relative lift', signedPct(t.rel_lift), t.rel_ci ? `${level} CI ${signedPct(t.rel_ci[0])} to ${signedPct(t.rel_ci[1])}` : 'undefined: control mean is 0'],
    ['Absolute difference', signedDiff(t.abs_lift, s.kind), `${level} CI ${ciText(t.abs_ci, s.kind)}`],
    ['p-value', pValue(t.p_value), report.primary === 'cuped' ? 'CUPED-adjusted' : s.kind === 'binary' ? 'two-proportion z-test' : 'Welch’s t-test'],
  ] as const;
  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-5 md:grid-cols-5">
      {stats.map(([label, value, sub]) => (
        <div key={label} className="border-t-2 border-[var(--ink)] pt-2">
          <dt className="stat-label">{label}</dt>
          <dd className="stat-value">{value}</dd>
          <dd className="muted text-[0.85rem]">{sub}</dd>
        </div>
      ))}
    </dl>
  );
}
