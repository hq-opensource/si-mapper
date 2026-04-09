# Phase 18: Optimize Skill for Ontology Validation — Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Rewrite `agent/skills/skill-ontology-validation/SKILL.md` to implement all 11 optimizations identified in the session analysis, plus any supporting changes required in `skill-ontology-lessons/SKILL.md` or other skill files. No new tools, no new agent code, no new Python files.

The 11 optimizations are:
1. Make class lookup structural (not implicit) — sub-steps 4a–4d
2. Make `scan_python_folder` (examples) conditional but explicit
3. Break step 4 apart into labeled sub-steps
4. Instruct agent to re-read error location before fixing
5. Add "minimum change" constraint to Fixing Strategy
6. Add graduated retry escalation tiers (3 / 5 / 10 attempts)
7. Re-consult lessons when a new error type appears mid-loop
8. Add ordering guidance for multiple root causes
9. Advisory pre-write verification note in Fixing Strategy
10. Elevate exit protocol to top of skill
11. Add error classification inline in Fixing Strategy

</domain>

<decisions>
## Implementation Decisions

### Instruction granularity (optimizations 1, 3, 4)
- The fix loop step 4 is broken into explicit numbered sub-steps: **4a, 4b, 4c, 4d** (each covering one action: extract class names → search_class_mapping → read_python_files → fix + write).
- Sub-steps 4a–4d apply when errors share the same root cause — they are one group within the loop.
- Retry escalation (#6) uses **independent numbered tiers**, NOT sub-steps of 4a–4d. Each tier is a standalone rule with its own trigger count and required action.

### Retry escalation tiers (optimization 6)
- **After 3 consecutive same-error attempts**: re-read library source (steps 4b–4c) AND examples (`scan_python_folder`) before next attempt. Do not retry with the same fix strategy.
- **After 5 consecutive same-error attempts**: re-read `skill-ontology-lessons` specifically for the failing error category.
- **After 10 consecutive same-error attempts**: call `exit_validator_failure`.
- These are presented as a dedicated "Retry Escalation" block, separate from the main loop steps.

### Error classification placement (optimization 11)
- Error classification is **inline within the Fixing Strategy section** — not a standalone top-level section.
- Two categories documented inline:
  - **Python execution errors**: non-zero returncode, traceback in stderr, has line number → look up line in ontology, then library source.
  - **Library semantic/validation errors**: errors in stdout, no line number, only class/method name → look up class in search_class_mapping, read library source, cross-reference examples.
- Note added: "Always check both stdout and stderr before classifying."

### Pre-write verification (optimization 9)
- **Advisory only** — listed as a note in Fixing Strategy, not a formal workflow sub-step.
- Phrasing: "Before calling write_ontology, re-read the specific section(s) you modified and confirm: (a) valid Python syntax, (b) fix addresses the identified root cause, (c) no adjacent code inadvertently changed."

### Scope of skill files
- **Primary file**: `agent/skills/skill-ontology-validation/SKILL.md` — all 11 optimizations applied.
- **Supporting file**: `agent/skills/skill-ontology-lessons/SKILL.md` — updated to support optimization #7 (mid-loop re-consultation guidance): add a note that lessons should be targeted by error category keyword, not re-read in full.
- No changes to `skill-ontology-generation/SKILL.md` unless a specific optimization bleeds into it (unlikely — generation already has structured lookup steps).
- No Python code changes.

### Plan structure
- **Single plan** — all 11 optimizations in one SKILL.md rewrite. No need to split by concern.

### Claude's Discretion
- Exact wording of each new instruction block
- Whether to use blockquotes, code blocks, or prose for the new Fixing Strategy additions
- Ordering of sections within the new Fixing Strategy (error classification first, then constraint, then pre-write note, then root-cause ordering)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Skill files to modify
- `agent/skills/skill-ontology-validation/SKILL.md` — current 61-line file; primary target of all 11 optimizations
- `agent/skills/skill-ontology-lessons/SKILL.md` — update for mid-loop re-consultation guidance

### Reference skill (model to mirror)
- `agent/skills/skill-ontology-generation/SKILL.md` — the generator skill already has structured lookup steps (steps 2–4), an Exit Protocol section at the top, and a lessons step. Use it as the structural reference for what the validator should look like after this phase.

### Tool implementations (read-only — understand what tools do, don't modify)
- `agent/tools/ontology_tools.py` — `search_class_mapping`, `read_python_files`, `scan_python_folder`, `execute_ontology`, `write_ontology`
- `agent/tools/ontology_exit_tools.py` — `exit_validator_success`, `exit_validator_failure`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/skills/skill-ontology-generation/SKILL.md` — generator steps 2–4 are the exact structural model for the new 4a–4d validator sub-steps; copy and adapt rather than invent from scratch

### Established Patterns
- Generator skill pattern: Exit Protocol at top → numbered workflow steps → Fixing Strategy → Available tools → Stop conditions → Success exit summary
- Lessons skill is short (35 lines) and uses a flat error-to-resolution list format; any additions should follow the same `## Category` / `- **Error:** ... -> **Fix:** ...` pattern

### Integration Points
- The validation skill is loaded as a `tool_context`-accessible skill during agent runs — no Python import needed; changes take effect immediately on next run

</code_context>

<specifics>
## Specific Ideas

- For sub-steps 4a–4d: mirror the exact structure of the generator's steps 2–4 (search → read library → read examples → fix/write) so both skills feel consistent.
- The Exit Protocol block at the top should use the same phrasing as the generator: "The ONLY valid ways to terminate are: exit_validator_success / exit_validator_failure."
- Error classification note: emphasize checking **both** stdout and stderr — agents often only check one.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 18-optimize-skill-for-ontology-validation*
*Context gathered: 2026-04-03*
