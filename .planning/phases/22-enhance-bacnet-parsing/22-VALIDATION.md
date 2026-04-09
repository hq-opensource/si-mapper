---
phase: 22
slug: enhance-bacnet-parsing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | agent/pytest.ini (or none — runs from agent/) |
| **Quick run command** | `cd agent && .venv/bin/python -m pytest tests/test_bacnet_helpers.py -q` |
| **Full suite command** | `cd agent && .venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent && .venv/bin/python -m pytest tests/test_bacnet_helpers.py -q`
- **After every plan wave:** Run `cd agent && .venv/bin/python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | enrich bacnet_helpers | unit | `cd agent && .venv/bin/python -m pytest tests/test_bacnet_helpers.py -q` | ✅ | ⬜ pending |
| 22-01-02 | 01 | 1 | enrich internal_grid_tools | unit | `cd agent && .venv/bin/python -m pytest tests/test_bacnet_helpers.py -q` | ✅ | ⬜ pending |
| 22-01-03 | 01 | 2 | enrich metadata_tools + MCP | unit | `cd agent && .venv/bin/python -m pytest tests/ -q` | ✅ | ⬜ pending |
| 22-02-01 | 02 | 1 | update ontology skills | manual | Review SKILL.md files for correct field references | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — `tests/test_bacnet_helpers.py` already exists with 6 passing tests. New enrichment tests extend that file.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SKILL.md prose accuracy | skill-ontology-* updates | Natural language — not automatable | Read updated SKILL.md files; verify `address` is described as URI, `ref_type` options listed, `apply_bacnet()` pattern removed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
