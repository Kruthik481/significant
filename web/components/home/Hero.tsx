import { PenUnderline } from '@/components/Pen';
import { Specimen } from './Specimen';

const TAGS = ['z-test & Welch', 'CUPED', 'Sample-ratio check', 'Always-valid p-values', 'Share links'];

type Props = { busy: string | null; onTry: () => void };

export function Hero({ busy, onTry }: Props) {
  return (
    <section className="grid items-center gap-12 pt-6 md:pt-14 lg:grid-cols-[1.15fr_0.85fr]">
      <div>
        <p className="eyebrow">A/B test analyzer</p>
        <h1 className="h-hero mt-3">An A/B test readout you can <PenUnderline delay={500}>defend.</PenUnderline></h1>
        <p className="lede mt-6">
          Drop in an experiment and get the answer with its uncertainty, after the checks a reviewer would ask for first.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button type="button" className="btn btn-solid btn-lg" disabled={busy !== null} onClick={onTry}>
            {busy === 'checkout_win' ? 'Running the sample…' : 'Run the checkout sample'}
          </button>
          <a className="btn btn-lg" href="#upload">Upload a CSV</a>
        </div>
        {busy && busy !== 'upload' && <p className="muted mt-3 text-[0.95rem]">The free server can take up to a minute to wake up.</p>}
        <ul className="mt-8 flex flex-wrap gap-2" aria-label="What every report includes">
          {TAGS.map((t) => <li key={t} className="tag">{t}</li>)}
        </ul>
      </div>
      <Specimen />
    </section>
  );
}
