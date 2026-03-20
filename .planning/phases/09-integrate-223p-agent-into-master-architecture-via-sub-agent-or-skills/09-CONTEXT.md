# Phase 9: Integrate 223P Agent into Master Architecture — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Promote the existing 223P ontology pipeline from a standalone runner into two flat, independent sub-agents that the Master Agent can delegate to directly. Scope:

1. Create two new sub-agent folders (do NOT modify `sub_agents/_223p/`)
2. Wire both as sub-agents in `create_master_agent.py`
3. Update `master_instruction.md` with the HITL trigger protocol
4. Save generated code string to `ToolContext.state` for frontend rendering
5. Add a "Code" tab to the frontend that displays the ontology code from state

**Out of scope for Phase 9 (deferred to Phase 10):**
- Neo4j / graph database setup (docker-compose)
- "Graph" tab in the frontend showing the TTL visualization
- Any changes to how the TTL file is stored on disk

</domain>

<decisions>
## Implementation Decisions

### Integration mechanism — two flat sub-agents, not SequentialAgent
- Do NOT use `Ontology223PSequentialAgent` or any `SequentialAgent` wrapper.
- Create **two independent `LoopWrapper` sub-agents**: the generator and the validator.
- The Master Agent itself decides the sequence: "generate code → then validate."
- This keeps both agents flat, directly accessible, and easy to swap to skills later if needed.
- Both agents are passed in the `subagents` list to `create_master_agent.py` (same pattern as other sub-agents).

### New folder names
- `agent/sub_agents/ontology_generator/` — code generation agent
- `agent/sub_agents/ontology_validator/` — code validation + fix agent
- Do NOT touch `agent/sub_agents/_223p/` — it remains untouched as the standalone runner.
- New folders mirror the internal structure of `_223p/generator/` and `_223p/validator/` respectively: `agent.py`, `prompt.md`, `__init__.py`.
- Reuse prompts and tool lists from the existing agents as the starting point.

### Trigger condition — HITL human instruction
- The master does NOT auto-trigger the 223P pipeline after visual verification.
- Trigger is explicit: the human completes HITL verification of ductwork + equipment + BACnet + control points, then explicitly says "create the code" (or equivalent).
- Only then does the master delegate first to `ontology_generator`, then (if successful) to `ontology_validator`.
- `master_instruction.md` must include a clear section: "When the human asks to generate the ASHRAE 223P ontology, delegate to `ontology_generator`. After it completes successfully, delegate to `ontology_validator`."

### Data handoff — versioned snapshot list in ToolContext.state
The validator runs in a loop (up to 100 iterations), applying a fix per iteration. Each iteration is a meaningful code version. The state stores a **list of snapshots** so the frontend can browse all versions.

**State key:** `ontology_code_snapshots` — a list of dicts, append-only, never overwritten:
```python
[
  {"label": "Initial",  "code": "...", "iteration": 0, "status": "generated"},
  {"label": "Fix 1",    "code": "...", "iteration": 1, "status": "fix"},
  {"label": "Fix 2",    "code": "...", "iteration": 2, "status": "fix"},
  {"label": "Final",    "code": "...", "iteration": 3, "status": "validated"},
]
```

**How snapshots are appended:**
- **Generator** (`exit_loop_generator_success`): appends `{"label": "Initial", "code": <code>, "iteration": 0, "status": "generated"}`.
- **Validator** — each iteration where it rewrites `ontology.py`, it calls a new `checkpoint_code` tool that appends `{"label": "Fix N", "code": <current_code>, "iteration": N, "status": "fix"}`. The validator calls this tool explicitly after each successful `write_ontology` call.
- **Validator** (`exit_loop_validator_success`): patches the last snapshot's `"status"` to `"validated"` and `"label"` to `"Final"`, then escalates.

**Why `checkpoint_code` is a separate tool (not baked into `write_ontology`):**
- `write_ontology` is shared with the generator and `_223p/`; modifying it would break those.
- An explicit tool call is predictable and visible in the agent's tool call log.
- The validator already calls `write_ontology` when it fixes errors — `checkpoint_code` is the next call in that same turn.

