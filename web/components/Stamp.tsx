import type { Tone } from '@/lib/verdict';

const LABEL: Record<Tone, string> = { win: 'Significant', loss: 'Significant', neutral: 'Inconclusive', invalid: 'Invalid split' };

export function Stamp({ tone, className = '' }: { tone: Tone; className?: string }) {
  return <span className={`stamp tone-${tone} ${className}`}>{LABEL[tone]}</span>;
}
