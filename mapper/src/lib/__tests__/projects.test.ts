/**
 * projects.test.ts
 * Unit tests for mapper/src/lib/projects.ts
 *
 * A real temporary directory is created for each test suite so every
 * operation is exercised against the actual file system.
 */

import fs from 'fs/promises';
import os from 'os';
import path from 'path';

// ── Bootstrap: point PROJECTS_FOLDER at a temp dir before importing the module ──

let tmpDir: string;

// We need to set the env var *before* the module is loaded so that
// PROJECTS_ROOT resolves to our temp directory.
beforeAll(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'si-mapper-test-'));
  process.env.PROJECTS_FOLDER = tmpDir;
});

afterAll(async () => {
  await fs.rm(tmpDir, { recursive: true, force: true });
});

// Import lazily after env is set (jest does not hoist dynamic imports).
// eslint-disable-next-line @typescript-eslint/no-var-requires
const getModule = () =>
  require('../projects') as typeof import('../projects');

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function mod() {
  return getModule();
}

// ─────────────────────────────────────────────────────────────────────────────
// Project CRUD
// ─────────────────────────────────────────────────────────────────────────────

describe('Project CRUD', () => {
  test('createProjectOnDisk creates folder and project.json', async () => {
    const { createProjectOnDisk, PROJECTS_ROOT } = mod();

    const project = await createProjectOnDisk({
      name: 'Test Building',
      graphivac_project_id: 'P-test123',
    });

    expect(project.id).toMatch(/^proj-/);
    expect(project.folder_path).toBe(project.id);
    expect(project.name).toBe('Test Building');
    expect(project.graphivac_project_id).toBe('P-test123');
    expect(project.created_at).toBeTruthy();
    expect(project.updated_at).toBeTruthy();

    // Folder must exist
    const stat = await fs.stat(path.join(PROJECTS_ROOT, project.folder_path));
    expect(stat.isDirectory()).toBe(true);

    // project.json must exist and be parseable
    const raw = await fs.readFile(
      path.join(PROJECTS_ROOT, project.folder_path, 'project.json'),
      'utf-8'
    );
    const parsed = JSON.parse(raw);
    expect(parsed.id).toBe(project.id);
  });

  test('listProjects returns created projects', async () => {
    const { createProjectOnDisk, listProjects } = mod();

    const p1 = await createProjectOnDisk({ name: 'A', graphivac_project_id: 'P-A' });
    const p2 = await createProjectOnDisk({ name: 'B', graphivac_project_id: 'P-B' });

    const list = await listProjects();
    const ids = list.map((p) => p.id);
    expect(ids).toContain(p1.id);
    expect(ids).toContain(p2.id);
  });

  test('getProject returns correct project by id', async () => {
    const { createProjectOnDisk, getProject } = mod();

    const created = await createProjectOnDisk({ name: 'Find Me', graphivac_project_id: 'P-FM' });

    const found = await getProject(created.id);
    expect(found).not.toBeNull();
    expect(found!.id).toBe(created.id);
    expect(found!.name).toBe('Find Me');
  });

  test('getProject returns null for unknown id', async () => {
    const { getProject } = mod();
    const result = await getProject('proj-does-not-exist');
    expect(result).toBeNull();
  });

  test('writeProject updates updated_at', async () => {
    const { createProjectOnDisk, writeProject, getProject } = mod();

    const project = await createProjectOnDisk({ name: 'Original', graphivac_project_id: 'P-upd' });
    const originalUpdatedAt = project.updated_at;

    // Small delay to guarantee a different timestamp
    await new Promise((r) => setTimeout(r, 20));

    await writeProject({ ...project, name: 'Renamed' });

    const updated = await getProject(project.id);
    expect(updated!.name).toBe('Renamed');
    expect(updated!.updated_at).not.toBe(originalUpdatedAt);
    // created_at must remain unchanged
    expect(updated!.created_at).toBe(project.created_at);
  });

  test('deleteProjectFromDisk removes the entire project folder', async () => {
    const { createProjectOnDisk, deleteProjectFromDisk, PROJECTS_ROOT } = mod();

    const project = await createProjectOnDisk({ name: 'To Delete', graphivac_project_id: 'P-del' });
    const dir = path.join(PROJECTS_ROOT, project.folder_path);

    // Sanity: folder exists
    await expect(fs.access(dir)).resolves.toBeUndefined();

    await deleteProjectFromDisk(project.folder_path);

    await expect(fs.access(dir)).rejects.toThrow();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// System CRUD
// ─────────────────────────────────────────────────────────────────────────────

describe('System CRUD', () => {
  let projectFolderPath: string;

  beforeEach(async () => {
    const { createProjectOnDisk } = mod();
    const project = await createProjectOnDisk({
      name: 'Container Project',
      graphivac_project_id: 'P-container',
    });
    projectFolderPath = project.folder_path;
  });

  test('createSystemOnDisk creates subfolder and system.json', async () => {
    const { createSystemOnDisk, PROJECTS_ROOT } = mod();

    const system = await createSystemOnDisk(projectFolderPath, {
      name: 'Chilled Water Plant',
      graphivac_grid_id: 'G-grid1',
      ai_model_name: 'gemini-pro',
    });

    expect(system.id).toMatch(/^sys-/);
    expect(system.folder_path).toBe(system.id);
    expect(system.name).toBe('Chilled Water Plant');
    expect(system.graphivac_grid_id).toBe('G-grid1');
    expect(system.ai_model_name).toBe('gemini-pro');

    const stat = await fs.stat(
      path.join(PROJECTS_ROOT, projectFolderPath, system.folder_path)
    );
    expect(stat.isDirectory()).toBe(true);

    const raw = await fs.readFile(
      path.join(PROJECTS_ROOT, projectFolderPath, system.folder_path, 'system.json'),
      'utf-8'
    );
    const parsed = JSON.parse(raw);
    expect(parsed.id).toBe(system.id);
  });

  test('listSystems returns all created systems', async () => {
    const { createSystemOnDisk, listSystems } = mod();

    const s1 = await createSystemOnDisk(projectFolderPath, {
      name: 'System 1',
      graphivac_grid_id: 'G-1',
      ai_model_name: 'model-a',
    });
    const s2 = await createSystemOnDisk(projectFolderPath, {
      name: 'System 2',
      graphivac_grid_id: 'G-2',
      ai_model_name: 'model-b',
    });

    const list = await listSystems(projectFolderPath);
    const ids = list.map((s) => s.id);
    expect(ids).toContain(s1.id);
    expect(ids).toContain(s2.id);
  });

  test('getSystem returns correct system by id', async () => {
    const { createSystemOnDisk, getSystem } = mod();

    const created = await createSystemOnDisk(projectFolderPath, {
      name: 'Find Me System',
      graphivac_grid_id: 'G-FM',
      ai_model_name: 'model-x',
    });

    const found = await getSystem(projectFolderPath, created.id);
    expect(found).not.toBeNull();
    expect(found!.id).toBe(created.id);
    expect(found!.name).toBe('Find Me System');
  });

  test('getSystem returns null for unknown id', async () => {
    const { getSystem } = mod();
    const result = await getSystem(projectFolderPath, 'sys-does-not-exist');
    expect(result).toBeNull();
  });

  test('writeSystem updates updated_at', async () => {
    const { createSystemOnDisk, writeSystem, getSystem } = mod();

    const system = await createSystemOnDisk(projectFolderPath, {
      name: 'Original System',
      graphivac_grid_id: 'G-upd',
      ai_model_name: 'model-old',
    });
    const originalUpdatedAt = system.updated_at;

    await new Promise((r) => setTimeout(r, 20));

    await writeSystem(projectFolderPath, { ...system, ai_model_name: 'model-new' });

    const updated = await getSystem(projectFolderPath, system.id);
    expect(updated!.ai_model_name).toBe('model-new');
    expect(updated!.updated_at).not.toBe(originalUpdatedAt);
    expect(updated!.created_at).toBe(system.created_at);
  });

  test('deleteSystemFromDisk removes system subfolder, project folder remains', async () => {
    const { createSystemOnDisk, deleteSystemFromDisk, PROJECTS_ROOT } = mod();

    const system = await createSystemOnDisk(projectFolderPath, {
      name: 'To Delete System',
      graphivac_grid_id: 'G-del',
      ai_model_name: 'model-z',
    });

    const sysDir = path.join(PROJECTS_ROOT, projectFolderPath, system.folder_path);
    const projDir = path.join(PROJECTS_ROOT, projectFolderPath);

    await expect(fs.access(sysDir)).resolves.toBeUndefined();

    await deleteSystemFromDisk(projectFolderPath, system.folder_path);

    // System folder is gone
    await expect(fs.access(sysDir)).rejects.toThrow();
    // Project folder still exists
    await expect(fs.access(projDir)).resolves.toBeUndefined();
  });

  test('deleting a project also deletes its systems', async () => {
    const { createSystemOnDisk, deleteProjectFromDisk, PROJECTS_ROOT } = mod();

    const system = await createSystemOnDisk(projectFolderPath, {
      name: 'Nested System',
      graphivac_grid_id: 'G-nested',
      ai_model_name: 'model-n',
    });

    const sysDir = path.join(PROJECTS_ROOT, projectFolderPath, system.folder_path);
    await deleteProjectFromDisk(projectFolderPath);

    await expect(fs.access(sysDir)).rejects.toThrow();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Path traversal protection
// ─────────────────────────────────────────────────────────────────────────────

describe('Path traversal protection', () => {
  test('projectDir throws on traversal attempt', () => {
    const { projectDir } = mod();
    expect(() => projectDir('../etc/passwd')).toThrow('Path traversal');
  });

  test('systemDir throws on traversal attempt relative to project', async () => {
    const { createProjectOnDisk, systemDir } = mod();
    const project = await createProjectOnDisk({ name: 'Safe Project', graphivac_project_id: 'P-safe' });
    expect(() => systemDir(project.folder_path, '../other-project')).toThrow('Path traversal');
  });

  test('systemDir throws when system path escapes PROJECTS_ROOT', () => {
    const { systemDir } = mod();
    expect(() => systemDir('../../etc', 'passwd')).toThrow('Path traversal');
  });
});

