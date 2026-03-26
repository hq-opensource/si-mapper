/**
 * sysid-route.test.ts
 * Tests for GET + PATCH + DELETE /api/projects/[id]/systems/[sysId]
 */

import { NextRequest } from 'next/server';
import type { Project, System } from '@/lib/projects';

// ── Mocks ─────────────────────────────────────────────────────────────────────

jest.mock('@/lib/projects');
jest.mock('@/lib/graphivac-client');

import * as projectsLib from '@/lib/projects';
import * as graphivacLib from '@/lib/graphivac-client';

const mProjects = jest.mocked(projectsLib);
const mGraphivac = jest.mocked(graphivacLib);

import { GET, PATCH, DELETE } from '../[id]/systems/[sysId]/route';

// ── Fixtures ──────────────────────────────────────────────────────────────────

const PROJECT: Project = {
  id: 'proj-abc123456789012',
  name: 'Test Building',
  folder_path: 'proj-abc123456789012',
  graphivac_project_id: 'P-gvtest',
  created_at: '2026-01-01T00:00:00.000Z',
  updated_at: '2026-01-01T00:00:00.000Z',
};

const SYSTEM: System = {
  id: 'sys-xyz789012345678',
  name: 'Chilled Water Plant',
  folder_path: 'sys-xyz789012345678',
  graphivac_grid_id: 'G-gridtest',
  ai_model_name: 'gemini-pro',
  created_at: '2026-01-01T00:00:00.000Z',
  updated_at: '2026-01-01T00:00:00.000Z',
};

function params(id: string, sysId: string) {
  return { params: Promise.resolve({ id, sysId }) };
}

const baseReq = new NextRequest(
  `http://localhost/api/projects/${PROJECT.id}/systems/${SYSTEM.id}`
);

beforeEach(() => jest.resetAllMocks());

// ── GET /api/projects/[id]/systems/[sysId] ────────────────────────────────────

describe('GET /api/projects/[id]/systems/[sysId]', () => {
  test('200 — returns system when found', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(SYSTEM);

    const res = await GET(baseReq, params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual(SYSTEM);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await GET(baseReq, params('proj-missing', SYSTEM.id));
    expect(res.status).toBe(404);
  });

  test('404 — when system does not exist in the project', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(null);

    const res = await GET(baseReq, params(PROJECT.id, 'sys-missing'));
    expect(res.status).toBe(404);
  });
});

// ── PATCH /api/projects/[id]/systems/[sysId] ──────────────────────────────────

function patchReq(body: unknown): NextRequest {
  return new NextRequest(
    `http://localhost/api/projects/${PROJECT.id}/systems/${SYSTEM.id}`,
    {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

describe('PATCH /api/projects/[id]/systems/[sysId]', () => {
  test('200 — updates name and returns fresh system', async () => {
    const updated = { ...SYSTEM, name: 'AHU-1', updated_at: '2026-06-01T00:00:00.000Z' };
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem
      .mockResolvedValueOnce(SYSTEM)   // first call: exists
      .mockResolvedValueOnce(updated); // second call: re-read after write
    mProjects.writeSystem.mockResolvedValue(undefined);

    const res = await PATCH(patchReq({ name: 'AHU-1' }), params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(200);
    expect((await res.json()).name).toBe('AHU-1');
    expect(mProjects.writeSystem).toHaveBeenCalledWith(
      PROJECT.folder_path,
      expect.objectContaining({ name: 'AHU-1', id: SYSTEM.id })
    );
  });

  test('200 — updates ai_model_name', async () => {
    const updated = { ...SYSTEM, ai_model_name: 'gpt-4o', updated_at: '2026-06-01T00:00:00.000Z' };
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValueOnce(SYSTEM).mockResolvedValueOnce(updated);
    mProjects.writeSystem.mockResolvedValue(undefined);

    const res = await PATCH(patchReq({ ai_model_name: 'gpt-4o' }), params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(200);
    expect((await res.json()).ai_model_name).toBe('gpt-4o');
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await PATCH(patchReq({ name: 'X' }), params('proj-missing', SYSTEM.id));
    expect(res.status).toBe(404);
  });

  test('404 — when system does not exist', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(null);

    const res = await PATCH(patchReq({ name: 'X' }), params(PROJECT.id, 'sys-missing'));
    expect(res.status).toBe(404);
  });

  test('400 — empty name string fails validation', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(SYSTEM);

    const res = await PATCH(patchReq({ name: '' }), params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(400);
  });

  test('immutable fields are not changed by PATCH', async () => {
    const fresh = { ...SYSTEM, updated_at: '2026-06-01T00:00:00.000Z' };
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValueOnce(SYSTEM).mockResolvedValueOnce(fresh);
    mProjects.writeSystem.mockResolvedValue(undefined);

    // Attempt to change graphivac_grid_id — not in PatchSystemSchema
    await PATCH(
      patchReq({ name: 'CWP', graphivac_grid_id: 'G-hacked' }),
      params(PROJECT.id, SYSTEM.id)
    );

    expect(mProjects.writeSystem).toHaveBeenCalledWith(
      PROJECT.folder_path,
      expect.objectContaining({ graphivac_grid_id: 'G-gridtest' })
    );
  });
});

// ── DELETE /api/projects/[id]/systems/[sysId] ─────────────────────────────────

describe('DELETE /api/projects/[id]/systems/[sysId]', () => {
  test('204 — deletes grid and system folder', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(SYSTEM);
    mGraphivac.deleteGrid.mockResolvedValue(undefined);
    mProjects.deleteSystemFromDisk.mockResolvedValue(undefined);

    const res = await DELETE(baseReq, params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(204);

    expect(mGraphivac.deleteGrid).toHaveBeenCalledWith(
      PROJECT.graphivac_project_id,
      SYSTEM.graphivac_grid_id
    );
    expect(mProjects.deleteSystemFromDisk).toHaveBeenCalledWith(
      PROJECT.folder_path,
      SYSTEM.folder_path
    );
  });

  test('204 — still deletes folder when Graphivac call fails (best-effort)', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(SYSTEM);
    mGraphivac.deleteGrid.mockRejectedValue(new Error('Graphivac down'));
    mProjects.deleteSystemFromDisk.mockResolvedValue(undefined);

    const res = await DELETE(baseReq, params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(204);
    expect(mProjects.deleteSystemFromDisk).toHaveBeenCalled();
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await DELETE(baseReq, params('proj-missing', SYSTEM.id));
    expect(res.status).toBe(404);
  });

  test('404 — when system does not exist', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(null);

    const res = await DELETE(baseReq, params(PROJECT.id, 'sys-missing'));
    expect(res.status).toBe(404);
  });

  test('500 — when disk deletion fails', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.getSystem.mockResolvedValue(SYSTEM);
    mGraphivac.deleteGrid.mockResolvedValue(undefined);
    mProjects.deleteSystemFromDisk.mockRejectedValue(new Error('EPERM'));

    const res = await DELETE(baseReq, params(PROJECT.id, SYSTEM.id));
    expect(res.status).toBe(500);
  });
});

