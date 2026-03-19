---
phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator
plan: 03
subsystem: testing
tags: [edn, graphivac, rest, integration-test, translator]

# Dependency graph
requires:
  - phase: 07-02
    provides: "Rewritten sync callbacks using translator + single REST PUT"
  - phase: 07-01
    provides: "Bidirectional EDN-JSON translator (grid_edn_translator.py)"
provides:
  - Standalone integration test script that exercises the full translator + REST pipeline against a real GraphyVAC grid
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Integration test as standalone runnable script (not pytest) for human visual verification"
    - "Env var pattern: GRAPHIVAC_BASE_URL, GRAPHIVAC_ORG_ID, GRAPHIVAC_PROJECT_ID, GRAPHIVAC_GRID_ID"

key-files:
  created:
    - tests/test_integration_grid_sync.py
  modified: []

key-decisions:
  - "Integration test is standalone (not pytest) so human can run it manually and verify in GraphyVAC UI"

patterns-established:
  - "Integration test pattern: GET -> parse -> modify -> translate -> PUT -> print VERIFICATION INSTRUCTIONS"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-03-19
---

# Phase 7 Plan 03: Integration Test Script Summary

**Standalone integration test script that reads a live GraphyVAC grid, adds 4 test components (duct, pipe, fan with rotation, temp sensor), PUTs back via REST, and prints human verification instructions**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-19T13:55:33Z
- **Completed:** 2026-03-19T14:00:00Z
- **Tasks:** 1 of 2 (paused at human-verify checkpoint)
- **Files modified:** 1

## Accomplishments
- Created `tests/test_integration_grid_sync.py` — standalone runnable script (not pytest)
- Script exercises the full GET -> translate -> modify -> translate back -> PUT flow
- All 12 acceptance criteria pass (syntax, imports, env var checks, test components, VERIFICATION INSTRUCTIONS, no MCP references)
- Paused at Task 2 (checkpoint:human-verify) — awaiting human to run test against real GraphyVAC

## Task Commits

Each task was committed atomically:

1. **Task 1: Create standalone integration test script** - `e0596f1` (feat)

## Files Created/Modified
- `tests/test_integration_grid_sync.py` — Standalone integration test: GET grid, add 4 test components, PUT back, print verification instructions

## Decisions Made
None - followed plan as specified.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
Human verification required. See checkpoint details:

1. Ensure GraphyVAC is running and set env vars:
   - `GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID`, `GRAPHIVAC_GRID_ID`

2. Run the integration test:
   ```
   cd /home/juan/codes/si-mapper
   GRAPHIVAC_BASE_URL=<url> GRAPHIVAC_ORG_ID=<org> GRAPHIVAC_PROJECT_ID=<proj> GRAPHIVAC_GRID_ID=<grid> python3 tests/test_integration_grid_sync.py
   ```

3. Verify in the GraphyVAC UI:
   - TEST-DUCT-1 appears as a duct line from [0,15] to [10,15]
   - TEST-PIPE-1 appears as a pipe line from [-3,17] to [1,17]
   - TEST-FAN-1 appears as a fan at [5,15] with 90-degree rotation
   - TEST-SENSOR-1 appears as a temperature sensor at [8,15]
   - Existing grid components are still present (not wiped)
   - Pipe and duct are visually distinct types

4. Clean up the test components from the UI after verification.

## Next Phase Readiness
- Phase 7 implementation complete pending human verification
- After human approval, the full EDN-JSON translator + REST sync pipeline is proven end-to-end

---
*Phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator*
*Completed: 2026-03-19*
