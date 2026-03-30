/**
 * id-route.test.ts
 * Tests for GET + PATCH + DELETE /api/projects/[id]
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

import { GET, PATCH, DELETE } from '../[id]/route';

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
  sessions: [],
};

function params(id: string) {
  return { params: Promise.resolve({ id }) };
}

const baseReq = new NextRequest('http://localhost/api/projects/proj-abc123456789012');

beforeEach(() => jest.resetAllMocks());

// ── GET /api/projects/[id] ────────────────────────────────────────────────────

describe('GET /api/projects/[id]', () => {
  test('200 — returns project when found', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);

    const res = await GET(baseReq, params(PROJECT.id));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual(PROJECT);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await GET(baseReq, params('proj-nonexistent'));
    expect(res.status).toBe(404);
  });

  test('500 — when getProject throws', async () => {
    mProjects.getProject.mockRejectedValue(new Error('disk error'));

    const res = await GET(baseReq, params(PROJECT.id));
    expect(res.status).toBe(500);
  });
});

// ── PATCH /api/projects/[id] ──────────────────────────────────────────────────

function patchReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/projects/proj-abc123456789012', {
    method: 'PATCH',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('PATCH /api/projects/[id]', () => {
  test('200 — updates name and returns fresh project', async () => {
    const updated = { ...PROJECT, name: 'New Name', updated_at: '2026-06-01T00:00:00.000Z' };
    mProjects.getProject
      .mockResolvedValueOnce(PROJECT)   // first call: project exists
      .mockResolvedValueOnce(updated);  // second call: re-read after write
    mProjects.writeProject.mockResolvedValue(undefined);

    const res = await PATCH(patchReq({ name: 'New Name' }), params(PROJECT.id));
    expect(res.status).toBe(200);
    expect((await res.json()).name).toBe('New Name');
    expect(mProjects.writeProject).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'New Name', id: PROJECT.id })
    );
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await PATCH(patchReq({ name: 'X' }), params('proj-missing'));
    expect(res.status).toBe(404);
  });

  test('400 — invalid JSON body', async () => {
    const req = new NextRequest('http://localhost/api/projects/proj-abc123456789012', {
      method: 'PATCH',
      body: 'not-json',
      headers: { 'Content-Type': 'application/json' },
    });
    mProjects.getProject.mockResolvedValue(PROJECT);

    const res = await PATCH(req, params(PROJECT.id));
    expect(res.status).toBe(400);
  });

  test('400 — name is empty string (fails zod validation)', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);

    const res = await PATCH(patchReq({ name: '' }), params(PROJECT.id));
    expect(res.status).toBe(400);
  });

  test('immutable fields cannot be changed via PATCH', async () => {
    const fresh = { ...PROJECT, name: 'Same Name', updated_at: '2026-06-01T00:00:00.000Z' };
    mProjects.getProject.mockResolvedValueOnce(PROJECT).mockResolvedValueOnce(fresh);
    mProjects.writeProject.mockResolvedValue(undefined);

    // Attempt to change graphivac_project_id — it is not in the PatchProjectSchema
    await PATCH(patchReq({ name: 'Same Name', graphivac_project_id: 'P-hacked' }), params(PROJECT.id));

    // writeProject should be called with the original graphivac_project_id
    expect(mProjects.writeProject).toHaveBeenCalledWith(
      expect.objectContaining({ graphivac_project_id: 'P-gvtest' })
    );
  });
});

// ── DELETE /api/projects/[id] ─────────────────────────────────────────────────

describe('DELETE /api/projects/[id]', () => {
  test('204 — deletes grids, graphivac project, and folder', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockResolvedValue([SYSTEM]);
    mGraphivac.deleteGrid.mockResolvedValue(undefined);
    mGraphivac.deleteGraphivacProject.mockResolvedValue(undefined);
    mProjects.deleteProjectFromDisk.mockResolvedValue(undefined);

    const res = await DELETE(baseReq, params(PROJECT.id));
    expect(res.status).toBe(204);

    expect(mGraphivac.deleteGrid).toHaveBeenCalledWith(PROJECT.graphivac_project_id, SYSTEM.graphivac_grid_id);
    expect(mGraphivac.deleteGraphivacProject).toHaveBeenCalledWith(PROJECT.graphivac_project_id);
    expect(mProjects.deleteProjectFromDisk).toHaveBeenCalledWith(PROJECT.folder_path);
  });

  test('204 — succeeds even when Graphivac calls fail (best-effort)', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockResolvedValue([SYSTEM]);
    mGraphivac.deleteGrid.mockRejectedValue(new Error('Graphivac unreachable'));
    mGraphivac.deleteGraphivacProject.mockRejectedValue(new Error('Graphivac unreachable'));
    mProjects.deleteProjectFromDisk.mockResolvedValue(undefined);

    const res = await DELETE(baseReq, params(PROJECT.id));
    expect(res.status).toBe(204);
    // Disk deletion must still be called
    expect(mProjects.deleteProjectFromDisk).toHaveBeenCalled();
  });

  test('204 — works when project has no systems', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockResolvedValue([]);
    mGraphivac.deleteGraphivacProject.mockResolvedValue(undefined);
    mProjects.deleteProjectFromDisk.mockResolvedValue(undefined);

    const res = await DELETE(baseReq, params(PROJECT.id));
    expect(res.status).toBe(204);
    expect(mGraphivac.deleteGrid).not.toHaveBeenCalled();
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await DELETE(baseReq, params('proj-missing'));
    expect(res.status).toBe(404);
  });

  test('500 — when disk deletion fails', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockResolvedValue([]);
    mGraphivac.deleteGraphivacProject.mockResolvedValue(undefined);
    mProjects.deleteProjectFromDisk.mockRejectedValue(new Error('EPERM'));

    const res = await DELETE(baseReq, params(PROJECT.id));
    expect(res.status).toBe(500);
  });
});

