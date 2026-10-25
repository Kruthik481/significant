import type { Created, PowerBody, SampleInfo, StoredReport, UploadOptions } from './types';

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8300';

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(0, 'network', 'Could not reach the analysis service. It may be waking up; try again in a minute.');
  }
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err = (body as { error?: { code?: string; message?: string } } | null)?.error;
    throw new ApiError(res.status, err?.code ?? 'http_error', err?.message ?? `Request failed (${res.status}).`);
  }
  return body as T;
}

export const listSamples = () => request<SampleInfo[]>('/samples');
export const runSample = (name: string) => request<Created>(`/analyses/samples/${encodeURIComponent(name)}`, { method: 'POST' });
export const getReport = (id: string, init?: RequestInit) => request<StoredReport>(`/analyses/${encodeURIComponent(id)}`, init);
export const sampleCsvUrl = (name: string) => `${API_URL}/samples/${encodeURIComponent(name)}.csv`;

export function uploadCsv(file: File, opts: UploadOptions = {}): Promise<Created> {
  const form = new FormData();
  form.set('file', file);
  if (opts.name) form.set('name', opts.name);
  if (opts.control) form.set('control', opts.control);
  if (opts.expectedSplit !== undefined) form.set('expected_split', String(opts.expectedSplit));
  if (opts.alpha !== undefined) form.set('alpha', String(opts.alpha));
  return request<Created>('/analyses', { method: 'POST', body: form });
}

export const power = (body: PowerBody) =>
  request<{ n_per_arm: number; total: number }>('/power', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
