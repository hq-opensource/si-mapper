/**
 * files-route.test.ts
 * Tests for:
 *   GET  /api/projects/[id]/systems/[sysId]/files
 *   POST /api/projects/[id]/systems/[sysId]/files
 *   DELETE /api/projects/[id]/systems/[sysId]/files/[filename]
 *
 * Real file-system operations run against a temp directory.
 * Only @/lib/projects is mocked so that systemDir returns the temp dir.
 */

import fs from 'fs/promises';
import os from 'os';
import path from 'path';
import { NextRequest } from 'next/server';
import type { Project, System } from '@/lib/projects';

// ── Mocks ─────────────────────────────────────────────────────────────────────

jest.mock('@/lib/projects');

import * as projectsLib from '@/lib/projects';

const mProjects = jest.mocked(projectsLib);

import { GET as getFiles, POST as uploadFiles } from '../[id]/systems/[sysId]/files/route';
import { DELETE as deleteFile } from '../[id]/systems/[sysId]/files/[filename]/route';

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

// ── Temp dir setup ────────────────────────────────────────────────────────────

let tmpDir: string;

beforeEach(async () => {
  jest.resetAllMocks();

  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'si-mapper-files-test-'));

  mProjects.getProject.mockResolvedValue(PROJECT);
  mProjects.getSystem.mockResolvedValue(SYSTEM);
  mProjects.systemDir.mockReturnValue(tmpDir);
});

