/**
 * files-root-route.test.ts
 * Tests for GET /api/files (root files route)
 *
 * Covers:
 *   - Tree without scoping (returns all uploads)
 *   - Tree scoped to a project folder (?project=)
 *   - Tree scoped to a project+system folder (?project=&system=)
 *   - Path-traversal rejection for project param
 *   - Path-traversal rejection for system param
 *
 * PROJECTS_FOLDER env var is set before the module is loaded so that the
 * lazy getProjectsFolder() helper resolves to the temp directory.
 */

import fs from 'fs/promises';
import os from 'os';
import path from 'path';

// ── Lazy module load (after env is set) ───────────────────────────────────────

let tmpDir: string;
let GET: (req: Request) => Promise<Response>;

beforeAll(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'si-mapper-files-root-test-'));
  process.env.PROJECTS_FOLDER = tmpDir;
  // Import after env var is set so getProjectsFolder() resolves to tmpDir
  ({ GET } = require('@/app/api/files/route'));
});

afterAll(async () => {
  await fs.rm(tmpDir, { recursive: true, force: true });
  delete process.env.PROJECTS_FOLDER;
});

// ── Helper ────────────────────────────────────────────────────────────────────

function makeRequest(params: Record<string, string>): Request {
  const url = new URL('http://localhost/api/files');
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  return new Request(url.toString());
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('GET /api/files — tree without scoping', () => {
  test('200 — returns file at uploads root', async () => {
    await fs.writeFile(path.join(tmpDir, 'root-file.txt'), 'hello');

    const res = await GET(makeRequest({ tree: 'true' }));

    expect(res.status).toBe(200);
    const body: any[] = await res.json();
    expect(body.some(f => f.value === 'root-file.txt')).toBe(true);

    // Cleanup
    await fs.unlink(path.join(tmpDir, 'root-file.txt'));
  });

  test('200 — returns empty array when uploads root is empty', async () => {
    // Remove all existing entries for a clean slate
    const entries = await fs.readdir(tmpDir);
    await Promise.all(entries.map(e => fs.rm(path.join(tmpDir, e), { recursive: true, force: true })));

    const res = await GET(makeRequest({ tree: 'true' }));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body)).toBe(true);
    expect(body).toHaveLength(0);
  });
});

describe('GET /api/files — tree scoped to project', () => {
  let projectDir: string;

  beforeEach(async () => {
    projectDir = path.join(tmpDir, 'proj-scope-test');
    await fs.mkdir(projectDir, { recursive: true });
    await fs.writeFile(path.join(projectDir, 'proj-file.txt'), 'hello project');
    await fs.writeFile(path.join(tmpDir, 'other-root-file.txt'), 'not in project');
  });

  afterEach(async () => {
    await fs.rm(projectDir, { recursive: true, force: true });
    const other = path.join(tmpDir, 'other-root-file.txt');
    await fs.rm(other, { force: true });
  });

  test('200 — returns only files within the project folder', async () => {
    const res = await GET(makeRequest({ tree: 'true', project: 'proj-scope-test' }));

    expect(res.status).toBe(200);
    const body: any[] = await res.json();
    expect(body.some(f => f.value === 'proj-file.txt')).toBe(true);
    expect(body.some(f => f.value === 'other-root-file.txt')).toBe(false);
  });

  test('200 — IDs are relative to project folder (start with /)', async () => {
    const res = await GET(makeRequest({ tree: 'true', project: 'proj-scope-test' }));

    const body: any[] = await res.json();
    const projFile = body.find(f => f.value === 'proj-file.txt');
    expect(projFile).toBeDefined();
    expect(projFile.id).toBe('/proj-file.txt');
    expect(projFile.pId).toBe('/');
  });
});

describe('GET /api/files — tree scoped to project + system', () => {
  let projectDir: string;
  let systemDir: string;

  beforeEach(async () => {
    projectDir = path.join(tmpDir, 'proj-sys-test');
    systemDir = path.join(projectDir, 'sys-001');
    await fs.mkdir(systemDir, { recursive: true });
    await fs.writeFile(path.join(systemDir, 'sys-file.txt'), 'system file');
    await fs.writeFile(path.join(projectDir, 'proj-only-file.txt'), 'project only');
  });

  afterEach(async () => {
    await fs.rm(projectDir, { recursive: true, force: true });
  });

  test('200 — returns only files within the system subfolder', async () => {
    const res = await GET(makeRequest({
      tree: 'true',
      project: 'proj-sys-test',
      system: 'sys-001',
    }));

    expect(res.status).toBe(200);
    const body: any[] = await res.json();
    expect(body.some(f => f.value === 'sys-file.txt')).toBe(true);
    expect(body.some(f => f.value === 'proj-only-file.txt')).toBe(false);
  });

  test('200 — IDs are relative to the system folder', async () => {
    const res = await GET(makeRequest({
      tree: 'true',
      project: 'proj-sys-test',
      system: 'sys-001',
    }));

    const body: any[] = await res.json();
    const sysFile = body.find(f => f.value === 'sys-file.txt');
    expect(sysFile).toBeDefined();
    expect(sysFile.id).toBe('/sys-file.txt');
    expect(sysFile.pId).toBe('/');
  });
});

describe('GET /api/files — path-traversal rejection', () => {
  test('400 — rejects path traversal in project param', async () => {
    const res = await GET(makeRequest({ tree: 'true', project: '../evil' }));
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toBeDefined();
  });

  test('400 — rejects path traversal in system param', async () => {
    // Create a valid project dir so the project check passes
    const projectDir = path.join(tmpDir, 'proj-traversal-test');
    await fs.mkdir(projectDir, { recursive: true });

    const res = await GET(makeRequest({
      tree: 'true',
      project: 'proj-traversal-test',
      system: '../../etc/passwd',
    }));

    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toBeDefined();

    await fs.rm(projectDir, { recursive: true, force: true });
  });

  test('400 — rejects absolute-path injection in project param', async () => {
    const res = await GET(makeRequest({ tree: 'true', project: '/etc' }));
    expect(res.status).toBe(400);
  });
});

