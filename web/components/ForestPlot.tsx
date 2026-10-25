import { signedDiff } from '@/lib/format';
import type { Kind, Report, TestOut } from '@/lib/types';

const W = 640;
const ROW = 46;
const LEFT = 150;
const RIGHT = 24;

type Row = { label: string; t: TestOut };

function finiteValues(rows: Row[]): number[] {
  return rows.flatMap(({ t }) => [t.abs_ci[0], t.abs_ci[1], t.abs_lift]).filter((v): v is number => v !== null);
}

export function ForestPlot({ report }: { report: Report }) {
  const rows: Row[] = [{ label: 'Raw', t: report.raw }];
  if (report.cuped) rows.push({ label: 'CUPED-adjusted', t: report.cuped.result });
  const values = [0, ...finiteValues(rows)];
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const pad = (hi - lo || 1) * 0.15;
  const x = (v: number) => LEFT + ((v - (lo - pad)) / (hi - lo + 2 * pad)) * (W - LEFT - RIGHT);
  const height = rows.length * ROW + 34;
  const kind: Kind = report.summary.kind;
  return (
    <figure data-testid="forest-plot" className="space-y-2">
      <svg viewBox={`0 0 ${W} ${height}`} className="w-full" role="img"
        aria-label={rows.map((r) => `${r.label}: ${signedDiff(r.t.abs_lift, kind)}`).join('; ')}>
        <line x1={x(0)} x2={x(0)} y1={6} y2={height - 26} stroke="var(--ink-soft)" strokeDasharray="4 4" />
        <text x={x(0)} y={height - 8} textAnchor="middle" className="data" fontSize="12" fill="var(--ink-soft)">no difference</text>
        {rows.map(({ label, t }, i) => {
          const y = 24 + i * ROW;
          const [a, b] = t.abs_ci;
          return (
            <g key={label}>
              <text x={0} y={y + 5} fontSize="15" fill="var(--ink)">{label}</text>
              {a !== null && b !== null && (
                <>
                  <line x1={x(a)} x2={x(b)} y1={y} y2={y} stroke="var(--ink)" strokeWidth="2.5" />
                  <line x1={x(a)} x2={x(a)} y1={y - 7} y2={y + 7} stroke="var(--ink)" strokeWidth="2" />
                  <line x1={x(b)} x2={x(b)} y1={y - 7} y2={y + 7} stroke="var(--ink)" strokeWidth="2" />
                </>
              )}
              {t.abs_lift !== null && <circle cx={x(t.abs_lift)} cy={y} r="6" fill="var(--ink)" />}
              {t.abs_lift !== null && (
                <text x={x(t.abs_lift)} y={y - 12} textAnchor="middle" className="data" fontSize="12" fill="var(--ink)">
                  {signedDiff(t.abs_lift, kind)}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <figcaption className="fig-caption">
        <b>Fig. 1</b> Difference in {kind === 'binary' ? 'conversion (percentage points)' : 'the metric'}, treatment minus control, with {Math.round((1 - report.alpha) * 100)}% intervals.
        {report.cuped && report.cuped.variance_reduction !== null &&
          ` CUPED removed ${(report.cuped.variance_reduction * 100).toFixed(0)}% of the variance using the pre-experiment metric.`}
      </figcaption>
    </figure>
  );
}
