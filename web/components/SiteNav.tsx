import Link from 'next/link';
import type { ReactNode } from 'react';

export const REPO_URL = 'https://github.com/Kruthik481/significant';

function Logo() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-6 w-6">
      <rect width="24" height="24" rx="4" fill="var(--ink)" />
      <path d="M4 15.5 H20" stroke="var(--pen)" strokeWidth="1.6" strokeDasharray="2.4 2" />
      <path d="M4.5 5 C 8 5.5, 9 8, 11 12 S 15 19, 19.5 19.5" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function SiteNav({ children }: { children?: ReactNode }) {
  return (
    <header className="site-nav">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="wordmark flex items-center gap-2"><Logo />Significant</Link>
        <nav className="flex items-center gap-1 sm:gap-2">{children}</nav>
      </div>
    </header>
  );
}
