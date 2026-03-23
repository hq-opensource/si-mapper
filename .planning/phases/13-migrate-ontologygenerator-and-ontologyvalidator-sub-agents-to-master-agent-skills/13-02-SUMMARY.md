---
phase: 13-migrate-ontologygenerator-and-ontologyvalidator-sub-agents-to-master-agent-skills
plan: "02"
subsystem: agent/master_architecture
tags: [migration, ontology, master-agent, skills, tools]
dependency_graph:
  requires: ["13-01"]
  provides: ["direct ontology tool execution in master agent"]
  affects: ["agent/master_architecture/create_master_agent.py", "agent/master_architecture/level_2_master_main_loop.py", "agent/master_architecture/prompts/master_instruction.md", "agent/tests/test_create_master_agent.py"]
tech_stack:
  added: []
  patterns: ["direct tool injection pattern (sub-agents replaced with tool functions)", "EXIT_LEVEL_2 termination via escalate=True"]
key_files:
  created: []
  modified:
    - agent/master_architecture/create_master_agent.py
    - agent/master_architecture/level_2_master_main_loop.py
    - agent/master_architecture/prompts/master_instruction.md
    - agent/tests/test_create_master_agent.py
decisions:
  - "all_subagents = subagents or [] — ontology agents removed from sub-agents list entirely"
  - "max_iterations increased from 10 to 100 — needed for multi-step ontology generation/validation loops"
  - "master_instruction.md Neo4j section updated to remove OntologyValidatorAgent reference — consistent cleanup"
metrics:
  duration: "~2 minutes"
  completed_date: "2026-03-23"
  tasks_completed: 3
  files_modified: 4
---

# Phase 13 Plan 02: Rewire Master Agent with Direct Ontology Tools Summary

**One-liner:** Removed OntologyGeneratorAgent and OntologyValidatorAgent sub-agent wrappers, wiring all 11 ontology tools (6 from _223p/tool.py + checkpoint_code + 4 adapted exit tools) directly into MasterLlmAgent's tool list with max_iterations raised to 100.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewire create_master_agent.py and increase max_iterations | 652c9ea | create_master_agent.py, level_2_master_main_loop.py |
| 2 | Update master_instruction.md ASHRAE protocol to reference skills | 6933a4f | master_instruction.md |
| 3 | Update tests to verify new architecture | 1aa3bef | test_create_master_agent.py |

## What Was Done

### Task 1: Rewire create_master_agent.py

- Removed `from sub_agents.ontology_generator.agent import OntologyGeneratorAgent`
- Removed `from sub_agents.ontology_validator.agent import OntologyValidatorAgent`
- Added imports from `sub_agents._223p.tool`: `scan_python_files_filtered`, `search_class_mapping`, `write_ontology`, `read_ontology`, `execute_ontology`, `read_prompt`
- Added import of `checkpoint_code` from `sub_agents.ontology_validator.exit_tools` (stays at original location)
- Added imports from `master_architecture.tools.ontology_exit_tools`: all 4 adapted exit tools
- Added all 11 ontology tools directly to the `task_tools` list
- Replaced `ontology_subagents = [...]; all_subagents = (subagents or []) + ontology_subagents` with `all_subagents = subagents or []`
- Changed `MasterMainLoopAgent` default `max_iterations` from `10` to `100`

### Task 2: Update master_instruction.md

- Replaced "Generate ASHRAE 223P Ontology" capability description from sub-agent delegation to skill-based direct tool usage
- Rewrote the ASHRAE 223P Code Generation Protocol to reference `skill-ontology-generation` and `skill-ontology-validation`
- Changed delegation language ("Delegate to OntologyGeneratorAgent") to direct execution language ("Apply the skill, use tools directly")
- Updated Neo4j Import Protocol section to remove lingering `OntologyValidatorAgent` reference
- All other protocol sections (Artifact Loading, Neo4j Import, Visual Verification) preserved unchanged

### Task 3: Update Tests

- Replaced 4 old tests (which asserted sub-agents ARE present) with 8 new tests (asserting sub-agents are GONE, tools ARE present)
- Tests use AST-based verification for `max_iterations=100`
- All 8 tests pass with `pytest 9.0.2`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Neo4j protocol section also referenced OntologyValidatorAgent**

- **Found during:** Task 2 verification
- **Issue:** The acceptance criteria required zero `OntologyValidatorAgent` occurrences in the file. The unchanged Neo4j Import Protocol section contained `After the OntologyValidatorAgent has successfully validated...`
- **Fix:** Updated that line to say `After the ontology validation skill has successfully validated...`
- **Files modified:** `agent/master_architecture/prompts/master_instruction.md`
- **Commit:** 6933a4f (included in Task 2 commit)

## Verification Results

- 8/8 pytest tests pass
- `grep -r "OntologyGeneratorAgent|OntologyValidatorAgent" master_architecture/` returns no matches
- `grep "skill-ontology-generation" master_instruction.md` finds 2 matches
- Sub-agent source files are unchanged (dead code kept as backup)
- `max_iterations: int = 100` confirmed in level_2_master_main_loop.py

## Self-Check: PASSED
