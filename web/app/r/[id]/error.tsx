'use client';

export default function ReportError({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="mx-auto max-w-2xl px-4 py-20">
      <div className="sheet space-y-4">
        <h1 className="h-section">Could not load this report</h1>
        <p className="muted">The analysis service did not answer. It may be waking up; try again in a minute.</p>
        <button type="button" className="btn" onClick={reset}>Try again</button>
      </div>
    </main>
  );
}
