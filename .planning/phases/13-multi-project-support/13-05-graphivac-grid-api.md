# 13-05 — Graphivac Grid API Integration

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-01` (Graphivac env vars must be externalized)
**Required by:** `13-04` (project create/delete calls this), `13-07` (agent Graphivac scoping references this pattern)

---

## Overview

Creating and deleting projects (`13-04`) requires calling the Graphivac HTTP API to provision and tear down grids. Currently the only Graphivac API client in the project is `mcp_server/graphivac/graphivac_api.py` (Python, server-side, for the MCP server) and the agent's `sync_graphivac_tool.py` (Python, reads env vars at call time).

Neither of these is available to the Next.js frontend. This task creates a thin TypeScript Graphivac client module (`mapper/src/lib/graphivac-client.ts`) used exclusively by Next.js API routes — it runs server-side only.

---

## Current Graphivac API Knowledge

From the Python implementation and the `mcp_server`, the Graphivac REST API follows this URL scheme:

```
{GRAPHIVAC_BASE_URL}/orgs/{org_id}/projects/{project_id}/grids
{GRAPHIVAC_BASE_URL}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}
```

Known operations (inferred from existing Python code):
- `GET  /orgs/:org/projects/:proj/grids` — list grids
- `GET  /orgs/:org/projects/:proj/grids/:grid` — get one grid (Accept: application/edn)
- `PUT  /orgs/:org/projects/:proj/grids/:grid` — update grid (Content-Type: application/edn)

**Unknown (to be researched):**
- `POST /orgs/:org/projects/:proj/grids` — create a new grid (body format TBD)
- `DELETE /orgs/:org/projects/:proj/grids/:grid` — delete a grid (availability TBD)

> **Research action required**: Before implementing, verify the create and delete endpoints by inspecting the Graphivac API documentation or the `mcp_server/graphivac/api.json` file that ships with the project.

---

## Environment Variables

The Graphivac base URL and Graphivac-level organisation/project identifiers are shared across all projects in a deployment. They are set as server-side env vars (no `NEXT_PUBLIC_` prefix needed).

| Variable | Description | Where set |
|---|---|---|
| `GRAPHIVAC_BASE_URL` | Base URL of the Graphivac API (e.g. `https://graphivac.hvac.io`) | `mapper/.env.example` (add in `13-01`) |
| `GRAPHIVAC_ORG_ID` | Organisation ID in Graphivac | `mapper/.env.example` |
| `GRAPHIVAC_PROJECT_ID` | Project container ID in Graphivac (the Graphivac "project", not a SI-MAPPER project) | `mapper/.env.example` |

> Note the naming distinction: a **Graphivac project** (`GRAPHIVAC_PROJECT_ID`) is the Graphivac-side container that holds multiple **grids**. A **SI-MAPPER project** is one HVAC project with its own grid, folder, and settings. Each SI-MAPPER project gets one Graphivac grid inside the single Graphivac project.

These variables must also be added to `mapper/frontend.env.example` (see `13-02`) so Docker deployments can configure them.

---

## TypeScript Client Module

### Location

`mapper/src/lib/graphivac-client.ts` — server-side only (no `NEXT_PUBLIC_` prefix on any variable it uses; never imported from a client component).

### Interface

```ts
export interface GraphivacGridSummary {
  id: string;       // Graphivac grid id (e.g. "G-LAiRS3mgp6")
  title: string;
  description?: string;
}

/** List all grids in the configured Graphivac project. */
export async function listGrids(): Promise<GraphivacGridSummary[]>

/**
 * Create a new empty grid in Graphivac.
 * @param title — the grid display name (typically the SI-MAPPER project name)
 * @returns the new grid's id
 */
export async function createGrid(title: string): Promise<string>

/**
 * Delete a Graphivac grid.
 * Resolves normally even if the grid is not found (idempotent delete).
 */
export async function deleteGrid(gridId: string): Promise<void>
```

### Implementation notes

