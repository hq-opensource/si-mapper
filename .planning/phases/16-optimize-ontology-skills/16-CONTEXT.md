# Phase 16: Optimize Ontology Skills — Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 21 identified issues in the ontology generation and validation pipeline. Scope is limited to:
- Correctness bugs in `ontology_tools.py` and `ontology_exit_tools.py`
- Token waste from redundant code passing and unbounded file scanning
- Redundant file writes from `_persist_python` and `_persist_ttl` helper functions
- Agent clarity issues in `skill-ontology-generation/SKILL.md` and `skill-ontology-validation/SKILL.md`
- Stale docstrings and SKILL.md prose

No new capabilities. No new tools. No new skills.

</domain>

<decisions>
## Implementation Decisions

### Signature breaking changes
- **Clean break only** — no backward-compatible defaults, no deprecation shims.
- `exit_generator_success(tool_context, summary)` — `code=` parameter removed entirely.
- `exit_validator_success(tool_context, summary)` — both `code=` and `ttl_content=` parameters removed; the function reads the TTL from disk internally.
- If any existing call site passes these parameters, it breaks — fix the call site, do not add defaults to mask the error.

### scan_python_folder cap behavior
- If keyword matches **> 10 files**: return a plain-text message only — no code. Message format: `"There are N files matching these keywords. Narrow your keywords and try again."`
- If keyword matches **≤ 10 files**: return file contents as before.
- **Retry protection**: the agent is expected to refine keywords and retry. If after 2 narrowing attempts the count is still > 10, return the top 10 matches (by alphabetical order or relevance). Implementation mechanism for tracking retries (e.g., a `force: bool` flag or an `attempt: int` counter) is Claude's discretion.
- The goal is to prevent the agent from consuming large token counts on broad scans before narrowing.

### Helper function deletion
- `_persist_python` and `_persist_ttl` in `ontology_exit_tools.py` are deleted entirely.
- All call sites removed: `write_ontology`, `execute_ontology`, `exit_generator_success`, `exit_validator_success`.
- The import line `from tools.ontology_exit_tools import _persist_python, _persist_ttl` in `ontology_tools.py` is removed.
- No replacement — the two-folder structure (`mapper/uploads/` for frontend, `agent/223p/*/session_N/` for history) already covers all persistence needs.

### checkpoint_code consolidation
- `checkpoint_code` is deleted as a standalone agent-callable tool.
- Its logic (append snapshot to `python_code_snapshots`, increment `ontology_code_iteration_count`) is moved inside `write_ontology` so it runs automatically on every write.
- Removed from `create_master_agent.py` tool registration.
- Validation SKILL.md updated to remove the `checkpoint_code` instruction.

### Test strategy
- Claude's discretion — update existing tests in `test_ontology_tools.py` or replace them, whichever is cleaner given the scope of signature changes.
- Tests must cover: `write_ontology` auto-increments counter, `exit_generator_success` and `exit_validator_success` no longer accept removed params, `execute_ontology` resolves Linux venv path, `scan_python_folder` returns message-only above cap.

### SKILL.md structure
- Keep existing numbered-step format; do not restructure.
- Add `## Exit Protocol` section near the top of generation SKILL.md.
- Add numbered `Step 0 — Preparation (run once)` before the fix loop in validation SKILL.md.
- Stale path references and ambiguous `%` operator descriptions updated in-place.

### Claude's Discretion
- Exact retry mechanism for `scan_python_folder` (force flag vs attempt counter)
- Whether to update existing tests or write new ones alongside
- Ordering of how to sort/select "top 10" when the retry protection triggers

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Tool implementations
- `agent/tools/ontology_tools.py` — `write_ontology`, `execute_ontology`, `scan_python_folder`, `search_class_mapping`
- `agent/tools/ontology_exit_tools.py` — `exit_generator_success`, `exit_validator_success`, `checkpoint_code`, `_persist_python`, `_persist_ttl`

### Skills
- `agent/skills/skill-ontology-generation/SKILL.md` — generation workflow, exit protocol, `%` operator rules
- `agent/skills/skill-ontology-validation/SKILL.md` — fix loop, preparation step, available tools section
- `agent/skills/skill-ontology-lessons/SKILL.md` — Sensor API lesson with `%` operator entry

### Tests
- `agent/tests/test_ontology_tools.py` — existing coverage to update

### Agent wiring
- `agent/master_architecture/create_master_agent.py` — tool registration (remove `checkpoint_code`)

### Plan (detailed task breakdown)
- `.planning/phases/16-optimize-ontology-skills/PLAN.md` — 11 tasks with execution order

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tool_context.state["python_code_snapshots"]` — list already used for iteration tracking; `checkpoint_code` logic appends to it; moving this into `write_ontology` reuses the same state key
- `tool_context.state["ontology_code_iteration_count"]` — single counter, incremented only by `checkpoint_code`; move increment to `write_ontology`
- `tool_context.state["ontology_session_id"]` — session ID auto-detection from disk already in `write_ontology`; no changes needed

### Established Patterns
- Three-write pattern (Phase 15): primary write + session archive + uploads. After deleting `_persist_python`/`_persist_ttl`, the pattern reduces to two-write: primary + session archive. Uploads write is handled by the primary write (same path).
- TDD pattern: all prior tool additions used test-first (see phase 11 history). This phase updates existing tests.
- Exit tool pattern: `EXIT_LEVEL_2 = True` + `tool_context.actions.escalate = True` — unchanged; only parameters removed.

### Integration Points
- `create_master_agent.py` — tool list must have `checkpoint_code` removed
- `exit_validator_success` reads `mapper/uploads/ttl/latest_ontology.ttl` — this file is written by `execute_ontology` before `exit_validator_success` is called, so it will always exist when the exit is triggered
- `scan_python_folder` is called from both SKILL.md files — cap behavior affects both skills

</code_context>

<specifics>
## Specific Ideas

- For `scan_python_folder` message when over limit: make the count explicit — "22 files match 'fan'. Narrow your keywords." so the agent knows how far over the limit it is.
- The `exit_validator_success` TTL read path: `mapper/uploads/ttl/latest_ontology.ttl` — same constant as `TTL_OUTPUT_DIR / "latest_ontology.ttl"` already used in `execute_ontology`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-optimize-ontology-skills*
*Context gathered: 2026-04-03*
