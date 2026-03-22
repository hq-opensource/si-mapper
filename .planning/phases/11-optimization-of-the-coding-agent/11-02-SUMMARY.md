---
phase: 11-optimization-of-the-coding-agent
plan: "02"
subsystem: agent
tags: [python, jsonl, tdd, pytest, tool, search, mapping, ashrae223p]

# Dependency graph
requires:
  - phase: 11-01
    provides: scan_python_files_filtered and test infrastructure in test_223p_tools.py
provides:
  - search_class_mapping function in tool.py with JSONL grep-like lookup across bob and scratch libraries
  - SEARCH_CLASS_MAPPING_SCHEMA for LiteLLM tool registration
  - _load_mapping helper with module-level caching (_mapping_cache)
  - _MAPPINGS_DIR constant using _PROJECT_ROOT anchor
  - 7 unit tests in TestSearchClassMapping covering matching, case-insensitivity, both libraries, all fields
affects: [11-03, 11-04, _223p agent tool usage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-level JSONL caching via _mapping_cache dict keyed by library name
    - _PROJECT_ROOT anchor for portable path construction to assets/mappings/

key-files:
  created: []
  modified:
    - agent/sub_agents/_223p/tool.py
    - agent/tests/test_223p_tools.py

key-decisions:
  - "search_class_mapping uses case-insensitive substring OR logic across all keywords — consistent with scan_python_files_filtered pattern from 11-01"
  - "_MAPPINGS_DIR uses _PROJECT_ROOT (not relative path) for portability regardless of working directory"
  - "Tests use real JSONL files (not mocks) since they are small static fixtures in the repo — simpler and tests actual data shape"
  - "_mapping_cache is module-level dict keyed by library name — lazy-load on first call, no re-reads thereafter"

patterns-established:
  - "JSONL caching pattern: _load_mapping(library) with module-level _mapping_cache mirrors _get_library_classes / _library_cache pattern"
  - "Tool returns json.dumps(list, ...) — callers json.loads to get list of dicts"

requirements-completed: [P11-02]

# Metrics
duration: 8min
completed: 2026-03-22
---

# Phase 11 Plan 02: search_class_mapping Summary

**Single-call JSONL grep replacing the expensive list_library_classes + get_class_details two-call workflow, covering both bob and scratch libraries with case-insensitive keyword matching and module-level caching**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-22T18:30:00Z
- **Completed:** 2026-03-22T18:38:00Z
- **Tasks:** 1 (TDD task with RED + GREEN phases)
- **Files modified:** 2

## Accomplishments

- Implemented `search_class_mapping(keywords: list[str]) -> str` with case-insensitive OR keyword matching across both classes_bob.jsonl and classes_scratch.jsonl
- Added `_load_mapping` helper with module-level `_mapping_cache` for lazy JSONL loading (no re-reads after first call)
- Added `_MAPPINGS_DIR` constant using `_PROJECT_ROOT` anchor for portable path construction
- Registered `SEARCH_CLASS_MAPPING_SCHEMA` and exported both symbols via `__all__`
- All 14 tests pass (7 new TestSearchClassMapping + 7 from plan 01 TestScanPythonFilesFiltered)

## Task Commits

1. **Task 1: TDD — search_class_mapping tests + implementation** - `e3dd848` (feat)

## Files Created/Modified

- `agent/sub_agents/_223p/tool.py` - Added _MAPPINGS_DIR, _JSONL_FILES, _mapping_cache constants; _load_mapping helper; search_class_mapping function; SEARCH_CLASS_MAPPING_SCHEMA; updated __all__
- `agent/tests/test_223p_tools.py` - Appended TestSearchClassMapping class with 7 tests using real JSONL files

## Decisions Made

- Tests use real JSONL files (not mocks) — they are small static fixtures, testing against real data is simpler and validates actual data shape
- Case-insensitive OR logic across keywords — consistent with scan_python_files_filtered from plan 11-01
- _mapping_cache is module-level to avoid re-parsing JSONL on every agent call

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing failure in `tests/test_capture_frontend_state.py::test_url_construction` (unrelated to this plan) was observed during full test suite run. Not caused by this task's changes and is out of scope.

## Next Phase Readiness

- `search_class_mapping` is ready for use by the _223p coding agent as a drop-in replacement for the two-call list_library_classes + get_class_details workflow
- No blockers for remaining phase 11 plans

## Self-Check: PASSED

All files verified on disk. Commit e3dd848 confirmed in git log.

---
*Phase: 11-optimization-of-the-coding-agent*
*Completed: 2026-03-22*
