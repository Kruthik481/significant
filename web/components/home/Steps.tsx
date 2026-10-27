import { InView } from '@/components/InView';

const STEPS = [
  ['Upload', 'A CSV with one row per user: variant, metric, and optionally a pre-period metric and timestamp.'],
  ['Check', 'The split is tested first, then the effect is estimated with CUPED and tracked with a sequential test.'],
  ['Decide', 'A verdict in plain words, the interval behind it, and a link you can drop into the review thread.'],
] as const;

export function Steps() {
  return (
    <InView className="steps">
      {STEPS.map(([title, body], i) => (
        <div key={title} className="rise step" style={{ animationDelay: `${i * 140}ms` }}>
          <span className="step-num pen">{i + 1}</span>
          <h3 className="mt-2 text-lg font-semibold text-[var(--ink)]">{title}</h3>
          <p className="muted mt-1 text-[0.95rem]">{body}</p>
        </div>
      ))}
    </InView>
  );
}
