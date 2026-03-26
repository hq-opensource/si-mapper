# 13-08 — Project & System Management UI

**Phase:** 13 — Multi-Project Support
**Status:** Done
**Updated:** 2026-03-26
**Depends on:** `13-05` (project & system CRUD API + file routes), `13-06` (Graphivac API), `13-07` (WorkspaceContext and selectors established)

---

## Overview

Task `13-07` establishes the lightweight navbar selectors for switching projects and systems. This task builds the **full management surface**:

1. A **dedicated `/projects` management page** with a two-panel layout: a left sidebar listing projects and a right panel showing system tabs + file manager.
2. A **Project Edit dialog** — rename a project.
3. A **System tab strip** per selected project — create, edit, delete systems.
4. A **System Edit dialog** — rename a system, change its AI model.
5. A **File & Folder Management panel** per system — upload files, create/rename/delete folders, navigate subfolders, delete files.
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
| **Create / rename / delete folders** | ❌ | ✅ |
| **List files and folders in a system** | ❌ | ✅ |
| **Delete a file from a system** | ❌ | ✅ |
| View system details (grid ID, dates, file count) | ❌ | ✅ |

---

## Management Page — `/projects`

**Route:** `mapper/src/app/projects/page.tsx`

### Access Point

**"⚙ Manage projects →"** `<Link href="/projects">` at the bottom of the `ProjectSelector` dropdown.

### URL Params (processed once on mount)

| Param | Value | Effect |
|---|---|---|
| `?create=project` | — | Opens the New Project prompt immediately |
| `?create=system&project=ID` | project ID | Selects that project and opens the New System prompt |

### Page Layout

The page uses a **two-panel layout** (full-height, no scroll at top level):

```
┌──────────────────────────────────────────────────────────────┐
│ ← Back  │  Project Management                                │  ← header
├──────────┼───────────────────────────────────────────────────┤
│          │  Systems ─────────────────────────────  [+ New]   │
│ Projects │  [Chilled Water Plant ✏ 🗑] [AHU Zone 1 ✏ 🗑] … │  ← tab strip
│  [+]     ├───────────────────────────────────────────────────┤
│          │                                                    │
│ 📁 Bldg A│  SystemFilePanel (selected system)                │
│ 📁 Bldg B│    Folders + Files card grid                      │
│ ...      │    [New Folder]  [Upload]                         │
│          │                                                    │
└──────────┴───────────────────────────────────────────────────┘
```

- **Left sidebar (w-60):** scrollable list of projects; each row has a color-coded folder icon (7-color palette), project name, and hover-revealed edit/delete icon buttons.
- **Right panel:** system tabs strip at the top (horizontal scroll), `SystemFilePanel` fills the remaining height for the selected system.
- Edit (✏) and delete (🗑) buttons for the **active** system tab are shown inline next to that tab; they are hidden for inactive tabs.
- Selecting a different project auto-selects the first system in that project.

### Color Palette

Projects cycle through 7 color variants for their folder icons (indigo → violet → blue → teal → emerald → amber → rose), using the project's list index.

---

## Edit Project Form

### Trigger

**[✏]** on a project sidebar row (hover-revealed) opens a modal dialog.

### Fields

| Field | Input type | Required |
|---|---|---|
| `name` | Text | ✅ |

> `graphivac_project_id` is immutable after creation and is not shown or editable in this dialog.

### Behaviour

1. `PATCH /api/projects/[id]` with `{ name }`.
2. On success: close dialog, call `refreshProjects()`.

### Component

`mapper/src/components/ProjectEditDialog.tsx`

---

## System Management

Each selected project shows a **horizontal tab strip** at the top of the right panel listing all its systems. Actions live inline in the active tab.

### System tab (active)

Shows: system name, and — revealed next to the tab — **[✏]** (edit) and **[🗑]** (delete) icon buttons.  
The Graphivac grid ID and AI model name are shown in the `SystemEditDialog` when editing.

### Create system

