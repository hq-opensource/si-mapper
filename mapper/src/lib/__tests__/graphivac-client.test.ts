/**
 * graphivac-client.test.ts
 * Unit tests for mapper/src/lib/graphivac-client.ts
 *
 * global.fetch is spied on so no real HTTP calls are made.
 */

import {
  createGraphivacProject,
  deleteGraphivacProject,
  listGrids,
  createGrid,
  deleteGrid,
} from '../graphivac-client';

// ── Helpers ───────────────────────────────────────────────────────────────────

const BASE_URL = 'https://graphivac.test';
const ORG_ID = 'org-test';

/** Build a minimal fetch-compatible response mock. */
function mockResponse(status: number, body: unknown): Response {
  const text = body === null ? '' : JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: `HTTP ${status}`,
    json: jest.fn().mockResolvedValue(body),
    text: jest.fn().mockResolvedValue(text),
  } as unknown as Response;
}

let fetchSpy: jest.SpyInstance;

beforeEach(() => {
  process.env.GRAPHIVAC_BASE_URL = BASE_URL;
  process.env.GRAPHIVAC_ORG_ID = ORG_ID;
  fetchSpy = jest.spyOn(global, 'fetch');
});

afterEach(() => {
  fetchSpy.mockRestore();
  delete process.env.GRAPHIVAC_BASE_URL;
  delete process.env.GRAPHIVAC_ORG_ID;
});

// ── createGraphivacProject ────────────────────────────────────────────────────

describe('createGraphivacProject', () => {
  test('returns id from response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, { id: 'P-abc' }));
    const id = await createGraphivacProject('Building A');
    expect(id).toBe('P-abc');
  });

  test('POSTs to correct URL with project-name body', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, { id: 'P-xyz' }));
    await createGraphivacProject('Test Project');

    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/v1/orgs/${ORG_ID}/projects`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ 'project-name': 'Test Project' }),
      })
    );
  });

  test('throws descriptive error on non-2xx response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(500, { error: 'boom' }));
    await expect(createGraphivacProject('Failing')).rejects.toThrow('500');
  });

  test('throws when GRAPHIVAC_BASE_URL is missing', async () => {
    delete process.env.GRAPHIVAC_BASE_URL;
    await expect(createGraphivacProject('Test')).rejects.toThrow('GRAPHIVAC_BASE_URL');
  });

  test('throws when GRAPHIVAC_ORG_ID is missing', async () => {
    delete process.env.GRAPHIVAC_ORG_ID;
    await expect(createGraphivacProject('Test')).rejects.toThrow('GRAPHIVAC_ORG_ID');
  });

  test('throws when response body has no id', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, { something: 'else' }));
    await expect(createGraphivacProject('Test')).rejects.toThrow('could not extract id');
  });
});

// ── deleteGraphivacProject ────────────────────────────────────────────────────

describe('deleteGraphivacProject', () => {
  test('resolves on 200', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, {}));
    await expect(deleteGraphivacProject('P-abc')).resolves.toBeUndefined();
  });

  test('resolves on 404 — idempotent, does not throw', async () => {
    fetchSpy.mockResolvedValue(mockResponse(404, { error: 'not found' }));
    await expect(deleteGraphivacProject('P-gone')).resolves.toBeUndefined();
  });

  test('throws on non-200/404 response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(500, {}));
    await expect(deleteGraphivacProject('P-abc')).rejects.toThrow('500');
  });

  test('DELETEs the correct URL', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, {}));
    await deleteGraphivacProject('P-abc123');

    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/v1/orgs/${ORG_ID}/projects/P-abc123`,
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});

// ── listGrids ─────────────────────────────────────────────────────────────────

describe('listGrids', () => {
  test('returns array response directly', async () => {
    const grids = [{ id: 'G-1', title: 'Grid 1' }, { id: 'G-2', title: 'Grid 2' }];
    fetchSpy.mockResolvedValue(mockResponse(200, grids));
    const result = await listGrids('P-proj');
    expect(result).toEqual(grids);
  });

  test('handles wrapped { grids: [...] } response shape', async () => {
    const grids = [{ id: 'G-1', title: 'Grid 1' }];
    fetchSpy.mockResolvedValue(mockResponse(200, { grids }));
    const result = await listGrids('P-proj');
    expect(result).toEqual(grids);
  });

  test('GETs the correct URL', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, []));
    await listGrids('P-projABC');

    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/v1/orgs/${ORG_ID}/projects/P-projABC/grids`,
      expect.objectContaining({ method: 'GET' })
    );
  });

  test('throws on non-2xx response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(403, { error: 'Forbidden' }));
    await expect(listGrids('P-proj')).rejects.toThrow('403');
  });
});

// ── createGrid ────────────────────────────────────────────────────────────────

describe('createGrid', () => {
  test('returns id from response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, { id: 'G-new' }));
    const id = await createGrid('P-proj', 'Chilled Water Plant');
    expect(id).toBe('G-new');
  });

  test('POSTs to correct URL with title body', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, { id: 'G-new' }));
    await createGrid('P-proj123', 'My System');

    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/v1/orgs/${ORG_ID}/projects/P-proj123/grids`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ title: 'My System' }),
      })
    );
  });

  test('throws on non-2xx response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(400, { error: 'Bad Request' }));
    await expect(createGrid('P-proj', 'Bad')).rejects.toThrow('400');
  });

  test('throws when response body has no id', async () => {
    fetchSpy.mockResolvedValue(mockResponse(200, { something: 'else' }));
    await expect(createGrid('P-proj', 'Test')).rejects.toThrow('could not extract id');
  });
});

// ── deleteGrid ────────────────────────────────────────────────────────────────

describe('deleteGrid', () => {
  test('resolves on 204', async () => {
    fetchSpy.mockResolvedValue(mockResponse(204, null));
    await expect(deleteGrid('P-proj', 'G-abc')).resolves.toBeUndefined();
  });

  test('resolves on 404 — idempotent, does not throw', async () => {
    fetchSpy.mockResolvedValue(mockResponse(404, { error: 'not found' }));
    await expect(deleteGrid('P-proj', 'G-gone')).resolves.toBeUndefined();
  });

  test('throws on non-200/404 response', async () => {
    fetchSpy.mockResolvedValue(mockResponse(500, {}));
    await expect(deleteGrid('P-proj', 'G-abc')).rejects.toThrow('500');
  });

  test('DELETEs the correct URL', async () => {
    fetchSpy.mockResolvedValue(mockResponse(204, null));
    await deleteGrid('P-proj123', 'G-grid456');

    expect(fetchSpy).toHaveBeenCalledWith(
      `${BASE_URL}/api/v1/orgs/${ORG_ID}/projects/P-proj123/grids/G-grid456`,
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});

