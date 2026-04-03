# Phase 18: Optimize Skill for Ontology Validation — Research

**Researched:** 2026-04-03
**Domain:** Agent skill authoring — markdown instruction files for LLM-driven ontology validation
**Confidence:** HIGH

## Summary

This phase is a pure markdown rewrite — no Python changes, no new tools, no test additions. The deliverables are two updated SKILL.md files: `agent/skills/skill-ontology-validation/SKILL.md` (all 11 optimizations) and `agent/skills/skill-ontology-lessons/SKILL.md` (one targeted addition for optimization 7). The skill files are LLM instruction documents loaded at runtime as `tool_context`-accessible skills; changes take effect immediately on the next agent run.

The structural reference is `agent/skills/skill-ontology-generation/SKILL.md`, which already exhibits the target shape: Exit Protocol at top, numbered workflow steps with labeled sub-steps, Fixing Strategy section, lessons step, Available tools, Stop conditions, and Success Exit Summary. The validator skill should mirror that organization after this phase.

The 11 optimizations fall into five categories: structural clarity (1, 2, 3), defensive reading (4, 9), constraint tightening (5), graduated escalation (6, 7, 8), and document organization (10, 11). All decisions on placement, phrasing scope, and tier boundaries are locked in CONTEXT.md.

**Primary recommendation:** Rewrite `skill-ontology-validation/SKILL.md` top-to-bottom using the generator skill as the structural template. Do not patch the existing 62-line file in place — a full rewrite is cleaner given the scope of changes.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Instruction granularity (optimizations 1, 3, 4)**
- Step 4 is broken into explicit numbered sub-steps: 4a, 4b, 4c, 4d — covering: extract class names → search_class_mapping → read_python_files → fix + write.
- Sub-steps 4a–4d apply when errors share the same root cause — they are one group within the loop.
- Retry escalation (#6) uses independent numbered tiers, NOT sub-steps of 4a–4d. Each tier is a standalone rule with its own trigger count and required action.

**Retry escalation tiers (optimization 6)**
- After 3 consecutive same-error attempts: re-read library source (steps 4b–4c) AND examples (`scan_python_folder`) before next attempt. Do not retry with the same fix strategy.
- After 5 consecutive same-error attempts: re-read `skill-ontology-lessons` specifically for the failing error category.
- After 10 consecutive same-error attempts: call `exit_validator_failure`.
- Presented as a dedicated "Retry Escalation" block, separate from the main loop steps.

**Error classification placement (optimization 11)**
- Inline within the Fixing Strategy section — not a standalone top-level section.
- Two categories documented inline:
  - Python execution errors: non-zero returncode, traceback in stderr, has line number → look up line in ontology, then library source.
  - Library semantic/validation errors: errors in stdout, no line number, only class/method name → look up class in search_class_mapping, read library source, cross-reference examples.
- Note added: "Always check both stdout and stderr before classifying."

**Pre-write verification (optimization 9)**
- Advisory only — listed as a note in Fixing Strategy, not a formal workflow sub-step.
- Phrasing: "Before calling write_ontology, re-read the specific section(s) you modified and confirm: (a) valid Python syntax, (b) fix addresses the identified root cause, (c) no adjacent code inadvertently changed."

**Scope of skill files**
- Primary file: `agent/skills/skill-ontology-validation/SKILL.md` — all 11 optimizations applied.
- Supporting file: `agent/skills/skill-ontology-lessons/SKILL.md` — add a note that lessons should be targeted by error category keyword, not re-read in full (optimization 7).
- No changes to `skill-ontology-generation/SKILL.md`.
- No Python code changes.

**Plan structure**
- Single plan — all 11 optimizations in one SKILL.md rewrite.

### Claude's Discretion
- Exact wording of each new instruction block
- Whether to use blockquotes, code blocks, or prose for the new Fixing Strategy additions
- Ordering of sections within the new Fixing Strategy (error classification first, then constraint, then pre-write note, then root-cause ordering)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Standard Stack

### Core
| File | Current State | Action |
|------|--------------|--------|
| `agent/skills/skill-ontology-validation/SKILL.md` | 62-line file; flat workflow, no sub-steps, no escalation, exit protocol buried at bottom in Stop Conditions | Full rewrite applying all 11 optimizations |
| `agent/skills/skill-ontology-lessons/SKILL.md` | 36-line file; flat error-to-resolution list in 6 category sections | Targeted addition: one-line consultation guidance note |

### Supporting Reference
| File | Role |
|------|------|
| `agent/skills/skill-ontology-generation/SKILL.md` | Structural model — copy section order, Exit Protocol phrasing, sub-step format |
| `agent/tools/ontology_tools.py` | Tool behavior reference — understand exact signatures and return shapes before writing tool instructions |
| `agent/tools/ontology_exit_tools.py` | Exit tool signatures — `exit_validator_success(summary="...")`, `exit_validator_failure(reason="...")` |

### No Installation Needed
This phase is pure text editing. No packages, no commands.

---

## Architecture Patterns

### Target Section Order for Rewritten Validator SKILL.md

Based on generator skill structure (HIGH confidence — file read directly):

```
---
name: skill-ontology-validation
description: ...
---

# 223P Ontology Validator & Fixer Agent

## Role

## Exit Protocol          ← optimization 10: elevated to TOP

## Workflow
  Step 0 — Preparation (run once)
  Fix loop:
    Step 1 — Read full ontology
    Step 2 — Execute ontology
    Step 3 — Success path → exit_validator_success
    Step 4 — Error path: fix (sub-steps 4a–4d)
    Step 5 — Loop back to step 2

  Retry Escalation        ← optimization 6: standalone block

## Fixing Strategy        ← optimizations 5, 9, 11 all land here
  Error Classification    ← optimization 11: inline
  Constraints             ← optimization 5: minimum-change rule
  Root-Cause Ordering     ← optimization 8: ordering guidance
  Pre-Write Verification  ← optimization 9: advisory note

## Available Skills and Tools

## Operator Reference

## Stop Conditions → exit_validator_failure

## Success Exit Summary
```

### Pattern 1: Exit Protocol at Top (optimization 10)

The generator SKILL.md uses this exact phrasing (HIGH confidence — verified in file):

```markdown
## Exit Protocol
The ONLY valid way to signal completion is to call `exit_validator_success(summary="...")` or `exit_validator_failure(reason="...")`.
```

Apply the same block to the validator, adapted to validator tool names. This prevents the agent from stopping mid-loop by returning text instead of calling an exit tool.

### Pattern 2: Sub-Steps 4a–4d (optimizations 1, 3)

Mirror the generator's steps 2–4 structure, adapted for the error-fix context:

```markdown
**Step 4 — Fix errors (when errors share the same root cause):**

- **4a. Extract class/method names** from the error message.
- **4b. Look up library source** — Call `search_class_mapping(keywords=[<names from 4a>])` to get absolute file paths.
- **4c. Read library source** — Call `read_python_files(<paths from 4b>, keywords=[<names from 4a>])`.
- **4d. Re-read the error location** — Call `read_python_files(["mapper/uploads/python/latest_ontology.py"], keywords=[<names from 4a>])` to read the specific lines before modifying them. Then fix the root cause and call `write_ontology` with the full corrected file.
```

Note: optimization 4 (re-read error location before fixing) is embedded in 4d as the pre-fix read step.

### Pattern 3: scan_python_folder Conditional but Explicit (optimization 2)

The current skill mentions `scan_python_folder` only in the Available Tools section. After the rewrite, it appears explicitly in Step 0 as an optional enrichment step and in the Retry Escalation tier-3 trigger:

```markdown
**Step 0 — Preparation (run once):**
1. Load `skill-ontology-lessons` — apply every lesson to your fixing strategy.
2. **Optional but recommended:** Call `scan_python_folder("agent/223p/examples/pritoni", keywords=[...])` for the equipment classes present in the ontology, to build a reference library of valid usage patterns before the fix loop begins.
```

### Pattern 4: Retry Escalation Tiers (optimization 6)

Standalone block after the fix loop, separate from sub-steps. Three independent tiers with explicit trigger counts:

```markdown
## Retry Escalation

Track consecutive fix attempts for each distinct error signature.

| Threshold | Action |
|-----------|--------|
| After 3 consecutive same-error attempts | Re-read library source (4b–4c) AND call `scan_python_folder` for the failing class before the next attempt. Do not retry with the same fix strategy. |
| After 5 consecutive same-error attempts | Load `skill-ontology-lessons` and search specifically for the failing error category keyword. |
| After 10 consecutive same-error attempts | Call `exit_validator_failure(reason="VALIDATION_FAILED: same error after 10 attempts — escalate to human review")`. |
```

### Pattern 5: Mid-Loop Lessons Re-Consultation (optimization 7)

Add a conditional instruction in the Fix loop (between step 3 and step 4) and a matching note in skill-ontology-lessons/SKILL.md:

Fix loop trigger (validator SKILL.md):
```markdown
If a **new error type** appears that was not present in earlier iterations: reload `skill-ontology-lessons` and search for the error category keyword before proceeding to step 4.
```

skill-ontology-lessons/SKILL.md addition:
```markdown
> **Consultation note:** When re-consulting mid-loop, search by error category keyword (e.g., "Sensor API", "Connection wiring") — do not re-read the full file. Target the relevant category section only.
```

### Pattern 6: Fixing Strategy Section (optimizations 5, 8, 9, 11)

The Fixing Strategy section expands from the current 4-bullet list to a structured subsection with four components in this order (Claude's discretion per CONTEXT.md):

1. **Error Classification** (inline) — two categories with stdout/stderr guidance
2. **Minimum-Change Constraint** — do not restructure unrelated sections
3. **Root-Cause Ordering** — when multiple root causes exist, fix the deepest dependency first (import errors before instantiation errors before connection errors)
4. **Pre-Write Verification** (advisory note) — three checks before `write_ontology`

### Lessons SKILL.md Pattern

The lessons file uses a flat format: `## Category` headers with `- **Error:** ... -> **Fix:** ...` lines. Any additions must follow this format. The only change for this phase is a consultation guidance note, best placed at the top of the file after the intro paragraph.

### Anti-Patterns to Avoid

- **Patching the existing 62-line file incrementally:** Given 11 changes distributed across the whole document, in-place patching creates inconsistent section ordering. A full rewrite is safer.
- **Burying exit protocol in Stop Conditions:** The current file does this — the rewrite must move the Exit Protocol to its own section at the top.
- **Making scan_python_folder mandatory in every loop iteration:** optimization 2 says conditional but explicit — make it recommended in Step 0 and Retry tier-3, not a required loop step.
- **Putting retry escalation as sub-steps of 4a–4d:** Per locked decision, tiers are independent numbered rules, not sub-steps.
- **Re-reading lessons in full during mid-loop (optimization 7):** The consultation note must say "search by category keyword, not re-read in full."

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Tracking retry count | Custom counter logic in skill prose | "Track consecutive fix attempts for each distinct error signature" — the agent manages this in working memory |
| Exit signaling | Text responses or tool-less returns | `exit_validator_success` / `exit_validator_failure` exclusively |
| Class lookup | Hardcoded paths in skill | `search_class_mapping` → `read_python_files` two-step |

---

## Common Pitfalls

### Pitfall 1: Over-specifying the Retry Counter Mechanism
**What goes wrong:** Writing detailed instructions about HOW the agent should count retries (e.g., tracking state variables) rather than WHAT triggers each tier.
**Why it happens:** Researchers conflate the agent's working memory with Python state.
**How to avoid:** State the trigger condition ("after 3 consecutive same-error attempts") and leave the counting to the agent's context window.

### Pitfall 2: Making Error Classification a Top-Level Section
**What goes wrong:** Agent treats classification as a pre-loop decision tree, spending tokens classifying before reading the actual error.
**Why it happens:** Easy to make "Error Classification" a standalone section.
**How to avoid:** Keep it inline within Fixing Strategy per the locked decision. The agent reads errors and classifies as part of fix strategy, not as a separate workflow step.

### Pitfall 3: Ambiguous "Same Error" Definition in Retry Tiers
**What goes wrong:** Agent cannot determine what "same error" means — same exception type? same line number? same message text?
**How to avoid:** Define "distinct error signature" as the combination of error type and class/method name (not line number, since code changes between attempts).

### Pitfall 4: scan_python_folder Cap (10 files)
**What goes wrong:** Skill instructs agent to call `scan_python_folder` with broad keywords, hitting the 10-file cap and getting a message-only response with no file contents.
**Why it happens:** The tool caps at 10 matching files and returns `{"message": "...", "files": []}` above the cap.
**How to avoid:** Skill must instruct agent to use specific class name keywords, not broad category keywords. For Retry tier-3, specify: use the exact class name from the failing error as keyword.

### Pitfall 5: Lessons Re-Read Causing Context Explosion
**What goes wrong:** Agent re-reads the full `skill-ontology-lessons` SKILL.md every iteration, wasting context window tokens.
**Why it happens:** Step 0 loads lessons once, but mid-loop trigger could be misread as "reload everything."
**How to avoid:** Optimization 7 explicitly says targeted by category keyword. The skill prose must be unambiguous: "search for the failing error category keyword — do not re-read in full."

### Pitfall 6: 4d Re-Read vs. Step 1 Re-Read Confusion
**What goes wrong:** Agent reads the ontology at step 1 (full file), then skips the targeted re-read in 4d because it "already read the file."
**Why it happens:** Step 1 uses `full_content=True` for the whole file; 4d uses keyword-targeted read to locate the specific error location in current state.
**How to avoid:** Make step 4d's re-read explicit: "re-read the specific error location in the current file state (the file may have changed since step 1 if earlier sub-loops ran write_ontology)."

---

## Code Examples

Verified from reading the actual skill and tool files:

### Tool Call Chain for Error in Class "Fan"
```
# 4a: extract "Fan" from error
# 4b:
search_class_mapping(keywords=["Fan"])
# → ["/abs/.../bob/equipment/hvac/fan.py"]

# 4c:
read_python_files(["/abs/.../bob/equipment/hvac/fan.py"], keywords=["Fan"])
# → JSON array with sections containing "Fan" class definition

# 4d re-read before fix:
read_python_files(["mapper/uploads/python/latest_ontology.py"], keywords=["Fan"])
# → shows current state of Fan usage in ontology

# Then fix and:
write_ontology(content="<full corrected file>")
```

### execute_ontology Return Shape
```json
{
  "success": false,
  "returncode": 1,
  "stdout": "...",
  "stderr": "Traceback (most recent call last):\n  File \"...\", line 42, in <module>...",
  "ttl_file": null
}
```
- Python execution errors: `returncode != 0`, traceback in `stderr`, has line number
- Library semantic errors: errors in `stdout`, `returncode == 0` is NOT always a clean run; check both

### exit_validator_success Signature (from ontology_exit_tools.py)
```python
exit_validator_success(tool_context, summary="...")
# Pass only the summary string — tool reads TTL from disk internally
# Do NOT pass ttl_content or code= parameters
```

### exit_validator_failure Signature
```python
exit_validator_failure(tool_context, reason="VALIDATION_FAILED: ...")
```

### scan_python_folder Safe Call Pattern
```
# Specific keyword (safe — unlikely to exceed 10-file cap)
scan_python_folder("agent/223p/examples/pritoni", keywords=["Fan"])

# Broad keyword (risky — may return cap message with no files)
scan_python_folder("agent/223p/examples/pritoni", keywords=["import"])
```

---

## State of the Art

| Old Approach | Current Approach | Changed In | Impact |
|--------------|------------------|------------|--------|
| Flat step 4 "analyze errors → fix → write" | Sub-steps 4a–4d with explicit class lookup chain | Phase 18 (this phase) | Agent follows structural procedure rather than improvising lookup |
| Exit protocol buried in Stop Conditions | Exit Protocol elevated to top section | Phase 18 | Agent cannot miss exit protocol; consistent with generator skill |
| No retry escalation | Three-tier graduated escalation (3/5/10 attempts) | Phase 18 | Prevents infinite same-error loops |
| Lessons loaded once at Step 0 | Lessons re-consulted when new error type appears | Phase 18 | Targeted mid-loop consultation without full re-read |
| scan_python_folder only in tool list | Explicit in Step 0 (conditional) and Retry tier-3 | Phase 18 | Agent knows when to invoke examples scan |
| No error classification | Inline error classification in Fixing Strategy | Phase 18 | stdout vs stderr distinction prevents wrong fix strategy |
| No ordering guidance | Root-cause ordering in Fixing Strategy | Phase 18 | Deepest dependency fixed first |
| checkpoint_code tool | Folded into write_ontology (auto-increment) | Phase 16 | write_ontology now auto-checkpoints; skill must NOT reference checkpoint_code |

**Deprecated/Outdated (must not appear in rewritten skill):**
- `checkpoint_code`: removed in Phase 16-02 — write_ontology handles checkpointing automatically
- `code=` parameter in exit calls: removed in Phase 16-02 — pass only `summary=` string
- `skill-read-code` references: removed in Phase 15-03

---

## Open Questions

1. **"Consecutive same-error" definition**
   - What we know: CONTEXT.md specifies 3/5/10 as tier thresholds
   - What's unclear: How to define "same error" in skill prose (same exception type? same class name? same line?)
   - Recommendation: Define as "same error type and same class/method name" — line numbers change between writes so they are not a reliable discriminator

2. **Ordering of sub-steps 4a–4d vs. Retry Escalation block**
   - What we know: Retry Escalation is a standalone block separate from 4a–4d (locked decision)
   - What's unclear: Whether Retry Escalation appears immediately after the fix loop or after the Fixing Strategy section
   - Recommendation: Place Retry Escalation immediately after the fix loop steps (before Fixing Strategy), since it governs loop behavior, not fix technique

---

## Validation Architecture

> config.json has no `workflow.nyquist_validation` key — treated as enabled. However, this phase produces only markdown files. There are no Python modules to unit test. Validation is structural (human review of skill prose) and functional (agent run outcome).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing, used in `agent/tests/`) |
| Config file | none detected — pytest runs from project root |
| Quick run command | `cd /home/juan/codes/si-mapper && python -m pytest agent/tests/ -x -q` |
| Full suite command | `cd /home/juan/codes/si-mapper && python -m pytest agent/tests/ -q` |

### Phase Requirements → Test Map

| ID | Behavior | Test Type | Automated Command | Note |
|----|----------|-----------|-------------------|------|
| OPT-01 through OPT-11 | Skill prose contains correct instruction text | manual-only | N/A | Markdown files have no automated test equivalent |
| Structural | Exit Protocol section exists at top of rewritten SKILL.md | manual-only (grep check) | `grep -n "Exit Protocol" agent/skills/skill-ontology-validation/SKILL.md | head -3` | Should be within first 20 lines |
| Structural | No `checkpoint_code` references in skill files | automated grep | `grep -r "checkpoint_code" agent/skills/` | Must return 0 matches |
| Structural | No `code=` parameter in exit calls in skill files | automated grep | `grep -n "code=" agent/skills/skill-ontology-validation/SKILL.md` | Must return 0 matches |
| Structural | No `skill-read-code` references | automated grep | `grep -r "skill-read-code" agent/skills/` | Must return 0 matches |

### Sampling Rate
- **Per task commit:** `grep -r "checkpoint_code" agent/skills/ && grep -r "skill-read-code" agent/skills/` (structural correctness)
- **Per wave merge:** Full grep battery above + human review of skill prose
- **Phase gate:** Human review confirming all 11 optimizations present in correct positions before `/gsd:verify-work`

### Wave 0 Gaps
None — no new test files needed. Validation is structural grep checks and human prose review. Existing `agent/tests/` suite covers Python tools and is unaffected by this phase.

---

## Sources

### Primary (HIGH confidence)
- Direct file read: `agent/skills/skill-ontology-validation/SKILL.md` — current 62-line file, all sections catalogued
- Direct file read: `agent/skills/skill-ontology-generation/SKILL.md` — structural model, section order verified
- Direct file read: `agent/skills/skill-ontology-lessons/SKILL.md` — current 36-line file, format confirmed
- Direct file read: `agent/tools/ontology_tools.py` — tool signatures, return shapes, cap behavior of scan_python_folder
- Direct file read: `agent/tools/ontology_exit_tools.py` — exit tool signatures confirmed (2-param: tool_context + summary/reason)
- Direct file read: `.planning/phases/18-optimize-skill-for-ontology-validation/18-CONTEXT.md` — all decisions locked

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` — history of Phase 16 decisions (checkpoint_code removal, exit signature changes) corroborates tool file contents

### Tertiary (LOW confidence)
None — all findings verified from primary source files.

---

## Metadata

**Confidence breakdown:**
- Current skill state: HIGH — files read directly
- Target structure: HIGH — generator skill read as reference model
- Tool behavior: HIGH — tool source read directly
- Optimization placement: HIGH — locked in CONTEXT.md
- Pitfalls: HIGH — derived from reading actual tool behavior (cap, signatures)

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable — skill files are the primary artifact, no external dependencies)
