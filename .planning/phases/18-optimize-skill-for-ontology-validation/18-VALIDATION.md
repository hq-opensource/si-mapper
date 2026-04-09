---
phase: 18
slug: optimize-skill-for-ontology-validation
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-04-03
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | grep (structural) + human prose review |
| **Config file** | none — markdown-only phase |
| **Quick run command** | `grep -r "checkpoint_code" agent/skills/ && grep -r "skill-read-code" agent/skills/` |
| **Full suite command** | `grep -n "Exit Protocol" agent/skills/skill-ontology-validation/SKILL.md \| head -3 && grep -c "4a\." agent/skills/skill-ontology-validation/SKILL.md && grep -c "4b\." agent/skills/skill-ontology-validation/SKILL.md && grep -c "4c\." agent/skills/skill-ontology-validation/SKILL.md && grep -c "4d\." agent/skills/skill-ontology-validation/SKILL.md` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick grep battery (no `checkpoint_code`, no `skill-read-code`, no `code=` in exit calls)
- **After every plan wave:** Full suite command + human review of skill prose for all 11 optimizations
- **Before `/gsd:verify-work`:** Human review confirming all 11 optimizations present in correct positions
- **Max feedback latency:** 2 seconds (grep checks instant)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Optimization | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 18-01-T1 | 01 | 1 | OPT-10: Exit Protocol at top | grep | `grep -n "Exit Protocol" agent/skills/skill-ontology-validation/SKILL.md \| head -1` (line ≤ 20) | ⬜ pending |
| 18-01-T1 | 01 | 1 | OPT-01/03/04: Sub-steps 4a–4d present | grep | `grep -c "4a\.\|4b\.\|4c\.\|4d\." agent/skills/skill-ontology-validation/SKILL.md` (≥ 4) | ⬜ pending |
| 18-01-T1 | 01 | 1 | OPT-06: Retry escalation tiers present | grep | `grep -c "3 consecutive\|5 consecutive\|10 consecutive" agent/skills/skill-ontology-validation/SKILL.md` (= 3) | ⬜ pending |
| 18-01-T1 | 01 | 1 | OPT-11: Error classification inline | grep | `grep -c "Python execution\|Library semantic" agent/skills/skill-ontology-validation/SKILL.md` (≥ 2) | ⬜ pending |
| 18-01-T1 | 01 | 1 | OPT-05: Minimum-change constraint | grep | `grep -i "minimum\|only what is necessary\|minimum.*change" agent/skills/skill-ontology-validation/SKILL.md` (≥ 1 match) | ⬜ pending |
| 18-01-T1 | 01 | 1 | OPT-08: Root-cause ordering | grep | `grep -i "root cause\|one at a time\|ordering" agent/skills/skill-ontology-validation/SKILL.md` (≥ 1 match) | ⬜ pending |
| 18-01-T1 | 01 | 1 | No deprecated references | grep | `grep -c "checkpoint_code\|code=\|skill-read-code" agent/skills/skill-ontology-validation/SKILL.md` (= 0) | ⬜ pending |
| 18-01-T2 | 01 | 1 | OPT-07: Lessons consultation note | grep | `grep -i "category keyword\|error category" agent/skills/skill-ontology-lessons/SKILL.md` (≥ 1 match) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — no test files needed. This phase produces only markdown files. All verification is structural grep checks and human prose review. Existing `agent/tests/` Python suite is unaffected.

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Optimization | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Skill prose instructs agent to re-read error location before fixing | OPT-04 (4d) | Prose quality cannot be grep-verified | Read Task 1 output; confirm 4d says "re-read the specific error location in current file state" |
| scan_python_folder conditional but explicit in Step 0 | OPT-02 | Intent (conditional vs mandatory) is prose-dependent | Read Step 0 in rewritten SKILL.md; confirm it says "optional but recommended" |
| Pre-write verification advisory note present | OPT-09 | Advisory vs mandatory distinction is prose-dependent | Read Fixing Strategy section; confirm note says "Before calling write_ontology, re-read and confirm..." |
| Error classification inline in Fixing Strategy (not standalone section) | OPT-11 | Section placement cannot be grep-verified | Read rewritten SKILL.md; confirm classification is inside Fixing Strategy, not a top-level section |
| Root-cause ordering guidance: deepest dependency first | OPT-08 | Ordering nuance is prose-dependent | Read Fixing Strategy section; confirm guidance mentions dependency order (imports before instantiation before connections) |
| Mid-loop lessons re-consultation trigger present | OPT-07 | Trigger condition is prose-dependent | Read Fix loop; confirm "If a new error type appears" trigger present |

---

## Validation Sign-Off

- [ ] All tasks have automated grep checks or are documented as manual-only
- [ ] All 8 automated grep checks pass (0 deprecated refs, ≥4 sub-steps, 3 retry tiers, ≥2 classification terms, ≥1 each for constraint/ordering/consultation)
- [ ] All 6 manual verifications reviewed and confirmed
- [ ] No `checkpoint_code` in any `agent/skills/` file
- [ ] No `code=` parameter in exit calls in rewritten SKILL.md
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