afterEach(async () => {
  await fs.rm(tmpDir, { recursive: true, force: true });
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function filesParams(id: string, sysId: string) {
  return { params: Promise.resolve({ id, sysId }) };
}

function fileParams(id: string, sysId: string, filename: string) {
  return { params: Promise.resolve({ id, sysId, filename }) };
}

const baseUrl = `http://localhost/api/projects/${PROJECT.id}/systems/${SYSTEM.id}/files`;

// ── GET /files ────────────────────────────────────────────────────────────────

describe('GET /api/projects/[id]/systems/[sysId]/files', () => {
  test('200 — returns empty array when folder has no files', async () => {
    const req = new NextRequest(baseUrl);
    const res = await getFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual([]);
  });

  test('200 — lists files with name, size, modified_at, url', async () => {
    await fs.writeFile(path.join(tmpDir, 'points.csv'), 'a,b,c');
    await fs.writeFile(path.join(tmpDir, 'schema.json'), '{}');

    const req = new NextRequest(baseUrl);
    const res = await getFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveLength(2);

    const names = body.map((f: { name: string }) => f.name).sort();
    expect(names).toEqual(['points.csv', 'schema.json'].sort());

    const first = body.find((f: { name: string }) => f.name === 'points.csv');
    expect(first).toMatchObject({
      name: 'points.csv',
      size: expect.any(Number),
      modified_at: expect.any(String),
      url: expect.stringContaining('points.csv'),
    });
  });

  test('200 — does not list subdirectories', async () => {
    await fs.mkdir(path.join(tmpDir, 'subdir'));
    await fs.writeFile(path.join(tmpDir, 'file.txt'), 'hello');

    const req = new NextRequest(baseUrl);
    const res = await getFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    const body = await res.json();
    expect(body).toHaveLength(1);
    expect(body[0].name).toBe('file.txt');
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const req = new NextRequest(baseUrl);
    const res = await getFiles(req, filesParams('proj-missing', SYSTEM.id));
    expect(res.status).toBe(404);
  });

  test('404 — when system does not exist', async () => {
    mProjects.getSystem.mockResolvedValue(null);

    const req = new NextRequest(baseUrl);
    const res = await getFiles(req, filesParams(PROJECT.id, 'sys-missing'));
    expect(res.status).toBe(404);
  });
});

// ── POST /files ───────────────────────────────────────────────────────────────

function makeUploadReq(files: { name: string; content: string }[], overwrite = false): NextRequest {
  const formData = new FormData();
  for (const f of files) {
    const blob = new Blob([f.content], { type: 'text/plain' });
    formData.append('files', blob, f.name);
  }
  if (overwrite) formData.append('overwrite', 'true');

  return new NextRequest(baseUrl, { method: 'POST', body: formData });
}

describe('POST /api/projects/[id]/systems/[sysId]/files', () => {
  test('200 — uploads a single file and returns metadata', async () => {
    const req = makeUploadReq([{ name: 'data.csv', content: 'col1,col2\n1,2' }]);
    const res = await uploadFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.uploaded).toHaveLength(1);
    expect(body.uploaded[0]).toMatchObject({
      name: 'data.csv',
      size: expect.any(Number),
      url: expect.stringContaining('data.csv'),
    });

    // File should actually exist on disk
    const exists = await fs.access(path.join(tmpDir, 'data.csv')).then(() => true).catch(() => false);
    expect(exists).toBe(true);
  });

  test('200 — uploads multiple files in one request', async () => {
    const req = makeUploadReq([
      { name: 'a.txt', content: 'aaa' },
      { name: 'b.txt', content: 'bbb' },
    ]);
    const res = await uploadFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(200);
    expect((await res.json()).uploaded).toHaveLength(2);
  });

  test('409 — when file already exists and overwrite is false (default)', async () => {
    await fs.writeFile(path.join(tmpDir, 'existing.csv'), 'old content');

    const req = makeUploadReq([{ name: 'existing.csv', content: 'new content' }]);
    const res = await uploadFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(409);

    // Original file must be untouched
    const content = await fs.readFile(path.join(tmpDir, 'existing.csv'), 'utf-8');
    expect(content).toBe('old content');
  });

  test('200 — overwrites existing file when overwrite=true', async () => {
    await fs.writeFile(path.join(tmpDir, 'existing.csv'), 'old content');

    const req = makeUploadReq([{ name: 'existing.csv', content: 'new content' }], true);
    const res = await uploadFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(200);
    const content = await fs.readFile(path.join(tmpDir, 'existing.csv'), 'utf-8');
    expect(content).toBe('new content');
  });

  test('400 — no files provided in form data', async () => {
    const formData = new FormData();
    const req = new NextRequest(baseUrl, { method: 'POST', body: formData });
    const res = await uploadFiles(req, filesParams(PROJECT.id, SYSTEM.id));

    expect(res.status).toBe(400);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const req = makeUploadReq([{ name: 'f.txt', content: 'x' }]);
    const res = await uploadFiles(req, filesParams('proj-missing', SYSTEM.id));
    expect(res.status).toBe(404);
  });
});

// ── DELETE /files/[filename] ──────────────────────────────────────────────────

describe('DELETE /api/projects/[id]/systems/[sysId]/files/[filename]', () => {
  test('204 — deletes an existing file', async () => {
    await fs.writeFile(path.join(tmpDir, 'target.csv'), 'delete me');

    const req = new NextRequest(`${baseUrl}/target.csv`, { method: 'DELETE' });
    const res = await deleteFile(req, fileParams(PROJECT.id, SYSTEM.id, 'target.csv'));

    expect(res.status).toBe(204);
    const exists = await fs.access(path.join(tmpDir, 'target.csv')).then(() => true).catch(() => false);
    expect(exists).toBe(false);
  });

  test('204 — URL-encoded filename is decoded', async () => {
    await fs.writeFile(path.join(tmpDir, 'my file.csv'), 'content');

    const req = new NextRequest(`${baseUrl}/my%20file.csv`, { method: 'DELETE' });
    const res = await deleteFile(req, fileParams(PROJECT.id, SYSTEM.id, 'my%20file.csv'));

    expect(res.status).toBe(204);
  });

  test('404 — when file does not exist', async () => {
    const req = new NextRequest(`${baseUrl}/ghost.csv`, { method: 'DELETE' });
    const res = await deleteFile(req, fileParams(PROJECT.id, SYSTEM.id, 'ghost.csv'));

    expect(res.status).toBe(404);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);

    const req = new NextRequest(`${baseUrl}/f.csv`, { method: 'DELETE' });
    const res = await deleteFile(req, fileParams('proj-missing', SYSTEM.id, 'f.csv'));

    expect(res.status).toBe(404);
  });

  test('404 — when system does not exist', async () => {
    mProjects.getSystem.mockResolvedValue(null);

    const req = new NextRequest(`${baseUrl}/f.csv`, { method: 'DELETE' });
    const res = await deleteFile(req, fileParams(PROJECT.id, 'sys-missing', 'f.csv'));

    expect(res.status).toBe(404);
  });

  test('400 — path traversal attempt is rejected', async () => {
    const req = new NextRequest(`${baseUrl}/..%2Fother`, { method: 'DELETE' });
    const res = await deleteFile(req, fileParams(PROJECT.id, SYSTEM.id, '..%2Fother'));

    // Either 400 (traversal detected) or 404 (path resolves outside, file not found)
    expect([400, 404]).toContain(res.status);
  });
});

