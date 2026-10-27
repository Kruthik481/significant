import Link from 'next/link';
import type { ReactNode } from 'react';
import { CopyLink } from '@/components/CopyLink';
import { ForestPlot } from '@/components/ForestPlot';
import { Glossary } from '@/components/Glossary';
import { Headline } from '@/components/Headline';
import { InView } from '@/components/InView';
import { PowerCalculator } from '@/components/PowerCalculator';
import { ReportAside } from '@/components/ReportAside';
import { SequentialChart } from '@/components/SequentialChart';
import { SiteNav } from '@/components/SiteNav';
import { SrmPanel } from '@/components/SrmPanel';
import { VerdictBanner } from '@/components/VerdictBanner';
import { REPORT_SECTIONS } from '@/lib/sections';
import type { StoredReport } from '@/lib/types';

type SectionId = (typeof REPORT_SECTIONS)[number][0];

function Section({ id, children }: { id: SectionId; children: ReactNode }) {
  const index = REPORT_SECTIONS.findIndex(([s]) => s === id);
  const title = REPORT_SECTIONS[index][1];
  return (
    <InView>
      <section id={id} className="sheet rise space-y-4" aria-label={title}>
        <p className="eyebrow"><span className="data">§{index + 1}</span></p>
        <h2 className="h-section -mt-2">{title}</h2>
        {children}
      </section>
    </InView>
  );
}

export function ReportView({ stored }: { stored: StoredReport }) {
  const { report } = stored;
  const created = new Date(stored.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  const source = stored.source.startsWith('sample:') ? 'built-in sample' : 'uploaded CSV';
  return (
    <>
      <SiteNav>
        <Link href="/" className="btn">New analysis</Link>
        <CopyLink />
      </SiteNav>
      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 md:py-10 lg:grid-cols-[250px_1fr] lg:items-start lg:gap-8">
        <ReportAside stored={stored} />
        <div className="min-w-0 space-y-6">
          <article id="verdict" className="sheet space-y-8">
            <p className="eyebrow">{stored.name} · {source} · {created}</p>
            <VerdictBanner report={report} />
            <Headline report={report} />
          </article>
          <Section id="effect"><ForestPlot report={report} /></Section>
          <Section id="sequential"><SequentialChart report={report} /></Section>
          <Section id="split"><SrmPanel report={report} /></Section>
          <Section id="plan"><PowerCalculator report={report} /></Section>
          <Section id="glossary"><Glossary /></Section>
        </div>
      </main>
    </>
  );
}
