import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ReportView } from '@/components/ReportView';
import { ApiError, getReport } from '@/lib/api';
import type { StoredReport } from '@/lib/types';
import { verdictCopy } from '@/lib/verdict';

async function load(id: string): Promise<StoredReport> {
  try {
    return await getReport(id, { cache: 'no-store' });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }
}

export async function generateMetadata({ params }: PageProps<'/r/[id]'>): Promise<Metadata> {
  const { id } = await params;
  const stored = await load(id);
  const copy = verdictCopy(stored.report.verdict, stored.report);
  return { title: `${stored.name}: ${copy.title} — Significant`, description: copy.body };
}

export default async function ReportPage({ params }: PageProps<'/r/[id]'>) {
  const { id } = await params;
  return <ReportView stored={await load(id)} />;
}
