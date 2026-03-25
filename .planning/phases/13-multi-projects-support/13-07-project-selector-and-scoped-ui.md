# 13-07 — Project Selector & Scoped UI

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-04` (data model), `13-05` (project CRUD API)

---

## Overview

This task wires the project data model and CRUD API into the frontend user experience. It covers:

1. A **React context** that tracks the currently active project across the entire app.
2. A **project selector component** (in the navbar) that lets users switch between projects, create new ones, or delete existing ones.
3. **Scoping the file manager** so it shows only files from the active project's folder.
4. **Scoping the Graphivac iframe** so it displays the active project's grid (view and edit tabs).
5. **Wiring the active project into CopilotKit state** so the agent receives project context (consumed by `13-08`).

---

## Active Project — State Design

### Storage: React context + `localStorage`

The active project is UI/session state. It is:
- **Not stored in `project.json`** (on-disk project config is per-project, not per-user-session).
- **Stored in a React context** (`ActiveProjectContext`) so any component can read it without prop-drilling.
- **Persisted to `localStorage`** under the key `active-project-id` so the selection survives page reloads.

On mount, the app:
1. Reads `active-project-id` from `localStorage`.
2. Fetches the project list from `GET /api/projects`.
3. If the stored ID is in the list → set it as active.
4. If the stored ID is not in the list (project was deleted) → set the first project as active, or `null` if none.

### Context interface

```ts
// mapper/src/context/ActiveProjectContext.tsx
interface ActiveProjectContextValue {
  /** The currently active project, or null if none exist. */
  activeProject: Project | null;
  /** All available projects. */
  projects: Project[];
  /** Switch the active project. Persists to localStorage. */
  setActiveProject: (project: Project) => void;
  /** Refresh the project list from the API. */
  refreshProjects: () => Promise<void>;
  /** True while the initial project list is loading. */
  isLoading: boolean;
}
```

---

## Project Selector Component

### Location

`mapper/src/components/ProjectSelector.tsx`

### Behaviour

- Rendered inside `AgentNavbar.tsx` (already in the navbar area).
- Displays the active project's name as the current selection label.
- Opens a dropdown listing all projects — clicking one sets it as active.
- Contains a **"New project"** button that opens a `PromptDialog` (the `PromptDialog.tsx` component already exists) asking for:
  - Project name (required).
  - AI model name (optional, defaults to env-configured default).
  - Graphivac org ID (pre-filled from `NEXT_PUBLIC_GRAPHIVAC_ORG_ID` — see env var addition below).
  - Graphivac project ID (pre-filled from `NEXT_PUBLIC_GRAPHIVAC_PROJECT_ID`).
- On creation confirm:
  1. `POST /api/projects` with the form data.
  2. Call `refreshProjects()`.
  3. Set the newly created project as active.
- Contains a **"Delete project"** button (with a `ConfirmationDialog` — already exists) on each project entry.
  - On confirm: `DELETE /api/projects/[id]`, then `refreshProjects()`.
  - If the deleted project was active, auto-select the next available project.

### UI wireframe (text)

```
┌─────────────────────────────────────────────┐
│ [Building A — HVAC ▼]  [+ New Project]      │  ← navbar area
└─────────────────────────────────────────────┘

