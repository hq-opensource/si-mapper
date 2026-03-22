---
phase: 11
slug: optimization-of-the-coding-agent
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.2 |
| **Config file** | `agent/pyproject.toml` |
| **Quick run command** | `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 0 | — | unit stub | `uv run pytest tests/test_223p_tools.py -x -q` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | — | unit | `uv run pytest tests/test_223p_tools.py -x -q` | ✅ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | — | unit | `uv run pytest tests/test_223p_tools.py tests/test_ontology_generator_agent.py tests/test_ontology_validator_agent.py -x -q` | ✅ W0 | ⬜ pending |
| 11-03-01 | 03 | 1 | — | manual | inspect SKILL.md + LESSONS.md | n/a | ⬜ pending |
| 11-04-01 | 04 | 2 | — | manual | confirm files deleted | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_223p_tools.py` — unit test stubs for `scan_python_files_filtered` (keyword filtering, case-insensitivity, empty result) and `search_class_mapping` (bob/scratch match, library field, no match)
- [ ] Extend `agent/tests/test_ontology_generator_agent.py` — add assertions: `scan_python_files_filtered` and `search_class_mapping` in `local_tools`; `list_library_classes` and `get_class_details` absent
- [ ] Extend `agent/tests/test_ontology_validator_agent.py` — same assertions

*Existing test infrastructure (pytest, uv, MockToolContext pattern) covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SKILL.md reads LESSONS.md when present, skips asset walk | — | Skill behavior is instructional text, not executable code | Read SKILL.md Section 3, confirm LESSONS.md-first logic is present |
| LESSONS.md skeleton file created with category headers | — | File creation, no runtime behavior to test | `ls agent/skills/skill-read-code/LESSONS.md` and inspect headers |
| full_bob.jsonl and full_scratch.jsonl deleted | — | File deletion | `ls agent/skills/skill-read-code/assets/mappings/` confirms only classes_*.jsonl remain |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
