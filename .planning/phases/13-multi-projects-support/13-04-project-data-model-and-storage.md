# 13-04 — Project & System Data Model & Storage

**Phase:** 13 — Multi-Project Support
**Status:** Done
**Updated:** 2026-03-26
**Depends on:** `13-01` (PROJECTS_FOLDER env var must exist before reading/writing configs)

---

## Overview

Before any CRUD API, UI selector, or agent context can be built, the shapes of a **project** and a **system** — and how they are persisted to disk — must be defined. This task establishes:

1. The canonical TypeScript schemas for `Project` and `System` records.
2. The physical storage layout on the file system under `PROJECTS_FOLDER`.
3. The read/write utility module used by all API routes (so file I/O is never duplicated).

Everything in tasks `13-05` through `13-08` depends on this foundation.

---

## Data Model

### `Project`

A project represents a building or facility. It maps to a **Graphivac Project** and acts as the container for one or more systems.

```ts
// mapper/src/lib/projects.ts
export interface Project {
  /** Stable, unique identifier. Generated once at creation (e.g. nanoid). */
  id: string;
  /** Human-readable display name (e.g. "Building A — HVAC"). */
  name: string;
  /**
   * Relative path of the project's folder inside PROJECTS_FOLDER.
   * Convention: same as `id` (e.g. "proj-abc123").
   * Absolute path: path.join(PROJECTS_FOLDER, folder_path)
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
```

### `System`

A system represents a single mechanical or HVAC system within a project. It maps to a **Graphivac Grid** and owns its own files and agent configuration.

```ts
// mapper/src/lib/projects.ts
export interface System {
  /** Stable, unique identifier. Generated once at creation (e.g. nanoid). */
  id: string;
  /** Human-readable display name (e.g. "Chilled Water Plant"). */
  name: string;
  /**
   * Relative path of the system's subfolder inside the project's folder.
   * Convention: same as `id` (e.g. "sys-xyz789").
   * Absolute path: path.join(PROJECTS_FOLDER, project.folder_path, folder_path)
   */
  folder_path: string;
  /**
   * ID of the Graphivac Grid that represents this system's canvas.
   * Created in the project's Graphivac Project when this system is created.
   */
  graphivac_grid_id: string;
  /** AI model used by the agent when working on this system. */
  ai_model_name: string;
  /** ISO 8601 timestamps managed by the storage layer. */
  created_at: string;
  updated_at: string;
}
```

### Design Decisions

- **`graphivac_org_id` is NOT stored**: The Graphivac organisation is fixed for a deployment. It is always read from `process.env.GRAPHIVAC_ORG_ID`. Storing it per-project would create maintenance burden and potential inconsistency.
- **`graphivac_project_id` is stored per Project**: Each SI-Mapper project maps to one Graphivac Project. This ID is needed to create/delete grids (systems) within it.
- **`graphivac_grid_id` is stored per System**: Each system owns one Graphivac Grid. This is the dynamic, per-system identifier.
- **`ai_model_name` is per System**: Different systems within the same project may use different models. There is no project-level model default — the agent always reads from the active system.
- **`folder_path` is immutable after creation**: renaming a project or system changes `name` only; the folder is never moved or renamed.
- **No `active` flag stored anywhere**: the active project and active system are session/UI state, not persisted on disk (see `13-07`).

---

## Storage Layout

```
{PROJECTS_FOLDER}/                     ← root — value of PROJECTS_FOLDER env var
├── proj-abc123/
│   ├── project.json                   ← project metadata
│   ├── sys-aaa111/                    ← system subfolder
│   │   ├── system.json                ← system metadata
│   │   ├── bacnet-export.csv          ← user-uploaded files for this system
│   │   └── drawings/
│   └── sys-bbb222/
│       ├── system.json
│       └── ...
├── proj-def456/
│   ├── project.json
│   └── sys-ccc333/
│       ├── system.json
│       └── ...
└── ...
```

### `project.json` example

```json
{
  "id": "proj-abc123",
  "name": "Building A",
  "folder_path": "proj-abc123",
  "graphivac_project_id": "P-j8QIvTGH7p",
  "created_at": "2026-03-25T10:00:00.000Z",
  "updated_at": "2026-03-25T10:00:00.000Z"
}
```

