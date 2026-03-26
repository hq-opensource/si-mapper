# 13-06 — Graphivac API Integration

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-01` (Graphivac env vars must be externalized)
**Required by:** `13-05` (project & system create/delete calls this)

---

## Overview

Creating and deleting projects and systems (`13-05`) requires calling the Graphivac HTTP API to provision and tear down **Graphivac Projects** and **Graphivac Grids**. This task creates a thin TypeScript Graphivac client module (`mapper/src/lib/graphivac-client.ts`) used exclusively by Next.js API routes — it runs server-side only.

### Graphivac ↔ SI-Mapper mapping

| SI-Mapper concept | Graphivac concept |
|---|---|
| Project | Graphivac Project |
| System | Graphivac Grid |
| (Deployment-wide org) | Graphivac Organisation — env var only |

The Graphivac **Organisation** is fixed for an entire deployment. It is read exclusively from `GRAPHIVAC_ORG_ID` and is never passed as a function parameter by callers — the client module reads it internally.

---

## Current Graphivac API Knowledge

From `mcp_server/graphivac/api.json` (Swagger 2.0), the Graphivac REST API base path is `/api/v1` and follows this URL scheme:

```
{GRAPHIVAC_BASE_URL}/api/v1/orgs/{org_id}/projects
{GRAPHIVAC_BASE_URL}/api/v1/orgs/{org_id}/projects/{project_id}
{GRAPHIVAC_BASE_URL}/api/v1/orgs/{org_id}/projects/{project_id}/grids
{GRAPHIVAC_BASE_URL}/api/v1/orgs/{org_id}/projects/{project_id}/grids/{grid_id}
```

### Confirmed operations (from `api.json`)

**Project endpoints:**
- `GET    /api/v1/orgs/:org/projects` — list projects
- `GET    /api/v1/orgs/:org/projects/:proj` — get project info
- `POST   /api/v1/orgs/:org/projects` — create a project; body: `{ "project-name": string }` (required)
- `PUT    /api/v1/orgs/:org/projects/:proj` — update project; body: `{ "project-name": string }` (required)
- `DELETE /api/v1/orgs/:org/projects/:proj` — delete project and all its contents

**Grid endpoints:**
- `GET    /api/v1/orgs/:org/projects/:proj/grids` — list grids
- `GET    /api/v1/orgs/:org/projects/:proj/grids/:grid` — get grid file and metadata
- `POST   /api/v1/orgs/:org/projects/:proj/grids` — create a grid; body: `Grid` (see schema below)
- `PUT    /api/v1/orgs/:org/projects/:proj/grids/:grid` — update a grid; body: `Grid`
- `DELETE /api/v1/orgs/:org/projects/:proj/grids/:grid` — delete a grid

### Request / Response schemas

**`Grid` body** (all fields optional):
```json
{
  "title": "string",
  "description": "string",
  "font": {
    "family": "Serif | Monospace | Sans-serif",
    "style": "Normal | Italic | Oblique",
    "size": 12 | 16 | 20,
    "weight": "Normal | Bold | Lighter | Bolder",
    "color": "string"
  }
}
```

**Create project body** (`project-name` required):
```json
{ "project-name": "string" }
```

> **Note on response shape**: The API spec uses `"default"` responses without explicit schemas. The returned `id` field (e.g. `"P-j8QIvTGH7p"` for projects, `"G-LAiRS3mgp6"` for grids) must be extracted from the response JSON at runtime. Inspect the actual response body to find the `id` key.

> ~~**Research action required**~~: ✅ Resolved — all create/delete endpoints are confirmed in `mcp_server/graphivac/api.json`.

---

## Environment Variables

| Variable | Description | Where set |
|---|---|---|
| `GRAPHIVAC_BASE_URL` | Base URL of the Graphivac API | `mapper/.env.example` |
| `GRAPHIVAC_ORG_ID` | Organisation ID — **deployment-wide constant, never stored in project/system records** | `mapper/.env.example` |

> `GRAPHIVAC_ORG_ID` is the only Graphivac coordinate that is never stored on disk. All other IDs (`graphivac_project_id`, `graphivac_grid_id`) are stored in `project.json` and `system.json` respectively because they vary per project/system.

---

## TypeScript Client Module

### Location

`mapper/src/lib/graphivac-client.ts` — server-side only. Never imported from a client component.

### Interface

```ts
// All functions read GRAPHIVAC_BASE_URL and GRAPHIVAC_ORG_ID from process.env internally.
// Callers never pass org_id — it is always read from env.

export interface GraphivacProjectSummary {
  id: string;   // Graphivac project id (e.g. "P-j8QIvTGH7p")
  title: string;
}

export interface GraphivacGridSummary {
  id: string;   // Graphivac grid id (e.g. "G-LAiRS3mgp6")
  title: string;
}

// ── Graphivac Project operations ──────────────────────────────────────────────

/**
 * Create a new Graphivac Project within the deployment's organisation.
 * @param title — display name (typically the SI-Mapper project name)
 * @returns the new Graphivac project id
 */
export async function createGraphivacProject(title: string): Promise<string>

/**
 * Delete a Graphivac Project (and all its grids).
 * Resolves normally if the project is already gone (idempotent).
 */
export async function deleteGraphivacProject(projectId: string): Promise<void>

// ── Graphivac Grid operations ─────────────────────────────────────────────────

/**
 * List all grids in a Graphivac Project.
 */
