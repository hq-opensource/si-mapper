/**
 * systems-route.test.ts
 * Tests for GET + POST /api/projects/[id]/systems
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

import { GET, POST } from '../[id]/systems/route';

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
  created_at: '2026-01-01T00:00:00.000Z',
  updated_at: '2026-01-01T00:00:00.000Z',
};

function params(id: string) {
  return { params: Promise.resolve({ id }) };
}

const baseReq = new NextRequest(`http://localhost/api/projects/${PROJECT.id}/systems`);

beforeEach(() => jest.resetAllMocks());

// ── GET /api/projects/[id]/systems ────────────────────────────────────────────

describe('GET /api/projects/[id]/systems', () => {
  test('200 — returns systems for the project', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockResolvedValue([SYSTEM]);

    const res = await GET(baseReq, params(PROJECT.id));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual([SYSTEM]);
  });

  test('200 — returns empty array when project has no systems', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockResolvedValue([]);

    const res = await GET(baseReq, params(PROJECT.id));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual([]);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await GET(baseReq, params('proj-missing'));
    expect(res.status).toBe(404);
  });

  test('500 — when listSystems throws', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mProjects.listSystems.mockRejectedValue(new Error('disk error'));

    const res = await GET(baseReq, params(PROJECT.id));
    expect(res.status).toBe(500);
  });
});

// ── POST /api/projects/[id]/systems ───────────────────────────────────────────

function postReq(body: unknown): NextRequest {
  return new NextRequest(`http://localhost/api/projects/${PROJECT.id}/systems`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('POST /api/projects/[id]/systems', () => {
  test('201 — creates system and returns it', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mGraphivac.createGrid.mockResolvedValue('G-new');
    mProjects.createSystemOnDisk.mockResolvedValue({ ...SYSTEM, graphivac_grid_id: 'G-new' });

    const res = await POST(postReq({ name: 'CWP' }), params(PROJECT.id));
    expect(res.status).toBe(201);
    const body = await res.json();
    expect(body.graphivac_grid_id).toBe('G-new');
  });

  test('201 — createGrid is called with the project graphivac id and system name', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mGraphivac.createGrid.mockResolvedValue('G-new');
    mProjects.createSystemOnDisk.mockResolvedValue(SYSTEM);

    await POST(postReq({ name: 'AHU-1' }), params(PROJECT.id));

    expect(mGraphivac.createGrid).toHaveBeenCalledWith(PROJECT.graphivac_project_id, 'AHU-1');
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const res = await POST(postReq({ name: 'X' }), params('proj-missing'));
    expect(res.status).toBe(404);
  });

  test('400 — missing name', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);

    const res = await POST(postReq({}), params(PROJECT.id));
    expect(res.status).toBe(400);
  });

  test('400 — invalid JSON', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    const req = new NextRequest(`http://localhost/api/projects/${PROJECT.id}/systems`, {
      method: 'POST',
      body: '{bad',
      headers: { 'Content-Type': 'application/json' },
    });

    const res = await POST(req, params(PROJECT.id));
    expect(res.status).toBe(400);
  });

  test('502 — when Graphivac grid creation fails', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mGraphivac.createGrid.mockRejectedValue(new Error('Graphivac down'));

    const res = await POST(postReq({ name: 'CWP' }), params(PROJECT.id));
    expect(res.status).toBe(502);
    // Disk write must NOT have been called
    expect(mProjects.createSystemOnDisk).not.toHaveBeenCalled();
  });

  test('500 — when disk creation fails after Graphivac succeeds', async () => {
    mProjects.getProject.mockResolvedValue(PROJECT);
    mGraphivac.createGrid.mockResolvedValue('G-new');
    mProjects.createSystemOnDisk.mockRejectedValue(new Error('ENOSPC'));

    const res = await POST(postReq({ name: 'CWP' }), params(PROJECT.id));
    expect(res.status).toBe(500);
  });
});

