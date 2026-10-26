const TERMS = [
  ['p-value', 'How surprising this data would be if the variants were truly identical. Small means surprising; it is not the probability that treatment is better.'],
  ['Confidence interval', 'The range of effects consistent with the data. If a 95% interval excludes zero, the direction holds at 95% confidence; its width tells you how precisely.'],
  ['CUPED', 'Uses each user’s pre-experiment behaviour to subtract predictable noise. Same data, tighter interval, and no added bias as long as the covariate was measured before the experiment began.'],
  ['Sample ratio mismatch', 'When the observed split differs from the designed one by more than chance allows. It usually means users were lost or duplicated, which can bias every number.'],
  ['Always-valid p-value', 'A p-value built to be checked continuously. Classic p-values inflate false positives when you peek; this one does not.'],
] as const;

export function Glossary() {
  return (
    <dl className="grid gap-4 md:grid-cols-2">
      {TERMS.map(([term, meaning]) => (
        <div key={term}>
          <dt className="font-semibold text-[var(--ink)]">{term}</dt>
          <dd className="muted">{meaning}</dd>
        </div>
      ))}
    </dl>
  );
}
