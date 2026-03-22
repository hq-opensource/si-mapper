---
phase: 11-optimization-of-the-coding-agent
plan: "01"
subsystem: testing
tags: [python, pytest, tool-function, keyword-filtering, context-window]

# Dependency graph
requires:
  - phase: 09-integrate-223p-agent
    provides: tool.py with scan_python_files and __all__ exports
provides:
  - scan_python_files_filtered function with TDD coverage (7 tests)
  - SCAN_PYTHON_FILES_FILTERED_SCHEMA OpenAI-compatible schema
affects: [11-02, 11-03, 11-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD with pytest tmp_path fixture for file-system tools]

key-files:
  created:
    - agent/tests/test_223p_tools.py
  modified:
    - agent/sub_agents/_223p/tool.py

key-decisions:
  - "scan_python_files_filtered uses case-insensitive substring matching (any kw in content.lower()) — OR logic across keywords"
  - "Files with read errors are skipped from filtered results (not included with error placeholder)"

patterns-established:
  - "TDD for tool functions: write 7 covering tests first (tmp_path fixture), then implement"
  - "Filtered scan inserts lower_keywords list once before walk loop for O(n*k) rather than per-character overhead"

requirements-completed: [P11-01]

# Metrics
duration: 2min
completed: 2026-03-22
---

# Phase 11 Plan 01: scan_python_files_filtered Summary

**Keyword-filtered Python file scanner that reduces coding-agent context window consumption by returning only .py files whose content matches agent-supplied keywords (case-insensitive OR match).**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-22T18:19:16Z
- **Completed:** 2026-03-22T18:20:50Z
- **Tasks:** 1 (TDD)
- **Files modified:** 2

## Accomplishments
- Wrote 7 failing tests (RED) covering keyword filtering, case-insensitivity, no-match edge case, path errors, multiple keywords, and JSON shape
- Implemented `scan_python_files_filtered(path, keywords)` with identical error handling to `scan_python_files`
- Added `SCAN_PYTHON_FILES_FILTERED_SCHEMA` with full OpenAI-compatible schema including `keywords` array parameter
- Exported both names in `__all__` under Library introspection section

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for scan_python_files_filtered** - `4aecb54` (test)
2. **Task 1 GREEN: Implementation with schema and __all__ export** - `ee26d7a` (feat)

**Plan metadata:** (docs commit — see below)

_Note: TDD tasks have multiple commits (test → feat)_

## Files Created/Modified
- `agent/tests/test_223p_tools.py` - 7 unit tests for scan_python_files_filtered using pytest tmp_path fixtures
- `agent/sub_agents/_223p/tool.py` - Added function, schema, and __all__ entries (85 lines added)

## Decisions Made
- Filter logic: `any(kw in content_lower for kw in lower_keywords)` — OR semantics, case-insensitive, pre-lowercased keyword list
- Files with OSError during read are skipped in filtered results (unlike scan_python_files which includes error placeholder) — simpler and avoids returning noise

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Pre-existing test failure in `test_capture_frontend_state.py::test_url_construction` (from phase 08-02) — hardcoded test-org/test-project URL no longer matches real env values. Logged to deferred-items.md, not fixed (out of scope for this plan).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `scan_python_files_filtered` available in tool.py for plans 11-02, 11-03, 11-04 to register in agent
- Pre-existing test failure in test_capture_frontend_state.py should be addressed before this phase is considered fully clean

---
*Phase: 11-optimization-of-the-coding-agent*
*Completed: 2026-03-22*
