# Phase 24: Remove Screenshots to the Front End - Research

**Researched:** 2026-04-04
**Domain:** Codebase cleanup — removing Playwright screenshot verification mechanism
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Removal scope
- Delete `agent/tools/capture_frontend_state_tool.py` entirely
- Delete `agent/tests/test_capture_frontend_state.py` entirely
- Delete `agent/tests/test_capture_frontend_state_live.py` entirely
- Remove `playwright>=1.40.0` from `agent/pyproject.toml`
- Remove import and registration of `capture_frontend_state_tool` from `agent/master_architecture/create_master_agent.py`

#### Skill updates — ductwork
- Remove Step 5 ("Duct Verification Checkpoint") entirely from `skill-ductwork/SKILL.md`
- Renumber Step 6 (Exit) to Step 5
- No correction loop, no retry cycle language

#### Skill updates — HVAC equipment
- Remove Step 6 ("Equipment Verification Checkpoint") entirely from `skill-hvac-equipments/SKILL.md`
- Renumber Step 7 (Exit) to Step 6
- No correction loop, no retry cycle language

#### Exit summary language (both skills)
- Require: count of components placed + confirmation that `sync_agent_to_graphivac` succeeded
- Example format: "5 ducts registered and synced to frontend (4 horizontal, 1 vertical)"
- Remove: "number of corrections made during verification" and "final verification result (pass/fail)"
- Remove: failure path triggered by unresolvable verification discrepancies

#### Verification philosophy
- No agent self-correction loop — agent places, syncs, exits
- Human reviews the result in the frontend and corrects manually if needed
- `master_instruction.md` is already clean — no references to remove there

### Claude's Discretion
- Exact wording of the updated exit summary requirements in SKILL.md
- Whether to add a note in the skills explaining WHY verification was removed (not required)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 24 is a pure removal and simplification phase. There is no new code to write. Every change is a deletion, a line removal, or a text edit in a Markdown skill file. The scope is precisely defined in CONTEXT.md with exact file paths, line numbers, and before/after examples.

The Playwright screenshot verification was added in Phase 8. It has since proven expensive and unreliable relative to its benefit: the agent runs Chromium headlessly, takes a screenshot, compares it to the reference drawing, and enters a correction loop. The new philosophy is: agent places components, calls `sync_agent_to_graphivac`, exits. Humans inspect the frontend directly and correct manually if needed.

There are no external dependencies to research. The entire research value is an audit of the current codebase state to confirm exactly what needs to change and to surface any hidden references that CONTEXT.md may have missed.

**Primary recommendation:** Execute all deletions and edits as a single focused plan (one wave, four tasks). Run the existing test suite after changes to confirm no regressions.

---

## Standard Stack

Not applicable — this phase adds no new libraries. It removes one: `playwright>=1.40.0`.

### Packages Removed
| Package | Current Version in pyproject.toml | Action |
|---------|----------------------------------|--------|
| playwright | `>=1.40.0` | Remove from `agent/pyproject.toml` dependencies list |

No installation needed. The `uv` lockfile will update automatically on next `uv sync`.

---

## Architecture Patterns

### Project's Deletion Pattern (established in Phase 15)

Prior phases have deleted modules cleanly. The verified pattern is:
1. Delete the file
2. Remove the import line from `create_master_agent.py`
3. Remove the singleton reference from the `task_tools` list
4. Run the test suite to confirm no import errors

This is exactly what Phase 15 did when deleting `skill-read-code/` and root `223p/`.

### Skill Edit Pattern (established in Phases 16, 18, 19)

Skill SKILL.md files use numbered execution flow. The deletion pattern:
1. Remove the step block entirely (heading + all sub-bullets)
2. Renumber all subsequent steps sequentially
3. Update exit summary bullets to remove deleted step's artifacts
4. Remove the failure path paragraph if it depends on the deleted step

This matches what Phases 19 and 16 did when removing checkpoint_code and simplifying exit tools.

---

## Current State Audit (HIGH confidence — read directly from source)

### Files Confirmed for Deletion

| File | Lines | Content |
|------|-------|---------|
| `agent/tools/capture_frontend_state_tool.py` | 95 | `CaptureFrontendStateTool` class + `capture_frontend_state_tool` singleton |
| `agent/tests/test_capture_frontend_state.py` | 108 | 4 unit tests with mocked Playwright |
| `agent/tests/test_capture_frontend_state_live.py` | 138 | Standalone smoke test (no pytest, runs with `uv run python`) |

### Lines to Remove in create_master_agent.py

