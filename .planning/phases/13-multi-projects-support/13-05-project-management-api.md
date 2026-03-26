# 13-05 — Project & System Management API

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-04` (project & system storage utilities), `13-06` (Graphivac API — for create/delete)

---

## Overview

This task implements the Next.js API routes that expose full CRUD operations on **projects** and **systems**. The routes are the single point of authority for:

- Listing and reading projects and their systems.
- Creating a new project (allocates a folder on disk and creates a Graphivac Project).
- Creating a new system under a project (allocates a subfolder and creates a Graphivac Grid).
- Updating project or system metadata.
- Deleting a project (removes all its systems, the project folder, and the Graphivac Project).
- Deleting a system (removes its folder and the Graphivac Grid).
- Managing files within a system's folder.

All routes run server-side (App Router `route.ts` files). They import from `mapper/src/lib/projects.ts` (data layer, `13-04`) and the Graphivac client (`mapper/src/lib/graphivac-client.ts`, `13-06`).

> **Note on `GRAPHIVAC_ORG_ID`:** All Graphivac API calls read the organisation ID exclusively from `process.env.GRAPHIVAC_ORG_ID`. It is never accepted from the client or stored in any record.

---

## Route Map

| Method | Path | Action |
|---|---|---|
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/[id]` | Get a single project |
| `PATCH` | `/api/projects/[id]` | Update project metadata |
| `DELETE` | `/api/projects/[id]` | Delete a project (all systems + folder + Graphivac Project) |
| `GET` | `/api/projects/[id]/systems` | List all systems within a project |
| `POST` | `/api/projects/[id]/systems` | Create a new system within a project |
| `GET` | `/api/projects/[id]/systems/[sysId]` | Get a single system |
| `PATCH` | `/api/projects/[id]/systems/[sysId]` | Update system metadata |
| `DELETE` | `/api/projects/[id]/systems/[sysId]` | Delete a system (folder + Graphivac Grid) |
| `GET` | `/api/projects/[id]/systems/[sysId]/files` | List files in a system's folder |
| `POST` | `/api/projects/[id]/systems/[sysId]/files` | Upload files into a system's folder |
| `DELETE` | `/api/projects/[id]/systems/[sysId]/files/[filename]` | Delete a file from a system's folder |

---

## Route Specifications

### `GET /api/projects`

Returns the full list of projects by scanning `PROJECTS_FOLDER`.

**Response `200`:**
```json
[
  {
    "id": "proj-abc123",
    "name": "Building A",
    "folder_path": "proj-abc123",
    "graphivac_project_id": "P-j8QIvTGH7p",
    "created_at": "2026-03-25T10:00:00.000Z",
    "updated_at": "2026-03-25T10:00:00.000Z"
  }
]
```

**Error `500`:** file system read failure.

---

### `POST /api/projects`

Creates a new project. The body specifies the human-facing fields; the API generates the `id`, allocates the folder, and creates a Graphivac Project.

**Request body:**
```json
{
  "name": "Building B — Chiller Plant"
}
```

> `graphivac_project_id` is absent from the request — it is returned by the Graphivac Project creation call (see `13-06`) and stored automatically.
> `graphivac_org_id` is never in the request — it comes from `GRAPHIVAC_ORG_ID` env var.

**Server-side flow:**
1. Validate required field (`name`).
2. Call `createGraphivacProject(name)` from the Graphivac client → receives `graphivac_project_id`.
3. Call `createProjectOnDisk({ name, graphivac_project_id })`.
4. Return the created `Project` record.

**Response `201`:** the full created `Project` object.
**Error `400`:** missing required fields.
**Error `502`:** Graphivac API call failed (project folder is NOT created if Graphivac fails — fail early, fail clean).

---

### `GET /api/projects/[id]`

Reads a single project by its `id`.

**Response `200`:** the `Project` object.
**Error `404`:** no project with that id found.

---

### `PATCH /api/projects/[id]`

Updates mutable fields of an existing project. Immutable fields (`id`, `folder_path`, `graphivac_project_id`, `created_at`) are ignored even if sent.

**Request body (all fields optional):**
```json
{
  "name": "New Display Name"
}
```

**Server-side flow:**
1. Load the existing project record.
2. Merge the patched fields (`name` only — Graphivac project ID is immutable after creation).
3. Update `updated_at` to now.
4. Write back via `writeProject`.

**Response `200`:** the updated `Project` object.
**Error `404`:** project not found.

---

### `DELETE /api/projects/[id]`

