# 13-01 — Externalize Frontend Configurations

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25

---

## Overview

The frontend (`mapper/`) currently embeds several service URLs and connection strings directly in source code. This makes it impossible to:
- Deploy the same build to different environments (development, staging, production).
- Switch projects without modifying and recompiling source files.
- Support multi-project workflows where different projects may point to different Graphivac grids.

This task extracts all environment-specific values into Next.js environment variables so the same compiled artifact can be configured at runtime without touching source code.

---

## Current State — Hardcoded Values

| File | Hardcoded Value | Problem |
|---|---|---|
| `src/app/api/copilotkit/route.ts:18` | `http://127.0.0.1:8001/` | Agent backend URL — breaks in Docker or remote deployments |
| `src/app/page.tsx:78` | `http://localhost:8001` | Agent polling URL — same issue, duplicated |
| `src/app/page/components/YourMainContent.tsx:111,116` | `https://graphivac.hvac.io/o/public/p/P-j8QIvTGH7p/g/G-LAiRS3mgp6?...` | Graphivac grid URL — must change per project |
| `src/app/api/graph/route.ts:9–12` | `bolt://localhost:7687`, `neo4j`, `neo4j_password` | Neo4j credentials — already reads `process.env` but lacks documentation and `.env.example` |

---

## Motivation

- **Deployability**: A Dockerized frontend (see `13-02`) requires URL configuration at container start time via environment variables, not at build time via source code edits.
- **Multi-project support**: Graphivac grid URLs are per-project (different `org_id`, `project_id`, `grid_id`). Once the project switcher exists, the active project's Graphivac URL will be selected dynamically. Until that switcher exists, the URL must at least be configurable outside source code.
- **Security**: Database credentials and internal service addresses should never be committed in plain source files.
- **DX**: A single `.env.local` file (gitignored) is the standard Next.js way to override defaults locally, making onboarding frictionless.

---

## Environment Variables to Introduce

### Server-Side (API routes only — never sent to the browser)

| Variable | Used in | Default | Description |
|---|---|---|---|
| `AGENT_BACKEND_URL` | `src/app/api/copilotkit/route.ts` | `http://127.0.0.1:8001` | Full base URL of the ADK agent's FastAPI server |
| `PROJECTS_FOLDER` | `src/app/api/files/route.ts` | `./uploads` (relative to `process.cwd()`) | Absolute path to the root folder where all project files are stored. In Docker this path is the container-side mount point of the projects volume. |
| `NEO4J_BOLT_URI` | `src/app/api/graph/route.ts` | `bolt://localhost:7687` | Neo4j Bolt connection URI (already partially used) |
| `NEO4J_USER` | `src/app/api/graph/route.ts` | `neo4j` | Neo4j username (already partially used) |
| `NEO4J_PASSWORD` | `src/app/api/graph/route.ts` | `neo4j_password` | Neo4j password (already partially used) |

### Client-Side (prefixed with `NEXT_PUBLIC_` — bundled into browser code)

| Variable | Used in | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_AGENT_BACKEND_URL` | `src/app/page.tsx` | `http://localhost:8001` | Agent polling base URL (must be reachable from the browser) |
| `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` | `src/app/page/components/YourMainContent.tsx` | _(none — required)_ | Full Graphivac grid URL, without query params (e.g. `https://graphivac.hvac.io/o/public/p/P-j8QIvTGH7p/g/G-LAiRS3mgp6`) |

> **Note on `NEXT_PUBLIC_` prefix:** Next.js inlines `NEXT_PUBLIC_*` variables at build time. Values used inside Server Components or API routes (e.g. `AGENT_BACKEND_URL`) do not need the prefix and remain secret.

---

## Implementation Plan

### Milestone 1 — Create Environment Variable Documentation

**Goal:** Provide a reference template so any developer (or Docker operator) knows exactly what variables to set.

**Steps:**
1. Create `mapper/.env.example` listing every variable with its default value and a one-line comment explaining its role.
2. Verify that `mapper/.env.local` is listed in `.gitignore` (Next.js default — confirm it is present).
3. Create or update `mapper/README.md` with a "Configuration" section pointing to `.env.example`.

**Files to create/modify:**
- `mapper/.env.example` _(new)_
- `mapper/README.md` _(update — add Configuration section)_

---

### Milestone 2 — Replace Server-Side Hardcoded URLs

**Goal:** The CopilotKit API route reads the agent backend URL from `process.env.AGENT_BACKEND_URL`.

**Steps:**
1. In `src/app/api/copilotkit/route.ts`, replace the literal `"http://127.0.0.1:8001/"` with:
   ```ts
   const agentUrl = process.env.AGENT_BACKEND_URL ?? "http://127.0.0.1:8001";
   ```
   and use `agentUrl` in the `HttpAgent` constructor.
2. Ensure the fallback preserves existing dev behaviour (no breaking change).
3. Confirm the variable is documented in `.env.example`.

**Files to modify:**
- `mapper/src/app/api/copilotkit/route.ts`

---

### Milestone 3 — Externalize the Projects Folder Path

**Goal:** The file-manager API (`/api/files`) reads project files from a configurable root directory instead of the hardcoded `./uploads` path relative to `process.cwd()`.

**Current state in `src/app/api/files/route.ts`:**
```ts
const UPLOADS_DIR = path.join(process.cwd(), 'uploads');
```
This is not overridable without editing source code, making it impossible to:
- Point to a different directory per environment.
- Mount a named Docker volume at a custom path.
- Support multi-project layouts where each project has its own sub-folder inside a shared projects root.