Line 18 (import):
```python
from tools.capture_frontend_state_tool import capture_frontend_state_tool
```

Line 84 (task_tools list entry):
```python
        capture_frontend_state_tool,
```

After removal, `load_ttl_to_neo4j_tool` will be the first tool after the internal grid tools block (no comment header change needed).

### pyproject.toml

Line 19:
```
    "playwright>=1.40.0",
```
Remove this line. No other playwright references exist in pyproject.toml.

### skill-ductwork/SKILL.md — Current State

Steps currently are:
- Step 1: Ingest Context
- Step 2: Analyze
- Step 3: Register findings internally
- Step 4: Send ductwork to the frontend
- **Step 5: Verify the ductwork** ← DELETE ENTIRELY
- Step 6: Exit ← RENUMBER to Step 5

Step 5 current text (lines 69-75) references `capture_frontend_state()`, `load_artifacts` with snapshot path, correction loop, and `sync_agent_to_graphivac` retry. All of this is removed.

Step 6 (new Step 5) current exit summary bullets require:
- "Number of ducts registered (horizontal and vertical counts)" ← KEEP
- "Number of corrections made during verification" ← REMOVE
- "Final verification result (pass/fail)" ← REMOVE

The failure path paragraph at line 83 is also removed:
```
**Failure path:** If verification cannot be resolved after 3 correction cycles...
```

New exit summary bullet list (per CONTEXT.md example):
- Count of ducts registered (horizontal and vertical counts)
- Confirmation that `sync_agent_to_graphivac` succeeded

### skill-hvac-equipments/SKILL.md — Current State

Steps currently are:
1. Load context
2. Read grid
3. Analyze
4. Register internally
5. Sync to frontend
**6. Verify** ← DELETE ENTIRELY
**7. Exit** ← RENUMBER to 6

Step 6 current text (lines 26-31) references `capture_frontend_state()`, `load_artifacts` with snapshot, correction loop. All removed.

Step 7 (new Step 6) current exit summary bullets require:
- "Number of equipment pieces placed" ← KEEP
- "Number of corrections made during verification" ← REMOVE
- "Final verification result (pass/fail)" ← REMOVE

The failure path at line 37 is also removed:
```
**Failure path:** If verification cannot be resolved after 3 correction cycles...
```

New exit summary (per CONTEXT.md example):
- Count of equipment pieces placed
- Confirmation that `sync_agent_to_graphivac` succeeded

### master_instruction.md — ALREADY CLEAN

CONTEXT.md confirms `master_instruction.md` has no references to remove. No changes needed there.

---

## Don't Hand-Roll

Not applicable — this is a removal phase. There are no problems being solved with new code.

---

## Common Pitfalls

### Pitfall 1: Orphaned `load_artifacts` References in Skills

**What goes wrong:** The ductwork skill Step 1 also uses `load_artifacts` for reference drawings (not snapshots). Removing Step 5 text could accidentally remove the Step 1 instruction to note artifact names.

**Why it happens:** Both the snapshot call (removed) and the reference drawing call (kept) use `load_artifacts`. The phrase "Note the artifact names returned — you will need them in the verification step" in Step 1 refers to the now-deleted verification step.

**How to avoid:** After removing Step 5, also update Step 1 to remove the forward reference to verification. The artifact name note in Step 1 of skill-ductwork is: "Note the artifact names returned — you will need them in the verification step." This can be simplified or removed since verification is gone.

**Warning signs:** Step 1 still references "the verification step" after Step 5 is deleted.

### Pitfall 2: Stale Test for capture_frontend_state_tool Import in test_create_master_agent.py

**What goes wrong:** `test_create_master_agent.py` contains AST-based and text-based tests that verify what IS and IS NOT imported. After removing `capture_frontend_state_tool`, a new test should confirm it is gone.

**Severity:** LOW — the existing test file has no test that asserts `capture_frontend_state_tool` IS imported, so deletion alone does not break tests. However, adding a regression guard is a good pattern.

**How to avoid:** Add a test assertion `"capture_frontend_state_tool" not in src` to `test_create_master_agent.py` — consistent with the existing `test_no_ontology_generator_agent_import` pattern.

### Pitfall 3: snapshots Directory

**What goes wrong:** `capture_frontend_state_tool.py` writes to `mapper/uploads/snapshots/`. After the tool is deleted, this directory becomes orphaned but harmless. The live test also wrote there.

**How to avoid:** No action required — the directory, if it exists, causes no issues. It is not tracked in git (uploads/ is gitignored). Document this as a non-issue.

### Pitfall 4: skill-hvac-equipments Note Reference After Step Removal

