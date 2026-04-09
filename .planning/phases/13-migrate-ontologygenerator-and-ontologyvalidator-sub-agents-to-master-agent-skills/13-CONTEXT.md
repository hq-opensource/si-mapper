# Phase 13: Migrate OntologyGenerator and OntologyValidator sub-agents to master agent skills - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove `OntologyGeneratorAgent` and `OntologyValidatorAgent` as `AgentTool`-wrapped sub-agents from `create_master_agent.py`. Instead, give all their tools directly to `MasterLlmAgent` and convert their per-agent prompts into two new ADK skills (`skill-ontology-generation` and `skill-ontology-validation`). The master agent runs generation and validation itself — in its own loop — fixing the root cause of sub-agent events not streaming to the frontend.

**In scope:**
1. Create `agent/skills/skill-ontology-generation/` — SKILL.md from `ontology_generator/prompt.md` content
2. Create `agent/skills/skill-ontology-validation/` — SKILL.md from `ontology_validator/prompt.md` content
3. Wire all ontology tools directly into `MasterLlmAgent` tool list
4. Create adapted exit tools for the master (EXIT_LEVEL_2, not EXIT_LEVEL_4)
5. Remove the two `AgentTool` sub-agent registrations from `create_master_agent.py`
6. Increase `MasterMainLoopAgent.max_iterations` to 100
7. Update `master_instruction.md` ASHRAE 223P protocol to reference the new skills

**Out of scope:**
- Any changes to `agent/sub_agents/ontology_generator/` or `agent/sub_agents/ontology_validator/` (kept as backup)
- Any changes to `agent/sub_agents/_223p/`
- Frontend changes
- Changes to `checkpoint_code` behavior

</domain>

<decisions>
## Implementation Decisions

### Exit tool behavior — adapted for master (EXIT_LEVEL_2)
- The existing exit tools in `sub_agents/ontology_generator/exit_tools.py` and `sub_agents/ontology_validator/exit_tools.py` set `EXIT_LEVEL_4` and `actions.escalate = True` — designed to break the sub-agent's `LoopWrapper`.
- Create **new adapted exit tools** in a separate location (e.g. `master_architecture/tools/ontology_exit_tools.py`) — do NOT modify the originals (they serve as backup).
- Adapted tools must:
  - Set `EXIT_LEVEL_2 = True` (what `MasterMainLoopAgent.is_loop_finished()` checks for)
  - Call `tool_context.actions.escalate = True` (propagates up through `MasterLlmAgent` to `MasterMainLoopAgent`)
  - Remove the `EXIT_LEVEL_4` flag (no longer relevant)
  - Preserve all state writes (python_code_snapshots, ttl_code_snapshots, ONTOLOGY_GENERATION_SUCCESS, ONTOLOGY_VALIDATION_SUCCESS)
- `checkpoint_code` stays unchanged — it does NOT escalate and does NOT set any exit flags.
- **User flow:** Master runs generator → exit tool fires → master loop terminates → user reviews → user re-triggers for validation. Each phase is a separate master invocation. This is intentional and fine.

### Master loop capacity — 100 iterations
- Increase `MasterMainLoopAgent.__init__` default `max_iterations` from 10 to **100**.
- This covers up to 100 iterations of ontology work (generation or validation) in a single master invocation.

### Prompt organization — two new ADK skills
- `ontology_generator/prompt.md` content becomes `agent/skills/skill-ontology-generation/SKILL.md`
- `ontology_validator/prompt.md` content becomes `agent/skills/skill-ontology-validation/SKILL.md`
- Both skills are auto-loaded by the existing skill-loading loop in `create_master_agent.py` (it walks all dirs under `agent/skills/` that have a `SKILL.md`).
- The master reads skill content as context — no special wiring needed beyond placing the SKILL.md files.
- The `master_instruction.md` ASHRAE 223P Code Generation Protocol section should reference these two skills by name so the master knows to apply them when those tasks are requested.

### Sub-agent file cleanup — keep as backup, unwire only
- Do NOT delete or modify `agent/sub_agents/ontology_generator/` or `agent/sub_agents/ontology_validator/`.
- They stay in place as a fallback if the skills migration needs to be reverted.
- The only change: remove the two `AgentTool` registrations from `create_master_agent.py` (the import + instantiation + `ontology_subagents` list).
- After migration the sub-agent folders are dead code — not imported anywhere — but intentionally kept.

