---
phase: 16-optimize-ontology-skills
plan: 03
subsystem: skills
tags: [ontology, skill-md, ashrae-223p, hvac, generation, validation, lessons]

# Dependency graph
requires:
  - phase: 16-optimize-ontology-skills/16-02
    provides: "Rewrote exit tool signatures to 2-param; deleted checkpoint_code function; folded auto-checkpoint into write_ontology"
provides:
  - "Updated generation SKILL.md: Exit Protocol section, clean exit call without code= param, unambiguous % operator docs"
  - "Updated validation SKILL.md: Step 0 preparation, clean exit signature, no checkpoint_code, correct paths, batch-fix strategy, % operator reference"
  - "Updated lessons SKILL.md: unambiguous % operator lesson distinguishing sensor%equipment (correct) from sensor%property (wrong)"
affects: [skill-ontology-generation, skill-ontology-validation, skill-ontology-lessons, ontology-agent-execution]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Exit Protocol section pattern: declare the only valid exit tools near the top of SKILL.md"
    - "Step 0 preparation pattern: numbered pre-loop step for loading lessons before the fix loop"
    - "Root-cause batching: fix all errors sharing a root cause in one write, not one per error line"

key-files:
  created: []
  modified:
    - agent/skills/skill-ontology-generation/SKILL.md
    - agent/skills/skill-ontology-validation/SKILL.md
    - agent/skills/skill-ontology-lessons/SKILL.md

key-decisions:
  - "grep-0 criterion for code= and ttl_content= requires rewriting 'do not pass code=' warnings to alternative phrasing ('pass only the summary string')"
  - "Exit Protocol section placed immediately after # Workflow header so it is the first thing an agent reads in the workflow section"

patterns-established:
  - "SKILL.md Exit Protocol: state exit tool names at top; do not repeat in every step"
  - "Validation Step 0: always load lessons before entering the fix loop"

requirements-completed: [P16-09, P16-10, P16-11]

# Metrics
duration: 3min
completed: 2026-04-03
---

# Phase 16 Plan 03: Optimize Ontology Skills SKILL.md Updates Summary

**Updated three ontology SKILL.md files to match Wave 2 code changes: Exit Protocol section, clean 2-param exit calls, Step 0 preparation, no checkpoint_code, correct file paths, root-cause fix batching, and unambiguous % operator documentation.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-03T11:43:35Z
- **Completed:** 2026-04-03T11:45:44Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Generation SKILL.md: added `## Exit Protocol` section; Step 10 clarifies no `code=` param needed; `%` operator docs now explain both correct (`sensor % equipment`) and wrong (`sensor % property`) usage
- Validation SKILL.md: `**Preparation**` replaced with numbered `Step 0 — Preparation (run once)`; exit call updated to `exit_validator_success(summary="...")`; `checkpoint_code` step and tool removed; `execute_ontology` and path references updated; `## Operator Reference` section added; fix strategy now batches by root cause
- Lessons SKILL.md: % operator lesson now explicitly states `sensor % equipment` is correct and `sensor % property` is wrong

## Task Commits

Each task was committed atomically:

1. **Task 1: Update generation SKILL.md** - `617c04e` (feat)
2. **Task 2: Update validation SKILL.md** - `67b51a5` (feat)
3. **Task 3: Update lessons SKILL.md** - `db3502c` (feat)

## Files Created/Modified
- `agent/skills/skill-ontology-generation/SKILL.md` - Exit Protocol section, clean exit call, unambiguous % operator docs
- `agent/skills/skill-ontology-validation/SKILL.md` - Step 0, clean exit, no checkpoint_code, correct paths, batch-fix strategy, % operator reference
- `agent/skills/skill-ontology-lessons/SKILL.md` - Unambiguous % operator lesson: sensor%equipment correct, sensor%property wrong

## Decisions Made
- The acceptance criteria required `grep -c "code="` to return 0. The plan's wording "do not pass `code=`" contains `code=` itself, so the warning text was rephrased to "pass only the summary string" to satisfy the grep count while preserving the intent.
- Exit Protocol section was placed immediately after the `# Workflow` header so it is the first element an agent reads when entering the workflow.

## Deviations from Plan

None — plan executed exactly as written, with one minor phrasing adjustment to satisfy the grep-0 acceptance criterion for `code=` in the validation SKILL.md (the "do not pass code=" wording was rewritten to avoid containing the literal string `code=`).

## Issues Encountered
- Step D and E in Task 2 are numbered relative to old step numbers (5→checkpoint_code was step 5, step 6 became step 5). The final loop is correctly 5 steps (0 prep + 5-step fix loop counting from 1).

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

All 4 files found. All 3 task commits found (617c04e, 67b51a5, db3502c).

## Next Phase Readiness
- All three SKILL.md files now match the Wave 2 code changes from plan 16-02
- Ready for plan 16-04: test updates to cover the new exit tool signatures and write_ontology auto-checkpoint behavior

---
*Phase: 16-optimize-ontology-skills*
*Completed: 2026-04-03*
