# 13-03 — Project Data Model & Storage

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-01` (PROJECTS_FOLDER env var must exist before reading/writing project configs)

---

## Overview

Before any CRUD API, UI selector, or agent context can be built, the shape of a "project" and how it is persisted to disk must be defined. This task establishes:

1. The canonical TypeScript schema for a project record.
2. The physical storage layout on the file system under `PROJECTS_FOLDER`.
3. The read/write utility module used by all API routes (so file I/O is never duplicated).

Everything in tasks `13-04` through `13-07` depends on this foundation.

---

## Project Schema

A project record carries exactly the fields required by all downstream consumers (UI selector, file manager, Graphivac iframe, and the agent).

```ts
// mapper/src/lib/projects.ts (canonical type)
export interface Project {
  /** Stable, unique identifier. Generated once at creation (e.g. nanoid). */
  id: string;
  /** Human-readable display name. */
  name: string;
  /**
   * Relative path of the project's folder inside PROJECTS_FOLDER.
   * Convention: same as `id` (e.g. "proj-abc123").
   * The absolute path is: path.join(PROJECTS_FOLDER, folder_path).
   */
  folder_path: string;
  /** Graphivac identifiers needed to construct iframe and API URLs. */
  graphivac_org_id: string;
  graphivac_project_id: string;
  graphivac_grid_id: string;
  /** AI model name passed to the agent for this project (e.g. "gemini-3.1-pro"). */
  ai_model_name: string;
  /** ISO 8601 timestamps managed by the storage layer. */
  created_at: string;
  updated_at: string;
}
```

### Design decisions

- **`folder_path` is relative**: API routes resolve it against `PROJECTS_FOLDER` at runtime, so the JSON file is portable if the root folder moves.
- **Graphivac IDs are stored per-project**: `graphivac_org_id` and `graphivac_project_id` may be the same for all projects in a single deployment but are stored explicitly to allow different Graphivac organisations or projects in the future.
- **`ai_model_name` per project**: Allows different projects to use different models (e.g. one on `gemini-3.1-pro`, another on `claude-3-7-sonnet`). The agent reads this at session start instead of the global `SHARED_ADK_MODEL` env var.
- **No `active` flag stored**: The active project is session/UI state, not persisted on disk (see `13-06`).

---

## Storage Layout

```
{PROJECTS_FOLDER}/                ← root — value of PROJECTS_FOLDER env var
├── proj-abc123/
│   ├── project.json              ← project metadata (one file per project)
│   ├── drawings/                 ← user-uploaded files for this project
│   ├── exports/
│   └── ...
├── proj-def456/
│   ├── project.json
│   └── ...
└── ...
```

### `project.json` example

```json
{
  "id": "proj-abc123",
  "name": "Building A — HVAC",
  "folder_path": "proj-abc123",
  "graphivac_org_id": "public",
  "graphivac_project_id": "P-j8QIvTGH7p",
  "graphivac_grid_id": "G-LAiRS3mgp6",
  "ai_model_name": "gemini-3.1-pro",
  "created_at": "2026-03-25T10:00:00.000Z",
  "updated_at": "2026-03-25T10:00:00.000Z"
}
```

### Why one `project.json` per folder (not a root index file)

- **Self-contained**: each project folder is a complete unit — copy or zip a folder and all its metadata goes with it.
- **No sync problem**: there is no index file that can drift out of sync with the on-disk reality.
- **Listing projects** = scan `PROJECTS_FOLDER` for subdirectories that contain `project.json`. This is a single `readdir` call — fast enough at any realistic project count.

---

## Storage Utility Module

A single server-side module (`mapper/src/lib/projects.ts`) owns all file-system access. API routes import from it — they never call `fs` directly.

### Functions to implement

```ts
// mapper/src/lib/projects.ts

import fs from 'fs/promises';
import path from 'path';
import { nanoid } from 'nanoid';
import type { Project } from './projects';

// Resolved once at module load — same logic as 13-01 PROJECTS_FOLDER
const PROJECTS_ROOT = process.env.PROJECTS_FOLDER
  ? path.resolve(process.env.PROJECTS_FOLDER)
  : path.join(process.cwd(), 'uploads');

/** Return the absolute path of a project's folder. */
export function projectDir(folderPath: string): string { ... }