export async function listGrids(graphivacProjectId: string): Promise<GraphivacGridSummary[]>

/**
 * Create a new Graphivac Grid inside a Graphivac Project.
 * @param graphivacProjectId — the Graphivac Project to create the grid in
 * @param title — display name (typically the SI-Mapper system name)
 * @returns the new grid id
 */
export async function createGrid(graphivacProjectId: string, title: string): Promise<string>

/**
 * Delete a Graphivac Grid.
 * Resolves normally if the grid is already gone (idempotent).
 */
export async function deleteGrid(graphivacProjectId: string, gridId: string): Promise<void>
```

### Implementation notes

- All functions read `GRAPHIVAC_BASE_URL` and `GRAPHIVAC_ORG_ID` from `process.env` at call time (not at module load).
- Use the native `fetch` API — no extra HTTP library needed.
- Throw a descriptive error on non-2xx responses so API routes can return structured error JSON.
- `GRAPHIVAC_ORG_ID` is used to build the URL internally — callers of this module never supply it.

---

## New Environment Variables to Add

Update `mapper/.env.example` (from `13-01`) and `mapper/frontend.env.example` (from `13-02`):

```dotenv
# Graphivac API — server-side only
GRAPHIVAC_BASE_URL=https://graphivac.hvac.io
GRAPHIVAC_ORG_ID=public
```

> Note: `GRAPHIVAC_PROJECT_ID` (a single deployment-wide Graphivac Project) is **no longer needed as an env var**. Each SI-Mapper project creates its own Graphivac Project dynamically and stores the resulting ID in `project.json`.

---

## Implementation Plan

### Milestone 1 — Research Graphivac endpoints ✅ Done

**Steps:**
1. ~~Open `mcp_server/graphivac/api.json` and identify create/delete endpoints for both Projects and Grids.~~ ✅ All endpoints confirmed — see "Current Graphivac API Knowledge" above.
2. Document findings as a comment block at the top of `graphivac-client.ts`.

**Key findings:**
- Base path: `/api/v1`
- `POST /api/v1/orgs/:org/projects` — body: `{ "project-name": string }`
- `DELETE /api/v1/orgs/:org/projects/:proj` — supported ✅
- `POST /api/v1/orgs/:org/projects/:proj/grids` — body: `Grid` (title, description, font — all optional)
- `DELETE /api/v1/orgs/:org/projects/:proj/grids/:grid` — supported ✅
- Response `id` field must be extracted from runtime response body (no explicit schema in spec).

**Files to create:**
- `mapper/src/lib/graphivac-client.ts`

---

### Milestone 2 — Implement Grid operations

**Steps:**
1. Implement `listGrids(graphivacProjectId)`.
2. Implement `createGrid(graphivacProjectId, title)` — returns new grid id.
3. Implement `deleteGrid(graphivacProjectId, gridId)` — handle 404 as no-op.

---

### Milestone 3 — Implement Project operations

**Steps:**
1. Implement `createGraphivacProject(title)` — POST to `/api/v1/orgs/:org/projects` with body `{ "project-name": title }`, return new project id.
2. Implement `deleteGraphivacProject(projectId)` — DELETE to `/api/v1/orgs/:org/projects/:proj`, handle 404 as no-op.

> Both operations are confirmed in `mcp_server/graphivac/api.json` — no fallback needed.

---

### Milestone 4 — Add env vars to documentation

**Steps:**
1. Add `GRAPHIVAC_BASE_URL` and `GRAPHIVAC_ORG_ID` to `mapper/.env.example`.
2. Add the same to `mapper/frontend.env.example`.
3. Remove any reference to a deployment-wide `GRAPHIVAC_PROJECT_ID` env var from documentation.

---

## Acceptance Criteria

- [ ] `mapper/src/lib/graphivac-client.ts` exports `createGraphivacProject`, `deleteGraphivacProject`, `listGrids`, `createGrid`, `deleteGrid`.
- [ ] All functions read `GRAPHIVAC_BASE_URL` and `GRAPHIVAC_ORG_ID` from `process.env` internally — callers never pass org_id.
- [ ] `createGrid` takes a `graphivacProjectId` parameter (not org_id — that is internal).
- [ ] Both delete functions handle `404` from Graphivac without throwing.
- [ ] The module is never imported from client components.
- [ ] `GRAPHIVAC_BASE_URL` and `GRAPHIVAC_ORG_ID` are documented in both `.env.example` files.
- [ ] No deployment-wide `GRAPHIVAC_PROJECT_ID` env var is introduced — project IDs are per-project, stored in `project.json`.

---

## Notes & Decisions

- **One Graphivac Organisation, many Graphivac Projects**: the deployment-level `GRAPHIVAC_ORG_ID` is fixed. Each SI-Mapper project creates its own Graphivac Project within that organisation.
- **`GRAPHIVAC_ORG_ID` is internal to the client**: it never surfaces in API routes, request bodies, or response payloads. This mirrors the on-disk model where `graphivac_org_id` is not stored.
- **No deployment-wide `GRAPHIVAC_PROJECT_ID`**: the previous design used a single shared Graphivac Project for all grids. The new design gives each SI-Mapper project its own Graphivac Project, enabling proper isolation and deletion.
- **No EDN in this module**: EDN is only needed for grid content operations. Grid and project management uses plain JSON.
- **No auth token in scope**: current integration uses public URLs. If auth is needed in the future, add `GRAPHIVAC_API_TOKEN` env var.
