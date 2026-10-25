export default function Loading() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-20">
      <div className="sheet space-y-2" role="status">
        <p className="pen">fetching the report…</p>
        <p className="muted">The free server can take up to a minute to wake up.</p>
      </div>
    </main>
  );
}
