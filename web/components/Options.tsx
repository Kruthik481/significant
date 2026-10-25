'use client';

export type OptionValues = { name: string; control: string; expectedSplit: string; alpha: string };

type Props = { value: OptionValues; onChange: (next: OptionValues) => void };

export function Options({ value, onChange }: Props) {
  const set = (key: keyof OptionValues) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onChange({ ...value, [key]: e.target.value });
  return (
    <details className="mt-4">
      <summary className="cursor-pointer font-semibold text-[var(--ink)]">Options</summary>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="field">Report name<input value={value.name} onChange={set('name')} placeholder="Checkout test, March" /></label>
        <label className="field">Control variant<input value={value.control} onChange={set('control')} placeholder="detected automatically" /></label>
        <label className="field">Designed share in control<input value={value.expectedSplit} onChange={set('expectedSplit')} inputMode="decimal" /></label>
        <label className="field">Significance level α<input value={value.alpha} onChange={set('alpha')} inputMode="decimal" /></label>
      </div>
    </details>
  );
}
