'use client';

import { useInView } from 'motion/react';
import { useRef, type ReactNode } from 'react';

// Marks its subtree data-seen once scrolled into view; CSS (.draw, .rise) runs the animations.
export function InView({ className, children }: { className?: string; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: '0px 0px -60px 0px' });
  return <div ref={ref} className={className} data-seen={seen}>{children}</div>;
}
