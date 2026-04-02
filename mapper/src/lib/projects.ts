/**
 * projects.ts
 * ──────────────────────────────────────────────────────────────────────────────
 * Single source-of-truth for all project / system file-system operations.
 * No other module should import `fs` directly — everything goes through here.
 */

import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';

/** 21-char URL-safe ID — same length/alphabet as nanoid's default. */
function newId(): string {
  return crypto.randomUUID().replace(/-/g, '').slice(0, 21);
}

// ── Root directory ────────────────────────────────────────────────────────────

export const PROJECTS_ROOT: string = process.env.PROJECTS_FOLDER
  ? path.resolve(process.env.PROJECTS_FOLDER)
  : path.join(process.cwd(), 'uploads');

// ── Interfaces ────────────────────────────────────────────────────────────────

export interface Project {
  /** Stable, unique identifier. Generated once at creation. */
  id: string;
  /** Human-readable display name (e.g. "Building A — HVAC"). */
  name: string;
  /**
   * Relative path of the project's folder inside PROJECTS_FOLDER.
   * Convention: same as `id` (e.g. "proj-abc123").
   * Absolute path: path.join(PROJECTS_ROOT, folder_path)
   */
  folder_path: string;
  /**
   * ID of the Graphivac Project that contains all grids for this project's systems.
   * The Graphivac Organisation is NOT stored here — it is fixed per deployment
   * and read exclusively from the GRAPHIVAC_ORG_ID environment variable.
   */
  graphivac_project_id: string;
  /** ISO 8601 timestamps managed by the storage layer. */
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  name: string;
  created_at: string;
}

export interface System {
  // ...existing fields...
  id: string;
  name: string;
  folder_path: string;
  graphivac_grid_id: string;
  /** CopilotKit thread ID of the last active conversation for this system. */
  thread_id?: string;
  /** Named conversation sessions for this system. */
  sessions?: Session[];
  created_at: string;
  updated_at: string;
}

// ── Internal guards ───────────────────────────────────────────────────────────

/**
 * Ensures that `resolvedPath` is a direct (or deeper) child of `rootDir`.
 * Throws if a path-traversal attempt is detected.
 */
function assertUnderRoot(resolvedPath: string, rootDir: string, label: string): void {
  if (!resolvedPath.startsWith(rootDir + path.sep)) {
    throw new Error(`Path traversal attempt detected (${label}): "${resolvedPath}"`);
  }
}

// ── Path helpers ──────────────────────────────────────────────────────────────

/** Absolute path of a project's folder. */
export function projectDir(folderPath: string): string {
  const resolved = path.resolve(PROJECTS_ROOT, folderPath);
  assertUnderRoot(resolved, PROJECTS_ROOT, 'projectDir');
  return resolved;
}

/** Absolute path of a project's metadata file. */
export function projectConfigPath(folderPath: string): string {
  return path.join(projectDir(folderPath), 'project.json');
}

/** Absolute path of a system's folder (inside a project folder). */
export function systemDir(projectFolderPath: string, systemFolderPath: string): string {
  const resolvedProject = projectDir(projectFolderPath);
  const resolved = path.resolve(resolvedProject, systemFolderPath);
  assertUnderRoot(resolved, resolvedProject, 'systemDir');
  return resolved;
}

/** Absolute path of a system's metadata file. */
export function systemConfigPath(projectFolderPath: string, systemFolderPath: string): string {
  return path.join(systemDir(projectFolderPath, systemFolderPath), 'system.json');
}

// ── Project CRUD ──────────────────────────────────────────────────────────────

/**
 * List all projects by scanning PROJECTS_ROOT for subdirectories that contain
 * a `project.json` file.
 */
export async function listProjects(): Promise<Project[]> {
  let entries: string[];
  try {
    const dirents = await fs.readdir(PROJECTS_ROOT, { withFileTypes: true });
    entries = dirents
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
  } catch {
    // If the root does not exist yet, return an empty list.
    return [];
  }

  const projects: Project[] = [];
  for (const entry of entries) {
    const configPath = path.join(PROJECTS_ROOT, entry, 'project.json');
    try {
      const raw = await fs.readFile(configPath, 'utf-8');
      projects.push(JSON.parse(raw) as Project);
    } catch {
      // Skip directories without a valid project.json.
    }
  }
  return projects;
}

