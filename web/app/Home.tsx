'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Dropzone } from '@/components/Dropzone';
import { Hero } from '@/components/home/Hero';
import { MethodGrid } from '@/components/home/MethodGrid';
import { Steps } from '@/components/home/Steps';
import { Options, type OptionValues } from '@/components/Options';
import { SampleCards } from '@/components/SampleCards';
import { REPO_URL, SiteNav } from '@/components/SiteNav';
import { ApiError, runSample, sampleCsvUrl, uploadCsv } from '@/lib/api';

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

  const runSampleNamed = (name: string) => run(name, () => runSample(name));

  return (
    <>
      <SiteNav>
        <a className="nav-link hidden sm:inline-flex" href="#samples">Samples</a>
        <a className="nav-link hidden sm:inline-flex" href="#method">Method</a>
        <a className="nav-link" href={REPO_URL}>GitHub</a>
        <a className="btn btn-solid" href="#upload">Upload</a>
      </SiteNav>
      <main className="mx-auto max-w-6xl space-y-20 px-4 pb-16 md:space-y-28">
        <Hero busy={busy} onTry={() => runSampleNamed('checkout_win')} />
        <Steps />
        <MethodGrid />

        <section aria-labelledby="samples" className="space-y-5">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <p className="eyebrow">Ground truth</p>
              <h2 id="samples" className="h-section mt-1">Try an experiment with a known answer</h2>
            </div>
            {busy && busy !== 'upload' && <p className="muted text-[0.95rem]">The free server can take up to a minute to wake up.</p>}
          </div>
          <SampleCards busy={busy === 'upload' ? 'upload' : busy} onRun={runSampleNamed} />
        </section>

        <section aria-labelledby="upload" className="sheet grid gap-10 lg:grid-cols-2">
          <div className="space-y-4">
            <p className="eyebrow">Your data</p>
            <h2 id="upload" className="h-section">Analyze your own</h2>
            <Dropzone disabled={busy !== null} onFile={upload} onReject={setError} />
            {busy === 'upload' && <p className="pen">analyzing…</p>}
            {error && <p role="alert" className="alert">{error}</p>}
            <Options value={options} onChange={setOptions} />
          </div>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-[var(--ink)]">Expected columns</h3>
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
          </div>
        </section>

        <footer id="method" className="grid gap-6 border-t-2 border-[var(--ink)] pt-8 md:grid-cols-[1fr_2fr]">
          <div>
            <p className="eyebrow">Method</p>
            <p className="wordmark mt-1">Significant</p>
            <a className="muted mt-2 inline-block underline underline-offset-4" href={REPO_URL}>Source on GitHub</a>
          </div>
          <div className="muted space-y-2 text-[0.95rem]">
            <p>CUPED follows Deng et al. (2013); sequential tests use the mixture SPRT of Johari et al. (2017); the SRM check follows Kohavi et al., <i>Trustworthy Online Controlled Experiments</i>.</p>
            <p>The z-test, Welch’s t-test, SRM and power match scipy/statsmodels; CUPED and the mSPRT are checked against their closed forms, and simulations confirm the false-positive rates.</p>
          </div>
        </footer>
      </main>
    </>
  );
}
