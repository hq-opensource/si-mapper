# 13-08 — Project Management UI

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-05` (project CRUD API + file routes), `13-06` (Graphivac grid API), `13-07` (ActiveProjectContext and selector established)

---

## Overview

Task `13-07` establishes the project selector — a navbar dropdown that lets users switch projects and perform quick create/delete actions. That lightweight switcher is intentionally minimal.

This task builds the **full project management surface** that the selector omits:

1. A **dedicated `/projects` management page** listing all projects with their configuration details.
2. An **Edit Project form** — the only UI for the `PATCH /api/projects/[id]` endpoint. Allows renaming a project, changing its AI model, or relinking it to a different Graphivac grid.
3. A **File Management panel** — the UI for `GET/POST/DELETE /api/projects/[id]/files`. Allows uploading, listing, and deleting files within a specific project folder.
4. A **"⚙ Manage projects →" entry point** in the selector dropdown (added in this task, wired to `/projects`) so management is discoverable without knowing a URL.

---

## What 13-07 Covers vs. What This Task Covers

| Action | 13-07 (Selector) | 13-08 (Management UI) |
|---|---|---|
| Switch active project | ✅ | — |
| Create project (quick, via PromptDialog) | ✅ | — |
| Delete project (quick, via ConfirmationDialog) | ✅ | — |
| **Edit project metadata** (name, model, Graphivac IDs) | ❌ | ✅ |
| **Upload files to a project** | ❌ | ✅ |
| **List files in a project** (management view) | ❌ | ✅ |
| **Delete a file from a project** | ❌ | ✅ |
| View project details (grid ID, created date, file count) | ❌ | ✅ |

---

## Management Page — `/projects`

### Access Point

A **"⚙ Manage projects →"** `<Link href="/projects">` is added to the bottom of the `ProjectSelector` dropdown (defined in `13-07`, wired here). This is the sole discovery point — no nav bar top-level link is added to avoid clutter.

```
Dropdown open:
┌─────────────────────────────────────────────┐
│ ● Building A — HVAC          [🗑]           │
│   Building B — Chiller Plant [🗑]           │
│ ─────────────────────────────────────────── │
│ + New project                               │
│ ⚙ Manage projects →                        │  ← navigates to /projects
└─────────────────────────────────────────────┘
```

### Page Layout

```
┌──────────────────────────────────────────────────────┐
│ ← Back to main view                                  │
│                                                      │
│ Projects                              [+ New Project] │
├──────────────────────────────────────────────────────┤
│ Building A — HVAC                                    │
│   Grid: G-LAiRS3mgp6  Model: gemini-3.1-pro          │
│   Created: 2026-03-25     Files: 3                   │
│   [✏ Edit]  [📁 Files (3)]  [🗑 Delete]              │
├──────────────────────────────────────────────────────┤
│ Building B — Chiller Plant                           │
│   Grid: G-XXXXXXXX  Model: claude-3-7-sonnet         │
│   Created: 2026-03-24     Files: 0                   │
│   [✏ Edit]  [📁 Files (0)]  [🗑 Delete]              │
└──────────────────────────────────────────────────────┘
```

**Route:** `mapper/src/app/projects/page.tsx`

The page is a standard Next.js App Router page. It inherits the root layout (which wraps `ActiveProjectProvider`), so `activeProject` and `refreshProjects()` are available. On any create/update/delete action, it calls `refreshProjects()` so the selector in the navbar reflects the change immediately.

---

## Edit Project Form

### Trigger

The **[✏ Edit]** button on a project card opens a modal dialog pre-filled with the project's current values.

### Fields

| Field | Input type | Required | Notes |
|---|---|---|---|
| `name` | Text | ✅ | The project display name |
| `ai_model_name` | Text | no | Falls back to global default if empty |
| `graphivac_org_id` | Text | no | Collapsible "Advanced" section |
| `graphivac_project_id` | Text | no | Collapsible "Advanced" section |
| `graphivac_grid_id` | Text | no | Allows relinking to an existing Graphivac grid |

> The Graphivac fields (org ID, project ID, grid ID) are hidden by default under a collapsible **"Advanced Settings"** section. Most users will never need to change them after project creation. Power users or operators relinking a project to a new grid can expand it.

### Behaviour

1. User clicks **[✏ Edit]** on a project card.
2. Dialog opens pre-filled with the current project record.
3. User edits one or more fields and clicks **Save**.
4. `PATCH /api/projects/[id]` is called with only the changed fields.
5. On success: close dialog, call `refreshProjects()`.
6. On error: show inline error message inside the dialog.

### Component

`mapper/src/components/ProjectEditDialog.tsx`

A custom multi-field dialog — **not** a reuse of `PromptDialog` (which accepts only a single text input). Uses the existing `Dialog`/`Sheet` pattern in the codebase.

---

## File Management Panel

### Trigger

The **[📁 Files (n)]** button on a project card expands an inline panel below the card (accordion pattern), or opens a full-width section. The file count shown on the button is fetched from `GET /api/projects/[id]/files` when the management page loads.

### Panel Layout

```
┌─────────────────────────────────────────────────────────┐
│ Files — Building A — HVAC          [⬆ Upload files]    │
├──────────────┬──────────┬───────────────┬───────────────┤
│ Name         │ Size     │ Modified      │ Actions       │
├──────────────┼──────────┼───────────────┼───────────────┤
│ bacnet.csv   │ 20 KB    │ 2026-03-25    │ [🗑 Delete]   │
│ drawing.pdf  │ 1.2 MB   │ 2026-03-24    │ [🗑 Delete]   │
└──────────────┴──────────┴───────────────┴───────────────┘
│ Drag & drop files here, or click "Upload files"         │
└─────────────────────────────────────────────────────────┘
```

### Upload Flow

1. User clicks **[⬆ Upload files]** or drops files onto the drop zone.
2. Files are sent via `POST /api/projects/[id]/files` as `multipart/form-data` with `overwrite: false`.
3. If a file already exists → `409 Conflict` from the API → show an inline per-file prompt:
   > "A file named `bacnet.csv` already exists. Replace it?"  [Replace] [Skip]
4. On success: refresh the file list.

### Delete Flow

1. User clicks **[🗑 Delete]** next to a file.
2. A small inline confirmation (tooltip or mini-alert) confirms the action.
3. `DELETE /api/projects/[id]/files/[filename]` is called.
4. File is removed from the list immediately.

### Component

`mapper/src/components/ProjectFilePanel.tsx`

---

## New Files to Create

| File | Purpose |
|---|---|
| `mapper/src/app/projects/page.tsx` | `/projects` management page |
| `mapper/src/components/ProjectCard.tsx` | Per-project row in the management page |
| `mapper/src/components/ProjectEditDialog.tsx` | Edit project metadata form/dialog |
| `mapper/src/components/ProjectFilePanel.tsx` | File listing, upload, delete within a project |

## Files to Modify

| File | Change |
|---|---|
| `mapper/src/components/ProjectSelector.tsx` | Add "⚙ Manage projects →" `<Link href="/projects">` at the bottom of the dropdown |

---

## Implementation Plan

### Milestone 1 — `/projects` Management Page & Navigation

**Steps:**
1. Create `mapper/src/app/projects/page.tsx`:
   - Fetch projects from `GET /api/projects` on load (client component with `useEffect`, or server component with fetch).
   - Render a `<ProjectCard>` for each project.
   - Include a **[+ New Project]** button that reuses the same `POST /api/projects` flow as the selector (can share a `createProject` helper from `ActiveProjectContext`).
   - Include a **[← Back to main view]** link.
2. Create `mapper/src/components/ProjectCard.tsx`:
   - Shows: name, Graphivac grid ID, AI model, created date, file count.
   - Actions: **[✏ Edit]**, **[📁 Files (n)]**, **[🗑 Delete]**.
   - Delete uses the existing `ConfirmationDialog` component; on confirm calls `DELETE /api/projects/[id]` and refreshes the list.
   - `ProjectEditDialog` and `ProjectFilePanel` are mounted inside the card (lazy — only rendered when opened).
3. Add the "⚙ Manage projects →" `<Link href="/projects">` to the bottom of `ProjectSelector.tsx`.

**Files to create:**
- `mapper/src/app/projects/page.tsx`
- `mapper/src/components/ProjectCard.tsx`

**Files to modify:**
- `mapper/src/components/ProjectSelector.tsx`

---

### Milestone 2 — Edit Project Dialog

**Steps:**
1. Create `mapper/src/components/ProjectEditDialog.tsx`:
   - Multi-field form: `name` (required), `ai_model_name`, and a collapsible "Advanced Settings" section for `graphivac_org_id`, `graphivac_project_id`, `graphivac_grid_id`.
   - Pre-populated from the `Project` record passed as a prop.
   - On submit: `PATCH /api/projects/[id]` with a diff of changed fields → close on success.
   - Error state: show inline error message.
2. Wire it into `ProjectCard.tsx` — the **[✏ Edit]** button opens the dialog with the project as prop.

**Files to create:**
- `mapper/src/components/ProjectEditDialog.tsx`

**Files to modify:**
- `mapper/src/components/ProjectCard.tsx`

---

### Milestone 3 — File Management Panel

**Steps:**
1. Create `mapper/src/components/ProjectFilePanel.tsx`:
   - On expand: fetch `GET /api/projects/[id]/files` and render the file table.
   - **Upload**: HTML `<input type="file" multiple>` + drag & drop zone → `POST /api/projects/[id]/files` with `overwrite=false`. Handle `409` with a per-file overwrite prompt (Replace / Skip).
   - **Delete**: per-row delete button → inline mini-confirm → `DELETE /api/projects/[id]/files/[filename]` → refresh file list.
   - Show file `name`, `size` (human-readable), `modified_at` in the table.
2. Wire it into `ProjectCard.tsx` — the **[📁 Files (n)]** button toggles the panel open/closed.

**Files to create:**
- `mapper/src/components/ProjectFilePanel.tsx`

**Files to modify:**
- `mapper/src/components/ProjectCard.tsx`

---

### Milestone 4 — Integration & State Sync

**Steps:**
1. Verify that `ActiveProjectContext` (from `13-07`, wrapping the root layout) is available on the `/projects` page without any additional provider.
2. After any create/update/delete on the management page, call `refreshProjects()` from `ActiveProjectContext` so the navbar selector reflects the change immediately.
3. After editing the currently active project's name, verify the navbar selector updates in real time.
4. Verify navigation flow: Main page → open selector → "Manage projects →" → `/projects` page → "[← Back]" → main page.

---

## Acceptance Criteria

- [ ] `/projects` page is accessible at the `Next.js` route `/projects`.
- [ ] The "⚙ Manage projects →" link in the `ProjectSelector` dropdown navigates to `/projects`.
- [ ] `/projects` page lists all projects fetched from `GET /api/projects`.
- [ ] Each project card shows: name, AI model, Graphivac grid ID, creation date, and file count.
- [ ] **[+ New Project]** on the management page calls `POST /api/projects` and adds the new project to the list.
- [ ] **[✏ Edit]** opens a pre-filled dialog; submitting calls `PATCH /api/projects/[id]` and refreshes the list.
- [ ] The edit dialog supports: `name`, `ai_model_name`, and Graphivac IDs (in a collapsible "Advanced" section).
- [ ] **[📁 Files (n)]** expands the file panel and loads files from `GET /api/projects/[id]/files`.
- [ ] File upload via file picker and drag & drop sends files to `POST /api/projects/[id]/files`.
- [ ] A `409` conflict on upload shows a per-file "Replace / Skip" prompt.
- [ ] **[🗑 Delete file]** calls `DELETE /api/projects/[id]/files/[filename]` and removes the file from the list.
- [ ] **[🗑 Delete project]** calls `DELETE /api/projects/[id]` with a confirmation dialog and removes the card.
- [ ] All create/update/delete actions call `refreshProjects()` so the navbar selector updates immediately.
- [ ] Editing the name of the currently active project is reflected in the selector's label without a page reload.
- [ ] A **[← Back to main view]** link is present on the `/projects` page.

---

## Notes & Decisions

- **Separate page vs. drawer**: A dedicated `/projects` route is chosen over a drawer/sheet. The management surface (project list + file manager + edit forms) has enough content to justify a full page. Drawers are more appropriate for quick, single-action interactions.
- **`ProjectEditDialog` vs. `PromptDialog` reuse**: `PromptDialog` accepts only a single text input. The edit form has 5+ fields with an advanced section — a custom dialog component is required.
- **File management here vs. `SvarFileManager`**: `SvarFileManager` (scoped in `13-07`) provides a tree-view sidebar for navigating project files alongside the canvas. `ProjectFilePanel` (this task) provides a flat administrative table for uploading, listing, and deleting files. Both views coexist with different purposes — one is for workflow, the other for administration.
- **File count on project card**: Fetching file counts requires one `GET /api/projects/[id]/files` call per project on page load. For typical project counts (< 20), this is acceptable. If performance becomes a concern, counts can be lazy-loaded when the card enters the viewport.
- **Overwrite dialog on upload conflict**: When a `409` is returned, the user is shown per-file options to "Replace" (retry with `overwrite=true`) or "Skip". This prevents silently clobbering existing files.
- **Advanced Graphivac fields in the edit form**: Hidden under a collapsible "Advanced Settings" section by default. Most users will never touch them post-creation. Power users relinking a project to an externally created grid can expand it.
- **Delete project from the management page**: Reuses the same `ConfirmationDialog` component already used in `ProjectSelector`. The delete flow is identical — `DELETE /api/projects/[id]` — so no new API logic is needed.
- **State sync with the selector**: The `/projects` page is wrapped in the same `ActiveProjectProvider` as the main page (root layout). Calling `refreshProjects()` after any mutation is sufficient to keep both views consistent.