/**
 * Read a single project by its `id`.
 * Scans all projects and returns the one whose id matches, or null.
 */
export async function getProject(id: string): Promise<Project | null> {
  const all = await listProjects();
  return all.find((p) => p.id === id) ?? null;
}

/**
 * Write (create or overwrite) a `project.json`.
 * Automatically updates `updated_at` to the current time.
 */
export async function writeProject(project: Project): Promise<void> {
  const dir = projectDir(project.folder_path);
  await fs.mkdir(dir, { recursive: true });
  const updated: Project = { ...project, updated_at: new Date().toISOString() };
  await fs.writeFile(projectConfigPath(project.folder_path), JSON.stringify(updated, null, 2), 'utf-8');
}

/**
 * Create the project folder and write `project.json`.
 * Returns the newly created `Project`.
 */
export async function createProjectOnDisk(
  partial: Omit<Project, 'id' | 'folder_path' | 'created_at' | 'updated_at'>
): Promise<Project> {
  const id = `proj-${newId()}`;
  const now = new Date().toISOString();
  const project: Project = {
    id,
    folder_path: id,
    created_at: now,
    updated_at: now,
    ...partial,
  };
  const dir = projectDir(project.folder_path);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(projectConfigPath(project.folder_path), JSON.stringify(project, null, 2), 'utf-8');
  return project;
}

/**
 * Delete a project's entire folder (recursive). All systems are deleted with it.
 */
export async function deleteProjectFromDisk(folderPath: string): Promise<void> {
  const dir = projectDir(folderPath);
  await fs.rm(dir, { recursive: true, force: true });
}

// ── System CRUD ───────────────────────────────────────────────────────────────

/**
 * List all systems within a project folder by scanning for subdirectories that
 * contain a `system.json` file.
 */
export async function listSystems(projectFolderPath: string): Promise<System[]> {
  const projDir = projectDir(projectFolderPath);
  let entries: string[];
  try {
    const dirents = await fs.readdir(projDir, { withFileTypes: true });
    entries = dirents
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
  } catch {
    return [];
  }

  const systems: System[] = [];
  for (const entry of entries) {
    const configPath = path.join(projDir, entry, 'system.json');
    try {
      const raw = await fs.readFile(configPath, 'utf-8');
      systems.push(JSON.parse(raw) as System);
    } catch {
      // Skip directories without a valid system.json.
    }
  }
  return systems;
}

/**
 * Read a single system by its `id` within a project.
 */
export async function getSystem(projectFolderPath: string, id: string): Promise<System | null> {
  const all = await listSystems(projectFolderPath);
  return all.find((s) => s.id === id) ?? null;
}

/**
 * Write (create or overwrite) a `system.json`.
 * Automatically updates `updated_at` to the current time.
 */
export async function writeSystem(projectFolderPath: string, system: System): Promise<void> {
  const dir = systemDir(projectFolderPath, system.folder_path);
  await fs.mkdir(dir, { recursive: true });
  const updated: System = { ...system, updated_at: new Date().toISOString() };
  await fs.writeFile(
    systemConfigPath(projectFolderPath, system.folder_path),
    JSON.stringify(updated, null, 2),
    'utf-8'
  );
}

/**
 * Create the system subfolder and write `system.json`.
 * Returns the newly created `System`.
 */
export async function createSystemOnDisk(
  projectFolderPath: string,
  partial: Omit<System, 'id' | 'folder_path' | 'created_at' | 'updated_at'>
): Promise<System> {
  const id = `sys-${newId()}`;
  const now = new Date().toISOString();
  const system: System = {
    id,
    folder_path: id,
    created_at: now,
    updated_at: now,
    ...partial,
  };
  const dir = systemDir(projectFolderPath, system.folder_path);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(
    systemConfigPath(projectFolderPath, system.folder_path),
    JSON.stringify(system, null, 2),
    'utf-8'
  );
  return system;
}

/**
 * Delete a system's subfolder (recursive). The parent project folder is left intact.
 */
export async function deleteSystemFromDisk(
  projectFolderPath: string,
  systemFolderPath: string
): Promise<void> {
  const dir = systemDir(projectFolderPath, systemFolderPath);
  await fs.rm(dir, { recursive: true, force: true });
}

