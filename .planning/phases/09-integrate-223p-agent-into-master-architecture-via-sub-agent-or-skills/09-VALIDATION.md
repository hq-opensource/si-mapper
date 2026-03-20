---
phase: 9
slug: integrate-223p-agent-into-master-architecture-via-sub-agent-or-skills
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `agent/pyproject.toml` |
| **Quick run command** | `cd agent && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd agent && uv run pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd agent && uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | exit-tools | unit | `cd agent && uv run pytest tests/test_ontology_generator_exit_tools.py -x -q` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | exit-tools | unit | `cd agent && uv run pytest tests/test_ontology_validator_exit_tools.py -x -q` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | checkpoint-tool | unit | `cd agent && uv run pytest tests/test_checkpoint_code.py -x -q` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 1 | agent-wiring | unit | `cd agent && uv run pytest tests/test_ontology_generator_agent.py -x -q` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | agent-wiring | unit | `cd agent && uv run pytest tests/test_ontology_validator_agent.py -x -q` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 2 | master-wiring | manual | Verify master can delegate to OntologyGeneratorAgent by name | N/A | ⬜ pending |
| 09-04-01 | 04 | 3 | frontend-tab | manual | Code tab visible, shows snapshots, version selector works | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_ontology_generator_exit_tools.py` — stubs for exit_generator_success, exit_generator_failure
- [ ] `agent/tests/test_ontology_validator_exit_tools.py` — stubs for checkpoint_code, exit_validator_success, exit_validator_failure
- [ ] `agent/tests/test_checkpoint_code.py` — stubs for state list appending logic
- [ ] `agent/tests/test_ontology_generator_agent.py` — stubs for OntologyGeneratorAgent instantiation
- [ ] `agent/tests/test_ontology_validator_agent.py` — stubs for OntologyValidatorAgent instantiation

*Existing pytest infrastructure in agent/tests/ covers all phase test requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Master delegates to OntologyGeneratorAgent by name | sub-agent wiring | Requires live ADK session with master | Start agent, send "generate the 223P ontology", verify master calls OntologyGeneratorAgent |
| Validator loop checkpoints each fix iteration | checkpoint_code | Requires live validator run with ontology errors | Run validator on broken ontology.py, check ontology_code_snapshots in state grows per iteration |
| Code tab version selector renders all snapshots | frontend | Browser UI interaction | Open Code tab, verify pill row shows Initial/Fix N/Final labels, click each to switch view |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
