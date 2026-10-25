import type { ReactNode } from 'react';

// Hand-drawn red-pen marks. Each path uses pathLength=1 so the CSS draw animation works at any size.

export function PenCircle({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  return (
    <span className="relative inline-block px-2">
      {children}
      <svg aria-hidden="true" viewBox="0 0 120 50" preserveAspectRatio="none" className="pointer-events-none absolute overflow-visible"
        style={{ left: -6, top: -10, width: 'calc(100% + 12px)', height: 'calc(100% + 20px)' }}>
        <path pathLength={1} className="pen-stroke" style={{ animationDelay: `${delay}ms` }}
          d="M64 4 C 30 2, 4 12, 5 26 C 6 42, 40 48, 70 46 C 100 44, 118 34, 115 20 C 112 7, 86 2, 52 6" />
      </svg>
    </span>
  );
}

export function PenUnderline({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  return (
    <span className="relative inline-block">
      {children}
      <svg aria-hidden="true" viewBox="0 0 100 8" preserveAspectRatio="none"
        className="pointer-events-none absolute -bottom-2 left-0 h-2.5 w-full overflow-visible">
        <path pathLength={1} className="pen-stroke" style={{ animationDelay: `${delay}ms` }}
          d="M1 5 C 20 2, 35 7, 52 4 S 85 3, 99 5" />
      </svg>
    </span>
  );
}

export function MarginNote({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  return (
    <p className="pen pen-fade flex items-start gap-2 text-[1.6rem]" style={{ animationDelay: `${delay}ms` }}>
      <svg aria-hidden="true" viewBox="0 0 28 20" className="mt-1 h-5 w-7 shrink-0 overflow-visible">
        <path pathLength={1} className="pen-stroke" style={{ animationDelay: `${delay}ms` }} d="M2 3 C 8 14, 16 16, 25 12 M19 8 L 25 12 L 19 17" />
      </svg>
      <span>{children}</span>
    </p>
  );
}