Permanently deletes a project and all its systems. Destructive and irreversible.

**Server-side flow:**
1. Load the project record to obtain `folder_path` and `graphivac_project_id`.
2. List all systems in the project.
3. For each system, call `deleteGrid(graphivac_project_id, grid_id)` from the Graphivac client (log errors, continue).
4. Call `deleteGraphivacProject(graphivac_project_id)` (log errors, continue).
5. Call `deleteProjectFromDisk(folder_path)` — this recursively removes all system subfolders.
6. Return `204 No Content`.

**Response `204`:** success.
**Error `404`:** project not found.

---

### `GET /api/projects/[id]/systems`

Lists all systems within the project.

**Response `200`:**
```json
[
  {
    "id": "sys-aaa111",
    "name": "Chilled Water Plant",
    "folder_path": "sys-aaa111",
    "graphivac_grid_id": "G-LAiRS3mgp6",
    "ai_model_name": "gemini-3.1-pro",
    "created_at": "2026-03-25T10:00:00.000Z",
    "updated_at": "2026-03-25T10:00:00.000Z"
  }
]
```

**Error `404`:** project not found.

---

### `POST /api/projects/[id]/systems`

Creates a new system within the project. Allocates a subfolder and creates a Graphivac Grid inside the project's Graphivac Project.

**Request body:**
```json
{
  "name": "AHU Zone 1",
  "ai_model_name": "gemini-3.1-pro"
}
```

> `graphivac_grid_id` is absent — returned by Graphivac Grid creation and stored automatically.

**Server-side flow:**
1. Load the project (→ `404` if not found) to obtain `graphivac_project_id`.
2. Validate required field (`name`).
3. Call `createGrid(graphivac_project_id, name)` from the Graphivac client → receives `graphivac_grid_id`.
4. Call `createSystemOnDisk(project.folder_path, { name, graphivac_grid_id, ai_model_name })`.
5. Return `201` with the created `System` record.

**Response `201`:** the full created `System` object.
**Error `400`:** missing required fields.
**Error `404`:** project not found.
**Error `502`:** Graphivac API call failed (system subfolder is NOT created if Graphivac fails).

---

### `GET /api/projects/[id]/systems/[sysId]`

Reads a single system by its `id` within the project.

**Response `200`:** the `System` object.
**Error `404`:** project or system not found.

---

### `PATCH /api/projects/[id]/systems/[sysId]`

Updates mutable fields of a system. Immutable fields (`id`, `folder_path`, `graphivac_grid_id`, `created_at`) are ignored.

**Request body (all fields optional):**
```json
{
  "name": "New System Name",
  "ai_model_name": "claude-3-7-sonnet"
}
```

**Response `200`:** the updated `System` object.
**Error `404`:** project or system not found.

---

### `DELETE /api/projects/[id]/systems/[sysId]`

Permanently deletes a system.

**Server-side flow:**
1. Load the project (→ `404`) and the system (→ `404`).
2. Call `deleteGrid(project.graphivac_project_id, system.graphivac_grid_id)` (log errors, continue).
3. Call `deleteSystemFromDisk(project.folder_path, system.folder_path)`.
4. Return `204 No Content`.

**Response `204`:** success.
**Error `404`:** project or system not found.

---

### `GET /api/projects/[id]/systems/[sysId]/files`

Lists all files (non-recursively) in the system's folder.

**Response `200`:**
```json
[
  {
    "name": "bacnet-export.csv",
    "size": 20480,
    "modified_at": "2026-03-25T10:00:00.000Z",
    "url": "/api/projects/proj-abc123/systems/sys-aaa111/files/bacnet-export.csv"
  }
]
```

**Error `404`:** project or system not found.

---

### `POST /api/projects/[id]/systems/[sysId]/files`

Uploads one or more files into the system's folder. Accepts `multipart/form-data` with a `files` field. An optional `overwrite` boolean controls conflict behaviour (default `false`).

**Server-side flow:**
1. Verify the project and system exist.
2. Resolve the system folder path; validate it stays inside `PROJECTS_FOLDER` (path traversal guard).
3. For each file: sanitise filename, check existence if `overwrite !== "true"`, write to disk.
4. Return `200` with the list of uploaded file descriptors.

**Response `200`:** `{ "uploaded": [{ "name", "size", "url" }] }`
**Error `400`:** no files in the request.
**Error `404`:** project or system not found.
**Error `409`:** file already exists and `overwrite` is `false`.

---

