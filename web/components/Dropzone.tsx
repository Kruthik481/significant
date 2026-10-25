'use client';

import { useRef, useState } from 'react';
import { MAX_UPLOAD_MB } from '@/lib/samples';

type Props = { disabled: boolean; onFile: (file: File) => void; onReject: (message: string) => void };

export function Dropzone({ disabled, onFile, onReject }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const accept = (file: File | undefined) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) return onReject('Choose a .csv file.');
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return onReject(`That file is over ${MAX_UPLOAD_MB} MB.`);
    onFile(file);
  };

  return (
    <div className="dropzone" data-over={over}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); if (!disabled) accept(e.dataTransfer.files[0]); }}>
      <p className="text-lg text-[var(--ink)]">Drop an experiment CSV here</p>
      <p className="muted text-[0.95rem]">or</p>
      <button type="button" className="btn mt-2" disabled={disabled} onClick={() => input.current?.click()}>
        Choose a file
      </button>
      <input ref={input} type="file" accept=".csv,text/csv" className="sr-only" aria-label="Experiment CSV file"
        onChange={(e) => { accept(e.target.files?.[0]); e.target.value = ''; }} />
    </div>
  );
}
