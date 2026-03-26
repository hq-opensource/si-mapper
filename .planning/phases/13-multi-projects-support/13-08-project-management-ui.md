# 13-08 — Project & System Management UI

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-05` (project & system CRUD API + file routes), `13-06` (Graphivac API), `13-07` (WorkspaceContext and selectors established)

---

## Overview

Task `13-07` establishes the lightweight navbar selectors for switching projects and systems. This task builds the **full management surface**:

1. A **dedicated `/projects` management page** listing all projects and their systems.
2. An **Edit Project form** — rename a project.
3. A **System management panel** per project — create, edit, delete systems; manage system files.
4. A **System Edit form** — rename a system, change its AI model.
5. A **File Management panel** per system — upload, list, delete files.
6. A **"⚙ Manage projects →" entry point** in the project selector (wired in `13-07`) that navigates to `/projects`.

---

## What 13-07 Covers vs. What This Task Covers

| Action | 13-07 (Selectors) | 13-08 (Management UI) |
|---|---|---|
| Switch active project | ✅ | — |
| Switch active system | ✅ | — |
| Create project (quick) | ✅ | — |
| Create system (quick) | ✅ | — |
| Delete project (quick) | ✅ | — |
| Delete system (quick) | ✅ | — |
| **Edit project name** | ❌ | ✅ |
| **Edit system name / model** | ❌ | ✅ |
| **Upload files to a system** | ❌ | ✅ |
| **List files in a system** | ❌ | ✅ |
| **Delete a file from a system** | ❌ | ✅ |
| View system details (grid ID, dates, file count) | ❌ | ✅ |

---

## Management Page — `/projects`

**Route:** `mapper/src/app/projects/page.tsx`

### Access Point

**"⚙ Manage projects →"** `<Link href="/projects">` at the bottom of the `ProjectSelector` dropdown.

### Page Layout

```
┌──────────────────────────────────────────────────────────┐
│ ← Back to main view                                      │
│                                                          │
│ Projects                            [+ New Project]      │
├──────────────────────────────────────────────────────────┤
│ Building A                                               │
│   Graphivac Project: P-j8QIvTGH7p                        │
│   Created: 2026-03-25                                    │
│   [✏ Edit]  [🗑 Delete]                                  │
│   ┌── Systems ──────────────────────────────────────┐   │
│   │ Chilled Water Plant  G-LAiRS3mgp6  gemini-3.1   │   │
│   │   [✏ Edit]  [📁 Files (3)]  [🗑 Delete]         │   │
│   │ AHU Zone 1           G-XXXXXXXX   claude-3-7    │   │
│   │   [✏ Edit]  [📁 Files (0)]  [🗑 Delete]         │   │
│   │ [+ New System]                                   │   │
│   └──────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│ Building B — Chiller Plant                               │
│   ...                                                    │
└──────────────────────────────────────────────────────────┘
```

---

## Edit Project Form

### Trigger

**[✏ Edit]** on a project card opens a modal dialog.

### Fields

| Field | Input type | Required |
|---|---|---|
| `name` | Text | ✅ |

> `graphivac_project_id` is immutable after creation and is shown read-only for reference only, not editable.

### Behaviour

1. `PATCH /api/projects/[id]` with `{ name }`.
2. On success: close dialog, call `refreshProjects()`.

### Component

`mapper/src/components/ProjectEditDialog.tsx`

---

## System Management Panel

Each project card has an inline **Systems** section listing all systems. It is always expanded on the management page (unlike the selector dropdown which is compact).

### System row

Each system row shows: name, Graphivac grid ID (read-only), AI model name, file count.
Actions: **[✏ Edit]**, **[📁 Files (n)]**, **[🗑 Delete]**.

### Create system

**[+ New System]** button at the bottom of the systems section → inline form or `PromptDialog` → `POST /api/projects/[id]/systems` → refreshes the system list.

---

## System Edit Form

### Trigger

**[✏ Edit]** on a system row.

### Fields

| Field | Input type | Required | Notes |
|---|---|---|---|
| `name` | Text | ✅ | |
| `ai_model_name` | Text | no | Model used by the agent for this system |

> `graphivac_grid_id` is immutable and shown read-only for reference.

### Behaviour

1. `PATCH /api/projects/[id]/systems/[sysId]` with changed fields.
2. On success: close dialog, call `refreshSystems()`.

### Component

`mapper/src/components/SystemEditDialog.tsx`

---

## File Management Panel

### Trigger

**[📁 Files (n)]** on a system row — toggles an inline accordion panel.

### Panel Layout

```
┌─────────────────────────────────────────────────────────┐
│ Files — Chilled Water Plant         [⬆ Upload files]    │
├──────────────┬──────────┬───────────────┬───────────────┤
│ Name         │ Size     │ Modified      │ Actions       │
├──────────────┼──────────┼───────────────┼───────────────┤
│ bacnet.csv   │ 20 KB    │ 2026-03-25    │ [🗑 Delete]   │
└──────────────┴──────────┴───────────────┴───────────────┘
│ Drag & drop files here, or click "Upload files"         │
└─────────────────────────────────────────────────────────┘
```

### API used

- `GET /api/projects/[id]/systems/[sysId]/files` — list files.
- `POST /api/projects/[id]/systems/[sysId]/files` — upload files (multipart/form-data).
- `DELETE /api/projects/[id]/systems/[sysId]/files/[filename]` — delete a file.

### Conflict handling

On `409 Conflict`: show a per-file "Replace / Skip" prompt before retrying with `overwrite=true`.

### Component

`mapper/src/components/SystemFilePanel.tsx`

---

## New Files to Create

| File | Purpose |
|---|---|
| `mapper/src/app/projects/page.tsx` | `/projects` management page |
| `mapper/src/components/ProjectCard.tsx` | Per-project row on the management page |
| `mapper/src/components/ProjectEditDialog.tsx` | Edit project name dialog |
| `mapper/src/components/SystemCard.tsx` | Per-system row within a project card |
| `mapper/src/components/SystemEditDialog.tsx` | Edit system name and model dialog |
| `mapper/src/components/SystemFilePanel.tsx` | File listing, upload, delete for a system |

## Files to Modify

| File | Change |
|---|---|
| `mapper/src/components/ProjectSelector.tsx` | Already has "⚙ Manage →" link (from `13-07`); no change needed |

---

## Implementation Plan

### Milestone 1 — `/projects` page and `ProjectCard`

**Steps:**
1. Create `mapper/src/app/projects/page.tsx` — fetches all projects, renders a `<ProjectCard>` per project, includes **[+ New Project]** and **[← Back]**.
2. Create `mapper/src/components/ProjectCard.tsx` — shows project metadata, systems list, and action buttons.

---

### Milestone 2 — Project edit and system list

**Steps:**
1. Create `mapper/src/components/ProjectEditDialog.tsx` — single-field form for `name`, calls `PATCH /api/projects/[id]`.
2. Create `mapper/src/components/SystemCard.tsx` — system row with name, grid ID, model, file count, actions.
3. Wire **[+ New System]** within `ProjectCard` → `POST /api/projects/[id]/systems`.
4. Wire **[🗑 Delete]** system → `ConfirmationDialog` → `DELETE /api/projects/[id]/systems/[sysId]`.

---

### Milestone 3 — System edit

**Steps:**
1. Create `mapper/src/components/SystemEditDialog.tsx` — form for `name` and `ai_model_name`.
2. On submit: `PATCH /api/projects/[id]/systems/[sysId]`, close dialog, refresh systems.

---

### Milestone 4 — File management panel

**Steps:**
1. Create `mapper/src/components/SystemFilePanel.tsx`:
   - On expand: `GET /api/projects/[id]/systems/[sysId]/files`.
   - Upload: drag & drop + file picker → `POST .../files` with `overwrite=false`. Handle `409` with Replace/Skip prompt.
   - Delete: per-row → mini-confirm → `DELETE .../files/[filename]` → refresh.
2. Wire **[📁 Files (n)]** in `SystemCard` to toggle the panel.

---

### Milestone 5 — Integration & state sync

**Steps:**
1. After any mutation on the management page, call `refreshProjects()` or `refreshSystems()` from `WorkspaceContext`.
2. Verify the navbar selectors reflect changes made on the management page immediately.

---

## Acceptance Criteria

- [ ] `/projects` page lists all projects, each showing its systems.
- [ ] Each project shows: name, Graphivac Project ID (read-only), creation date.
- [ ] Each system shows: name, Graphivac Grid ID (read-only), AI model, file count.
- [ ] **[✏ Edit]** on a project opens a dialog; saving calls `PATCH /api/projects/[id]` and updates the list.
- [ ] **[✏ Edit]** on a system opens a dialog with `name` and `ai_model_name`; saving calls `PATCH /api/projects/[id]/systems/[sysId]`.
- [ ] **[+ New System]** calls `POST /api/projects/[id]/systems` and adds the system to the list.
- [ ] **[🗑 Delete]** on a system calls `DELETE .../systems/[sysId]` with confirmation.
- [ ] **[🗑 Delete]** on a project calls `DELETE /api/projects/[id]` with confirmation, removes all systems.
- [ ] **[📁 Files (n)]** expands the file panel; files are fetched from `GET .../systems/[sysId]/files`.
- [ ] File upload via file picker and drag & drop sends to `POST .../systems/[sysId]/files`.
- [ ] A `409` conflict shows a per-file "Replace / Skip" prompt.
- [ ] **[🗑 Delete file]** calls `DELETE .../files/[filename]` and removes the file from the list.
- [ ] All mutations call `refreshProjects()` / `refreshSystems()` so the navbar selectors update immediately.
- [ ] The Graphivac `graphivac_org_id` is never displayed or editable in any form.

---

## Notes & Decisions

- **`graphivac_org_id` is completely absent from the management UI**: it is a deployment constant. There is no field for it in any form, and it is not shown in the project or system detail views.
- **`graphivac_project_id` and `graphivac_grid_id` are read-only**: they are shown for reference (useful for debugging or manual Graphivac operations) but cannot be edited after creation. They are displayed in a collapsible "Technical details" section to avoid clutter.
- **Files belong to systems, not projects**: there is no project-level file panel. All file management is on the system row.
- **`SystemFilePanel` vs `SvarFileManager`**: `SvarFileManager` (in `13-07`) provides a tree-view sidebar for the main working view. `SystemFilePanel` (this task) provides a flat admin table for uploading/deleting. Both coexist with different purposes.
- **State sync via `WorkspaceContext`**: the `/projects` page is wrapped in the same `WorkspaceProvider` as the main page (root layout). Calling `refreshProjects()` / `refreshSystems()` is sufficient to keep the selector and the management page in sync.
