# Deferred Items — Phase 11

## Out-of-Scope Issues Discovered During Execution

### 1. Pre-existing test failure: test_capture_frontend_state.py::test_url_construction

- **Discovered during:** Plan 11-01, Task 1 (full suite run)
- **File:** agent/tests/test_capture_frontend_state.py
- **Issue:** Test was written in phase 08-02 with hardcoded URL segments ("test-org/test-project/test-grid") but the actual capture tool now uses real environment values ("public/P-j8QIvTGH7p/G-LAiRS3mgp6") and `wait_until="load"` instead of `"networkidle"`.
- **Action required:** Update the test mock env vars or the assertion to match current implementation.
- **Not fixed:** Pre-existing failure, not caused by plan 11-01 changes.