### `system.json` example

```json
{
  "id": "sys-aaa111",
  "name": "Chilled Water Plant",
  "folder_path": "sys-aaa111",
  "graphivac_grid_id": "G-LAiRS3mgp6",
  "ai_model_name": "gemini-3.1-pro",
  "created_at": "2026-03-25T10:00:00.000Z",
  "updated_at": "2026-03-25T10:00:00.000Z"
}
```

### Why one JSON file per entity (not a root index file)

- **Self-contained**: each folder is a complete unit — copy or zip it and all metadata goes with it.
- **No sync problem**: no index file that can drift out of sync with on-disk reality.
- **Listing projects** = scan `PROJECTS_FOLDER` for subdirectories containing `project.json`.
- **Listing systems** = scan a project folder for subdirectories containing `system.json`.

---

## Storage Utility Module

A single server-side module (`mapper/src/lib/projects.ts`) owns all file-system access. API routes import from it — they never call `fs` directly.

### Functions to implement

```ts
// mapper/src/lib/projects.ts

import fs from 'fs/promises';
import path from 'path';
import { nanoid } from 'nanoid';

const PROJECTS_ROOT = process.env.PROJECTS_FOLDER
  ? path.resolve(process.env.PROJECTS_FOLDER)
  : path.join(process.cwd(), 'uploads');

// ── Path helpers ──────────────────────────────────────────────────────────────

/** Absolute path of a project's folder. */
export function projectDir(folderPath: string): string { ... }

/** Absolute path of a project's metadata file. */
export function projectConfigPath(folderPath: string): string { ... }

/** Absolute path of a system's folder (inside a project folder). */
export function systemDir(projectFolderPath: string, systemFolderPath: string): string { ... }

/** Absolute path of a system's metadata file. */
export function systemConfigPath(projectFolderPath: string, systemFolderPath: string): string { ... }

// ── Project CRUD ──────────────────────────────────────────────────────────────

/** List all projects by scanning PROJECTS_ROOT for project.json files. */
export async function listProjects(): Promise<Project[]> { ... }

/** Read a single project by id. */
export async function getProject(id: string): Promise<Project | null> { ... }

/** Write (create or overwrite) a project.json. Updates updated_at automatically. */
export async function writeProject(project: Project): Promise<void> { ... }

/** Create the project folder and write project.json. Returns the new Project. */
export async function createProjectOnDisk(
  partial: Omit<Project, 'id' | 'folder_path' | 'created_at' | 'updated_at'>
): Promise<Project> { ... }

/** Delete a project's entire folder (recursive). All systems are deleted with it. */
export async function deleteProjectFromDisk(folderPath: string): Promise<void> { ... }

// ── System CRUD ───────────────────────────────────────────────────────────────

/** List all systems within a project folder. */
export async function listSystems(projectFolderPath: string): Promise<System[]> { ... }

/** Read a single system by id within a project. */
export async function getSystem(projectFolderPath: string, id: string): Promise<System | null> { ... }

/** Write (create or overwrite) a system.json. Updates updated_at automatically. */
export async function writeSystem(projectFolderPath: string, system: System): Promise<void> { ... }

/** Create the system subfolder and write system.json. Returns the new System. */
export async function createSystemOnDisk(
  projectFolderPath: string,
  partial: Omit<System, 'id' | 'folder_path' | 'created_at' | 'updated_at'>
): Promise<System> { ... }

/** Delete a system's subfolder (recursive). */
export async function deleteSystemFromDisk(
  projectFolderPath: string,
  systemFolderPath: string
): Promise<void> { ... }
```

### Security constraint: path traversal

Every function that accepts `folderPath` or `id` from user input MUST validate that the resolved path stays inside `PROJECTS_ROOT`:

```ts
// For project paths:
if (!resolvedPath.startsWith(PROJECTS_ROOT + path.sep)) {
  throw new Error('Path traversal attempt detected');
}

// For system paths (must stay inside the project folder):
if (!resolvedPath.startsWith(resolvedProjectDir + path.sep)) {
  throw new Error('Path traversal attempt detected');
}
```