**[+ New system]** button at the end of the tab strip → `PromptDialog` (name only; model defaults to `gemini-2.0-flash`) → `POST /api/projects/[id]/systems` → refreshes system list → auto-selects created system.

---

## System Edit Dialog

### Trigger

**[✏]** on an active system tab.

### Fields

| Field | Input type | Required | Notes |
|---|---|---|---|
| `name` | Text | ✅ | |
| `ai_model_name` | Text | no | Model used by the agent for this system |

> `graphivac_grid_id` is immutable and shown read-only for reference in the `SystemEditDialog`.

### Behaviour

1. `PATCH /api/projects/[id]/systems/[sysId]` with changed fields.
2. On success: close dialog, call `refreshSystems()` / `fetchSystems()`.

### Component

`mapper/src/components/SystemEditDialog.tsx`

---

## File & Folder Management Panel

### Trigger

Selecting a system tab automatically displays `SystemFilePanel` in the right panel (always open on the management page).

### Panel Layout (card-grid, not a table)

```
┌─────────────────────────────────────────────────────────────┐
│ SystemName  ›  FolderName        [New Folder]  [Upload]     │  ← header / breadcrumb
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 📁 dark  │  │ 📁 dark  │  │ + Add    │  │ 📄 CSV   │    │
│  │ Data     │  │ Plans    │  │ folder   │  │ bacnet   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  (click folder to navigate in; three-dot menu: Rename/Del)  │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Drag & drop files here or click Upload                   ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

- **Folder cards:** uniform dark-navy SVG folder icon; click to navigate into subfolder; three-dot (⋮) menu → Rename / Delete.
- **File cards:** coloured document SVG icon keyed by extension (PDF=red, CSV=green, TTL=purple, etc.) with the extension label overlaid; three-dot menu → Delete.
- **Breadcrumb:** `SystemName › FolderName`; clicking the system name returns to the root level.
- **"← Back to parent folder"** link appears when inside a subfolder.
- **Drag & drop overlay:** full-panel overlay with animated `CloudUpload` icon while dragging.
- **New Folder button** is only shown at the root level.

### API used

- `GET /api/projects/[id]/systems/[sysId]/files` — list files (supports `?subfolder=` param).
- `POST /api/projects/[id]/systems/[sysId]/files` — upload files (multipart/form-data; supports `overwrite=true` and `subfolder=` fields).
- `DELETE /api/projects/[id]/systems/[sysId]/files/[filename]` — delete a file (supports `?subfolder=` param).
- `GET /api/projects/[id]/systems/[sysId]/folders` — list folders (root only).
- `POST /api/projects/[id]/systems/[sysId]/folders` — create a folder `{ name }`.
- `PATCH /api/projects/[id]/systems/[sysId]/folders/[name]` — rename a folder `{ name }`.
- `DELETE /api/projects/[id]/systems/[sysId]/folders/[name]` — delete a folder and all its contents.

### Conflict handling

On `409 Conflict`: a modal prompt asks **Replace / Skip** per file before retrying with `overwrite=true`.

### Component

`mapper/src/components/SystemFilePanel.tsx`

---

## New Files Created

| File | Purpose |
|---|---|
| `mapper/src/app/projects/page.tsx` | `/projects` management page (two-panel layout) |
| `mapper/src/components/ProjectEditDialog.tsx` | Edit project name dialog |
| `mapper/src/components/SystemEditDialog.tsx` | Edit system name and model dialog |
| `mapper/src/components/SystemFilePanel.tsx` | File & folder manager (card-grid view, subfolder navigation, drag & drop) |

> `ProjectCard.tsx` and `SystemCard.tsx` were created during development but were never consumed by the live `/projects` page. They were removed as dead code.

## Files Modified

| File | Change |
|---|---|
| `mapper/src/components/ProjectSelector.tsx` | Already has "⚙ Manage projects →" link (from `13-07`); no change needed |

---

## Implementation Notes

### Layout divergence from original plan

The original plan described a **scrollable card list** where each `ProjectCard` expanded inline to show its systems and `SystemFilePanel`. The final implementation uses a **two-panel SPA-style layout** instead:
- Left sidebar = project list (selection, edit, delete)
- Right panel = system tabs + full-height `SystemFilePanel`

`ProjectCard` and `SystemCard` were created during development but were never imported by the `/projects` page or any other live route. They were **removed as dead code**.

### SystemFilePanel — folder management (beyond original scope)

`SystemFilePanel` was extended beyond the flat file-list described in the plan to include:
- **Subfolder creation**, **rename**, and **delete** via a `/folders` API.
- **Card-grid layout** (styled after SVAR Willow "Files" tab) instead of a table.
- **Breadcrumb navigation** for entering and leaving subfolders.
- Per-extension **coloured SVG file icons** and a uniform dark-navy **folder SVG icon**.
- **Three-dot (⋮) dropdown menu** per card for Rename (folders) / Delete actions.

---

## Acceptance Criteria

- [x] `/projects` page lists all projects; selecting a project shows its systems in a tab strip.
- [x] Each project in the sidebar shows its name and a colour-coded folder icon.
- [x] `graphivac_project_id` is not shown by default in any form or panel (immutable, hidden).
- [x] Each system tab shows its name; the active tab reveals edit and delete icon buttons inline.
- [x] **[✏]** on a project opens a dialog; saving calls `PATCH /api/projects/[id]` and updates the list.
- [x] **[✏]** on a system opens a dialog with `name` and `ai_model_name`; saving calls `PATCH /api/projects/[id]/systems/[sysId]`.
- [x] **[+ New system]** calls `POST /api/projects/[id]/systems` and adds the system tab.
- [x] **[🗑]** on a system calls `DELETE .../systems/[sysId]` with `ConfirmationDialog`.
- [x] **[🗑]** on a project calls `DELETE /api/projects/[id]` with `ConfirmationDialog`, removes all systems.
- [x] `SystemFilePanel` is always open on the management page for the selected system.
- [x] Files are fetched from `GET .../systems/[sysId]/files` (with subfolder param support).
- [x] File upload via file picker and drag & drop sends to `POST .../systems/[sysId]/files`.
- [x] A `409` conflict shows a per-file "Replace / Skip" prompt.
- [x] **[🗑]** on a file (three-dot menu) calls `DELETE .../files/[filename]` and removes the card.
- [x] Folders can be created (`POST .../folders`), renamed (`PATCH .../folders/[name]`), and deleted (`DELETE .../folders/[name]`).
- [x] Clicking a folder card navigates into it (subfolder view); breadcrumb and "← Back" link return to root.
- [x] All mutations call `refreshProjects()` / `fetchSystems()` so the navbar selectors update immediately.
- [x] URL params `?create=project` and `?create=system&project=ID` open the relevant creation prompt on page load.
- [x] The Graphivac `graphivac_org_id` is never displayed or editable in any form.

---

## Notes & Decisions

- **`graphivac_org_id` is completely absent from the management UI**: it is a deployment constant. There is no field for it in any form, and it is not shown in the project or system detail views.
- **`graphivac_project_id` and `graphivac_grid_id` are read-only**: shown for reference only in the `SystemEditDialog`; neither can be edited after creation.
- **Files belong to systems, not projects**: there is no project-level file panel.
- **`SystemFilePanel` vs `SvarFileManager`**: `SvarFileManager` (in `13-07`) provides a tree-view sidebar for the main working view. `SystemFilePanel` (this task) provides a card-grid admin panel for uploading/organising files. Both coexist with different purposes.
- **State sync via `WorkspaceContext`**: the `/projects` page is wrapped in the same `WorkspaceProvider` as the main page (root layout). Calling `refreshProjects()` / `fetchSystems()` is sufficient to keep the selector and the management page in sync.
- **`Suspense` wrapper required**: `useSearchParams` in Next.js App Router requires the component to be wrapped in `<Suspense>`. `ProjectsPageInner` contains the logic; `ProjectsPage` (the default export) wraps it.