### Claude's Discretion
- Exact file location for adapted exit tools — `master_architecture/tools/ontology_exit_tools.py` is suggested, but planner can choose.
- Whether `exit_generator_failure` and `exit_validator_failure` also set `EXIT_LEVEL_2` or just escalate without setting the flag — implementation detail.
- Whether `read_prompt` is included in the master's tools (it reads the old sub-agent `prompt.md` — now superseded by the skill, so it can be omitted).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Files to replace (sub-agent prompts → skills)
- `agent/sub_agents/ontology_generator/prompt.md` — source content for `skill-ontology-generation/SKILL.md`
- `agent/sub_agents/ontology_validator/prompt.md` — source content for `skill-ontology-validation/SKILL.md`

### Master architecture files to modify
- `agent/master_architecture/create_master_agent.py` — remove ontology sub-agent imports + registrations, add ontology tool list
- `agent/master_architecture/level_2_master_main_loop.py` — increase `max_iterations` from 10 to 100
- `agent/master_architecture/level_3_master_main_llm.py` — reference for tool list wiring pattern
- `agent/master_architecture/prompts/master_instruction.md` — update ASHRAE 223P Code Generation Protocol section

### Exit tools — source for adaptation
- `agent/sub_agents/ontology_generator/exit_tools.py` — copy and adapt (EXIT_LEVEL_4 → EXIT_LEVEL_2); DO NOT modify original
- `agent/sub_agents/ontology_validator/exit_tools.py` — copy and adapt; DO NOT modify original

### Ontology tools (all to be added to master tool list)
- `agent/sub_agents/_223p/tool.py` — contains `scan_python_files_filtered`, `search_class_mapping`, `write_ontology`, `read_ontology`, `execute_ontology`, `read_prompt`
- `agent/sub_agents/ontology_validator/exit_tools.py` — `checkpoint_code` (unchanged, add to master)

### Skill pattern reference
- `agent/skills/skill-read-code/SKILL.md` — reference for SKILL.md format and structure
- `agent/master_architecture/create_master_agent.py` lines 44-59 — skill auto-loading loop (new skills are picked up automatically)

### Prior phase decisions (still binding)
- `.planning/phases/09-integrate-223p-agent-into-master-architecture-via-sub-agent-or-skills/09-CONTEXT.md` — HITL gate, snapshot state shape, `checkpoint_code` no-escalate invariant
- `.planning/phases/11-optimization-of-the-coding-agent/11-CONTEXT.md` — `scan_python_files_filtered` and `search_class_mapping` as the canonical tool pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `create_master_agent.py:44-59` — skill auto-loading loop already handles any new `skills/*/SKILL.md` file; no changes needed for skill discovery
- `checkpoint_code` in `ontology_validator/exit_tools.py` — safe to add directly to master tool list unchanged
- All tools in `_223p/tool.py` are plain Python functions; they already accept `Optional[ToolContext]` so they work when called from master

### Established Patterns
- Master tools are registered in `create_master_agent.py:task_tools` list — same pattern for adding ontology tools
- Adapted exit tools should follow the same structure as `master_architecture/tools/load_ttl_to_neo4j_tool.py`
- Skills auto-loaded from `agent/skills/` — just adding a `SKILL.md` is sufficient

### Integration Points
- `create_master_agent.py:78-82` — remove the `ontology_subagents` block and the two imports
- `create_master_agent.py:61-75` — add ontology tools to `task_tools` list
- `level_2_master_main_loop.py:17` — change `max_iterations=10` to `max_iterations=100`
- `master_instruction.md` — ASHRAE 223P Code Generation Protocol section already exists; update to name the two new skills

### What NOT to touch
- `agent/sub_agents/ontology_generator/` — keep as-is (backup)
- `agent/sub_agents/ontology_validator/` — keep as-is (backup)
- `agent/sub_agents/_223p/` — keep as-is (standalone runner, untouched since Phase 9)

</code_context>

<specifics>
## Specific Ideas

- Skill names: `skill-ontology-generation` and `skill-ontology-validation` — directories under `agent/skills/`
- Adapted exit tools live in a new file `master_architecture/tools/ontology_exit_tools.py` (separate from the originals)
- The master instruction should say something like: "When the user asks to generate the 223P ontology, apply the `skill-ontology-generation` skill and use the ontology tools directly. When the user asks to validate, apply `skill-ontology-validation`."
- `exit_generator_success` and `exit_validator_success` adapted versions set `EXIT_LEVEL_2=True` so the master loop terminates cleanly after each phase — the user re-triggers for the next step

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-migrate-ontologygenerator-and-ontologyvalidator-sub-agents-to-master-agent-skills*
*Context gathered: 2026-03-23*
