import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-20">
      <div className="sheet space-y-4">
        <h1 className="h-display">Report not found</h1>
        <p className="lede">This link is mistyped, or the report is older than 90 days and was deleted.</p>
        <Link href="/" className="btn btn-solid">Run a new analysis</Link>
      </div>
    </main>
  );
}
