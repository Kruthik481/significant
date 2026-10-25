import { pText, pct } from '@/lib/format';
import type { Report } from '@/lib/types';

export function SrmPanel({ report }: { report: Report }) {
  const { srm, summary } = report;
  const total = srm.control_n + srm.treatment_n;
  const rows = [
    [summary.control, srm.control_n, total * srm.expected_split],
    [summary.treatment, srm.treatment_n, total * (1 - srm.expected_split)],
  ] as const;
  return (
    <section data-testid="srm-panel" className="space-y-3">
      <p className={srm.flagged ? 'alert' : 'muted'}>
        {srm.flagged
          ? `Sample ratio mismatch (${pText(srm.p_value)}). The split is too far from the design to be chance, so the users in each arm are no longer comparable.`
          : `The split matches the design (${pText(srm.p_value)}); nothing suggests users were lost or double-counted.`}
      </p>
      <div className="overflow-x-auto">
        <table className="ledger">
          <thead><tr><th>Variant</th><th className="text-right">Observed</th><th className="text-right">Expected</th><th className="text-right">Share</th></tr></thead>
          <tbody>
            {rows.map(([name, observed, expected]) => (
              <tr key={name}>
                <td>{name}</td>
                <td className="data text-right">{observed.toLocaleString()}</td>
                <td className="data text-right">{Math.round(expected).toLocaleString()}</td>
                <td className="data text-right">{pct(total ? observed / total : null)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
