---
phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator
plan: "01"
subsystem: agent

tags: [edn-format, python, translator, internal-grid, graphivac, bidirectional]

requires:
  - phase: 06-internal-grid-state
    provides: "LINE_TYPES, ROTATION_TYPES, EQUIPMENT_TYPES, SENSOR_TYPES, COORD_TYPES constants in internal_grid_tools.py"

provides:
  - "agent/utils/edn_to_mutable.py — standalone recursive EDN-to-Python converter, no mcp_server imports"
  - "agent/utils/grid_edn_translator.py — bidirectional translator with 23-entry SYMBOL_TO_AGENT/AGENT_TO_SYMBOL maps"
  - "edn_comps_to_internal_grid(comps_map) — parse EDN comps dict to internal_grid"
  - "internal_grid_to_edn_comps(internal_grid) — rebuild EDN comps dict from internal_grid"
  - "tests/test_grid_edn_translator.py — 15 unit tests covering all 25 types, rotation bug fix, pipe/duct distinction"

affects:
  - 07-02-rewrite-sync-callbacks

tech-stack:
  added: []
  patterns:
    - "EDN key tuple pattern: (Keyword(type), name_str) for line types, (Keyword('obj'), name_str) for equipment/sensors"
    - "Rotation uses Keyword('rot') — NOT Keyword('rotation') — confirmed as bug fix"
    - "Test stub pattern: sys.modules stubs for google.adk, utils.logging_config, tools.internal_grid_tools before translator import"
    - "Unknown EDN symbols: silently dropped with logger.warning, never raise"

key-files:
  created:
    - agent/utils/edn_to_mutable.py
    - agent/utils/grid_edn_translator.py
    - tests/test_grid_edn_translator.py
  modified: []

key-decisions:
  - "Rotation uses Keyword('rot') not Keyword('rotation') — this was a pre-existing bug in grid_sync_graphivac_to_agent.py that the new translator explicitly fixes"
  - "Pipe line types use Keyword('pipe') as EDN key, distinct from Keyword('duct') — not conflated"
  - "edn_to_mutable.py is a standalone local copy — no imports from mcp_server package"
  - "Unknown EDN symbols are silently dropped with a logged warning — acceptable for current scope"
  - "SYMBOL_TO_AGENT has exactly 23 entries covering all equipment (15) and sensor (8) types; AGENT_TO_SYMBOL is its inverse"

patterns-established:
  - "Translator test pattern: stub tools.internal_grid_tools with real constant values before importing from agent.utils"
  - "Roundtrip test pattern: EDN -> internal_grid -> EDN and assert structural equality"

requirements-completed: []

duration: 4min
completed: 2026-03-19
---

# Phase 07 Plan 01: Bidirectional EDN-JSON Translator Summary

**23-entry bidirectional symbol mapping for all 25 HVAC component types with rotation bug fix (Keyword('rot') not Keyword('rotation')) and pipe/duct key distinction**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-19T13:43:06Z
- **Completed:** 2026-03-19T13:47:15Z
- **Tasks:** 2
- **Files modified:** 3 created

## Accomplishments

- Created `agent/utils/edn_to_mutable.py` — standalone recursive EDN mutable converter, no cross-package imports
- Created `agent/utils/grid_edn_translator.py` with 23-entry `SYMBOL_TO_AGENT`/`AGENT_TO_SYMBOL` maps and two public functions
- Fixed the `:rot` vs `:rotation` bug: new translator reads/writes `Keyword("rot")` correctly
- Verified pipe lines use `Keyword("pipe")` key (not `Keyword("duct")`) in both parse and rebuild directions
- 15 unit tests all passing including full roundtrip for all 25 component types

## Task Commits

Each task was committed atomically:

1. **Task 1: Create edn_to_mutable and translator module** - `ac4e9de` (feat)
2. **Task 2: Unit tests for translator** - `67d421e` (test)

## Files Created/Modified

- `agent/utils/edn_to_mutable.py` — standalone copy of EDN recursive converter, imports stdlib only
- `agent/utils/grid_edn_translator.py` — bidirectional translator: SYMBOL_TO_AGENT, AGENT_TO_SYMBOL, edn_comps_to_internal_grid, internal_grid_to_edn_comps
- `tests/test_grid_edn_translator.py` — 15 pytest tests covering all 25 types, rotation bug, pipe/duct distinction, unknown symbols

## Decisions Made

- `edn_to_mutable.py` is a local copy — importing from `mcp_server` package inside the agent would create a cross-package dependency
- The rotation bug fix (`Keyword("rot")` not `Keyword("rotation")`) is captured both in code and in a dedicated test `test_rotation_bug_fix`
- Test stubs for `tools.internal_grid_tools` use hardcoded set literals (same values as real module) to avoid importing ADK

## Deviations from Plan

None — plan executed exactly as written. The verification command in the plan omitted the required `tools.internal_grid_tools` stub, but the test file handles this correctly using the same stub pattern as existing tests.

## Issues Encountered

The plan's verification command (`python -c "from agent.utils.grid_edn_translator import ..."`) omitted the `tools.internal_grid_tools` stub that is required when importing from project root (since `tools` is an internal agent package path). Test file correctly handles this with sys.modules stubs. All 15 tests pass with the agent venv.

## Next Phase Readiness

- Translator module is complete and fully tested — ready for 07-02 callback rewrites
- `edn_comps_to_internal_grid` replaces the manual parse loop in `grid_sync_graphivac_to_agent.py`
- `internal_grid_to_edn_comps` is the core of the new `grid_sync_agent_to_graphivac.py` (REST PUT)

---
*Phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator*
*Completed: 2026-03-19*
