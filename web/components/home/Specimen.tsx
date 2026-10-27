import { PenCircle, PenUnderline } from '@/components/Pen';
import { Stamp } from '@/components/Stamp';
import { SPECIMEN_POINTS, SPECIMEN_STOP, SPECIMEN_TOTAL } from '@/lib/specimen';

const W = 360;
const H = 150;
const PAD = { left: 34, right: 8, top: 8, bottom: 20 };
const DECADES = 4; // log scale from 1 down to 1e-4
const x = (n: number) => PAD.left + (n / SPECIMEN_TOTAL) * (W - PAD.left - PAD.right);
const y = (p: number) => PAD.top + (-Math.log10(p) / DECADES) * (H - PAD.top - PAD.bottom);
const PATH = SPECIMEN_POINTS.map(([n, p], i) => `${i ? 'L' : 'M'}${x(n).toFixed(1)},${y(p).toFixed(1)}`).join(' ');
const STOP_P = SPECIMEN_POINTS.find(([n]) => n === SPECIMEN_STOP)![1];

// A real report from the checkout sample, pinned to the page like a printout.
export function Specimen() {
  return (
    <figure className="specimen" aria-label="Example report from the checkout sample: treatment wins by 11.4%, p below 0.001">
      <span aria-hidden="true" className="tape" />
      <div className="flex items-start justify-between gap-3">
        <p className="eyebrow">Specimen · checkout sample</p>
        <Stamp tone="win" className="stamp-in" />
      </div>
      <p className="tone-win mt-1 text-3xl font-bold tracking-tight">Treatment wins</p>
      <p className="mt-2 flex items-baseline gap-5 text-[var(--ink)]">
        <span className="data text-2xl font-semibold"><PenUnderline delay={900}>+11.4%</PenUnderline></span>
        <span className="data"><PenCircle delay={1300}>p &lt; 0.001</PenCircle></span>
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-4 w-full" aria-hidden="true">
        {[1, 0.01, 0.0001].map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} stroke="var(--rule)" />
            <text x={PAD.left - 6} y={y(t) + 4} textAnchor="end" fontSize="10" className="data" fill="var(--ink-soft)">{t === 1 ? '1' : t === 0.01 ? '0.01' : '10⁻⁴'}</text>
          </g>
        ))}
        <line x1={PAD.left} x2={W - PAD.right} y1={y(0.05)} y2={y(0.05)} stroke="var(--pen)" strokeDasharray="5 4" strokeWidth="1.3" />
        <text x={W - PAD.right} y={y(0.05) - 5} textAnchor="end" className="pen" fontSize="15" fill="var(--pen)">α = 0.05</text>
        <path d={PATH} pathLength={1} className="ink-draw" fill="none" stroke="var(--ink)" strokeWidth="2.2" strokeLinejoin="round" />
        <circle cx={x(SPECIMEN_STOP)} cy={y(STOP_P)} r="7" pathLength={1} className="pen-stroke" style={{ animationDelay: '1700ms' }} />
        <text x={PAD.left} y={H - 4} fontSize="10" className="data" fill="var(--ink-soft)">0</text>
        <text x={W - PAD.right} y={H - 4} textAnchor="end" fontSize="10" className="data" fill="var(--ink-soft)">40,000 users</text>
      </svg>
      <figcaption className="fig-caption mt-1">Always-valid p-value: safe to stop at {SPECIMEN_STOP.toLocaleString()} of {SPECIMEN_TOTAL.toLocaleString()} users.</figcaption>
      <dl className="mt-4 grid grid-cols-3 gap-3 border-t border-[var(--rule)] pt-3 text-sm">
        <div><dt className="stat-label">control</dt><dd className="data text-[var(--ink)]">12.71%</dd></div>
        <div><dt className="stat-label">treatment</dt><dd className="data text-[var(--ink)]">14.15%</dd></div>
        <div><dt className="stat-label">split</dt><dd className="data text-[var(--ink)]">50 / 50 ✓</dd></div>
      </dl>
    </figure>
  );
}