/** Return the absolute path of a project's metadata file. */
export function projectConfigPath(folderPath: string): string { ... }

/** List all projects by scanning PROJECTS_ROOT for project.json files. */
export async function listProjects(): Promise<Project[]> { ... }

/** Read a single project by id (scans to find matching id). */
export async function getProject(id: string): Promise<Project | null> { ... }

/** Read a project directly from its folder path (faster — no scan). */
export async function getProjectByFolder(folderPath: string): Promise<Project | null> { ... }

/** Write (create or overwrite) a project.json. Updates `updated_at` automatically. */
export async function writeProject(project: Project): Promise<void> { ... }

/** Create the project folder and write its project.json. Returns the new Project. */
export async function createProjectOnDisk(
  partial: Omit<Project, 'id' | 'folder_path' | 'created_at' | 'updated_at'>
): Promise<Project> { ... }

/** Delete a project's entire folder (recursive). */
export async function deleteProjectFromDisk(folderPath: string): Promise<void> { ... }
```

### Security constraint: path traversal

Every function that accepts `folderPath` or `id` from user input MUST validate that the resolved path stays inside `PROJECTS_ROOT`:

```ts
if (!resolvedPath.startsWith(PROJECTS_ROOT + path.sep)) {
  throw new Error('Path traversal attempt detected');
}
```

---

## Implementation Plan

### Milestone 1 — Install `nanoid` and define the type

**Steps:**
1. Run `pnpm add nanoid` in `mapper/` to get a URL-safe ID generator.
2. Create `mapper/src/lib/projects.ts` with the `Project` interface and the `PROJECTS_ROOT` constant.

**Files to create:**
- `mapper/src/lib/projects.ts`

---

### Milestone 2 — Implement storage utilities

**Steps:**
1. Implement `listProjects` — `readdir` PROJECTS_ROOT, filter for subdirectories containing `project.json`, parse and return.
2. Implement `getProject` — call `listProjects`, find by `id`.
3. Implement `writeProject` — stringify to JSON and write `project.json` inside the project folder.
4. Implement `createProjectOnDisk` — generate `id` with `nanoid`, `mkdir` the folder, call `writeProject`.
5. Implement `deleteProjectFromDisk` — validate path, call `fs.rm({ recursive: true })`.
6. Add path-traversal guard to every function that accepts external input.

**Files to modify:**
- `mapper/src/lib/projects.ts`

---

### Milestone 3 — Unit tests

**Steps:**
1. Write tests in `mapper/src/lib/__tests__/projects.test.ts` using a temporary directory (`os.tmpdir()`):
   - Create a project → folder and `project.json` appear.
   - List projects → returns all created projects.
   - Get project by id → returns correct record.
   - Update project → `updated_at` changes.
   - Delete project → folder gone.
   - Path traversal attempt → throws.
2. Run `pnpm test` to confirm all pass.

**Files to create:**
- `mapper/src/lib/__tests__/projects.test.ts`

---

## Acceptance Criteria

- [ ] `Project` interface is defined in `mapper/src/lib/projects.ts` with all required fields.
- [ ] `PROJECTS_ROOT` is resolved from `PROJECTS_FOLDER` env var with a fallback to `./uploads`.
- [ ] `listProjects`, `getProject`, `writeProject`, `createProjectOnDisk`, `deleteProjectFromDisk` are all implemented.
- [ ] Every function validates against path traversal.
- [ ] Unit tests pass for all CRUD operations and the traversal guard.
- [ ] No API route or component reads from `fs` directly — all go through `mapper/src/lib/projects.ts`.

---

## Notes & Decisions

- **`nanoid` over `uuid`**: shorter, URL-safe IDs (21 chars vs 36). Better for folder names and query params.
- **No database**: the context explicitly proposes a JSON file per project. A database would be introduced as a later phase if scale demands it.
- **`folder_path === id`**: this convention eliminates the need to look up the folder from the id in most cases — if you have the id, you have the folder path. If a project is ever renamed, the folder is NOT renamed (only `name` changes); `folder_path` is immutable after creation.
- **`PROJECTS_ROOT` vs `UPLOADS_DIR`**: `13-01` renames the hardcoded constant in `files/route.ts` from `UPLOADS_DIR` to `PROJECTS_FOLDER`. This library module uses the same env var, ensuring consistency.

