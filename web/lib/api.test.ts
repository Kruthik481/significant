// api.test.ts
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, runSample } from './api';

afterEach(() => vi.unstubAllGlobals());

describe('api', () => {
  it('returns the created report', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response(JSON.stringify({ id: 'abc', report: { verdict: 'not_significant' } }), { status: 201 })));
    await expect(runSample('pricing_null')).resolves.toMatchObject({ id: 'abc' });
  });
  it('raises the server error code and message', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response(JSON.stringify({ error: { code: 'rate_limited', message: 'Slow down.' } }), { status: 429 })));
    const err = await runSample('x').catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 429, code: 'rate_limited', message: 'Slow down.' });
  });
});
