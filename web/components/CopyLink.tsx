'use client';

import { useState } from 'react';

export function CopyLink() {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };
  return (
    <button type="button" data-testid="copy-link" className="btn" onClick={copy} aria-live="polite">
      {copied ? 'Link copied' : 'Copy link'}
    </button>
  );
}
