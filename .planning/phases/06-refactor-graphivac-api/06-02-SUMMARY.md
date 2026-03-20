---
phase: 06-refactor-graphivac-api
plan: 02
subsystem: sync
tags: [mcp, streamablehttp, asyncio, httpx, polling, internal-grid, graphivac]

# Dependency graph
requires:
  - phase: 06-01
    provides: internal_grid_tools.py with LINE_TYPES/COORD_TYPES/ROTATION_TYPES constants and component schema
  - phase: mcp_server
    provides: MCP server at port 8080 with create_*/delete_* tools for all component types

provides:
  - Standalone sync service (sync_service/) that bridges agent internal state and Graphivac rendering
  - McpSyncClient — maps any component type to correct MCP create/delete tool call
  - SyncEngine — diffs internal_grid by component name, persists crash-recovery state
  - main.py — polling loop that reads agent /session_state every 2 seconds

affects:
  - 06-03 (agent prompt updates will reference sync service as the Graphivac bridge)

# Tech tracking
tech-stack:
  added:
    - httpx (async HTTP client for polling agent state endpoint)
  patterns:
    - Each MCP call opens its own streamablehttp_client session (matches test_create_50_fans.py pattern, MCP server handles concurrency)
    - Diff by component name (names are unique, enforced by internal_grid_tools)
    - Deletes before creates to avoid name collisions during replacement
    - Persist last-synced state to JSON for crash recovery

key-files:
  created:
    - sync_service/__init__.py
    - sync_service/mcp_client.py
    - sync_service/sync_engine.py
    - sync_service/main.py

key-decisions:
  - "Diff keyed by component name (not id) — names are unique and stable identifiers in the internal grid"
  - "Process deletes before creates to avoid name collisions when replacing a component"
  - "Each MCP call opens its own streamablehttp_client session — mirrors ADK parallel tool call pattern"
  - "Poll interval default 2s, configurable via SYNC_POLL_INTERVAL env var"
  - "No modifications to MCP server or existing agent code — purely additive standalone service"

patterns-established:
  - "McpSyncClient pattern: open session -> call_tool -> close (one session per MCP call)"
  - "SyncEngine pattern: diff() pure function + sync() async orchestrator + persist_state() for crash recovery"

requirements-completed: [REFAC-03, REFAC-04]

# Metrics
duration: 10min
completed: 2026-03-18
---

# Phase 06 Plan 02: Sync Service Summary

**Standalone async polling service using streamablehttp_client that diffs ToolContext internal_grid state against last-synced state and calls MCP create/delete tools for each change, with crash recovery via JSON persistence**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-18T21:42:53Z
- **Completed:** 2026-03-18T21:53:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- McpSyncClient correctly maps all 25 component types (line types, rotation types, coord types) to the right MCP tool name and parameter shape
- SyncEngine diffs internal_grid by component name, produces create/delete lists, calls MCP for each change, persists state for crash recovery
- Sync service main entry point polls agent /session_state every 2 seconds, handles agent unavailability gracefully, runnable as `python -m sync_service.main`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MCP sync client and sync engine** - `6be9deb` (feat)
2. **Task 2: Create sync service entry point with polling loop** - `38cfb51` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `sync_service/__init__.py` - Empty package marker
- `sync_service/mcp_client.py` - McpSyncClient that maps component types to MCP create/delete tool calls using streamablehttp_client
- `sync_service/sync_engine.py` - SyncEngine that diffs internal_grid state by component name, calls MCP for changes, persists last-synced state to .last_synced_state.json
- `sync_service/main.py` - Polling loop entry point (2s interval, reads agent /session_state, feeds to SyncEngine)

## Decisions Made
- Diff keyed by component name (not id): names are unique and stable, id is only internal
- Deletes processed before creates: avoids name collisions when a component is replaced (same name, different coords)
- One streamablehttp_client session per MCP call: mirrors ADK parallel tool call pattern, MCP server handles concurrency
- Purely additive: zero modifications to MCP server or agent code

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Sync service uses existing agent (port 8001) and MCP server (port 8080) endpoints.

## Next Phase Readiness
- Sync service is ready: `python -m sync_service.main` once agent and MCP server are running
- 06-03 (agent prompt updates) can proceed — sync service is the bridge that makes internal_grid changes visible in Graphivac

---
*Phase: 06-refactor-graphivac-api*
*Completed: 2026-03-18*