**Iteration counter:** `ontology_code_iteration_count` — an integer in state, incremented by `checkpoint_code` each time it is called. Used to set `"iteration": N` in each snapshot.

**TTL file:** continues to be written to disk at `223p/ttl/ontology.ttl` (unchanged from current behavior).

### Exit tools — per-agent, not shared with _223p
- `ontology_generator/exit_tools.py`:
  - `exit_generator_success(tool_context, code: str, summary: str)` — appends Initial snapshot + sets `ONTOLOGY_GENERATION_SUCCESS = True` + escalates.
  - `exit_generator_failure(tool_context, reason: str)` — sets `ONTOLOGY_GENERATION_SUCCESS = False` + escalates.
- `ontology_validator/exit_tools.py`:
  - `checkpoint_code(tool_context, code: str)` — appends a Fix N snapshot, increments `ontology_code_iteration_count`. Does NOT escalate (validator loop continues).
  - `exit_validator_success(tool_context, code: str, summary: str)` — calls `checkpoint_code` internally, patches last snapshot label to "Final" / status to "validated", escalates.
  - `exit_validator_failure(tool_context, reason: str)` — escalates with failure flag.
- Do NOT import from `sub_agents/_223p/exit_tools.py`.

### Frontend — Code tab with version selector
- Add `'code'` to the tab union type in `AgentNavbar.tsx` and `YourMainContent.tsx`.
- Create `mapper/src/app/page/components/CodeWindow.tsx`:
  - Reads `ontology_code_snapshots` from agent state.
  - Shows a tab/pill row at the top: `Initial | Fix 1 | Fix 2 | Final` — user clicks to switch.
  - The selected snapshot's `code` is rendered below in a `<pre><code>` block (or syntax-highlighted if a highlighting lib is already in the project).
  - Shows placeholder "No ontology code generated yet" when `ontology_code_snapshots` is absent or empty.
  - Defaults to showing the last snapshot in the list (most recent version).
- The frontend Graph tab already exists but is deferred — leave it as-is for Phase 9.

### Sub-agent wiring in create_master_agent.py
- Instantiate both new agents and pass them in the `subagents` parameter:
  ```python
  from sub_agents.ontology_generator.agent import OntologyGeneratorAgent
  from sub_agents.ontology_validator.agent import OntologyValidatorAgent

  subagents = [OntologyGeneratorAgent(model_name=model_name), OntologyValidatorAgent(model_name=model_name)]
  ```
- The `subagents` parameter already exists in `create_master_agent` — just populate it.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing agents to mirror (source of truth for structure)
- `agent/sub_agents/_223p/generator/agent.py` — exact pattern for `OntologyGeneratorAgent`: `LoopWrapper` wrapping an `LlmAgent`, `load_prompt_instruction`, `before_model_callback`, `after_model_callback`, tool deduplication.
- `agent/sub_agents/_223p/validator/agent.py` — exact pattern for `OntologyValidatorAgent`: same structure, `execute_ontology` + `read_ontology` + `write_ontology` tools.
- `agent/sub_agents/_223p/exit_tools.py` — source for exit tool pattern; copy and adapt into new `exit_tools.py` files in each new folder.
- `agent/sub_agents/_223p/tool.py` — all shared tool functions to import into new agents.

### Master agent wiring
- `agent/master_architecture/create_master_agent.py` — the `subagents` parameter is already defined but currently defaults to `None`; populate it with the two new agents.
- `agent/master_architecture/prompts/master_instruction.md` — add "ASHRAE 223P Code Generation Protocol" section after the Visual Verification Protocol.

### Frontend tab pattern
- `mapper/src/app/page/components/AgentNavbar.tsx` — existing tab list to extend with `'code'`.
- `mapper/src/app/page/components/StateWindow.tsx` — reference for reading agent state in a tab component.
- `mapper/src/app/page/components/YourMainContent.tsx` — where to add the `case 'code':` branch for rendering `<CodeWindow />`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- `LoopWrapper` (`sub_agents/loop_agents/loop_wrapper.py`) — ready to use; terminates on `EXIT_LEVEL_4` flag or `max_iterations`.
- `shared_model_callback`, `shared_before_model_callback` (`utils/callback_utils.py`) — already used by all existing agents; use the same imports.
- `get_adk_model` (`utils/models.py`) — already handles model string → ADK model conversion.
- `load_prompt_instruction` (`utils/prompt_utils.py`) — loads `.md` prompt files by path string relative to `agent/`.
- `skills_toolset` from `sub_agents/_223p/tool.py` — already wired into the existing agents; reuse.

