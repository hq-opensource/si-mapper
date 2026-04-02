---
phase: 15
slug: refactor-coding-skills-and-standardize-agent-architecture
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 15-01-01 | 01 | 1 | sub_agents deletion | unit | `cd agent && python -m pytest tests/test_create_master_agent.py -v` | ✅ | ⬜ pending |
| 15-01-02 | 01 | 1 | test file deletion | unit | `cd agent && python -m pytest tests/ -v` | ✅ | ⬜ pending |
| 15-02-01 | 02 | 2 | 223p migration | unit | `cd agent && python -m pytest tests/ -v` | ✅ | ⬜ pending |
| 15-03-01 | 03 | 3 | skill refactor | unit | `cd agent && python -m pytest tests/ -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_ontology_tools_extended.py` — new tests for three-write behavior in `write_ontology` / `execute_ontology`
- [ ] Update `agent/tests/test_create_master_agent.py` — remove stale sub_agents import assertions

*Existing infrastructure covers test runner and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `read_prompt` returns correct content after path update | Workstream 3 | Requires running agent session | Call `read_prompt` tool in a live session and verify content matches `agent/223p/ref/code/prompt.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
