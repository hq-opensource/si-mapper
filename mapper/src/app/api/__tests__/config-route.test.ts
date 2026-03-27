/**
 * config-route.test.ts
 * Tests for GET /api/config
 *
 * The config route reads GRAPHIVAC_PUBLIC_BASE_URL (with fallback to
 * GRAPHIVAC_BASE_URL) and GRAPHIVAC_ORG_ID from env vars and returns them as
 * JSON. These tests verify the happy path, the fallback behaviour, and the
 * precedence of GRAPHIVAC_PUBLIC_BASE_URL over GRAPHIVAC_BASE_URL.
 */

import { GET } from '../config/route';

// ── Setup ─────────────────────────────────────────────────────────────────────

const BASE_URL = 'https://graphivac.hvac.io';
const PUBLIC_BASE_URL = 'http://localhost:8888';
const ORG_ID = 'test-org-id';

beforeEach(() => {
  process.env.GRAPHIVAC_BASE_URL = BASE_URL;
  process.env.GRAPHIVAC_ORG_ID = ORG_ID;
  delete process.env.GRAPHIVAC_PUBLIC_BASE_URL;
});

afterEach(() => {
  delete process.env.GRAPHIVAC_BASE_URL;
  delete process.env.GRAPHIVAC_ORG_ID;
  delete process.env.GRAPHIVAC_PUBLIC_BASE_URL;
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('GET /api/config', () => {
  test('200 — returns GRAPHIVAC_BASE_URL as graphivacBaseUrl when PUBLIC var is absent', async () => {
    const res = await GET();

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({
      graphivacBaseUrl: BASE_URL,
      graphivacOrgId: ORG_ID,
    });
  });

  test('200 — GRAPHIVAC_PUBLIC_BASE_URL takes precedence over GRAPHIVAC_BASE_URL', async () => {
    process.env.GRAPHIVAC_PUBLIC_BASE_URL = PUBLIC_BASE_URL;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.graphivacBaseUrl).toBe(PUBLIC_BASE_URL);
    expect(body.graphivacOrgId).toBe(ORG_ID);
  });

  test('200 — returns empty string for graphivacBaseUrl when neither var is set', async () => {
    delete process.env.GRAPHIVAC_BASE_URL;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.graphivacBaseUrl).toBe('');
    expect(body.graphivacOrgId).toBe(ORG_ID);
  });

  test('200 — returns empty strings when GRAPHIVAC_BASE_URL is not set', async () => {
    delete process.env.GRAPHIVAC_BASE_URL;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.graphivacBaseUrl).toBe('');
    expect(body.graphivacOrgId).toBe(ORG_ID);
  });

  test('200 — returns empty strings when GRAPHIVAC_ORG_ID is not set', async () => {
    delete process.env.GRAPHIVAC_ORG_ID;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.graphivacBaseUrl).toBe(BASE_URL);
    expect(body.graphivacOrgId).toBe('');
  });

  test('200 — returns both as empty strings when neither env var is set', async () => {
    delete process.env.GRAPHIVAC_BASE_URL;
    delete process.env.GRAPHIVAC_ORG_ID;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({
      graphivacBaseUrl: '',
      graphivacOrgId: '',
    });
  });

  test('body contains exactly the two expected keys', async () => {
    const res = await GET();
    const body = await res.json();
    expect(Object.keys(body).sort()).toEqual(['graphivacBaseUrl', 'graphivacOrgId']);
  });
});


// ── Tests ─────────────────────────────────────────────────────────────────────

describe('GET /api/config', () => {
  test('200 — returns graphivacBaseUrl and graphivacOrgId from env vars', async () => {
    const res = await GET();

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({
      graphivacBaseUrl: BASE_URL,
      graphivacOrgId: ORG_ID,
    });
  });

  test('200 — returns empty strings when GRAPHIVAC_BASE_URL is not set', async () => {
    delete process.env.GRAPHIVAC_BASE_URL;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.graphivacBaseUrl).toBe('');
    expect(body.graphivacOrgId).toBe(ORG_ID);
  });

  test('200 — returns empty strings when GRAPHIVAC_ORG_ID is not set', async () => {
    delete process.env.GRAPHIVAC_ORG_ID;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.graphivacBaseUrl).toBe(BASE_URL);
    expect(body.graphivacOrgId).toBe('');
  });

  test('200 — returns both as empty strings when neither env var is set', async () => {
    delete process.env.GRAPHIVAC_BASE_URL;
    delete process.env.GRAPHIVAC_ORG_ID;

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({
      graphivacBaseUrl: '',
      graphivacOrgId: '',
    });
  });

  test('body contains exactly the two expected keys', async () => {
    const res = await GET();
    const body = await res.json();
    expect(Object.keys(body).sort()).toEqual(['graphivacBaseUrl', 'graphivacOrgId']);
  });
});

