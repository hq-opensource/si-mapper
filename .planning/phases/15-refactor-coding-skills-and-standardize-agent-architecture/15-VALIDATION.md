---
phase: 15
slug: refactor-coding-skills-and-standardize-agent-architecture
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-02
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `agent/tests/` (existing) |
| **Quick run command** | `cd agent && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd agent && python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd agent && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | sub_agents deletion | unit | `cd agent && python -m pytest tests/test_create_master_agent.py -v` | yes | pending |
| 15-02-01 | 02 | 1 | 223p migration | filesystem | `test -f agent/223p/LESSONS.md && echo PASS` | n/a | pending |
| 15-02-02 | 02 | 1 | three-write + extract_lessons tests (Wave 0) | unit | `cd agent && python -c "import ast; ast.parse(open('tests/test_ontology_tools.py').read())"` | **creates** test_ontology_tools.py | pending |
| 15-02-03 | 02 | 1 | path constants + three-write + extract_lessons impl | unit | `cd agent && python -m pytest tests/test_ontology_tools.py tests/test_create_master_agent.py -v` | yes (from 15-02-02) | pending |
| 15-03-01 | 03 | 2 | skill refactor | unit | `cd agent && python -m pytest tests/ -v` | yes | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] `agent/tests/test_ontology_tools.py` — created in Plan 15-02 Task 2 (Wave 0) BEFORE implementation in Task 3
- [ ] Update `agent/tests/test_create_master_agent.py` — remove stale sub_agents import assertions (Plan 15-01 Task 1)

*Existing infrastructure covers test runner and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `read_prompt` returns correct content after path update | Workstream 3 | Requires running agent session | Call `read_prompt` tool in a live session and verify content matches `agent/223p/ref/code/prompt.md` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
