---
phase: 22-enhance-bacnet-parsing
plan: "03"
subsystem: agent-skills
tags: [bacnet, ontology, skill-update, documentation]
dependency_graph:
  requires: []
  provides: [updated-skill-ontology-generation, updated-skill-ontology-validation, updated-skill-ontology-lessons]
  affects: [ontology-generation-agent, ontology-validation-agent]
tech_stack:
  added: []
  patterns: [pre-computed-bacnet-fields, direct-uri-consumption]
key_files:
  created: []
  modified:
    - agent/skills/skill-ontology-generation/SKILL.md
    - agent/skills/skill-ontology-validation/SKILL.md
    - agent/skills/skill-ontology-lessons/SKILL.md
decisions:
  - "Pre-computed bacnet_N fields (code, address, ref_type) documented across all three ontology skills — agents consume address URI directly without manual parsing"
  - "Lessons skill retains all existing address-parsing content as legacy fallback while Phase 22 update note is prepended at the top of the BACnet section"
metrics:
  duration: "61s"
  completed_date: "2026-04-03"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 3
---

# Phase 22 Plan 03: Update Ontology Skills for Pre-Computed BACnet Fields Summary

**One-liner:** Updated three ontology SKILL.md files to document pre-computed `bacnet_N` fields (`code`, `address` URI, `ref_type`) so agents consume enriched data directly instead of manually parsing raw BACnet addresses.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update skill-ontology-generation BACnet section | 2e8c8a1 | agent/skills/skill-ontology-generation/SKILL.md |
| 2 | Update skill-ontology-validation and skill-ontology-lessons | b7290a5 | agent/skills/skill-ontology-validation/SKILL.md, agent/skills/skill-ontology-lessons/SKILL.md |

## What Was Done

### Task 1: skill-ontology-generation/SKILL.md
Replaced the 1-line reference to `skill-ontology-lessons` for address-parsing rules with full documentation of pre-computed fields:
- Documented `code`, `address`, and `ref_type` fields in each `bacnet_N` entry
- Instructed agents to use `bacnet_N["address"]` directly when constructing `BACnetExternalReference`
- Added skip logic for entries where `ref_type == "skip"` or `address` is `null`
- Removed reference to old "address-parsing rules, type suffix map" pattern

### Task 2: skill-ontology-validation/SKILL.md and skill-ontology-lessons/SKILL.md
**Validation skill:** Same pre-computed field documentation added (matching generation skill format), replacing the 1-line reference.

**Lessons skill:** Added Phase 22 update note as a blockquote at the very top of the "BACnet External References" section, before all existing content. All legacy parsing rules, suffix maps, and code patterns are preserved as fallback documentation — no content was removed.

## Verification Results

All acceptance criteria passed:
- `grep -c "ref_type"` returns >= 2 in generation and validation skills
- `grep -c "No manual address parsing"` returns 1 in both skills
- `grep -c 'bacnet_N["address"]'` returns 1 in both skills
- Old "address-parsing rules, type suffix map" text removed from generation and validation skills
- `grep -c "Phase 22 update"` returns 1 in lessons skill
- `grep -c "legacy fallback"` returns 1 in lessons skill
- `BACnetExternalReference` still has 4 matches in lessons (existing patterns preserved)
- `analog-input` still has 2 matches in lessons (suffix map preserved)
- Overall: all 3 SKILL.md files contain `ref_type`

## Decisions Made

1. **Pre-computed field documentation:** All three skills now document the `code`, `address`, and `ref_type` fields consistently so agents know exactly what to expect from the Python pre-computation layer.
2. **Legacy fallback preservation:** The lessons skill retains every line of existing BACnet content — the Phase 22 note prepends context rather than replacing anything. This ensures continuity if agents need fallback parsing logic.

## Deviations from Plan

None - plan executed exactly as written.
