---
phase: 20
slug: agent-session-logging
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `agent/pyproject.toml` (`[tool.pytest.ini_options]`, `asyncio_mode = "auto"`) |
| **Quick run command** | `cd agent && python -m pytest tests/test_session_logger.py -x` |
| **Full suite command** | `cd agent && python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent && python -m pytest tests/test_session_logger.py -x`
- **After every plan wave:** Run `cd agent && python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 0 | P20-01..P20-05 | unit stub | `cd agent && python -m pytest tests/test_session_logger.py -x` | ❌ W0 | ⬜ pending |
| 20-01-02 | 01 | 1 | P20-01 | unit | `cd agent && python -m pytest tests/test_session_logger.py::test_creates_log_dir_on_first_write -x` | ✅ W0 | ⬜ pending |
| 20-01-03 | 01 | 1 | P20-02 | unit | `cd agent && python -m pytest tests/test_session_logger.py::test_each_event_is_one_json_line -x` | ✅ W0 | ⬜ pending |
| 20-01-04 | 01 | 1 | P20-03 | unit | `cd agent && python -m pytest tests/test_session_logger.py::test_log_filename_format -x` | ✅ W0 | ⬜ pending |
| 20-01-05 | 01 | 1 | P20-04 | unit | `cd agent && python -m pytest tests/test_session_logger.py::test_agent_event_fields_complete -x` | ✅ W0 | ⬜ pending |
| 20-01-06 | 01 | 1 | P20-05 | unit | `cd agent && python -m pytest tests/test_session_logger.py::test_append_does_not_truncate -x` | ✅ W0 | ⬜ pending |
| 20-01-07 | 01 | 2 | P20-01..P20-05 | integration | `cd agent && python -m pytest tests/ -x` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_session_logger.py` — 5 unit test stubs covering P20-01 through P20-05
- [ ] `agent/utils/session_logger.py` — module skeleton (must exist before tests can import)

*Wave 0 must complete before Wave 1 tasks begin.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Log file readable by LLM tools after a real agent run | P20-01..05 | Requires live agent execution | Start agent, send a task, check `agent/logs/sessions/` for a `.jsonl` file with valid JSON lines |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
