'use client';

import { SAMPLES } from '@/lib/samples';

type Props = { busy: string | null; onRun: (name: string) => void };

export function SampleCards({ busy, onRun }: Props) {
  return (
    <ul className="grid gap-4 md:grid-cols-3">
      {SAMPLES.map((s) => (
        <li key={s.name}>
          <button type="button" data-testid={`sample-${s.name}`} className="card h-full" disabled={busy !== null}
            onClick={() => onRun(s.name)}>
            <span className="block text-lg font-semibold text-[var(--ink)]">{s.title}</span>
            <span className="mt-1 block text-[0.95rem] muted">{s.description}</span>
            <span className="pen mt-3 block">{busy === s.name ? 'running…' : `planted: ${s.note}`}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
