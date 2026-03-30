/**
 * folders-route.test.ts
 * Tests for:
 *   GET  /api/projects/[id]/systems/[sysId]/folders
 *   POST /api/projects/[id]/systems/[sysId]/folders
 *   PATCH  /api/projects/[id]/systems/[sysId]/folders/[folderName]
 *   DELETE /api/projects/[id]/systems/[sysId]/folders/[folderName]
 *
 * Also tests the subfolder-aware behaviour added to the existing files routes:
 *   GET  /api/projects/[id]/systems/[sysId]/files?subfolder=X
 *   POST /api/projects/[id]/systems/[sysId]/files  (with subfolder form field)
 *   DELETE /api/projects/[id]/systems/[sysId]/files/[filename]?subfolder=X
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

import { GET as getFolders, POST as createFolder } from '../[id]/systems/[sysId]/folders/route';
import {
  PATCH as renameFolder,
  DELETE as deleteFolder,
} from '../[id]/systems/[sysId]/folders/[folderName]/route';
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
  ai_model_name: 'gemini-pro',
  created_at: '2026-01-01T00:00:00.000Z',
  updated_at: '2026-01-01T00:00:00.000Z',
  sessions: [],
};

// ── Temp dir setup ────────────────────────────────────────────────────────────

let tmpDir: string;

beforeEach(async () => {
  jest.resetAllMocks();
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'si-mapper-folders-test-'));
  mProjects.getProject.mockResolvedValue(PROJECT);
  mProjects.getSystem.mockResolvedValue(SYSTEM);
  mProjects.systemDir.mockReturnValue(tmpDir);
});

afterEach(async () => {
  await fs.rm(tmpDir, { recursive: true, force: true });
});

// ── Param helpers ─────────────────────────────────────────────────────────────

const foldersBaseUrl = `http://localhost/api/projects/${PROJECT.id}/systems/${SYSTEM.id}/folders`;
const filesBaseUrl   = `http://localhost/api/projects/${PROJECT.id}/systems/${SYSTEM.id}/files`;

function foldersParams() {
  return { params: Promise.resolve({ id: PROJECT.id, sysId: SYSTEM.id }) };
}

function folderNameParams(folderName: string) {
  return { params: Promise.resolve({ id: PROJECT.id, sysId: SYSTEM.id, folderName }) };
}

function filesParams() {
  return { params: Promise.resolve({ id: PROJECT.id, sysId: SYSTEM.id }) };
}

function fileParams(filename: string) {
  return { params: Promise.resolve({ id: PROJECT.id, sysId: SYSTEM.id, filename }) };
}

// ── GET /folders ──────────────────────────────────────────────────────────────

describe('GET /api/.../folders', () => {
  test('200 — returns empty array when no subdirectories exist', async () => {
    const req = new NextRequest(foldersBaseUrl);
    const res = await getFolders(req, foldersParams());
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual([]);
  });

  test('200 — lists subdirectories with name and file_count', async () => {
    await fs.mkdir(path.join(tmpDir, 'schemas'));
    await fs.writeFile(path.join(tmpDir, 'schemas', 'a.json'), '{}');
    await fs.writeFile(path.join(tmpDir, 'schemas', 'b.json'), '{}');
    await fs.mkdir(path.join(tmpDir, 'docs'));

    const req = new NextRequest(foldersBaseUrl);
    const res = await getFolders(req, foldersParams());
    expect(res.status).toBe(200);
    const body: { name: string; file_count: number }[] = await res.json();
    expect(body).toHaveLength(2);
    const schemas = body.find(f => f.name === 'schemas');
    expect(schemas?.file_count).toBe(2);
    const docs = body.find(f => f.name === 'docs');
    expect(docs?.file_count).toBe(0);
  });

  test('200 — does not include plain files as folders', async () => {
    await fs.writeFile(path.join(tmpDir, 'system.json'), '{}');
    await fs.writeFile(path.join(tmpDir, 'data.csv'), 'a,b');

    const req = new NextRequest(foldersBaseUrl);
    const res = await getFolders(req, foldersParams());
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual([]);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);
    const req = new NextRequest(foldersBaseUrl);
    const res = await getFolders(req, foldersParams());
    expect(res.status).toBe(404);
  });

  test('404 — when system does not exist', async () => {
    mProjects.getSystem.mockResolvedValue(null);
    const req = new NextRequest(foldersBaseUrl);
    const res = await getFolders(req, foldersParams());
    expect(res.status).toBe(404);
  });
});

// ── POST /folders ─────────────────────────────────────────────────────────────

describe('POST /api/.../folders', () => {
  function postReq(body: unknown): NextRequest {
    return new NextRequest(foldersBaseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  test('201 — creates a new directory', async () => {
    const res = await createFolder(postReq({ name: 'schemas' }), foldersParams());
    expect(res.status).toBe(201);
    const body = await res.json();
    expect(body.name).toBe('schemas');
    expect(body.file_count).toBe(0);

    const stat = await fs.stat(path.join(tmpDir, 'schemas'));
    expect(stat.isDirectory()).toBe(true);
  });

  test('409 — returns conflict when folder already exists', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    const res = await createFolder(postReq({ name: 'docs' }), foldersParams());
    expect(res.status).toBe(409);
  });

  test('400 — rejects invalid folder names (path separators)', async () => {
    const res = await createFolder(postReq({ name: '../escape' }), foldersParams());
    expect(res.status).toBe(400);
  });

  test('400 — rejects folder names with slashes', async () => {
    const res = await createFolder(postReq({ name: 'a/b' }), foldersParams());
    expect(res.status).toBe(400);
  });

  test('400 — rejects empty name', async () => {
    const res = await createFolder(postReq({ name: '' }), foldersParams());
    expect(res.status).toBe(400);
  });

  test('400 — rejects invalid JSON', async () => {
    const req = new NextRequest(foldersBaseUrl, {
      method: 'POST',
      body: 'not-json',
      headers: { 'Content-Type': 'application/json' },
    });
    const res = await createFolder(req, foldersParams());
    expect(res.status).toBe(400);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);
    const res = await createFolder(postReq({ name: 'docs' }), foldersParams());
    expect(res.status).toBe(404);
  });
});

// ── PATCH /folders/[folderName] ───────────────────────────────────────────────

describe('PATCH /api/.../folders/[folderName]', () => {
  function patchReq(body: unknown, folderName = 'docs'): NextRequest {
    return new NextRequest(`${foldersBaseUrl}/${folderName}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  test('200 — renames a folder', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    await fs.writeFile(path.join(tmpDir, 'docs', 'readme.md'), '# hi');

    const res = await renameFolder(patchReq({ name: 'documentation' }), folderNameParams('docs'));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.name).toBe('documentation');
    expect(body.file_count).toBe(1);

    // Old path should not exist; new path should.
    await expect(fs.access(path.join(tmpDir, 'docs'))).rejects.toThrow();
    const stat = await fs.stat(path.join(tmpDir, 'documentation'));
    expect(stat.isDirectory()).toBe(true);
  });

  test('404 — when source folder does not exist', async () => {
    const res = await renameFolder(patchReq({ name: 'new-name' }, 'nonexistent'), folderNameParams('nonexistent'));
    expect(res.status).toBe(404);
  });

  test('409 — when destination folder already exists', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    await fs.mkdir(path.join(tmpDir, 'schemas'));
    const res = await renameFolder(patchReq({ name: 'schemas' }), folderNameParams('docs'));
    expect(res.status).toBe(409);
  });

  test('400 — rejects invalid new name', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    const res = await renameFolder(patchReq({ name: '../escape' }), folderNameParams('docs'));
    expect(res.status).toBe(400);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);
    const res = await renameFolder(patchReq({ name: 'x' }), folderNameParams('docs'));
    expect(res.status).toBe(404);
  });
});

// ── DELETE /folders/[folderName] ──────────────────────────────────────────────

describe('DELETE /api/.../folders/[folderName]', () => {
  function delReq(folderName: string): NextRequest {
    return new NextRequest(`${foldersBaseUrl}/${folderName}`, { method: 'DELETE' });
  }

  test('204 — deletes a folder and its contents', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    await fs.writeFile(path.join(tmpDir, 'docs', 'file.txt'), 'hi');

    const res = await deleteFolder(delReq('docs'), folderNameParams('docs'));
    expect(res.status).toBe(204);
    await expect(fs.access(path.join(tmpDir, 'docs'))).rejects.toThrow();
  });

  test('404 — when folder does not exist', async () => {
    const res = await deleteFolder(delReq('ghost'), folderNameParams('ghost'));
    expect(res.status).toBe(404);
  });

  test('400 — when path escapes system folder (traversal attempt)', async () => {
    const res = await deleteFolder(delReq('..%2Fescape'), folderNameParams('..%2Fescape'));
    expect(res.status).toBe(400);
  });

  test('404 — when project does not exist', async () => {
    mProjects.getProject.mockResolvedValue(null);
    const res = await deleteFolder(delReq('docs'), folderNameParams('docs'));
    expect(res.status).toBe(404);
  });
});

// ── Subfolder-aware GET /files?subfolder=X ────────────────────────────────────

describe('GET /api/.../files?subfolder=X', () => {
  test('200 — lists only files inside the subfolder', async () => {
    await fs.mkdir(path.join(tmpDir, 'schemas'));
    await fs.writeFile(path.join(tmpDir, 'schemas', 'a.json'), '{"x":1}');
    await fs.writeFile(path.join(tmpDir, 'root.csv'), 'root');

    const req = new NextRequest(`${filesBaseUrl}?subfolder=schemas`);
    const res = await getFiles(req, filesParams());
    expect(res.status).toBe(200);
    const body: { name: string }[] = await res.json();
    expect(body).toHaveLength(1);
    expect(body[0].name).toBe('a.json');
    // URL should include subfolder param
    // @ts-ignore
    expect(body[0].url).toContain('subfolder=schemas');
  });

  test('400 — rejects subfolder with path separator', async () => {
    const req = new NextRequest(`${filesBaseUrl}?subfolder=../escape`);
    const res = await getFiles(req, filesParams());
    expect(res.status).toBe(400);
  });
});

// ── Hidden metadata files ─────────────────────────────────────────────────────

describe('GET /api/.../files — hidden metadata files', () => {
  test('200 — system.json is excluded from root listing', async () => {
    await fs.writeFile(path.join(tmpDir, 'system.json'), '{}');
    await fs.writeFile(path.join(tmpDir, 'data.csv'), 'a,b');

    const req = new NextRequest(filesBaseUrl);
    const res = await getFiles(req, filesParams());
    expect(res.status).toBe(200);
    const body: { name: string }[] = await res.json();
    expect(body.map(f => f.name)).not.toContain('system.json');
    expect(body.map(f => f.name)).toContain('data.csv');
  });

  test('200 — project.json is excluded from root listing', async () => {
    await fs.writeFile(path.join(tmpDir, 'project.json'), '{}');
    await fs.writeFile(path.join(tmpDir, 'notes.txt'), 'hi');

    const req = new NextRequest(filesBaseUrl);
    const res = await getFiles(req, filesParams());
    expect(res.status).toBe(200);
    const body: { name: string }[] = await res.json();
    expect(body.map(f => f.name)).not.toContain('project.json');
    expect(body.map(f => f.name)).toContain('notes.txt');
  });

  test('200 — system.json placed inside a subfolder is also excluded', async () => {
    await fs.mkdir(path.join(tmpDir, 'schemas'));
    await fs.writeFile(path.join(tmpDir, 'schemas', 'system.json'), '{}');
    await fs.writeFile(path.join(tmpDir, 'schemas', 'real.json'), '{}');

    const req = new NextRequest(`${filesBaseUrl}?subfolder=schemas`);
    const res = await getFiles(req, filesParams());
    expect(res.status).toBe(200);
    const body: { name: string }[] = await res.json();
    expect(body.map(f => f.name)).not.toContain('system.json');
    expect(body.map(f => f.name)).toContain('real.json');
  });
});

// ── Subfolder-aware POST /files (upload to subfolder) ─────────────────────────

describe('POST /api/.../files with subfolder form field', () => {
  test('200 — uploads file into the subfolder', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));

    const fd = new FormData();
    fd.append('files', new File(['hello'], 'note.txt', { type: 'text/plain' }));
    fd.append('subfolder', 'docs');

    const req = new NextRequest(filesBaseUrl, { method: 'POST', body: fd });
    const res = await uploadFiles(req, filesParams());
    expect(res.status).toBe(200);

    const body = await res.json();
    expect(body.uploaded[0].name).toBe('note.txt');
    expect(body.uploaded[0].url).toContain('subfolder=docs');

    const stat = await fs.stat(path.join(tmpDir, 'docs', 'note.txt'));
    expect(stat.isFile()).toBe(true);
  });

  test('404 — returns 404 when subfolder does not exist', async () => {
    const fd = new FormData();
    fd.append('files', new File(['x'], 'x.txt'));
    fd.append('subfolder', 'ghost');

    const req = new NextRequest(filesBaseUrl, { method: 'POST', body: fd });
    const res = await uploadFiles(req, filesParams());
    expect(res.status).toBe(404);
  });

  test('409 — returns conflict when file exists in subfolder', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    await fs.writeFile(path.join(tmpDir, 'docs', 'note.txt'), 'old content');

    const fd = new FormData();
    fd.append('files', new File(['new content'], 'note.txt'));
    fd.append('subfolder', 'docs');

    const req = new NextRequest(filesBaseUrl, { method: 'POST', body: fd });
    const res = await uploadFiles(req, filesParams());
    expect(res.status).toBe(409);
  });

  test('200 — overwrites file in subfolder when overwrite=true', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    await fs.writeFile(path.join(tmpDir, 'docs', 'note.txt'), 'old');

    const fd = new FormData();
    fd.append('files', new File(['new'], 'note.txt'));
    fd.append('subfolder', 'docs');
    fd.append('overwrite', 'true');

    const req = new NextRequest(filesBaseUrl, { method: 'POST', body: fd });
    const res = await uploadFiles(req, filesParams());
    expect(res.status).toBe(200);

    const content = await fs.readFile(path.join(tmpDir, 'docs', 'note.txt'), 'utf-8');
    expect(content).toBe('new');
  });
});

// ── Subfolder-aware DELETE /files/[filename]?subfolder=X ──────────────────────

describe('DELETE /api/.../files/[filename]?subfolder=X', () => {
  test('204 — deletes file from the subfolder', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    await fs.writeFile(path.join(tmpDir, 'docs', 'note.txt'), 'hi');

    const req = new NextRequest(
      `${filesBaseUrl}/note.txt?subfolder=docs`,
      { method: 'DELETE' },
    );
    const res = await deleteFile(req, fileParams('note.txt'));
    expect(res.status).toBe(204);
    await expect(fs.access(path.join(tmpDir, 'docs', 'note.txt'))).rejects.toThrow();
  });

  test('404 — when file does not exist in subfolder', async () => {
    await fs.mkdir(path.join(tmpDir, 'docs'));
    const req = new NextRequest(
      `${filesBaseUrl}/ghost.txt?subfolder=docs`,
      { method: 'DELETE' },
    );
    const res = await deleteFile(req, fileParams('ghost.txt'));
    expect(res.status).toBe(404);
  });

  test('400 — rejects subfolder with path separator', async () => {
    const req = new NextRequest(
      `${filesBaseUrl}/file.txt?subfolder=../escape`,
      { method: 'DELETE' },
    );
    const res = await deleteFile(req, fileParams('file.txt'));
    expect(res.status).toBe(400);
  });
});

