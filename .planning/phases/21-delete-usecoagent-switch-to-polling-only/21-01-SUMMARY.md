---
phase: 21-delete-usecoagent-switch-to-polling-only
plan: "01"
subsystem: frontend
tags: [react, copilotkit, polling, render-loop-fix, typescript]
dependency_graph:
  requires: []
  provides: [simplified-page-tsx, polling-only-state]
  affects: [mapper/src/app/page.tsx]
tech_stack:
  added: []
  patterns: [pooledState-as-sole-source-of-truth, stable-module-level-default-constant]
key_files:
  created: []
  modified:
    - mapper/src/app/page.tsx
decisions:
  - "useCoAgent removed entirely — agentState was always empty at runtime (data flows via ADK callbacks not CopilotKit streaming); pooledState is now the sole source of truth"
  - "DEFAULT_AGENT_STATE is a module-level constant (not created inside component) to prevent reference churn causing re-renders"
  - "StateSyncer simplified to single-source: no array merging, no agentRest, no adkData — only reads from pooledState"
  - "AgentState type imported from AgentStateOverlay canonical definition (includes index signature [key: string]: unknown)"
metrics:
  duration_seconds: 176
  completed_date: "2026-04-03"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 21 Plan 01: Delete useCoAgent Switch to Polling Only Summary

**One-liner:** Removed useCoAgent from page.tsx, replaced combinedState merge with `pooledState ?? DEFAULT_AGENT_STATE`, and simplified StateSyncer to sync from pooledState only — eliminating "Maximum update depth exceeded" render loop.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Remove useCoAgent and simplify combinedState | a1962cc | mapper/src/app/page.tsx |
| 2 | Simplify StateSyncer to single-source sync | efedc8b | mapper/src/app/page.tsx |

## What Was Built

**Root cause fixed:** `useCoAgent` returned a new `agentState` object reference on every render. `StateSyncer`'s `useEffect` had `agentState` in its dependency array, so it fired on every render, calling `syncThoughts`/`syncData`/etc, which updated ThoughtsContext, which re-rendered `CopilotKitPage`, which triggered `useCoAgent` again — an infinite loop.

**Changes to mapper/src/app/page.tsx:**
- Removed `useCoAgent` from import and deleted the call site (lines 84-93)
- Added `DEFAULT_AGENT_STATE` module-level constant with stable reference (includes `data: {}` for downstream consumers)
- `combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE` (replaces 7-line merge block)
- Removed unused type imports (`Thought`, `ToolCall`, `AgentEvent`)
- Imported `AgentState` from canonical `AgentStateOverlay` component (has index signature)
- Rewrote `StateSyncer`: removed `agentState` prop, removed array merging, removed `agentRest`/`adkData` logic, added early `if (!pooledState) return` guard
- Updated `StateSyncer` JSX call site from `<StateSyncer pooledState={pooledState} agentState={agentState} />` to `<StateSyncer pooledState={pooledState} />`

## Verification Results

- `grep -c "useCoAgent" mapper/src/app/page.tsx` → 0
- `grep -c "agentState" mapper/src/app/page.tsx` (excluding JSX prop `agentState={combinedState}`) → 0
- `npx tsc --noEmit` → exits 0 (no errors)
- `npm run build` → Next.js build succeeds (Node 24)
- `useCopilotAction` remains present (not removed)
- `useAgentPolling` remains present (not removed)
- `DEFAULT_AGENT_STATE` has 2 matches (definition + combinedState fallback)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript error in StateSyncer data destructure**
- **Found during:** Task 1 TypeScript compile check
- **Issue:** `const { data } = pooledState || {}` caused TS2339 error — TypeScript inferred type `AgentState | {}` and `{}` does not have a `data` property
- **Fix:** Changed to `const data = pooledState?.data as Record<string, unknown> | undefined`
- **Files modified:** mapper/src/app/page.tsx
- **Commit:** a1962cc (included in Task 1 commit)

## Self-Check: PASSED

- `mapper/src/app/page.tsx` exists and contains expected patterns
- Commits a1962cc and efedc8b verified in git log
- TypeScript compiles clean
- Next.js build succeeds
