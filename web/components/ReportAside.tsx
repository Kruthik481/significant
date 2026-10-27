import { ReportNav } from '@/components/ReportNav';
import { Stamp } from '@/components/Stamp';
import { pText, signedDiff, signedPct } from '@/lib/format';
import type { StoredReport } from '@/lib/types';
import { primaryResult, TONE } from '@/lib/verdict';

export function ReportAside({ stored }: { stored: StoredReport }) {
  const { report } = stored;
  const t = primaryResult(report);
  const users = report.summary.control_n + report.summary.treatment_n;
  const facts = [
    ['Lift', t.rel_lift !== null ? signedPct(t.rel_lift) : signedDiff(t.abs_lift, report.summary.kind)],
    ['Evidence', pText(t.p_value)],
    ['Users', users.toLocaleString()],
    ['Split', report.srm.flagged ? 'mismatch' : 'healthy'],
  ] as const;
  return (
    <aside className="aside-card lg:sticky lg:top-24">
      <Stamp tone={TONE[report.verdict]} />
      <p className="mt-3 font-semibold text-[var(--ink)]">{stored.name}</p>
      <dl className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-1 lg:gap-2">
        {facts.map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between gap-3 border-b border-dashed border-[var(--rule)] pb-1">
            <dt className="stat-label">{k}</dt>
            <dd className="data text-sm font-semibold text-[var(--ink)]">{v}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-6 hidden lg:block"><ReportNav /></div>
    </aside>
  );
}