- All functions read `GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID` from `process.env` at call time (not at module load) — this is consistent with how the Python agent tools work.
- Use the native `fetch` API (available in Next.js 14+ server context) — no extra HTTP library needed.
- Throw a descriptive error (not a raw fetch error) on non-2xx responses so API routes can return structured error JSON.
- The `createGrid` function body must be determined from the Graphivac API docs (`mcp_server/graphivac/api.json`). A likely candidate:
  ```json
  { "title": "Building B — Chiller Plant" }
  ```
  Accept `application/json` for the list and create responses; `application/edn` is only needed for grid content reads/writes (handled by the MCP server, not here).

---

## New Environment Variables to Add

Update `mapper/.env.example` (from `13-01`) and `mapper/frontend.env.example` (from `13-02`) to include:

```dotenv
# Graphivac API — server-side only (used by Next.js API routes for grid management)
GRAPHIVAC_BASE_URL=https://graphivac.hvac.io
GRAPHIVAC_ORG_ID=public
GRAPHIVAC_PROJECT_ID=P-j8QIvTGH7p
```

---

## Implementation Plan

### Milestone 1 — Research Graphivac create/delete endpoints

**Steps:**
1. Open `mcp_server/graphivac/api.json` and identify:
   - The endpoint and HTTP method for creating a grid.
   - The request body schema (content type, required fields).
   - The endpoint and HTTP method for deleting a grid.
   - Whether delete is supported; if not, note the limitation (grids may need manual deletion via the Graphivac UI).
2. Document findings as a comment block at the top of `graphivac-client.ts`.

**Files to create:**
- `mapper/src/lib/graphivac-client.ts` _(stub with documented findings)_

---

### Milestone 2 — Implement `listGrids` and `createGrid`

**Steps:**
1. Implement `listGrids` — `GET /orgs/:org/projects/:proj/grids`, parse JSON response.
2. Implement `createGrid` — `POST /orgs/:org/projects/:proj/grids`, parse the returned `id` from the response.
3. Manual test: call `createGrid("Test Grid")` from a temp API route (`/api/test-graphivac`), confirm a new grid appears in the Graphivac UI.

---

### Milestone 3 — Implement `deleteGrid`

**Steps:**
1. Implement `deleteGrid` — `DELETE /orgs/:org/projects/:proj/grids/:grid`.
2. Handle `404` from Graphivac as a no-op (idempotent).
3. Manual test: delete the grid created in Milestone 2, confirm it disappears from the Graphivac UI.

**Fallback if DELETE is unsupported by Graphivac API:**
- Log a warning instead of throwing.
- Document that deleted SI-MAPPER projects leave orphaned Graphivac grids that must be cleaned up manually.
- Update `13-04` delete route to reflect this limitation.

---

### Milestone 4 — Add env vars to documentation

**Steps:**
1. Add `GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID` to `mapper/.env.example`.
2. Add the same to `mapper/frontend.env.example`.
3. Update the `13-01` and `13-02` env var tables to include these new variables.

---

## Acceptance Criteria

- [ ] `mapper/src/lib/graphivac-client.ts` exists with `listGrids`, `createGrid`, `deleteGrid`.
- [ ] All functions read Graphivac coordinates from `process.env` (never hardcoded).
- [ ] `createGrid` returns the new grid ID as a string.
- [ ] `deleteGrid` handles `404` from Graphivac without throwing.
- [ ] The module is never imported from client components (server-only).
- [ ] `GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID` are documented in both `.env.example` and `frontend.env.example`.
- [ ] If the Graphivac API does not support grid deletion, the limitation is documented and the `deleteGrid` function logs a warning instead of failing.

---

## Notes & Decisions

- **One Graphivac project, many grids**: the deployment-level `GRAPHIVAC_PROJECT_ID` is a single shared Graphivac container. All SI-MAPPER projects create their grids inside it. This simplifies auth and avoids the need to create Graphivac-level projects via API.
- **No EDN in this module**: EDN encoding/decoding is only required for grid content operations (read/write component data). Grid management (create, list, delete) uses plain JSON. The MCP server and agent tools handle EDN; this TypeScript client does not.
- **No auth token in scope**: the current Graphivac integration in the project uses public URLs with no auth header. If auth is ever needed, it will be added as a `GRAPHIVAC_API_TOKEN` env var.
- **`api.json` as the source of truth**: `mcp_server/graphivac/api.json` was shipped with the project and describes the Graphivac REST API. It must be consulted before implementing the create/delete endpoints.

