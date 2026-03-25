# 13-05 — Project Management API

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-04` (project storage utilities), `13-06` (Graphivac grid API — for create/delete)

---

## Overview

This task implements the Next.js API routes that expose full CRUD operations on projects. The routes are consumed by the project selector UI (`13-07`) and are the single point of authority for:

- Listing and reading projects.
- Creating a new project (allocates a folder on disk and creates a grid in Graphivac).
- Updating project metadata (name, model, Graphivac IDs).
- Deleting a project (removes the disk folder and the Graphivac grid).

All routes run server-side (App Router `route.ts` files). They import from `mapper/src/lib/projects.ts` (data layer, `13-04`) and the Graphivac client (`mapper/src/lib/graphivac-client.ts`, `13-06`).

---

## Route Map

| Method | Path | Action |
|---|---|---|
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/[id]` | Get a single project |
| `PATCH` | `/api/projects/[id]` | Update project metadata |
| `DELETE` | `/api/projects/[id]` | Delete a project (folder + grid) |

---

## Route Specifications

### `GET /api/projects`

Returns the full list of projects by scanning `PROJECTS_FOLDER`.

**Response `200`:**
```json
[
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
]
```

**Error `500`:** file system read failure.

---

### `POST /api/projects`

Creates a new project. The body specifies the human-facing fields; the API generates the `id`, allocates the folder, and creates the Graphivac grid.

**Request body:**
```json
{
  "name": "Building B — Chiller Plant",
  "graphivac_org_id": "public",
  "graphivac_project_id": "P-j8QIvTGH7p",
  "ai_model_name": "gemini-3.1-pro"
}
```

> `graphivac_grid_id` is intentionally **absent** from the request — it is returned by the Graphivac grid creation call (see `13-06`) and stored automatically.

**Server-side flow:**
1. Validate required fields (`name`, `graphivac_org_id`, `graphivac_project_id`).
2. Call `createGrid(org_id, project_id, name)` from the Graphivac client → receives `grid_id`.
3. Call `createProjectOnDisk({ name, folder_path: id, graphivac_org_id, graphivac_project_id, graphivac_grid_id, ai_model_name })`.
4. Return the created `Project` record.

**Response `201`:** the full created `Project` object.
**Error `400`:** missing required fields.
**Error `502`:** Graphivac API call failed (project folder is NOT created if grid creation fails — fail early, fail clean).

---

### `GET /api/projects/[id]`

Reads a single project by its `id`.

**Response `200`:** the `Project` object.
**Error `404`:** no project with that id found.

---

### `PATCH /api/projects/[id]`

Updates mutable fields of an existing project. Immutable fields (`id`, `folder_path`, `created_at`) are ignored even if sent.

**Request body (all fields optional):**
```json
{
  "name": "New Display Name",
  "ai_model_name": "claude-3-7-sonnet",
  "graphivac_grid_id": "G-XXXXXXXX"
}
```

> Updating `graphivac_grid_id` directly (without going through Graphivac API) is supported for cases where the grid was created externally or needs to be relinked.

**Server-side flow:**
1. Load the existing project record.
2. Merge the patched fields.
3. Update `updated_at` to now.
4. Write back via `writeProject`.

**Response `200`:** the updated `Project` object.
**Error `404`:** project not found.

---

### `DELETE /api/projects/[id]`

Permanently deletes a project. This is destructive and irreversible.

**Server-side flow:**
1. Load the project record to obtain `folder_path`, `graphivac_org_id`, `graphivac_project_id`, `graphivac_grid_id`.
2. Call `deleteGrid(org_id, project_id, grid_id)` from the Graphivac client.
   - If the Graphivac call fails, log the error but **continue** with folder deletion (the grid may already be gone).
3. Call `deleteProjectFromDisk(folder_path)`.
4. Return `204 No Content`.

**Response `204`:** success.
**Error `404`:** project not found.

---

## File Structure

