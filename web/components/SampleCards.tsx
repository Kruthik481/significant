'use client';

import { Stamp } from '@/components/Stamp';
import { SAMPLES } from '@/lib/samples';
import { TONE } from '@/lib/verdict';

type Props = { busy: string | null; onRun: (name: string) => void };

export function SampleCards({ busy, onRun }: Props) {
  return (
    <ul className="grid gap-4 md:grid-cols-3">
      {SAMPLES.map((s) => (
        <li key={s.name}>
          <button type="button" data-testid={`sample-${s.name}`} className="card group h-full" disabled={busy !== null}
            onClick={() => onRun(s.name)}>
            <span className="flex items-start justify-between gap-3">
              <span className="block text-lg font-semibold text-[var(--ink)]">{s.title}</span>
              <Stamp tone={TONE[s.truth]} className="stamp-sm" />
            </span>
            <span className="mt-1 block text-[0.95rem] muted">{s.description}</span>
            <span className="pen mt-3 block">planted: {s.note}</span>
            <span className="card-cta mt-auto pt-4">{busy === s.name ? 'Running…' : 'Run analysis →'}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