### `DELETE /api/projects/[id]/systems/[sysId]/files/[filename]`

Permanently deletes a single file from the system's folder.

**Response `204`:** success.
**Error `404`:** project, system, or file not found.
**Error `400`:** resolved path escapes the system folder (traversal attempt).

---

## File Structure

```
mapper/src/app/api/projects/
├── route.ts                          ← GET (list) + POST (create project)
└── [id]/
    ├── route.ts                      ← GET + PATCH + DELETE (project)
    └── systems/
        ├── route.ts                  ← GET (list systems) + POST (create system)
        └── [sysId]/
            ├── route.ts              ← GET + PATCH + DELETE (system)
            └── files/
                ├── route.ts          ← GET (list files) + POST (upload files)
                └── [filename]/
                    └── route.ts      ← DELETE (delete file)
```

---

## Implementation Plan

### Milestone 1 — Scaffold project routes

**Steps:**
1. Create stub `GET` and `POST` handlers in `mapper/src/app/api/projects/route.ts`.
2. Create stub `GET`, `PATCH`, and `DELETE` handlers in `mapper/src/app/api/projects/[id]/route.ts`.

---

### Milestone 2 — Implement project read-only routes

**Steps:**
1. Implement `GET /api/projects` using `listProjects()`.
2. Implement `GET /api/projects/[id]` using `getProject(id)`.

---

### Milestone 3 — Implement project create/delete routes

**Prerequisite:** `13-06` Graphivac project + grid client.

**Steps:**
1. Implement `POST /api/projects` — call `createGraphivacProject`, then `createProjectOnDisk`.
2. Implement `DELETE /api/projects/[id]` — list systems, delete all grids, delete Graphivac Project, delete folder.

---

### Milestone 4 — Scaffold and implement system routes

**Steps:**
1. Create `mapper/src/app/api/projects/[id]/systems/route.ts` — `GET` and `POST`.
2. Create `mapper/src/app/api/projects/[id]/systems/[sysId]/route.ts` — `GET`, `PATCH`, `DELETE`.
3. Implement all four system CRUD handlers using storage utilities from `13-04`.

---

### Milestone 5 — File management routes (system-scoped)

**Steps:**
1. Create `mapper/src/app/api/projects/[id]/systems/[sysId]/files/route.ts` — `GET` and `POST`.
2. Create `mapper/src/app/api/projects/[id]/systems/[sysId]/files/[filename]/route.ts` — `DELETE`.
3. Both handlers verify project + system exist before any file operation.

---

### Milestone 6 — Validation and error handling

**Steps:**
1. Add `zod` validation schemas for `POST` and `PATCH` bodies on both project and system routes.
2. Ensure all routes return structured `{ error: string }` JSON on failure, never raw stack traces.

---

## Acceptance Criteria

- [ ] `GET /api/projects` returns a JSON array of all projects.
- [ ] `POST /api/projects` accepts only `{ name }`, creates a Graphivac Project, creates the folder, returns `201`.
- [ ] `POST /api/projects` never accepts `graphivac_org_id` from the client.
- [ ] `DELETE /api/projects/[id]` deletes all systems' grids, the Graphivac Project, and the entire folder.
- [ ] `GET /api/projects/[id]/systems` returns all systems for a project.
- [ ] `POST /api/projects/[id]/systems` creates a Graphivac Grid and a system subfolder, returns `201`.
- [ ] `DELETE /api/projects/[id]/systems/[sysId]` deletes the Graphivac Grid and the system subfolder.
- [ ] File routes are scoped to the system's subfolder (`PROJECTS_FOLDER/{proj}/{sys}/`).
- [ ] `zod` validates `POST` and `PATCH` bodies for both projects and systems.
- [ ] All routes return structured JSON errors.
- [ ] No route duplicates file-system logic from `13-04`.

---

## Notes & Decisions

- **`graphivac_org_id` is never in any request body or response**: it is a server-side env var (`GRAPHIVAC_ORG_ID`) consumed only inside the Graphivac client (`13-06`). The client never sees it.
- **File routes live under the system, not the project**: files belong to a system. There are no project-level file routes.
- **Delete project is cascade**: deleting a project deletes all its systems (on-disk and in Graphivac). This is consistent with the parent-child relationship.
- **Delete is best-effort on Graphivac**: if a Graphivac call returns 404, the error is logged but folder deletion proceeds. The on-disk state is the source of truth.
- **No project-level `ai_model_name`**: the model is per-system. The `PATCH /api/projects/[id]` route only accepts `name`.