### Exit tool pattern (state flag + escalate)
- All exit tools follow: set state flags → `tool_context.actions.escalate = True` → return dict.
- `checkpoint_code` does NOT escalate — it only appends to `ontology_code_snapshots` and increments `ontology_code_iteration_count`.
- `exit_generator_success` appends the Initial snapshot + sets `ONTOLOGY_GENERATION_SUCCESS = True` + escalates.
- `exit_validator_success` patches the last snapshot to "Final"/"validated" + escalates.

### Frontend state reading pattern
- The frontend reads agent state via the `useThoughts` context or equivalent state context.
- `StateWindow.tsx` shows the full state dict; `CodeWindow.tsx` extracts `state.ontology_code_snapshots`.
- The `'code'` tab ID must be added to the TypeScript union type in both `AgentNavbar.tsx` and `YourMainContent.tsx`.
- Version selector UI: pill/tab row built from `snapshots.map(s => s.label)` — selected index defaults to `snapshots.length - 1` (latest).

### _223p folder — DO NOT MODIFY
- `sub_agents/_223p/` stays untouched. It is the standalone runner and remains valid for `python -m sub_agents._223p.run pipeline`.
- All new code goes into `sub_agents/ontology_generator/` and `sub_agents/ontology_validator/`.

</code_context>

<specifics>
## Specific Details

- New agent class names: `OntologyGeneratorAgent` (in `ontology_generator/agent.py`) and `OntologyValidatorAgent` (in `ontology_validator/agent.py`).
- Internal LlmAgent names: `"OntologyGeneratorInternal"` and `"OntologyValidatorInternal"` (avoids collision with the identically-named classes in `_223p/`).
- LoopWrapper names: `"OntologyGeneratorAgent"` and `"OntologyValidatorAgent"` (these are the names the master sees).
- Generator max iterations: 50 (same as existing). Validator max iterations: 100 (same as existing).
- Model default: `"github_copilot/claude-sonnet-4.5"` (same as `_PIPELINE_MODEL` in `_223p/agent.py`).
- `master_instruction.md` section title: **"ASHRAE 223P Code Generation Protocol"** — placed after the Visual Verification Protocol section.
- The master instruction should say: after HITL sign-off, wait for the human to explicitly request ontology generation. Then: (1) delegate to `OntologyGeneratorAgent`, (2) if `ONTOLOGY_GENERATION_SUCCESS` is True in state, delegate to `OntologyValidatorAgent`, (3) confirm to human that ontology.py and ontology.ttl have been generated.
- Code tab icon: `Code2` from lucide-react (not already used in the navbar).
- State keys: `ontology_code_snapshots` (list of snapshot dicts), `ontology_code_iteration_count` (int, starts at 0).
- Snapshot dict shape: `{"label": str, "code": str, "iteration": int, "status": "generated"|"fix"|"validated"}`.
- `checkpoint_code` tool signature: `checkpoint_code(tool_context: ToolContext, code: str) -> dict` — reads current `ontology_code_iteration_count`, builds snapshot, appends, increments counter.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 10: Neo4j + Graph tab** — Create a `docker-compose.yml` service for Neo4j, load `223p/ttl/ontology.ttl` into it after generation, and wire the existing "Graph" tab in the frontend to visualize the Neo4j graph.
- **Skills refactor** — Once both sub-agents are working, consider converting them to ADK skills if the skill pattern proves more ergonomic for delegation. The flat sub-agent structure decided here makes this migration straightforward.

</deferred>

---

*Phase: 09-integrate-223p-agent-into-master-architecture-via-sub-agent-or-skills*
*Context gathered: 2026-03-20*
