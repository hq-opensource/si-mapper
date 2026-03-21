---
phase: 09
plan: "04"
subsystem: frontend
tags: [ui, code-viewer, ontology, tabs, ttl, python]
dependency_graph:
  requires:
    - mapper/src/app/page/components/SharedPageContainer.tsx
    - mapper/src/app/page/components/StatusPlaceholder.tsx
    - mapper/src/app/page/context/ThoughtsContext.tsx
  provides:
    - mapper/src/app/page/components/CodeWindow.tsx
  affects:
    - mapper/src/app/page/components/AgentNavbar.tsx
    - mapper/src/app/page/components/YourMainContent.tsx
tech_stack:
  added: []
  patterns:
    - SharedPageContainer wrapper (same as StateWindow)
    - StatusPlaceholder for empty state
    - useThoughts() hook for data access
    - Version pill selector for snapshot browsing
key_files:
  created:
    - mapper/src/app/page/components/CodeWindow.tsx
  modified:
    - mapper/src/app/page/components/AgentNavbar.tsx
    - mapper/src/app/page/components/YourMainContent.tsx
decisions:
  - "User renamed 'code' tab to 'TTL' and added separate 'Python' tab — accepted as intentional UX improvement"
  - "CodeWindow accepts type prop ('python' | 'ttl') to serve both tabs from one component"
  - "Python tab reads data.python_code_snapshots; TTL tab reads data.ttl_code_snapshots"
metrics:
  duration: "continuation after checkpoint approval"
  completed_date: "2026-03-21"
  tasks_completed: 3
  tasks_total: 3
requirements:
  - P9-07
  - P9-08
---

# Phase 09 Plan 04: Code/TTL Tab Frontend Component Summary

TTL and Python code viewer tabs added to the agent UI, with a shared CodeWindow component that renders version pill selectors and scrollable code output for ontology snapshots.

## Objective

Add code snapshot viewer tabs to the frontend so the human can inspect all iterations of generated Python and TTL ontology code, from Initial through Fix N to Final.

## What Was Built

### Task 1: CodeWindow.tsx component (commit: 0c78b97)

Created `mapper/src/app/page/components/CodeWindow.tsx` — a reusable code viewer component that:

- Accepts a `type` prop (`'python' | 'ttl'`) to serve both the Python and TTL tabs
- Reads snapshot arrays from ThoughtsContext (`data.python_code_snapshots` or `data.ttl_code_snapshots`)
- Renders a version pill selector row — one pill per snapshot, auto-advances to latest on new arrival
- Displays `validated` status snapshots with a green dot indicator on their pill
- Shows `StatusPlaceholder` when no snapshots exist yet
- Uses `SharedPageContainer` with `fullWidth` and `fullHeight` (same visual pattern as StateWindow)
- Renders code in plain `<pre><code>` with `font-mono` — no external syntax highlighting library

### Task 2: Add tabs to AgentNavbar.tsx and YourMainContent.tsx (commit: 509d60b)

Updated the tab union type in four locations across two files, added `Code2` icon import, added the new tab entry to `navItems`, and wired `case 'code'` in `renderContent()` to render `<CodeWindow />`.

### Task 3: Visual verification checkpoint (approved by user)

Human verified the tab appears in the navbar, renders the empty state placeholder correctly, and visual style matches existing tabs.

## Deviations from Plan

### User deviation: 'Code' tab split into 'Python' and 'TTL' tabs

**Found during:** Task 3 (post-checkpoint, user-applied before approval)

**What happened:** The user renamed the single `code` tab to `ttl` (label: "TTL") and added a separate `python` tab alongside it. They also updated `CodeWindow.tsx` to accept a `type` prop so one component serves both tabs.

**Why accepted:** The original plan assumed one unified "Code" tab for ontology code snapshots. The user's split reflects the actual agent data shape — Python source code (`python_code_snapshots`) and TTL serialized output (`ttl_code_snapshots`) are distinct artifacts that merit separate views. This is a correct UX improvement, not a regression.

**Files modified by user (post-plan, uncommitted):**
- `mapper/src/app/page/components/AgentNavbar.tsx` — tab id changed from `code` to `ttl`/`python`, union types updated
- `mapper/src/app/page/components/CodeWindow.tsx` — added `CodeWindowProps` with `type` prop, dual-data-key logic
- `mapper/src/app/page/components/YourMainContent.tsx` — `case 'ttl'` and `case 'python'` replace `case 'code'`

**Action:** Accepted as intentional. Do not revert. These changes are correct and working (user confirmed visual verification).

**Note:** These user-applied changes were uncommitted at SUMMARY creation time. The user should commit them manually:
```bash
git add mapper/src/app/page/components/AgentNavbar.tsx \
        mapper/src/app/page/components/CodeWindow.tsx \
        mapper/src/app/page/components/YourMainContent.tsx
git commit -m "feat(09-04): user deviation — split code tab into TTL and Python, CodeWindow type prop"
```

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create CodeWindow.tsx component | 0c78b97 | mapper/src/app/page/components/CodeWindow.tsx |
| 2 | Add 'code' tab to AgentNavbar and YourMainContent | 509d60b | AgentNavbar.tsx, YourMainContent.tsx |
| 3 | Visual verification checkpoint | approved | — (no code changes) |

## Success Criteria Verification

- [x] Code tab visible in navbar with Code2 icon — TTL and Python tabs both present
- [x] Clicking tab shows CodeWindow with placeholder text — confirmed by user
- [x] Visual style matches existing tabs (SharedPageContainer wrapper) — confirmed by user
- [x] TypeScript compiles without errors — confirmed in task commits
- [x] No new npm dependencies added — Code2/Database from existing lucide-react

## Self-Check: PASSED

- `mapper/src/app/page/components/CodeWindow.tsx` — exists (created in commit 0c78b97, extended by user)
- `mapper/src/app/page/components/AgentNavbar.tsx` — exists (modified in 509d60b, further by user)
- `mapper/src/app/page/components/YourMainContent.tsx` — exists (modified in 509d60b, further by user)
- Commits 0c78b97 and 509d60b verified in git log
