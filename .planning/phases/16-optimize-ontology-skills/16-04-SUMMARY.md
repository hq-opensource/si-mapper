---
phase: 16-optimize-ontology-skills
plan: "04"
subsystem: tests
tags: [tests, ontology, wave-4, refactor]
dependency_graph:
  requires: [16-01, 16-02]
  provides: [test-coverage-wave-1-2]
  affects: [agent/tests/test_ontology_tools.py]
tech_stack:
  added: []
  patterns: [pytest, unittest.mock.patch, inspect.signature]
key_files:
  created: []
  modified:
    - agent/tests/test_ontology_tools.py
decisions:
  - "Rename tests to reflect two-write pattern instead of three-write (no _persist_python/_persist_ttl mocks)"
  - "New test_write_ontology_auto_increments_iteration_count verifies counter increments twice across two write_ontology calls"
  - "exit_validator_success TTL test patches _TTL_LATEST Path constant directly for isolation"
  - "venv order test reads source via open() and checks string positions to avoid subprocess overhead"
metrics:
  duration_seconds: 149
  completed_date: "2026-04-03"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
---

# Phase 16 Plan 04: Update Test Suite for Wave 1+2 Changes Summary

Updated `test_ontology_tools.py` to remove all mocks of deleted helpers (`_persist_python`, `_persist_ttl`) and add 6 new tests covering auto-increment counter, clean exit signatures, disk-based TTL read, Linux venv priority, scan cap, and force bypass.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update existing tests and add new tests for all changed behavior | b578b6c | agent/tests/test_ontology_tools.py |

## What Was Built

Rewrote the test file to match the post-Wave 1+2 implementation:

**Fixed tests (removed deleted function mocks):**
- `test_write_ontology_two_write_pattern` — removed `_persist_python` mock and "3. Uploads write called" assertion
- `test_write_ontology_auto_detects_session_id` — removed `_persist_python` mock
- `test_write_ontology_zero_pads_iteration_filename` — removed `_persist_python` mock
- `test_execute_ontology_two_write_ttl` — removed `_persist_ttl` mock and assertion; now verifies archive only
- `test_execute_ontology_auto_detects_session_from_python_iterations` — removed `_persist_ttl` mock

**New tests added:**
- `test_scan_python_folder_caps_at_10_files` — verifies message-only response when > 10 matches
- `test_scan_python_folder_force_bypasses_cap` — verifies all 12 files returned when force=True
- `test_write_ontology_auto_increments_iteration_count` — verifies counter goes 0 → 1 → 2 across two calls
- `test_execute_ontology_checks_linux_venv_first` — reads source and checks string positions (bin/python before Scripts/python.exe)
- `test_exit_generator_success_no_code_param` — verifies signal_sent + ONTOLOGY_GENERATION_SUCCESS + no code= param
- `test_exit_validator_success_reads_ttl_from_disk` — patches _TTL_LATEST, verifies TTL in snapshots, Final label, no ttl_content= param

**Imports updated:** Added `from tools.ontology_exit_tools import exit_generator_success, exit_validator_success`

## Deviations from Plan

None — plan executed exactly as written. All docstring references to `_persist_ttl` were also removed from comments to satisfy grep-0 criterion cleanly.

## Self-Check

- [x] `agent/tests/test_ontology_tools.py` modified
- [x] Commit b578b6c exists
- [x] 31 tests pass (0 failures)
- [x] `grep -c "checkpoint_code"` = 0
- [x] `grep -c "_persist_python\|_persist_ttl"` = 0
- [x] All 6 new test functions present in file

## Self-Check: PASSED
