---
phase: 15-refactor-coding-skills-and-standardize-agent-architecture
plan: 03
subsystem: agent
tags: [skills, ontology, ashrae-223p, lessons, bacnet, hitl]

# Dependency graph
requires:
  - phase: 15-02
    provides: agent/223p/ directory with LESSONS.md, extract_lessons tool, three-write pattern, skill-read-code deleted
provides:
  - skill-ontology-generation/SKILL.md with LESSONS.md Step 0, fixed paths, BACnet custom_fields awareness, extract_lessons HITL section
  - skill-ontology-validation/SKILL.md with updated Preparation step, fixed paths, no skill-read-code references
affects:
  - ontology generation and validation workflow (LLM instructions updated)
  - agent master instruction for 223P code generation

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LESSONS.md-first: Step 0 in generation workflow reads agent/223p/LESSONS.md before any other action"
    - "HITL-gated lesson extraction: extract_lessons only triggered by explicit user instruction, never auto"
    - "BACnet custom_fields propagation: read_internal_grid custom_fields key used as ontology properties"

key-files:
  created: []
  modified:
    - agent/skills/skill-ontology-generation/SKILL.md
    - agent/skills/skill-ontology-validation/SKILL.md

key-decisions:
  - "skill-read-code mention removed from Step 0 text (even as a 'do not use' warning) to pass grep-count acceptance criterion"
  - "Lesson Extraction section is HITL-gated: extract_lessons only called when user explicitly requests it"
  - "BACnet custom_fields bullet placed in Equipment section under Modeling Guidelines (not Sensors)"

patterns-established:
  - "LESSONS.md Step 0: generation skill reads agent/223p/LESSONS.md as first workflow step"
  - "Skills reference agent/223p/ absolute-style paths (no ../223p/ relative paths)"

requirements-completed:
  - P15-08
  - P15-09
  - P15-10

# Metrics
duration: 12min
completed: 2026-04-02
---

# Phase 15 Plan 03: Ontology Skills Audit Summary

**Both ontology SKILL.md files audited and updated: LESSONS.md Step 0, BACnet custom_fields awareness, extract_lessons HITL section added to generation skill; skill-read-code removed and paths fixed in both skills**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-02T14:35:00Z
- **Completed:** 2026-04-02T14:47:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added Step 0 to skill-ontology-generation workflow to read agent/223p/LESSONS.md before any generation work
- Added BACnet custom_fields awareness bullet in Equipment modeling guidelines
- Added HITL-gated Lesson Extraction section (only triggered by explicit user instruction)
- Removed all 3 references to deleted skill-read-code from skill-ontology-validation
- Fixed both skills to use agent/223p/ paths instead of ../223p/ relative paths
- Updated validation Preparation step to use LESSONS.md direct read + read_prompt for generation guidelines

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit and rewrite skill-ontology-generation/SKILL.md** - `61e173b` (feat)
2. **Task 2: Audit and rewrite skill-ontology-validation/SKILL.md** - `67a9468` (feat)

**Plan metadata:** (docs commit - see final commit)

## Files Created/Modified
- `agent/skills/skill-ontology-generation/SKILL.md` - Added Step 0 LESSONS.md read, fixed path, removed skill-read-code, added extract_lessons HITL section, added BACnet custom_fields awareness
- `agent/skills/skill-ontology-validation/SKILL.md` - Replaced skill-read-code Preparation with LESSONS.md direct read, fixed path ../223p/ -> agent/223p/, updated stop conditions

## Decisions Made
- Removed `skill-read-code` mention even from "do NOT use" warning in Step 0 text to satisfy acceptance criterion of 0 grep matches
- Lesson Extraction is HITL-gated with explicit user trigger requirement (consistent with Decision 11-04)
- BACnet custom_fields added as Equipment guideline since `read_internal_grid` returns this data alongside equipment components

## Deviations from Plan

None - plan executed exactly as written. Minor adjustment: Step 0 text in the action description said to include "Do NOT use `skill-read-code` — that skill no longer exists" but the acceptance criteria required 0 grep hits for `skill-read-code`. Removed the mention to satisfy the machine-verifiable criterion while preserving the guidance intent through the replacement text.

## Issues Encountered
- Pre-existing test failure in `tests/test_capture_frontend_state.py::test_url_construction` (wait_until='networkidle' vs 'load') — unrelated to this plan, deferred to `deferred-items.md`.

## Next Phase Readiness
- Both ontology skills are now fully consistent with the post-15-02 codebase (agent/223p/ paths, no skill-read-code, LESSONS.md-first workflow)
- Phase 15 all plans complete — ontology generation/validation pipeline fully refactored

---
*Phase: 15-refactor-coding-skills-and-standardize-agent-architecture*
*Completed: 2026-04-02*
