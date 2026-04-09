# Phase 19: Standardize agent exit tools across all skills - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning
**Source:** Conversation context capture

<domain>
## Phase Boundary

Replace the 5 fragmented exit tools (`exit_generator_success`, `exit_generator_failure`, `exit_validator_success`, `exit_validator_failure`, `exit_loop_level_2`) with 2 generic tools (`exit_with_success`, `exit_with_failure`). Add explicit exit steps to all 5 skills. Add a one-task-at-a-time rule to the master instruction.

This phase does NOT change how the loop terminates — `EXIT_LEVEL_2 + actions.escalate` remain the mechanism. It only standardizes the interface and removes domain logic from exit tools.

</domain>

<decisions>
## Implementation Decisions

### New tools — `exit_with_success` and `exit_with_failure`

- **New file:** `agent/tools/exit_tools.py`
- **`exit_with_success(tool_context, summary: str) -> dict`**
  - Sets `tool_context.state["EXIT_LEVEL_2"] = True`
  - Sets `tool_context.actions.escalate = True`
  - Logs calling agent name from `tool_context.agent_name`
  - Returns `{"status": "success", "summary": summary}`
- **`exit_with_failure(tool_context, reason: str) -> dict`**
  - Sets `tool_context.state["EXIT_LEVEL_2"] = True`
  - Sets `tool_context.actions.escalate = True`
  - Logs calling agent name from `tool_context.agent_name`
  - Returns `{"status": "failure", "reason": reason}`
- No domain-specific state keys written (no ONTOLOGY_GENERATION_SUCCESS etc.)

### Move snapshot patching out of exit tools

- **Problem:** `exit_validator_success` currently reads the TTL file from disk, patches `python_code_snapshots` to "Final/validated", and appends to `ttl_code_snapshots`. This is domain logic that doesn't belong in an exit tool.
- **Decision:** Move this logic into `execute_ontology` in `agent/tools/ontology_tools.py`. After a successful subprocess run, `execute_ontology` already has the TTL content and knows execution succeeded — it should patch state there.
- **Exact state mutations to move:**
  - Read `mapper/uploads/ttl/latest_ontology.ttl` from disk
  - Patch `python_code_snapshots[-1]["label"] = "Final"` and `["status"] = "validated"`
  - Append to `ttl_code_snapshots`: `{"label": "TTL", "code": ttl_content, "iteration": 0, "status": "validated"}`

### Delete old exit tool files

- **Delete:** `agent/tools/loop_exit_tools.py`
- **Delete:** `agent/tools/ontology_exit_tools.py`
- Both fully replaced by the new `agent/tools/exit_tools.py`

### Registration changes

- **`level_3_master_main_llm.py`:** Replace `exit_loop_level_2` in `default_tools` with `exit_with_success, exit_with_failure`
- **`create_master_agent.py`:** Remove imports and registrations of all 4 ontology exit tools. The two new tools come through `default_tools` and do not need separate registration in `task_tools`.

### Skills — add exit steps

All 5 skills need an explicit final exit step:

**`skill-ductwork`** (currently step 6 = "Summarize your actions"):
- Replace with: call `exit_with_success(summary="...")` — summary must include: duct count registered, corrections made, verification result.
- Failure path: if verification cannot be resolved after 3 correction cycles, call `exit_with_failure(reason="...")`.

**`skill-hvac-equipments`** (currently step 7 = "Summarize your actions"):
- Replace with: call `exit_with_success(summary="...")` — summary must include: equipment count placed, corrections made, verification result.
- Failure path: same 3-cycle rule.

**`skill-bacnet-points`** (currently step 5 ends in prose):
- Add final tool call: `exit_with_success(summary="...")` — summary must include: points extracted, equipment matched, unmatched items.
- Failure path: if CSV cannot be parsed or no equipment matched, call `exit_with_failure(reason="...")`.

**`skill-ontology-generation`** (currently uses `exit_generator_success`/`exit_generator_failure`):
- Replace with `exit_with_success` / `exit_with_failure` — same positions in the workflow.

**`skill-ontology-validation`** (currently uses `exit_validator_success`/`exit_validator_failure`):
- Replace with `exit_with_success` / `exit_with_failure`.
- The snapshot patching (now moved to `execute_ontology`) happens before the exit call — skill workflow does not change structurally.

### Master instruction — one task at a time

- **File:** `agent/master_architecture/prompts/master_instruction.md`
- Add rule: "Execute one skill at a time. After a skill calls `exit_with_success` or `exit_with_failure`, wait for the user to give the next instruction before starting another skill."
- Intent: prevent the agent from chaining ductwork → equipment → ontology unprompted.

### Claude's Discretion

- Exact placement of the new master instruction rule within the file (before or after STOP block — should follow existing doc structure)
- Whether to add `skill_name` as an optional parameter to the exit tools for better traceability (acceptable either way)
- Error handling detail in `execute_ontology` snapshot patching (OSError on TTL read should warn and continue, not block exit)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Exit tool implementations (being replaced)
- `agent/tools/loop_exit_tools.py` — current `exit_loop_level_2`
- `agent/tools/ontology_exit_tools.py` — current 4 ontology exit tools

### Files being modified
- `agent/tools/ontology_tools.py` — `execute_ontology` function (lines ~576+), snapshot patching moves here
- `agent/master_architecture/level_3_master_main_llm.py` — `default_tools` list (line 41)
- `agent/master_architecture/create_master_agent.py` — imports and task_tools (lines 28-33, 94-97)
- `agent/master_architecture/prompts/master_instruction.md` — one-task-at-a-time rule

### Skills being modified
- `agent/skills/skill-ductwork/SKILL.md`
- `agent/skills/skill-hvac-equipments/SKILL.md`
- `agent/skills/skill-bacnet-points/SKILL.md`
- `agent/skills/skill-ontology-generation/SKILL.md`
- `agent/skills/skill-ontology-validation/SKILL.md`

### Loop termination logic (read-only reference)
- `agent/master_architecture/level_2_master_main_loop.py` — `is_loop_finished()` checks `EXIT_LEVEL_2`

</canonical_refs>

<specifics>
## Specific Ideas

- `exit_generator_success` and `exit_loop_level_2` are structurally identical today — both set `EXIT_LEVEL_2=True` and `actions.escalate=True`. The only difference is the parameter name (`summary` vs none) and domain state keys.
- `exit_validator_success` is the only tool with non-exit logic — the TTL read and snapshot patching must move to `execute_ontology` before this refactor can work cleanly.
- Skills that lack exit tools (`skill-ductwork`, `skill-hvac-equipments`, `skill-bacnet-points`) cause the agent to re-enter the loop and invent new actions (e.g., starting equipment extraction after ductwork without being asked).
- The `exit_with_failure` failure path should be triggered after N failed correction attempts, not immediately on first error.

</specifics>

<deferred>
## Deferred Ideas

- Adding `skill_name` as a mandatory parameter to exit tools for structured audit logging — acceptable future improvement, not required for this phase
- Centralized exit state audit log (writing exit events to a session log) — future observability work
- Updating existing unit tests in `test_ontology_tools.py` to cover the new snapshot-patching behavior in `execute_ontology` — included in this phase's scope

</deferred>

---

*Phase: 19-standardize-agent-exit-tools-across-all-skills*
*Context gathered: 2026-04-03 via conversation context capture*
