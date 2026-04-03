---
phase: 19-standardize-agent-exit-tools-across-all-skills
plan: "02"
subsystem: agent-skills
tags: [skills, exit-tools, master-instruction, standardization]
dependency_graph:
  requires: [19-01]
  provides: [standardized-skill-exit-calls, one-task-at-a-time-rule]
  affects: [skill-ductwork, skill-hvac-equipments, skill-bacnet-points, skill-ontology-generation, skill-ontology-validation, master-instruction]
tech_stack:
  added: []
  patterns: [exit_with_success, exit_with_failure]
key_files:
  created: []
  modified:
    - agent/skills/skill-ductwork/SKILL.md
    - agent/skills/skill-hvac-equipments/SKILL.md
    - agent/skills/skill-bacnet-points/SKILL.md
    - agent/skills/skill-ontology-generation/SKILL.md
    - agent/skills/skill-ontology-validation/SKILL.md
    - agent/master_architecture/prompts/master_instruction.md
decisions:
  - "All 5 skills now instruct agents to call exit_with_success/exit_with_failure; ductwork/equipment/bacnet exit steps include domain-specific summary requirements"
  - "One-task-at-a-time rule added to master instruction before ASHRAE 223P Code Generation Protocol — prevents unprompted skill chaining"
  - "Removed checkpoint_code from validation tool list in master instruction ASHRAE Sequence step 3"
metrics:
  duration: "2 minutes"
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 6
---

# Phase 19 Plan 02: Update Skills to Use Generic Exit Tools Summary

Replaced all fragmented exit tool references in 5 skill files and master instruction with generic `exit_with_success`/`exit_with_failure` calls; added one-task-at-a-time rule to prevent unprompted skill chaining.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update all 5 skills with exit_with_success/exit_with_failure | 0d4be6c | skill-ductwork/SKILL.md, skill-hvac-equipments/SKILL.md, skill-bacnet-points/SKILL.md, skill-ontology-generation/SKILL.md, skill-ontology-validation/SKILL.md |
| 2 | Add one-task-at-a-time rule to master instruction | b29b0ae | agent/master_architecture/prompts/master_instruction.md |

## What Was Built

**Task 1 — Skills updated:**
- `skill-ductwork`: Step 6 "Exit" now calls `exit_with_success(summary="...")` with mandatory duct count, correction count, and verification result; `exit_with_failure` on unresolvable verification.
- `skill-hvac-equipments`: Step 7 "Exit" now calls `exit_with_success(summary="...")` with mandatory equipment count, correction count, and verification result; `exit_with_failure` on unresolvable verification.
- `skill-bacnet-points`: Step 5 "Verify and Exit" now calls `exit_with_success(summary="...")` with mandatory BACnet points extracted, equipment matched, and unmatched items; `exit_with_failure` if CSV unparseable.
- `skill-ontology-generation`: Replaced `exit_generator_success`/`exit_generator_failure` with `exit_with_success`/`exit_with_failure` in Exit Protocol, Step 10, and Failure conditions section.
- `skill-ontology-validation`: Replaced `exit_validator_success`/`exit_validator_failure` with `exit_with_success`/`exit_with_failure` in workflow step 3, Available tools list, and Stop Conditions heading.

**Task 2 — Master instruction updated:**
- Added `## Task Execution Rule` section before `## ASHRAE 223P Code Generation Protocol`.
- Rule text: "Execute one skill at a time. After a skill calls `exit_with_success` or `exit_with_failure`, wait for the user to give the next instruction before starting another skill."
- Updated ASHRAE Sequence steps 1-4 to use `exit_with_success`/`exit_with_failure` throughout.
- Removed `checkpoint_code` from step 3 tool list.

## Verification Results

- `grep -r "exit_with_success" agent/skills/ agent/master_architecture/prompts/ --include="*.md" -l | wc -l` → **6** (5 skills + master_instruction.md)
- `grep -r "exit_generator_success|exit_generator_failure|exit_validator_success|exit_validator_failure|exit_loop_level_2" agent/skills/ agent/master_architecture/prompts/ --include="*.md"` → **0 matches**
- `grep "one skill at a time" agent/master_architecture/prompts/master_instruction.md` → **match found**

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

All 6 modified files confirmed on disk. Both task commits (0d4be6c, b29b0ae) confirmed in git log.
