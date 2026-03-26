# 13-07 — Project & System Selector and Scoped UI

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-04` (data model), `13-05` (project & system CRUD API)
**See also:** `13-08` (Project Management UI — edit, file management; NOT covered here)

---

## Overview

This task wires the project and system data model into the frontend user experience. It covers:

1. A **React context** that tracks the currently active project and active system across the entire app.
2. A **two-level selector** in the navbar: one for the active project, one for the active system within that project.
3. **Scoping the file manager** so it shows only files from the active system's folder.
4. **Scoping the Graphivac iframe** so it displays the active system's grid (view and edit tabs).
5. **Wiring the active project and system into CopilotKit state** so the agent receives full context (consumed by `13-09`).

> **Scope boundary:** Quick create/delete actions in the selectors use `PromptDialog` / `ConfirmationDialog`. Full management — editing settings, uploading files — is handled in `13-08`.

---

## Active Workspace — State Design

### Storage: React context + `localStorage`

The active project and active system are UI/session state:
- Stored in a `WorkspaceContext` React context so any component can read them without prop-drilling.
- Persisted to `localStorage` under the keys `active-project-id` and `active-system-id`.

On mount, the app:
1. Reads `active-project-id` from `localStorage`.
2. Fetches the project list from `GET /api/projects`.
3. Resolves the active project (stored ID → project object, or first in list, or `null`).
4. Fetches the system list for the active project from `GET /api/projects/[id]/systems`.
5. Resolves the active system (stored `active-system-id` → system object, or first in list, or `null`).

When the active project changes, the system list is refreshed and `active-system-id` is reset.

### Context interface

```ts
// mapper/src/context/WorkspaceContext.tsx
interface WorkspaceContextValue {
  /** The currently active project, or null if none exist. */
  activeProject: Project | null;
  /** The currently active system within the active project, or null. */
  activeSystem: System | null;
  /** All available projects. */
  projects: Project[];
  /** All systems within the active project. */
  systems: System[];
  /** Switch the active project. Refreshes system list. Persists to localStorage. */
  setActiveProject: (project: Project) => Promise<void>;
  /** Switch the active system. Persists to localStorage. */
  setActiveSystem: (system: System) => void;
  /** Refresh the project list from the API. */
  refreshProjects: () => Promise<void>;
  /** Refresh the system list for the active project from the API. */
  refreshSystems: () => Promise<void>;
  /** True while the initial project or system list is loading. */
  isLoading: boolean;
}
```

---

## Navbar Selectors

### Location

Both selectors are rendered inside `AgentNavbar.tsx`.

### Project Selector

`mapper/src/components/ProjectSelector.tsx`

- Displays the active project's name.
- Dropdown lists all projects; clicking one sets it as active and reloads the system list.
- **"+ New project"** button → `PromptDialog` asking for the project name → `POST /api/projects` → activates the new project → loads its (empty) system list.
- **"🗑 Delete"** per project → `ConfirmationDialog` → `DELETE /api/projects/[id]` → refreshes everything.
- **"⚙ Manage →"** link at the bottom navigates to `/projects` (built in `13-08`).

### System Selector

`mapper/src/components/SystemSelector.tsx`

- Displayed next to the project selector, scoped to the active project.
- Displays the active system's name (e.g. "Chilled Water Plant").
- Dropdown lists all systems in the active project; clicking one sets it as active.
- **"+ New system"** button → `PromptDialog` asking for system name and optionally AI model → `POST /api/projects/[id]/systems` → activates the new system.
- **"🗑 Delete"** per system → `ConfirmationDialog` → `DELETE /api/projects/[id]/systems/[sysId]` → refreshes.
- Disabled (greyed out) when no project is active.

### UI wireframe (text)

```
┌─────────────────────────────────────────────────────────────┐
│ [Building A ▼]  [Chilled Water Plant ▼]  [+ New System]     │  ← navbar
└─────────────────────────────────────────────────────────────┘

Project dropdown open:
┌──────────────────────────────────────┐
│ ● Building A                [🗑]     │
│   Building B — Chiller Plant [🗑]   │
│ ─────────────────────────────────── │
│ + New project                        │
│ ⚙ Manage projects →                 │
└──────────────────────────────────────┘