```
mapper/src/app/api/projects/
├── route.ts              ← GET (list) + POST (create)
└── [id]/
    └── route.ts          ← GET (single) + PATCH (update) + DELETE (delete)
```

---

## Implementation Plan

### Milestone 1 — Scaffold route files

**Steps:**
1. Create `mapper/src/app/api/projects/route.ts` with stub `GET` and `POST` handlers that return `501 Not Implemented`.
2. Create `mapper/src/app/api/projects/[id]/route.ts` with stub `GET`, `PATCH`, and `DELETE` handlers.

**Files to create:**
- `mapper/src/app/api/projects/route.ts`
- `mapper/src/app/api/projects/[id]/route.ts`

---

### Milestone 2 — Implement read-only routes

**Steps:**
1. Implement `GET /api/projects` using `listProjects()` from `13-04`.
2. Implement `GET /api/projects/[id]` using `getProject(id)`.
3. Confirm both routes return correct JSON with `pnpm dev` running.

---

### Milestone 3 — Implement create route

**Prerequisite:** `13-06` Graphivac grid creation client must be implemented first.

**Steps:**
1. Implement `POST /api/projects`:
   - Parse and validate the body.
   - Call `createGrid` → receive `grid_id`.
   - Call `createProjectOnDisk`.
   - Return `201` with the new project.
2. Test: POST a new project via `curl` or Postman, confirm folder appears in `PROJECTS_FOLDER`, confirm `project.json` is written correctly.

---

### Milestone 4 — Implement update route

**Steps:**
1. Implement `PATCH /api/projects/[id]`:
   - Load project, merge fields, write back.
2. Test: PATCH the name → confirm `project.json` is updated and `updated_at` changes.

---

### Milestone 5 — Implement delete route

**Prerequisite:** `13-06` Graphivac grid deletion client.

**Steps:**
1. Implement `DELETE /api/projects/[id]`:
   - Call `deleteGrid` (log errors, do not abort).
   - Call `deleteProjectFromDisk`.
   - Return `204`.
2. Test: DELETE a project → confirm folder is gone, confirm Graphivac grid is deleted.

---

### Milestone 6 — Input validation & error handling

**Steps:**
1. Add `zod` validation schemas for `POST` and `PATCH` request bodies (or use manual checks if zod is already a dependency — check `package.json`; it is).
2. Ensure all routes return structured `{ error: string }` JSON on failure, never raw stack traces.
3. Confirm 404 is returned for non-existent project IDs.

---

## Acceptance Criteria

- [ ] `GET /api/projects` returns a JSON array of all projects on disk.
- [ ] `POST /api/projects` creates the project folder, writes `project.json`, creates the Graphivac grid, and returns the new project.
- [ ] `POST /api/projects` returns `502` if the Graphivac call fails, and does NOT create a folder.
- [ ] `GET /api/projects/[id]` returns `404` for unknown IDs.
- [ ] `PATCH /api/projects/[id]` updates only the provided fields and refreshes `updated_at`.
- [ ] `DELETE /api/projects/[id]` removes the project folder and the Graphivac grid.
- [ ] All routes return structured JSON errors (never raw exceptions).
- [ ] `zod` is used to validate `POST` and `PATCH` request bodies.
- [ ] No route duplicates file-system logic from `13-04` — all go through `mapper/src/lib/projects.ts`.

---

## Notes & Decisions

- **Graphivac grid creation is synchronous and blocking**: the `POST` route awaits the Graphivac call before writing to disk. If Graphivac is slow, the route will be slow. This is acceptable for a CRUD operation that happens infrequently.
- **Delete is best-effort on Graphivac**: if the Graphivac grid was already manually deleted, the API call will 404 — this is logged but does not block the disk deletion. The project folder is always deleted.
- **No optimistic locking**: multiple simultaneous writes to the same `project.json` are not protected. This is acceptable — project CRUD operations are rare, single-user workflows.
- **`folder_path` is never exposed in URL params**: the routes use `id` in the URL. The folder is looked up from the project record, not from user input. This prevents traversal via URL manipulation.

