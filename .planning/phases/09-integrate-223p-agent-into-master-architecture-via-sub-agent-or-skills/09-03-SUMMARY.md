---
phase: 09-integrate-223p-agent-into-master-architecture-via-sub-agent-or-skills
plan: "03"
subsystem: master-agent
tags: [ontology, master-agent, sub-agents, 223p, wiring]
dependency_graph:
  requires: ["09-02"]
  provides: ["master-agent-ontology-delegation"]
  affects: ["agent/master_architecture/create_master_agent.py", "agent/master_architecture/prompts/master_instruction.md"]
tech_stack:
  added: []
  patterns: ["AgentTool sub-agent delegation via LoopWrapper", "HITL gate before ontology generation"]
key_files:
  created: []
  modified:
    - agent/master_architecture/create_master_agent.py
    - agent/master_architecture/prompts/master_instruction.md
decisions:
  - "ASHRAE 223P Code Generation Protocol requires explicit human instruction — no auto-trigger"
  - "all_subagents merges externally-passed subagents with ontology sub-agents preserving existing interface"
metrics:
  duration: "~5 minutes"
  completed_date: "2026-03-21"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 09 Plan 03: Wire Ontology Sub-agents into Master Architecture Summary

**One-liner:** Wired OntologyGeneratorAgent and OntologyValidatorAgent into create_master_agent.py and added HITL-gated two-step 223P delegation protocol to master_instruction.md.

## What Was Built

Both ontology sub-agents (created in plan 09-02) are now registered as AgentTools in the master LLM agent, and the master instruction prompt has a new protocol section defining when and how to delegate to them.

### Task 1: Wire sub-agents into create_master_agent.py

- Added imports for `OntologyGeneratorAgent` and `OntologyValidatorAgent`
- Inside `create_master_agent()`, instantiated both with `model_name=model_name`
- Combined with any externally-passed subagents via `all_subagents = (subagents or []) + ontology_subagents`
- Passed `all_subagents` to `MasterLlmAgent` instead of the original `subagents` parameter
- Import verification passed: `uv run python -c "from master_architecture.create_master_agent import create_master_agent; print('import OK')"`

### Task 2: Add ASHRAE 223P Code Generation Protocol to master_instruction.md

- Appended `## ASHRAE 223P Code Generation Protocol` section at end of file
- Protocol is HITL-gated: requires explicit human request ("create the code", "generate the 223P ontology", etc.)
- Two-step delegation sequence: generator first, then validator (after checking `ONTOLOGY_GENERATION_SUCCESS` in state)
- Documents expected output files: `223p/src/ontology.py` and `223p/ttl/ontology.ttl`

## Verification

- `uv run pytest tests/ -q --ignore=tests/test_capture_frontend_state.py`: 30/30 tests pass
- `grep "ASHRAE 223P Code Generation Protocol" master_instruction.md`: 1 match confirmed
- `grep "OntologyGeneratorAgent" create_master_agent.py`: confirmed present

## Deviations from Plan

### Pre-existing Test Failure (Out of Scope)

The test `tests/test_capture_frontend_state.py::test_url_construction` was already failing before this plan (expects `wait_until='networkidle'`, actual is `wait_until='load'`). This is unrelated to ontology wiring. Per scope boundary rules, it was not fixed and logged as a deferred item.

No deviations to the plan tasks themselves — both tasks executed exactly as specified.

## Decisions Made

1. **ASHRAE 223P Code Generation Protocol requires explicit human instruction** — "Do NOT auto-trigger this protocol" ensures safety; only acts on: "create the code", "generate the 223P ontology", "build the ontology", or similar explicit requests.

2. **all_subagents preserves existing interface** — externally-passed subagents (the `subagents` parameter) are prepended so any future callers can still inject additional agents, while ontology agents are always appended.

## Self-Check: PASSED

- agent/master_architecture/create_master_agent.py: FOUND
- agent/master_architecture/prompts/master_instruction.md: FOUND
- Commit d8634c2 (Task 1): FOUND
- Commit 325fcd9 (Task 2): FOUND