---

## Implementation Plan

### ✅ Milestone 1 — Install `nanoid` and define types

**Steps:**
1. ~~Run `pnpm add nanoid` in `mapper/`.~~ Used `crypto.randomUUID()` (built-in) instead — no package needed.
2. Created `mapper/src/lib/projects.ts` with the `Project` and `System` interfaces and the `PROJECTS_ROOT` constant.

**Files created:**
- `mapper/src/lib/projects.ts`

---

### ✅ Milestone 2 — Implement project storage utilities

**Steps:**
1. Implemented `listProjects`, `getProject`, `writeProject`, `createProjectOnDisk`, `deleteProjectFromDisk`.
2. Added path-traversal guard to every function accepting external input.

**Files modified:**
- `mapper/src/lib/projects.ts`

---

### ✅ Milestone 3 — Implement system storage utilities

**Steps:**
1. Implemented `listSystems`, `getSystem`, `writeSystem`, `createSystemOnDisk`, `deleteSystemFromDisk`.
2. System functions take the project's `folder_path` as their first argument to resolve paths correctly.
3. Added path-traversal guard scoped to the project directory.

**Files modified:**
- `mapper/src/lib/projects.ts`

---

### ✅ Milestone 4 — Unit tests

**Steps:**
1. Wrote 16 tests in `mapper/src/lib/__tests__/projects.test.ts` using a real temporary directory:
   - Create a project → folder and `project.json` appear. ✓
   - Create a system under a project → subfolder and `system.json` appear. ✓
   - List projects / list systems → returns all created records. ✓
   - Get project by id / get system by id → returns correct record. ✓
   - Update project / update system → `updated_at` changes, `created_at` unchanged. ✓
   - Delete system → system subfolder gone, project folder intact. ✓
   - Delete project → entire project folder gone (including systems). ✓
   - Three path traversal attempts → throw. ✓
2. All 16 tests pass (`pnpm test`).

**Files created:**
- `mapper/src/lib/__tests__/projects.test.ts`

**Files modified:**
- `mapper/jest.config.js` — extended transform pattern to `[jt]sx?` (no mock mapper needed)

---

## Acceptance Criteria

- [x] `Project` interface has: `id`, `name`, `folder_path`, `graphivac_project_id`, `created_at`, `updated_at`. No `graphivac_org_id`, no `graphivac_grid_id`, no `ai_model_name`.
- [x] `System` interface has: `id`, `name`, `folder_path`, `graphivac_grid_id`, `ai_model_name`, `created_at`, `updated_at`.
- [x] `PROJECTS_ROOT` is resolved from `PROJECTS_FOLDER` env var with a fallback to `./uploads`.
- [x] All project CRUD functions are implemented and validated against path traversal.
- [x] All system CRUD functions are implemented and validated against path traversal (two-level: inside project folder).
- [x] Unit tests pass for all operations on both projects and systems.
- [x] No API route or component reads from `fs` directly — all go through `mapper/src/lib/projects.ts`.

---

## Notes & Decisions

- **`graphivac_org_id` removed from all persisted records**: it is a deployment-wide constant, not a per-project or per-system value. Reading it from env ensures a single source of truth.
- **`graphivac_project_id` stays on `Project`**: each SI-Mapper project corresponds to one Graphivac Project, so this ID is inherently project-scoped.
- **`graphivac_grid_id` belongs to `System`**: a grid is the Graphivac canvas for one system, not for an entire project.
- **`ai_model_name` on `System`**: the agent works on a system, so the model is configured at the system level. This allows two systems in the same project to use different models.
- **`nanoid` over `uuid`**: shorter, URL-safe IDs. Better for folder names and query params. ~~`nanoid` was initially planned but replaced with Node's built-in `crypto.randomUUID()` (strips dashes, takes 21 chars) — identical output, zero extra dependency, no ESM/CJS friction in Jest.~~
- **No database**: JSON files per entity. A database would be introduced in a later phase if scale demands it.
- **System folder is a child of the project folder**: the absolute path of a system's files is always `PROJECTS_ROOT/{project.folder_path}/{system.folder_path}/`.