**What goes wrong:** Step 1 of skill-hvac-equipments says "Note the artifact names of the reference drawings — you will need them in the verification step." After Step 6 is deleted, this forward reference is stale.

**How to avoid:** Remove the parenthetical "(you will need them in the verification step)" from Step 1 while keeping the instruction to `load_artifacts`.

---

## Code Examples

### Pattern: Removing an import + singleton from create_master_agent.py

Established by Phase 16-02 when `checkpoint_code` was removed. The pattern is:
1. Remove the `from tools.X import Y` import line
2. Remove `Y,` from the `task_tools` list
3. Verify no other reference to Y remains in the file

Current `create_master_agent.py` after this phase should have `load_ttl_to_neo4j_tool` as the first tool after the internal grid block (line 85 currently), with no gap or comment needed.

### Pattern: Skill step deletion with renumbering

From Phase 19-02 (exit tool skill updates). Numbered steps are plain `## N. Title` headings in SKILL.md files. Renumbering means changing `## 6.` to `## 5.` in skill-ductwork and `## 7.` to `## 6.` in skill-hvac-equipments. No other structural changes are needed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Agent self-verification loop (Phase 8) | Human reviews frontend, corrects manually | Phase 24 | Simpler skills, no Playwright dep, faster agent exit |
| Screenshot artifact in `verification/latest_snapshot.png` | No screenshot artifact | Phase 24 | load_artifacts calls for snapshot path no longer valid |

---

## Open Questions

None. All details are fully specified in CONTEXT.md and verified against source files.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `agent/pyproject.toml` (tool.pytest.ini_options) |
| Quick run command | `cd agent && uv run pytest tests/test_create_master_agent.py -x -q` |
| Full suite command | `cd agent && uv run pytest tests/ -x -q --ignore=tests/test_capture_frontend_state_live.py` |

### Phase Requirements → Test Map

No formal REQ-IDs for this phase. The behavioral requirements are:

| Behavior | Test Type | Automated Command | Notes |
|----------|-----------|-------------------|-------|
| `capture_frontend_state_tool` not imported in create_master_agent.py | static/text | `pytest tests/test_create_master_agent.py -x -q` | Add assertion to existing test file |
| playwright not in pyproject.toml | static/text | grep check or text assertion | Simple file read check |
| skill-ductwork Step 5 removed, no `capture_frontend_state` reference | static/text | grep for "capture_frontend_state" in SKILL.md | Should return 0 matches |
| skill-hvac-equipments Step 6 removed, no `capture_frontend_state` reference | static/text | grep for "capture_frontend_state" in SKILL.md | Should return 0 matches |
| Full test suite still passes (no regressions) | regression | `cd agent && uv run pytest tests/ -x -q --ignore=tests/test_capture_frontend_state_live.py` | After all files deleted |

### Sampling Rate
- **Per task commit:** `cd agent && uv run pytest tests/test_create_master_agent.py -x -q`
- **Per wave merge:** `cd agent && uv run pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Add `test_no_capture_frontend_state_import` assertion to `agent/tests/test_create_master_agent.py` — confirms removal is permanent (regression guard matching existing pattern)

---

## Sources

### Primary (HIGH confidence)
- Direct file reads: `agent/tools/capture_frontend_state_tool.py` — full content confirmed
- Direct file reads: `agent/master_architecture/create_master_agent.py` — import at line 18, registration at line 84
- Direct file reads: `agent/pyproject.toml` — `playwright>=1.40.0` at line 19
- Direct file reads: `agent/skills/skill-ductwork/SKILL.md` — Step 5 at lines 69-83, Step 6 at lines 77-83
- Direct file reads: `agent/skills/skill-hvac-equipments/SKILL.md` — Step 6 at lines 26-31, Step 7 at lines 32-37
- Direct file reads: `agent/tests/test_capture_frontend_state.py` — 4 tests, all import from `tools.capture_frontend_state_tool`
- Direct file reads: `agent/tests/test_capture_frontend_state_live.py` — standalone smoke test, no pytest

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` decisions log — Phase 08-01 and 08-02 context confirming original implementation choices

### Tertiary (LOW confidence)
None.

---

## Metadata

**Confidence breakdown:**
- Removal scope: HIGH — read directly from every file to be changed
- Skill edit content: HIGH — current step text verified line by line
- Pitfalls: HIGH — derived from direct inspection of cross-references (load_artifacts in Step 1)
- Test strategy: HIGH — existing test pattern in test_create_master_agent.py confirmed

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stable — no external dependencies)