**Steps:**
1. In `src/app/api/files/route.ts`, replace the hardcoded constant with:
   ```ts
   const PROJECTS_FOLDER = process.env.PROJECTS_FOLDER
     ? path.resolve(process.env.PROJECTS_FOLDER)
     : path.join(process.cwd(), 'uploads');
   ```
   and replace every reference to `UPLOADS_DIR` with `PROJECTS_FOLDER`.
2. Ensure the path-traversal guard (`targetPath.startsWith(UPLOADS_DIR)`) is updated to use `PROJECTS_FOLDER`.
3. Add `PROJECTS_FOLDER` to `.env.example` with a comment explaining that in Docker it should match the container-side mount point.

**Files to modify:**
- `mapper/src/app/api/files/route.ts`
- `mapper/.env.example` _(covered in Milestone 1)_

---

### Milestone 4 — Replace Client-Side Hardcoded URLs

**Goal:** The polling config and the Graphivac iframe both read from `NEXT_PUBLIC_*` variables.

**Steps:**
1. In `src/app/page.tsx`, replace the literal `"http://localhost:8001"` in `pollingConfig` with:
   ```ts
   baseUrl: process.env.NEXT_PUBLIC_AGENT_BACKEND_URL ?? "http://localhost:8001",
   ```
2. In `src/app/page/components/YourMainContent.tsx`, replace the two hardcoded Graphivac URLs with:
   ```ts
   const graphivacBase = process.env.NEXT_PUBLIC_GRAPHIVAC_GRID_URL ?? "";
   // view tab:
   src={`${graphivacBase}?iframe=t&init-zoom=t`}
   // edit tab:
   src={`${graphivacBase}?mode=editor&init-zoom=t`}
   ```
3. If `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is empty, the `ExternalPageIframe` should render a placeholder message instead of a broken iframe.

**Files to modify:**
- `mapper/src/app/page.tsx`
- `mapper/src/app/page/components/YourMainContent.tsx`
- `mapper/src/app/page/components/ExternalPageIframe.tsx` _(add empty-src guard)_

---

### Milestone 5 — Consolidate & Document Neo4j Variables

**Goal:** The Neo4j env vars are already read via `process.env` but lack documentation and consistent defaults.

**Steps:**
1. Confirm `NEO4J_BOLT_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` appear in `.env.example` with correct defaults.
2. No code change needed in `src/app/api/graph/route.ts` — it already reads from `process.env` with fallbacks.

**Files to modify:**
- `mapper/.env.example` _(covered in Milestone 1)_

---

### Milestone 6 — Validation

**Steps:**
1. Run `pnpm dev` from `mapper/` without any `.env.local` — confirm all defaults work identically to the current behaviour.
2. Create a `mapper/.env.local` overriding each variable to a dummy value — confirm the app reads the override (check network tab / console logs).
3. Set `PROJECTS_FOLDER` to a temporary directory and confirm the file manager lists files from it instead of `uploads/`.
4. Confirm no env variable is accidentally leaked to the browser (`AGENT_BACKEND_URL` and `PROJECTS_FOLDER` must NOT appear in browser JS bundle).

---

## Acceptance Criteria

- [ ] `mapper/.env.example` exists with every variable documented.
- [ ] No hardcoded `127.0.0.1:8001` or `localhost:8001` remains in any source file.
- [ ] No hardcoded Graphivac URL remains in any source file.
- [ ] `UPLOADS_DIR` constant in `src/app/api/files/route.ts` is replaced by `PROJECTS_FOLDER` read from `process.env`.
- [ ] Path-traversal guard in the files API uses the `PROJECTS_FOLDER` value as its root boundary.
- [ ] Server-side variables (`AGENT_BACKEND_URL`, `PROJECTS_FOLDER`, `NEO4J_*`) are not prefixed with `NEXT_PUBLIC_` and are NOT bundled in browser JS.
- [ ] Client-side variables (`NEXT_PUBLIC_*`) fall back to dev-friendly defaults.
- [ ] A missing or empty `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` renders a graceful placeholder instead of a broken iframe.
- [ ] `mapper/README.md` includes a Configuration section explaining how to set up `.env.local`.
- [ ] All existing functionality works with default values (no regression).

---

## Notes & Decisions

- **`PROJECTS_FOLDER` and Docker volumes**: The value set in `frontend.env` for a Docker deployment must exactly match the container-side path used in the `docker-compose.yml` volume mount (see `13-02`). Example: if the compose file mounts `./mapper/uploads:/app/uploads`, then `PROJECTS_FOLDER=/app/uploads` must be set in `frontend.env`.
- **Multi-project Graphivac URL**: Phase 13 ultimately wants per-project Graphivac URLs managed via a project switcher. `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is the static, single-project stepping stone toward that goal. When the project switcher (Phase 13 core) lands, the active project's grid URL will override this env var dynamically from state.
- **`NEXT_PUBLIC_` build-time inlining**: Because Next.js inlines public env vars at build time, a single Docker image cannot support multiple Graphivac URLs without a runtime injection strategy (e.g. a `/api/config` endpoint that reads server-side vars and serves them to the client). This is acceptable for now — each deployment targets one environment. The project-switcher feature will address per-project grid switching within a single deployment.
- **`.env.local` vs `.env`**: Use `.env.local` for local overrides (gitignored). The committed `.env.example` serves as documentation. Docker deployments pass variables via `docker-compose.yml` `environment:` or `env_file:`.
