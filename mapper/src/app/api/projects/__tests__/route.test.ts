/**
 * route.test.ts
 * Tests for GET + POST /api/projects
 */

import { NextRequest } from 'next/server';
import type { Project } from '@/lib/projects';

// ── Mocks (hoisted before imports) ────────────────────────────────────────────

jest.mock('@/lib/projects');
jest.mock('@/lib/graphivac-client');

import * as projectsLib from '@/lib/projects';
import * as graphivacLib from '@/lib/graphivac-client';

const mProjects = jest.mocked(projectsLib);
const mGraphivac = jest.mocked(graphivacLib);

import { GET, POST } from '../route';

// ── Fixtures ──────────────────────────────────────────────────────────────────

const PROJECT: Project = {
  id: 'proj-abc123456789012',
  name: 'Test Building',
  folder_path: 'proj-abc123456789012',
  graphivac_project_id: 'P-gvtest',
  created_at: '2026-01-01T00:00:00.000Z',
  updated_at: '2026-01-01T00:00:00.000Z',
};

beforeEach(() => jest.resetAllMocks());

// ── GET /api/projects ─────────────────────────────────────────────────────────

describe('GET /api/projects', () => {
  test('200 — returns list of projects', async () => {
    mProjects.listProjects.mockResolvedValue([PROJECT]);

    const res = await GET();
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual([PROJECT]);
  });

  test('200 — returns empty array when no projects exist', async () => {
    mProjects.listProjects.mockResolvedValue([]);

    const res = await GET();
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual([]);
  });

  test('500 — when listProjects throws', async () => {
    mProjects.listProjects.mockRejectedValue(new Error('disk error'));

    const res = await GET();
    expect(res.status).toBe(500);
    const body = await res.json();
    expect(body).toHaveProperty('error');
  });
});

// ── POST /api/projects ────────────────────────────────────────────────────────

function postReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/projects', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('POST /api/projects', () => {
  test('201 — creates project and returns it', async () => {
    mGraphivac.createGraphivacProject.mockResolvedValue('P-new');
    mProjects.createProjectOnDisk.mockResolvedValue({
      ...PROJECT,
      graphivac_project_id: 'P-new',
    });

    const res = await POST(postReq({ name: 'Building A' }));
    expect(res.status).toBe(201);
    const body = await res.json();
    expect(body.graphivac_project_id).toBe('P-new');
    expect(body.name).toBe('Test Building');
  });

  test('201 — createGraphivacProject is called with the project name', async () => {
    mGraphivac.createGraphivacProject.mockResolvedValue('P-new');
    mProjects.createProjectOnDisk.mockResolvedValue(PROJECT);

    await POST(postReq({ name: 'My Building' }));
    expect(mGraphivac.createGraphivacProject).toHaveBeenCalledWith('My Building');
  });

  test('400 — missing name field', async () => {
    const res = await POST(postReq({}));
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body).toHaveProperty('error');
  });

  test('400 — empty name string', async () => {
    const res = await POST(postReq({ name: '' }));
    expect(res.status).toBe(400);
  });

  test('400 — invalid JSON body', async () => {
    const req = new NextRequest('http://localhost/api/projects', {
      method: 'POST',
      body: 'not-json',
      headers: { 'Content-Type': 'application/json' },
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  test('502 — when Graphivac create fails', async () => {
    mGraphivac.createGraphivacProject.mockRejectedValue(new Error('Graphivac down'));

    const res = await POST(postReq({ name: 'Building X' }));
    expect(res.status).toBe(502);
    const body = await res.json();
    expect(body).toHaveProperty('error');
    // Disk operation must NOT have been called
    expect(mProjects.createProjectOnDisk).not.toHaveBeenCalled();
  });

  test('500 — when disk creation fails after Graphivac succeeds', async () => {
    mGraphivac.createGraphivacProject.mockResolvedValue('P-new');
    mProjects.createProjectOnDisk.mockRejectedValue(new Error('ENOSPC'));

    const res = await POST(postReq({ name: 'Building X' }));
    expect(res.status).toBe(500);
  });
});

