import Link from 'next/link';
import type { ReactNode } from 'react';
import { CopyLink } from '@/components/CopyLink';
import { ForestPlot } from '@/components/ForestPlot';
import { Glossary } from '@/components/Glossary';
import { Headline } from '@/components/Headline';
import { PowerCalculator } from '@/components/PowerCalculator';
import { SequentialChart } from '@/components/SequentialChart';
import { SrmPanel } from '@/components/SrmPanel';
import { VerdictBanner } from '@/components/VerdictBanner';
import type { StoredReport } from '@/lib/types';

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="sheet space-y-4" aria-label={title}>
      <h2 className="h-section">{title}</h2>
      {children}
    </section>
  );
}

export function ReportView({ stored }: { stored: StoredReport }) {
  const { report } = stored;
  const created = new Date(stored.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  const source = stored.source.startsWith('sample:') ? 'built-in sample' : 'uploaded CSV';
  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 md:py-12">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/" className="wordmark">Significant</Link>
        <div className="flex gap-2">
          <Link href="/" className="btn">New analysis</Link>
          <CopyLink />
        </div>
      </header>
      <article className="sheet space-y-8">
        <p className="muted text-[0.95rem]">{stored.name} · {source} · {created}</p>
        <VerdictBanner report={report} />
        <Headline report={report} />
      </article>
      <Section title="Effect size"><ForestPlot report={report} /></Section>
      <Section title="Peeking-safe view over time"><SequentialChart report={report} /></Section>
      <Section title="Is the split healthy?"><SrmPanel report={report} /></Section>
      <Section title="Plan the next test"><PowerCalculator report={report} /></Section>
      <Section title="How to read this"><Glossary /></Section>
    </main>
  );
}
