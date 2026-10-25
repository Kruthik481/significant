'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Dropzone } from '@/components/Dropzone';
import { Options, type OptionValues } from '@/components/Options';
import { SampleCards } from '@/components/SampleCards';
import { ApiError, runSample, sampleCsvUrl, uploadCsv } from '@/lib/api';

const CHECKS = [
  ['Significance and intervals', 'two-proportion z-test or Welch’s t-test, with the lift as a range, not a point'],
  ['CUPED', 'a pre-experiment covariate removes noise, so the same data gives a tighter answer'],
  ['Sample ratio mismatch', 'a broken split invalidates everything else, so it is checked first'],
  ['Safe peeking', 'always-valid p-values: look as often as you like and stop when it is decided'],
] as const;

const COLUMNS = [
  ['user_id', 'required', 'one row per user'],
  ['variant', 'required', 'exactly two values, e.g. control and treatment'],
  ['metric', 'required', '0/1 for conversion, or any number'],
  ['pre_metric', 'optional', 'the same metric before the test; enables CUPED'],
  ['timestamp', 'optional', 'ISO-8601 or epoch seconds; enables sequential testing'],
] as const;

const DEFAULT_OPTIONS: OptionValues = { name: '', control: '', expectedSplit: '0.5', alpha: '0.05' };

function message(e: unknown): string {
  return e instanceof ApiError ? e.message : 'Something went wrong. Please try again.';
}

export function Home() {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [options, setOptions] = useState(DEFAULT_OPTIONS);

  const run = async (label: string, job: () => Promise<{ id: string }>) => {
    setBusy(label);
    setError('');
    try {
      const { id } = await job();
      router.push(`/r/${id}`);
    } catch (e) {
      setError(message(e));
      setBusy(null);
    }
  };

  const upload = (file: File) =>
    run('upload', () =>
      uploadCsv(file, {
        name: options.name.trim() || undefined,
        control: options.control.trim() || undefined,
        expectedSplit: Number(options.expectedSplit),
        alpha: Number(options.alpha),
      }),
    );

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-4 py-8 md:py-14">
      <header className="flex items-baseline justify-between">
        <span className="wordmark">Significant</span>
        <a className="muted text-[0.95rem] underline decoration-[var(--rule)] underline-offset-4" href="#method">Method</a>
      </header>

      <section className="sheet">
        <h1 className="h-display">An A/B test readout you can defend.</h1>
        <p className="lede mt-4">
          Drop in an experiment and get the answer with its uncertainty, after the checks a reviewer would ask for first.
        </p>
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {CHECKS.map(([title, body]) => (
            <li key={title} className="flex gap-3">
              <span aria-hidden="true" className="pen">✓</span>
              <span><b className="text-[var(--ink)]">{title}:</b> <span className="muted">{body}</span></span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="samples" className="space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="samples" className="h-section">Try an experiment with a known answer</h2>
          {busy && busy !== 'upload' && <p className="muted text-[0.95rem]">The free server can take up to a minute to wake up.</p>}
        </div>
        <SampleCards busy={busy === 'upload' ? 'upload' : busy} onRun={(name) => run(name, () => runSample(name))} />
      </section>

      <section aria-labelledby="upload" className="sheet space-y-4">
        <h2 id="upload" className="h-section">Analyze your own</h2>
        <Dropzone disabled={busy !== null} onFile={upload} onReject={setError} />
        {busy === 'upload' && <p className="pen">analyzing…</p>}
        {error && <p role="alert" className="alert">{error}</p>}
        <Options value={options} onChange={setOptions} />
        <div className="overflow-x-auto">
          <table className="ledger">
            <thead><tr><th>Column</th><th></th><th>Meaning</th></tr></thead>
            <tbody>
              {COLUMNS.map(([name, need, meaning]) => (
                <tr key={name}><td className="data">{name}</td><td className="muted">{need}</td><td>{meaning}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted text-[0.95rem]">
          Not sure about the format? Download a sample:{' '}
          <a className="underline underline-offset-4" href={sampleCsvUrl('checkout_win')}>checkout_win.csv</a>. Files stay
          private: only the computed report is saved, under an unguessable link.
        </p>
      </section>

      <footer id="method" className="muted space-y-1 pb-8 text-[0.95rem]">
        <p><b className="text-[var(--ink)]">Method.</b> CUPED follows Deng et al. (2013); sequential tests use the mixture SPRT of Johari et al. (2017); the SRM check follows Kohavi et al., <i>Trustworthy Online Controlled Experiments</i>.</p>
        <p>Every statistic is checked against scipy/statsmodels, and simulations confirm the false-positive rates.</p>
      </footer>
    </main>
  );
}
