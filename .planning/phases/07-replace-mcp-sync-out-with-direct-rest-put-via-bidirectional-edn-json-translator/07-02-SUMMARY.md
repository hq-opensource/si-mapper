---
phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator
plan: "02"
subsystem: agent
tags: [edn, rest, sync, callback, graphivac, requests, adk]

requires:
  - phase: 07-01
    provides: grid_edn_translator.py with edn_comps_to_internal_grid and internal_grid_to_edn_comps

provides:
  - Updated before_agent_callback that saves _raw_edn_grid and uses translator for sync-in
  - Rewritten after_agent_callback that does full comps rebuild and single REST PUT
  - Eliminated MCP from sync lifecycle — N per-component MCP calls replaced with 1 REST PUT per turn

affects:
  - level_3_master_main_llm.py (uses both callbacks — no changes needed, just new behavior)
  - agent/utils/grid_sync_graphivac_to_agent.py
  - agent/utils/grid_sync_agent_to_graphivac.py

tech-stack:
  added: []
  patterns:
    - "before_callback fetches raw EDN, converts to mutable, saves _raw_edn_grid and internal_grid"
    - "after_callback rebuilds comps via translator, replaces comps key in raw_edn_grid, single REST PUT"
    - "Retry-once pattern for PUT failure with types.Content error injection on unrecoverable failure"
    - "asyncio.to_thread() for blocking HTTP calls in async callbacks"

key-files:
  created: []
  modified:
    - agent/utils/grid_sync_graphivac_to_agent.py
    - agent/utils/grid_sync_agent_to_graphivac.py

key-decisions:
  - "No diff, no snapshot: after_callback does full comps rebuild from internal_grid every turn"
  - "Only the comps key in _raw_edn_grid is replaced — title, font configs, and other metadata are preserved from the before_callback fetch"
  - "Retry once on PUT failure; inject types.Content error message to agent on unrecoverable failure"
  - "Return None on success, types.Content with SYNC ERROR message on failure"

patterns-established:
  - "Sync-in: fetch EDN -> edn_to_mutable -> save _raw_edn_grid -> extract comps -> edn_comps_to_internal_grid -> save internal_grid"
  - "Sync-out: get _raw_edn_grid -> internal_grid_to_edn_comps -> replace comps key -> edn_format.dumps -> requests.put"

requirements-completed: []

duration: 8min
completed: 2026-03-19
---

# Phase 07 Plan 02: Sync Callbacks Rewrite Summary

**Sync callbacks rewritten to use EDN translator: before_callback saves raw EDN grid, after_callback does full comps rebuild and single REST PUT — MCP eliminated from sync lifecycle.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-19T13:50:00Z
- **Completed:** 2026-03-19T13:58:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Rewrote `before_agent_callback` to use the translator for EDN parsing, save `_raw_edn_grid`, and remove `_initial_grid_snapshot`
- Fully replaced `after_agent_callback`: dropped all MCP code, replaced with `internal_grid_to_edn_comps()` + single `requests.put()` call
- Added retry-once logic and `types.Content` error injection on unrecoverable PUT failure

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite before_agent_callback** - `d41459f` (feat)
2. **Task 2: Rewrite after_agent_callback** - `ee67459` (feat)

**Plan metadata:** *(this commit)*

## Files Created/Modified

- `agent/utils/grid_sync_graphivac_to_agent.py` - Before callback: uses translator, saves _raw_edn_grid, removes snapshot
- `agent/utils/grid_sync_agent_to_graphivac.py` - After callback: full rewrite, single REST PUT, no MCP

## Decisions Made

- No diff, no snapshot: the after_callback does a full comps rebuild from `internal_grid` every turn — whatever is in `internal_grid` at turn end is the truth
- Only the `comps` key is replaced in `_raw_edn_grid` — title, font configs, and other metadata are preserved from the before_callback fetch
- Retry once on PUT failure; inject `types.Content` error message to agent on unrecoverable failure so it stops grid operations rather than silently diverging

## Deviations from Plan

None - plan executed exactly as written.

Note: The plan's `<verify>` script for Task 1 contained a minor error (it checked for `_raw_edn_grid` inside `_fetch_and_parse_grid`'s source, but that string only appears in the callback). All acceptance criteria and overall verification checks passed.

## Issues Encountered

None - straightforward rewrite, translator API was exactly as documented in 07-01 output.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Both sync callbacks are now MCP-free and use the translator
- The sync lifecycle is: fetch EDN -> save raw + translate to internal_grid -> agent turn -> translate back -> single REST PUT
- Integration test (standalone script to verify against live GraphyVAC) was noted as deferred to the verification checkpoint in plan 07-03

---
*Phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator*
*Completed: 2026-03-19*
