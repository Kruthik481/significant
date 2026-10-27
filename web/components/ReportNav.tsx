'use client';

import { useEffect, useState } from 'react';
import { REPORT_SECTIONS } from '@/lib/sections';


// Highlights the section currently in the upper part of the viewport.
export function ReportNav() {
  const [active, setActive] = useState<string>(REPORT_SECTIONS[0][0]);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: '-15% 0px -70% 0px' },
    );
    REPORT_SECTIONS.forEach(([id]) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);
  return (
    <nav aria-label="Report sections">
      <ol className="space-y-1">
        {REPORT_SECTIONS.map(([id, label], i) => (
          <li key={id}>
            <a href={`#${id}`} className="toc-link" aria-current={active === id ? 'true' : undefined}>
              <span className="data text-xs">{String(i + 1).padStart(2, '0')}</span>{label}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