Dropdown open:
┌─────────────────────────────────────────────┐
│ ● Building A — HVAC          [🗑]           │
│   Building B — Chiller Plant [🗑]           │
│ ─────────────────────────────────────────── │
│ + New project                               │
└─────────────────────────────────────────────┘
```

---

## File Manager Scoping

### Current behaviour

`SvarFileManager.tsx` fetches `/api/files?tree=true` — which returns everything under `PROJECTS_FOLDER`.

### Required behaviour

The file manager should show only the active project's subfolder. 

**Approach:** Pass a `projectFolder` query parameter to `/api/files`:
```
/api/files?tree=true&project=proj-abc123
```

The `files/route.ts` already has `PROJECTS_FOLDER` as its root (after `13-01`). When `project` is provided, the API resolves the target as `path.join(PROJECTS_FOLDER, project)` and uses that as the tree root — with path-traversal validation.

**Changes required:**
1. `mapper/src/app/api/files/route.ts` — accept optional `project` query param, resolve sub-path, validate against traversal.
2. `mapper/src/components/SvarFileManager.tsx` — read `activeProject.folder_path` from `ActiveProjectContext`, append as `?project=` to the fetch URL.
3. When `activeProject` changes, `SvarFileManager` re-fetches the tree.

---

## Graphivac Iframe Scoping

### Current behaviour (after `13-01`)

Both the View and Edit tabs use `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` — a static env var baked in at build time.

### Required behaviour

The Graphivac grid URL is derived dynamically from the active project at runtime, not from a build-time env var. This requires a runtime configuration approach because `NEXT_PUBLIC_` variables are inlined at build time and cannot change per-project.

**Approach:** Replace the static env var usage with the active project's Graphivac fields, delivered via a server-side API endpoint.

1. Add `GET /api/config` — a server-side route that returns the Graphivac base URL and any other runtime config that the browser needs but cannot receive via `NEXT_PUBLIC_`:
   ```json
   {
     "graphivacBaseUrl": "https://graphivac.hvac.io"
   }
   ```
2. In `YourMainContent.tsx`, construct the Graphivac iframe URL from:
   - `activeProject.graphivac_org_id`
   - `activeProject.graphivac_project_id`
   - `activeProject.graphivac_grid_id`
   - `graphivacBaseUrl` fetched from `/api/config`
3. The resulting URL follows the pattern already in use:
   ```
   https://graphivac.hvac.io/o/{org_id}/p/{project_id}/g/{grid_id}?iframe=t&init-zoom=t
   ```
   > **Note:** verify this URL pattern against the live Graphivac URL format. The current hardcoded URL uses `/o/public/p/P-.../g/G-...` — adapt accordingly.

4. `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` (from `13-01`) becomes the **fallback** when no project is active (zero-project state), and can be removed once a project always exists.

**New env vars to add (for `/api/config`):**

| Variable | Description |
|---|---|
| `GRAPHIVAC_BASE_URL` | Already added in `13-06` — reuse here |

No additional `NEXT_PUBLIC_` variables are introduced for the Graphivac URL — the base URL is served via `/api/config` instead.

---

## CopilotKit State — Active Project Wire-up

The agent needs to know the active project. The mechanism is CopilotKit's `useCoAgent` state, which is already used in `page.tsx`. 

**Steps:**
1. In `page.tsx`, read `activeProject` from `ActiveProjectContext`.
2. Add a `useCopilotAction` or set initial state that includes:
   ```ts
   initialState: {
     ...
     active_project: activeProject ? {
       id: activeProject.id,
       name: activeProject.name,
       folder_path: activeProject.folder_path,
       graphivac_org_id: activeProject.graphivac_org_id,
       graphivac_project_id: activeProject.graphivac_project_id,
       graphivac_grid_id: activeProject.graphivac_grid_id,
       ai_model_name: activeProject.ai_model_name,
     } : null,
   }
   ```
3. When `activeProject` changes, update the agent state so the agent knows it switched projects.

> The agent consuming this state is described in `13-08`.

---

## Implementation Plan

### Milestone 1 — `ActiveProjectContext`

**Steps:**
1. Create `mapper/src/context/ActiveProjectContext.tsx`.
2. On mount: fetch `/api/projects`, restore selection from `localStorage`, resolve active project.
3. Wrap `CopilotKitPage` (or the root layout) with `<ActiveProjectProvider>`.

**Files to create:**
- `mapper/src/context/ActiveProjectContext.tsx`

**Files to modify:**
- `mapper/src/app/layout.tsx` or `mapper/src/app/page.tsx` _(wrap with provider)_

---

### Milestone 2 — `ProjectSelector` component

**Steps:**
1. Create `mapper/src/components/ProjectSelector.tsx`.
2. Integrate into `mapper/src/app/page/components/AgentNavbar.tsx`.
3. Wire `POST /api/projects` for creation using the existing `PromptDialog`.
4. Wire `DELETE /api/projects/[id]` for deletion using the existing `ConfirmationDialog`.

**Files to create:**
- `mapper/src/components/ProjectSelector.tsx`

**Files to modify:**
- `mapper/src/app/page/components/AgentNavbar.tsx`

---

### Milestone 3 — Scope the file manager

**Steps:**
1. Update `mapper/src/app/api/files/route.ts` — accept `project` query param, validate, resolve sub-path.
2. Update `mapper/src/components/SvarFileManager.tsx` — read active project from context, append `?project=` to fetch.

**Files to modify:**
- `mapper/src/app/api/files/route.ts`
- `mapper/src/components/SvarFileManager.tsx`

---

### Milestone 4 — Dynamic Graphivac iframe

**Steps:**
1. Create `mapper/src/app/api/config/route.ts` returning `{ graphivacBaseUrl }`.
2. Update `mapper/src/app/page/components/YourMainContent.tsx` to:
   - Fetch `/api/config` once on mount.
   - Derive the Graphivac iframe URL from `activeProject` fields + `graphivacBaseUrl`.
   - Re-render the iframe when `activeProject` changes.

**Files to create:**
- `mapper/src/app/api/config/route.ts`

**Files to modify:**
- `mapper/src/app/page/components/YourMainContent.tsx`

---

### Milestone 5 — CopilotKit state wire-up

**Steps:**
1. In `mapper/src/app/page.tsx`, inject `active_project` into the agent's initial/updated state.
2. Confirm the agent receives the object by checking the state debug tab in the UI.

**Files to modify:**
- `mapper/src/app/page.tsx`

---

### Milestone 6 — Zero-project state

**Steps:**
1. When `projects.length === 0`, show a prompt encouraging the user to create the first project via the project selector.
2. Disable the chat interface and file manager until at least one project exists.
3. Show a placeholder in the View/Edit tabs when no project is active.

---

## Acceptance Criteria

- [ ] `ActiveProjectContext` exists and wraps the app, providing `activeProject`, `projects`, `setActiveProject`, `refreshProjects`, `isLoading`.
- [ ] Active project selection persists across page reloads via `localStorage`.
- [ ] `ProjectSelector` in the navbar shows the active project name and allows switching.
- [ ] Creating a project via the selector calls `POST /api/projects` and immediately activates the new project.
- [ ] Deleting a project via the selector calls `DELETE /api/projects/[id]` and switches to another project.
- [ ] The file manager shows only files under the active project's folder.
- [ ] The Graphivac View and Edit iframes display the active project's grid.
- [ ] Switching projects updates the file manager and Graphivac iframes without a full page reload.
- [ ] The active project is included in the CopilotKit agent state.
- [ ] A graceful zero-project state is displayed when no projects exist.

---

## Notes & Decisions

- **`/api/config` for runtime config**: this is the standard pattern to serve server-side env vars to the browser without `NEXT_PUBLIC_` inlining. It adds a one-time fetch on mount but avoids the build-time constraint.
- **`PromptDialog` and `ConfirmationDialog` reuse**: both components already exist in `mapper/src/components/`. The project creation dialog and delete confirmation do not require new modal components.
- **File manager root change**: scoping the file manager to a project subfolder is implemented entirely in the API route (`?project=` param) rather than in the component, keeping the component stateless regarding path resolution.
- **CopilotKit state update on project switch**: when the user switches project, `active_project` in the agent state is updated. The agent must be designed (in `13-08`) to re-read this value at the start of each task rather than caching it.

