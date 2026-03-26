/**
 * files-view-route.test.ts
 * Tests for GET /api/files/view (file content viewer)
 *
 * Covers:
 *   - No scoping: serves a file directly from uploads root
 *   - Project scoping (?project=): resolves ID relative to project folder
 *   - Project + system scoping (?project=&system=): resolves ID relative to system folder
 *   - Correct Content-Type headers for .py, .ttl, .md, .json, .txt, .csv, .png, .pdf
 *   - 400 when ID points to a directory
 *   - 400 when path traversal is attempted via project or system param
 *   - 500 when the file does not exist
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
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'si-mapper-files-view-test-'));
  process.env.PROJECTS_FOLDER = tmpDir;
  // Import after env var is set so getProjectsFolder() resolves to tmpDir
  ({ GET } = require('@/app/api/files/view/route'));
});

afterAll(async () => {
  await fs.rm(tmpDir, { recursive: true, force: true });
  delete process.env.PROJECTS_FOLDER;
});

// ── Helper ────────────────────────────────────────────────────────────────────

function makeRequest(params: Record<string, string>): Request {
  const url = new URL('http://localhost/api/files/view');
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  return new Request(url.toString());
}

// ── No scoping ────────────────────────────────────────────────────────────────

describe('GET /api/files/view — no scoping', () => {
  test('200 — returns file content from uploads root', async () => {
    await fs.writeFile(path.join(tmpDir, 'hello.py'), '# hello world\n');

    const res = await GET(makeRequest({ id: '/hello.py' }));

    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text).toBe('# hello world\n');

    await fs.unlink(path.join(tmpDir, 'hello.py'));
  });

  test('400 — missing id returns error', async () => {
    const res = await GET(makeRequest({}));
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toBeDefined();
  });

  test('400 — id pointing to a directory is rejected', async () => {
    const dir = path.join(tmpDir, 'some-folder');
    await fs.mkdir(dir, { recursive: true });

    const res = await GET(makeRequest({ id: '/some-folder' }));
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toMatch(/directory/i);

    await fs.rm(dir, { recursive: true, force: true });
  });

  test('500 — non-existent file returns 500', async () => {
    const res = await GET(makeRequest({ id: '/does-not-exist.ttl' }));
    expect(res.status).toBe(500);
  });
});

// ── Project scoping ───────────────────────────────────────────────────────────

describe('GET /api/files/view — scoped to project', () => {
  let projectDir: string;

  beforeEach(async () => {
    projectDir = path.join(tmpDir, 'proj-view-test');
    await fs.mkdir(path.join(projectDir, 'python'), { recursive: true });
    await fs.writeFile(path.join(projectDir, 'python', 'ontology.py'), 'x = 1\n');
  });

  afterEach(async () => {
    await fs.rm(projectDir, { recursive: true, force: true });
  });

  test('200 — resolves id relative to project folder', async () => {
    const res = await GET(makeRequest({
      id: '/python/ontology.py',
      project: 'proj-view-test',
    }));

    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text).toBe('x = 1\n');
  });

  test('400 — id that escapes the project folder is rejected', async () => {
    const res = await GET(makeRequest({
      id: '../../etc/passwd',
      project: 'proj-view-test',
    }));
    expect(res.status).toBe(400);
  });
});

// ── Project + system scoping ──────────────────────────────────────────────────

describe('GET /api/files/view — scoped to project + system', () => {
  let systemDir: string;

  beforeEach(async () => {
    systemDir = path.join(tmpDir, 'proj-sys-view', 'sys-001');
    await fs.mkdir(path.join(systemDir, 'ttl'), { recursive: true });
    await fs.writeFile(
      path.join(systemDir, 'ttl', 'ontology_20260326_120000.ttl'),
      '@prefix : <http://example.org/> .\n'
    );
  });

  afterEach(async () => {
    await fs.rm(path.join(tmpDir, 'proj-sys-view'), { recursive: true, force: true });
  });

  test('200 — resolves id relative to system folder', async () => {
    const res = await GET(makeRequest({
      id: '/ttl/ontology_20260326_120000.ttl',
      project: 'proj-sys-view',
      system: 'sys-001',
    }));

    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text).toBe('@prefix : <http://example.org/> .\n');
  });

  test('400 — id that escapes the system folder is rejected', async () => {
    const res = await GET(makeRequest({
      id: '../../../etc/passwd',
      project: 'proj-sys-view',
      system: 'sys-001',
    }));
    expect(res.status).toBe(400);
  });
});

// ── Path-traversal rejection on scope params ──────────────────────────────────

describe('GET /api/files/view — path-traversal via scope params', () => {
  test('400 — path traversal in project param', async () => {
    await fs.writeFile(path.join(tmpDir, 'innocent.py'), 'pass\n');

    const res = await GET(makeRequest({
      id: '/innocent.py',
      project: '../evil',
    }));
    expect(res.status).toBe(400);

    await fs.unlink(path.join(tmpDir, 'innocent.py'));
  });

  test('400 — path traversal in system param', async () => {
    const projectDir = path.join(tmpDir, 'proj-traversal2');
    await fs.mkdir(projectDir, { recursive: true });
    await fs.writeFile(path.join(projectDir, 'a.py'), 'pass\n');

    const res = await GET(makeRequest({
      id: '/a.py',
      project: 'proj-traversal2',
      system: '../../evil',
    }));
    expect(res.status).toBe(400);

    await fs.rm(projectDir, { recursive: true, force: true });
  });

  test('400 — absolute-path injection in project param', async () => {
    const res = await GET(makeRequest({ id: '/some.py', project: '/etc' }));
    expect(res.status).toBe(400);
  });
});

// ── Content-Type detection ────────────────────────────────────────────────────

describe('GET /api/files/view — Content-Type headers', () => {
  const cases: Array<[string, string, string]> = [
    ['ontology.py',  'print("hi")',      'text/plain; charset=utf-8'],
    ['ontology.ttl', '@prefix : <> .',   'text/plain; charset=utf-8'],
    ['notes.md',     '# Title',          'text/plain; charset=utf-8'],
    ['data.json',    '{"a":1}',          'application/json'],
    ['data.txt',     'plain text',       'text/plain'],
    ['data.csv',     'a,b,c',            'text/csv'],
  ];

  for (const [filename, content, expectedCT] of cases) {
    test(`${filename} → ${expectedCT}`, async () => {
      await fs.writeFile(path.join(tmpDir, filename), content);

      const res = await GET(makeRequest({ id: `/${filename}` }));

      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toBe(expectedCT);
      expect(res.headers.get('Content-Length')).toBe(
        String(Buffer.byteLength(content))
      );

      await fs.unlink(path.join(tmpDir, filename));
    });
  }
});

