import type { ReactNode } from 'react';
import { InView } from '@/components/InView';

// Small diagrams for each check; .draw paths trace themselves when the grid scrolls into view.
const d = (delay: number) => ({ pathLength: 1, className: 'draw', style: { animationDelay: `${delay}ms` } });
const ink = { fill: 'none', stroke: 'var(--ink)', strokeWidth: 2.5, strokeLinecap: 'round' as const };
const soft = { ...ink, stroke: 'var(--grid-major)' };
const label = { fontSize: 11, className: 'data', fill: 'var(--ink-soft)' };

const SignificanceArt = (
  <>
    <path d="M70 10 V80" stroke="var(--ink-soft)" strokeDasharray="4 4" />
    <text x="70" y="94" textAnchor="middle" {...label}>0</text>
    <path d="M120 45 H236 M120 37 V53 M236 37 V53" {...ink} {...d(100)} />
    <circle cx="178" cy="45" r="6" fill="var(--ink)" className="rise" style={{ animationDelay: '700ms' }} />
  </>
);

const CupedArt = (
  <>
    <text x="0" y="34" {...label}>raw</text>
    <path d="M60 30 H244 M60 23 V37 M244 23 V37" {...soft} {...d(0)} />
    <text x="0" y="70" {...label}>CUPED</text>
    <path d="M104 66 H200 M104 59 V73 M200 59 V73" {...ink} {...d(500)} />
  </>
);

const SrmArt = (
  <>
    <text x="0" y="22" {...label}>designed</text>
    <path d="M0 34 H130" {...ink} strokeWidth={12} strokeLinecap="butt" {...d(0)} />
    <path d="M130 34 H260" {...soft} strokeWidth={12} strokeLinecap="butt" {...d(300)} />
    <text x="0" y="62" {...label}>observed</text>
    <path d="M0 74 H150" {...ink} strokeWidth={12} strokeLinecap="butt" {...d(600)} />
    <path d="M150 74 H260" {...soft} strokeWidth={12} strokeLinecap="butt" {...d(900)} />
    <path d="M130 26 V86" stroke="var(--pen)" strokeWidth="1.5" strokeDasharray="3 3" />
  </>
);

const SequentialArt = (
  <>
    <path d="M0 52 H460" stroke="var(--pen)" strokeWidth="1.4" strokeDasharray="5 4" />
    <text x="460" y="46" textAnchor="end" className="pen" fontSize="15" fill="var(--pen)">α</text>
    <path d="M0 8 C 40 9, 60 12, 80 22 S 130 26, 160 27 S 190 30, 205 52 S 240 70, 280 74 S 380 80, 460 84" {...ink} {...d(0)} />
    <circle cx="205" cy="52" r="8" pathLength={1} className="pen-stroke draw-pen" />
    <text x="220" y="40" className="pen" fontSize="16" fill="var(--pen)">stop here</text>
  </>
);

const CELLS: { title: string; body: string; art: ReactNode; width: number; span: string }[] = [
  { title: 'Significance with intervals', body: 'Two-proportion z-test or Welch’s t-test. The lift is reported as a range, not a point.', art: SignificanceArt, width: 260, span: 'md:col-span-3' },
  { title: 'CUPED variance reduction', body: 'A pre-experiment covariate subtracts predictable noise, so the same data gives a tighter answer.', art: CupedArt, width: 260, span: 'md:col-span-3' },
  { title: 'Sample ratio mismatch', body: 'A broken split invalidates everything else, so it is checked first.', art: SrmArt, width: 260, span: 'md:col-span-2' },
  { title: 'Safe peeking', body: 'Always-valid p-values and confidence sequences: look as often as you like and stop once it is decided.', art: SequentialArt, width: 460, span: 'md:col-span-4' },
];

export function MethodGrid() {
  return (
    <section aria-labelledby="checks" className="space-y-5">
      <div>
        <p className="eyebrow">What every report runs</p>
        <h2 id="checks" className="h-section mt-1">The checks a reviewer would ask for first</h2>
      </div>
      <InView className="grid gap-4 md:grid-cols-6">
        {CELLS.map((c, i) => (
          <article key={c.title} className={`bento rise ${c.span}`} style={{ animationDelay: `${i * 100}ms` }}>
            <svg viewBox={`0 0 ${c.width} 100`} className="h-24 w-full overflow-visible" aria-hidden="true" preserveAspectRatio="xMinYMid meet">{c.art}</svg>
            <h3 className="mt-4 text-lg font-semibold text-[var(--ink)]">{c.title}</h3>
            <p className="muted mt-1 text-[0.95rem]">{c.body}</p>
          </article>
        ))}
      </InView>
    </section>
  );
}
