---
phase: 18-optimize-skill-for-ontology-validation
plan: 01
subsystem: agent-skills
tags: [skill, ontology, validation, llm-instructions, markdown]
dependency_graph:
  requires: []
  provides:
    - agent/skills/skill-ontology-validation/SKILL.md (rewritten with all 11 optimizations)
    - agent/skills/skill-ontology-lessons/SKILL.md (targeted consultation note added)
  affects:
    - ontology validation loop behavior (agent follows structured procedure)
tech_stack:
  added: []
  patterns:
    - Exit Protocol elevated to top section (mirrors generator skill)
    - Sub-steps 4a-4d for class lookup chain (search → read → re-read → fix)
    - Retry Escalation three-tier table (3/5/10 consecutive attempts)
    - Inline Error Classification within Fixing Strategy
key_files:
  created: []
  modified:
    - agent/skills/skill-ontology-validation/SKILL.md
    - agent/skills/skill-ontology-lessons/SKILL.md
decisions:
  - Exit tool names kept as exit_with_success/exit_with_failure (Phase 19 names, already in current skill)
  - scan_python_folder kept conditional (Step 0 optional + Retry tier-3 trigger)
  - Error Classification inline in Fixing Strategy per locked CONTEXT.md decision
  - Pre-Write Verification as advisory blockquote, not formal workflow step
metrics:
  duration_seconds: 156
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 2
---

# Phase 18 Plan 01: Optimize Skill for Ontology Validation Summary

**One-liner:** Rewrote validation SKILL.md with 11 optimizations: sub-steps 4a-4d, 3/5/10 retry escalation, inline error classification, and elevated Exit Protocol; added targeted consultation note to lessons skill.

---

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Full rewrite of skill-ontology-validation/SKILL.md with all 11 optimizations | 1e98222 | agent/skills/skill-ontology-validation/SKILL.md |
| 2 | Add targeted consultation note to skill-ontology-lessons/SKILL.md | 3c27a68 | agent/skills/skill-ontology-lessons/SKILL.md |

---

## What Changed

### skill-ontology-validation/SKILL.md

Full rewrite from 62 lines to ~120 lines implementing all 11 optimizations:

1. **Exit Protocol elevated (opt 10):** Moved from implicit (buried in Stop Conditions) to explicit `## Exit Protocol` section at line 12 — before Workflow.
2. **Sub-steps 4a-4d (opts 1, 3):** Step 4 now has four explicit labeled sub-steps: extract class/method names (4a), `search_class_mapping` (4b), `read_python_files` on library (4c), re-read error location in ontology then fix (4d).
3. **scan_python_folder in Step 0 (opt 2):** Added as optional-but-recommended enrichment step before fix loop begins. Also appears in Retry tier-3.
4. **Re-read before fix in 4d (opt 4):** Sub-step 4d explicitly requires reading the current error location in the ontology before writing (`read_python_files(["...latest_ontology.py"], keywords=[...])`), acknowledging file may have changed since step 1.
5. **Minimum-Change Constraint (opt 5):** Added as subsection of Fixing Strategy — fix only what error requires, minimum lines per `write_ontology` call.
6. **Retry Escalation tiers (opt 6):** Standalone `## Retry Escalation` block after fix loop with table of three independent tiers (3/5/10 consecutive same-error attempts).
7. **Mid-loop lessons re-consultation (opt 7):** Trigger added between step 3 and step 4 — when new error type appears, reload lessons and search by category keyword.
8. **Root-Cause Ordering (opt 8):** Four-level ordering in Fixing Strategy: import → instantiation → connection/wiring → serialization.
9. **Pre-Write Verification (opt 9):** Advisory blockquote in Fixing Strategy with three checks before `write_ontology`.
10. **Error Classification inline (opt 11):** `### Error Classification` subsection inside Fixing Strategy — two categories (Python execution errors vs. library semantic errors) with stdout/stderr guidance.

### skill-ontology-lessons/SKILL.md

Single addition: consultation guidance blockquote inserted after intro paragraph (line 8), before `---` separator. Directs agent to search by error category keyword during mid-loop re-consultation, not re-read the full file.

---

## Deviations from Plan

### Plan Reference Note

The PLAN.md target section text used `exit_validator_success/failure` names (from Phase 13), but the current skill and exit_tools.py use `exit_with_success/exit_with_failure` (Phase 19 generic names). The rewrite used the correct current names to avoid introducing deprecated references. This is consistent with STATE.md Decision (19-02) and the existing skill state.

No auto-fix rules triggered. All other plan instructions followed exactly.

---

## Verification Results

All acceptance criteria passed:

| Check | Result |
|-------|--------|
| Exit Protocol within first 20 lines | Line 12 |
| 4a. present | 1 match |
| 4b. present | 1 match |
| 4c. present | 1 match |
| 4d. present | 1 match |
| Retry Escalation present | 2 matches (heading + table) |
| After 3 consecutive | 1 match |
| After 5 consecutive | 1 match |
| After 10 consecutive | 1 match |
| Error Classification | 1 match |
| Minimum-Change | 1 match |
| Root-Cause Ordering | 1 match |
| Pre-Write Verification | 1 match |
| scan_python_folder in skill | 4 matches |
| new error type trigger | 1 match |
| checkpoint_code (must be 0) | 0 matches |
| skill-read-code (must be 0) | 0 matches |
| Consultation note in lessons | 1 match |
| search by error category keyword | 1 match |

Pytest: pre-existing failures in test_capture_frontend_state and test_load_ttl_to_neo4j_tool/test_create_master_agent confirmed present before this phase's changes. No new failures introduced.

## Self-Check: PASSED

- agent/skills/skill-ontology-validation/SKILL.md: FOUND (rewritten, 120+ lines)
- agent/skills/skill-ontology-lessons/SKILL.md: FOUND (38 lines, consultation note added)
- Commit 1e98222: FOUND
- Commit 3c27a68: FOUND
