# Phase 24: Remove Screenshots to the Front End - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove the Playwright/screenshot verification mechanism entirely from the codebase. This includes the tool implementation, test files, pyproject dependency, agent registration, and skill instructions. Trust the agent's first-shot output; humans correct manually if needed.

</domain>

<decisions>
## Implementation Decisions

### Removal scope
- Delete `agent/tools/capture_frontend_state_tool.py` entirely
- Delete `agent/tests/test_capture_frontend_state.py` entirely
- Delete `agent/tests/test_capture_frontend_state_live.py` entirely
- Remove `playwright>=1.40.0` from `agent/pyproject.toml`
- Remove import and registration of `capture_frontend_state_tool` from `agent/master_architecture/create_master_agent.py`

### Skill updates — ductwork
- Remove Step 5 ("Duct Verification Checkpoint") entirely from `skill-ductwork/SKILL.md`
- Renumber Step 6 (Exit) to Step 5
- No correction loop, no retry cycle language

### Skill updates — HVAC equipment
- Remove Step 6 ("Equipment Verification Checkpoint") entirely from `skill-hvac-equipments/SKILL.md`
- Renumber Step 7 (Exit) to Step 6
- No correction loop, no retry cycle language

### Exit summary language (both skills)
- Require: count of components placed + confirmation that `sync_agent_to_graphivac` succeeded
- Example format: "5 ducts registered and synced to frontend (4 horizontal, 1 vertical)"
- Remove: "number of corrections made during verification" and "final verification result (pass/fail)"
- Remove: failure path triggered by unresolvable verification discrepancies

### Verification philosophy
- No agent self-correction loop — agent places, syncs, exits
- Human reviews the result in the frontend and corrects manually if needed
- `master_instruction.md` is already clean — no references to remove there

### Claude's Discretion
- Exact wording of the updated exit summary requirements in SKILL.md
- Whether to add a note in the skills explaining WHY verification was removed (not required)

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above.

### Files to touch
- `agent/tools/capture_frontend_state_tool.py` — delete
- `agent/tests/test_capture_frontend_state.py` — delete
- `agent/tests/test_capture_frontend_state_live.py` — delete
- `agent/master_architecture/create_master_agent.py` — remove import + tool registration
- `agent/pyproject.toml` — remove playwright dependency
- `agent/skills/skill-ductwork/SKILL.md` — remove verification step, update exit
- `agent/skills/skill-hvac-equipments/SKILL.md` — remove verification step, update exit

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `capture_frontend_state_tool` is registered as a singleton in `create_master_agent.py` at line 84 — single removal point

### Established Patterns
- Skills follow numbered execution flow — removing a step requires renumbering subsequent steps
- Exit summaries across all skills use domain-specific bullet requirements (count + outcome) — keep that pattern, just drop the verification bullets

### Integration Points
- `create_master_agent.py` imports `capture_frontend_state_tool` at line 18 and registers it at line 84
- Both skill SKILL.md files reference `capture_frontend_state()` and `load_artifacts` with snapshot artifact paths — `load_artifacts` stays (used for reference drawings), only the snapshot-related calls are removed

</code_context>

<specifics>
## Specific Ideas

- "Trust that the agent did a good job. If there is something to correct, the human will correct it." — this is the guiding principle for the simplified skill instructions.
- Agent is costly to run correction loops on; human correction in the frontend UI is faster and cheaper.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 24-remove-screenshots-to-the-front-end*
*Context gathered: 2026-04-04*
