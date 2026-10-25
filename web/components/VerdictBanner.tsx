import { MarginNote, PenCircle, PenUnderline } from '@/components/Pen';
import { pText, signedDiff, signedPct } from '@/lib/format';
import type { Report } from '@/lib/types';
import { primaryResult, verdictCopy } from '@/lib/verdict';

function note(r: Report): string | null {
  if (r.verdict === 'srm_invalid') return `split is off: ${pText(r.srm.p_value)}`;
  const stop = r.sequential?.stopped_at;
  if (stop) return `decided early, at ${stop.toLocaleString()} of ${(r.summary.control_n + r.summary.treatment_n).toLocaleString()} users`;
  if (r.verdict === 'not_significant') return 'inconclusive, not "no effect"';
  return null;
}

export function VerdictBanner({ report }: { report: Report }) {
  const copy = verdictCopy(report.verdict, report);
  const t = primaryResult(report);
  const lift = t.rel_lift !== null ? signedPct(t.rel_lift) : signedDiff(t.abs_lift, report.summary.kind);
  const margin = note(report);
  return (
    <section data-testid="verdict" aria-label="Verdict" className="grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
      <div>
        <h1 className={`h-display tone-${copy.tone}`}>{copy.title}</h1>
        <p className="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-2 text-[var(--ink)]">
          <span className="data text-3xl font-semibold"><PenUnderline delay={200}>{lift}</PenUnderline></span>
          <span className="data text-xl"><PenCircle delay={600}>{pText(t.p_value)}</PenCircle></span>
        </p>
        <p className="lede mt-4">{copy.body}</p>
      </div>
      {margin && <div className="md:max-w-56 md:pb-2"><MarginNote delay={1100}>{margin}</MarginNote></div>}
    </section>
  );
}