System dropdown open (for Building A):
┌──────────────────────────────────────┐
│ ● Chilled Water Plant       [🗑]     │
│   AHU Zone 1                [🗑]     │
│ ─────────────────────────────────── │
│ + New system                         │
└──────────────────────────────────────┘
```

---

## File Manager Scoping

The file manager shows only files from the **active system's folder**.

**Approach:** Pass the project folder and system folder as query parameters:
```
/api/files?tree=true&project=proj-abc123&system=sys-aaa111
```

The `files/route.ts` resolves the target as `path.join(PROJECTS_FOLDER, project, system)` with path-traversal validation.

**Changes required:**
1. `mapper/src/app/api/files/route.ts` — accept optional `project` and `system` query params, resolve sub-path.
2. `mapper/src/components/SvarFileManager.tsx` — read `activeProject.folder_path` and `activeSystem.folder_path` from `WorkspaceContext`, append as `?project=&system=` to the fetch URL.
3. When either changes, re-fetch the tree.

---

## Graphivac Iframe Scoping

The Graphivac iframe URL is derived from the **active system's `graphivac_grid_id`** and the **active project's `graphivac_project_id`**, combined with the deployment-wide `GRAPHIVAC_ORG_ID` served via `/api/config`.

**Approach:**
1. `GET /api/config` returns:
   ```json
   { "graphivacBaseUrl": "https://graphivac.hvac.io", "graphivacOrgId": "public" }
   ```
2. In `YourMainContent.tsx`, construct the iframe URL from:
   - `graphivacBaseUrl` + `graphivacOrgId` from `/api/config`
   - `activeProject.graphivac_project_id`
   - `activeSystem.graphivac_grid_id`
3. The resulting URL pattern:
   ```
   https://graphivac.hvac.io/o/{org_id}/p/{project_id}/g/{grid_id}?iframe=t&init-zoom=t
   ```
4. Re-render the iframe whenever `activeSystem` changes.

> `GRAPHIVAC_ORG_ID` is served via `/api/config` (server-side route) rather than a `NEXT_PUBLIC_` env var. This keeps the org ID consistent with the server-side behaviour and avoids build-time baking.

---

## CopilotKit State — Wire-up

The agent needs to know both the active project and the active system.

```ts
initialState: {
  ...
  active_project: activeProject ? {
    id: activeProject.id,
    name: activeProject.name,
    folder_path: activeProject.folder_path,
    graphivac_project_id: activeProject.graphivac_project_id,
  } : null,
  active_system: activeSystem ? {
    id: activeSystem.id,
    name: activeSystem.name,
    folder_path: activeSystem.folder_path,
    graphivac_grid_id: activeSystem.graphivac_grid_id,
    ai_model_name: activeSystem.ai_model_name,
  } : null,
}
```

When `activeSystem` changes, update the agent state accordingly.

> Note: `graphivac_org_id` is NOT included in the agent state passed from the frontend. The agent reads it from its own env var (`GRAPHIVAC_ORG_ID`). This is consistent with the on-disk model.

---

## Implementation Plan

### Milestone 1 — `WorkspaceContext`

**Steps:**
1. Create `mapper/src/context/WorkspaceContext.tsx`.
2. On mount: fetch projects, restore selections from `localStorage`, fetch systems for active project.
3. Wrap root layout with `<WorkspaceProvider>`.

**Files to create:**
- `mapper/src/context/WorkspaceContext.tsx`

**Files to modify:**
- `mapper/src/app/layout.tsx`

---

### Milestone 2 — `ProjectSelector` and `SystemSelector` components

**Steps:**
1. Create `mapper/src/components/ProjectSelector.tsx` — project switcher with create/delete.
2. Create `mapper/src/components/SystemSelector.tsx` — system switcher with create/delete, disabled when no project.
3. Integrate both into `mapper/src/app/page/components/AgentNavbar.tsx`.

**Files to create:**
- `mapper/src/components/ProjectSelector.tsx`
- `mapper/src/components/SystemSelector.tsx`

**Files to modify:**
- `mapper/src/app/page/components/AgentNavbar.tsx`

---

### Milestone 3 — Scope the file manager to the active system

**Steps:**
1. Update `mapper/src/app/api/files/route.ts` — accept `project` and `system` query params.
2. Update `mapper/src/components/SvarFileManager.tsx` — append both to the fetch URL from context.

---

### Milestone 4 — Dynamic Graphivac iframe (system-scoped)

**Steps:**
1. Create `mapper/src/app/api/config/route.ts` — returns `{ graphivacBaseUrl, graphivacOrgId }`.
2. Update `YourMainContent.tsx` to derive the iframe URL from `activeProject.graphivac_project_id` + `activeSystem.graphivac_grid_id` + config.

---

### Milestone 5 — CopilotKit state wire-up

**Steps:**
1. In `page.tsx`, inject `active_project` and `active_system` into CopilotKit state.
2. Update when `activeProject` or `activeSystem` changes.

---

### Milestone 6 — Zero-project and zero-system states

**Steps:**
1. When `projects.length === 0`, show a prompt to create the first project.
2. When a project exists but `systems.length === 0`, show a prompt to create the first system.
3. Disable the chat interface and file manager until both an active project and active system exist.

---

## Acceptance Criteria

- [ ] `WorkspaceContext` provides `activeProject`, `activeSystem`, `projects`, `systems`, `setActiveProject`, `setActiveSystem`, `refreshProjects`, `refreshSystems`, `isLoading`.
- [ ] Active selections persist across page reloads via `localStorage`.
- [ ] Selecting a different project reloads the system list and resets the active system.
- [ ] The file manager shows only files under the active system's folder.
- [ ] The Graphivac iframe displays the active system's grid.
- [ ] Switching systems updates the file manager and Graphivac iframe without a full page reload.
- [ ] The agent state includes both `active_project` and `active_system`; neither includes `graphivac_org_id`.
- [ ] A zero-project state is displayed when no projects exist.
- [ ] A zero-system state is displayed when a project has no systems.
- [ ] `SystemSelector` is disabled when no project is active.

---

## Notes & Decisions

- **`WorkspaceContext` replaces `ActiveProjectContext`**: the scope has grown to cover both project and system selection. The new name better reflects this dual responsibility.
- **`graphivac_org_id` NOT in CopilotKit state**: the agent reads it from its own `GRAPHIVAC_ORG_ID` env var. Sending it from the frontend would be redundant and inconsistent with the design principle that org ID is a deployment constant.
- **System selector is disabled, not hidden, when no project is active**: this communicates the dependency clearly without removing the UI affordance.
- **`/api/config` exposes `graphivacOrgId`**: this is not sensitive (it appears in Graphivac iframe URLs already) and allows the frontend to construct accurate iframe URLs without a `NEXT_PUBLIC_` env var.
