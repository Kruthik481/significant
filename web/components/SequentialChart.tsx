import { signedDiff } from '@/lib/format';
import type { Kind, Report, SequentialOut } from '@/lib/types';

const W = 640;
const H = 240;
const M = { top: 16, right: 20, bottom: 34, left: 86 };
const MIN_P = 1e-6;

type Scale = (v: number) => number;

function axisX(seq: SequentialOut): Scale {
  const maxN = seq.points[seq.points.length - 1].n;
  return (n) => M.left + (n / maxN) * (W - M.left - M.right);
}

function XAxis({ seq, x }: { seq: SequentialOut; x: Scale }) {
  const maxN = seq.points[seq.points.length - 1].n;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(maxN * f));
  return (
    <g>
      <line x1={M.left} x2={W - M.right} y1={H - M.bottom} y2={H - M.bottom} stroke="var(--ink)" />
      {ticks.map((n) => (
        <text key={n} x={x(n)} y={H - M.bottom + 18} textAnchor="middle" fontSize="12" className="data" fill="var(--ink-soft)">
          {n.toLocaleString()}
        </text>
      ))}
    </g>
  );
}

function PValuePath({ report, seq }: { report: Report; seq: SequentialOut }) {
  const x = axisX(seq);
  const floor = Math.max(MIN_P, Math.min(report.alpha / 10, ...seq.points.map((p) => p.p_value ?? 1)));
  const top = 0;
  const bottom = Math.log10(floor);
  const y: Scale = (p) => M.top + ((top - Math.log10(Math.max(p, floor))) / (top - bottom)) * (H - M.top - M.bottom);
  const path = seq.points.map((p, i) => `${i ? 'L' : 'M'}${x(p.n)},${y(p.p_value ?? 1)}`).join(' ');
  const ticks = [1, 0.1, 0.01, 0.001, 1e-4, 1e-5, 1e-6].filter((t) => t >= floor);
  const stop = seq.points.find((p) => p.n === seq.stopped_at);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
      aria-label={stop ? `Always-valid p-value crossed alpha at ${stop.n} users` : 'Always-valid p-value never crossed alpha'}>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke="var(--rule)" />
          <text x={M.left - 8} y={y(t) + 4} textAnchor="end" fontSize="12" className="data" fill="var(--ink-soft)">{t >= 0.001 ? t : t.toExponential(0)}</text>
        </g>
      ))}
      <line x1={M.left} x2={W - M.right} y1={y(report.alpha)} y2={y(report.alpha)} stroke="var(--pen)" strokeDasharray="6 4" strokeWidth="1.5" />
      <text x={W - M.right} y={y(report.alpha) - 6} textAnchor="end" className="pen" fontSize="18" fill="var(--pen)">α = {report.alpha}</text>
      <path d={path} fill="none" stroke="var(--ink)" strokeWidth="2.5" strokeLinejoin="round" />
      {stop && (
        <g>
          <circle cx={x(stop.n)} cy={y(stop.p_value ?? 1)} r="9" fill="none" stroke="var(--pen)" strokeWidth="2.5" />
          <text x={x(stop.n) + 14} y={y(stop.p_value ?? 1) - 10} className="pen" fontSize="20" fill="var(--pen)">safe to stop here</text>
        </g>
      )}
      <XAxis seq={seq} x={x} />
    </svg>
  );
}

function ConfidenceBand({ seq, kind }: { seq: SequentialOut; kind: Kind }) {
  const x = axisX(seq);
  const pts = seq.points.filter((p) => p.ci_low !== null && p.ci_high !== null) as { n: number; ci_low: number; ci_high: number }[];
  if (pts.length < 2) return null;
  const values = [0, ...pts.map((p) => p.ci_low), ...pts.map((p) => p.ci_high)];
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const y: Scale = (v) => M.top + ((hi - v) / (hi - lo || 1)) * (H - M.top - M.bottom);
  const area = `${pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.n)},${y(p.ci_high)}`).join(' ')} ${[...pts].reverse().map((p) => `L${x(p.n)},${y(p.ci_low)}`).join(' ')} Z`;
  const last = pts[pts.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
      aria-label={`Confidence sequence narrows to ${signedDiff(last.ci_low, kind)} to ${signedDiff(last.ci_high, kind)}`}>
      <path d={area} fill="var(--ink)" fillOpacity="0.14" stroke="var(--ink)" strokeWidth="1.5" />
      <line x1={M.left} x2={W - M.right} y1={y(0)} y2={y(0)} stroke="var(--ink-soft)" strokeDasharray="4 4" />
      <text x={M.left - 8} y={y(0) + 4} textAnchor="end" fontSize="12" className="data" fill="var(--ink-soft)">0</text>
      <text x={M.left - 8} y={y(hi) + 10} textAnchor="end" fontSize="12" className="data" fill="var(--ink-soft)">{signedDiff(hi, kind)}</text>
      <text x={M.left - 8} y={y(lo)} textAnchor="end" fontSize="12" className="data" fill="var(--ink-soft)">{signedDiff(lo, kind)}</text>
      <XAxis seq={seq} x={x} />
    </svg>
  );
}

export function SequentialChart({ report }: { report: Report }) {
  const seq = report.sequential;
  if (!seq || seq.points.length === 0) {
    return (
      <p className="muted">
        Sequential testing needs a <span className="data">timestamp</span> column and at least 100 users per variant.
      </p>
    );
  }
  return (
    <div data-testid="sequential-chart" className="space-y-10">
      <figure className="space-y-2">
        <PValuePath report={report} seq={seq} />
        <figcaption className="fig-caption">
          <b>Fig. 2</b> Always-valid p-value as users arrived (log scale). Unlike a classic p-value, it stays honest
          however often you look{seq.stopped_at ? `; it crossed α at ${seq.stopped_at.toLocaleString()} users.` : ', and it never crossed α.'}
        </figcaption>
      </figure>
      <figure className="space-y-2">
        <ConfidenceBand seq={seq} kind={report.summary.kind} />
        <figcaption className="fig-caption">
          <b>Fig. 3</b> Confidence sequence for the difference: a range that holds at every look. Once it excludes 0, the
          direction of the effect is settled.
        </figcaption>
      </figure>
    </div>
  );
}
