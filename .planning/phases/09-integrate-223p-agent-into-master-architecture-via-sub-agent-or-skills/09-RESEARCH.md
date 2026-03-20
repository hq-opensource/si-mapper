# Phase 9: Integrate 223P Agent into Master Architecture — Research

**Researched:** 2026-03-20
**Domain:** Google ADK sub-agent wiring, ToolContext.state list management, React frontend tab extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Do NOT use `Ontology223PSequentialAgent` or any `SequentialAgent` wrapper.
- Create two independent `LoopWrapper` sub-agents: the generator and the validator.
- The Master Agent itself decides the sequence: "generate code → then validate."
- Both agents are passed in the `subagents` list to `create_master_agent.py` (same pattern as other sub-agents).
- New folder names: `agent/sub_agents/ontology_generator/` and `agent/sub_agents/ontology_validator/`
- Do NOT touch `agent/sub_agents/_223p/` — it remains the standalone runner.
- New folders mirror `_223p/generator/` and `_223p/validator/` structure: `agent.py`, `prompt.md`, `__init__.py`.
- Trigger is explicit HITL: human says "create the code" after all verification is done.
- State key: `ontology_code_snapshots` — append-only list of `{"label": str, "code": str, "iteration": int, "status": "generated"|"fix"|"validated"}`.
- State key: `ontology_code_iteration_count` — int, incremented by `checkpoint_code`.
- `checkpoint_code` tool does NOT escalate (loop continues); only `exit_*` tools escalate.
- `exit_validator_success` patches last snapshot to "Final"/"validated" + escalates.
- Frontend: add `'code'` tab, create `CodeWindow.tsx`, version selector defaults to last snapshot.
- Code tab icon: `Code2` from lucide-react.
- Internal LlmAgent names: `"OntologyGeneratorInternal"` and `"OntologyValidatorInternal"`.
- LoopWrapper names: `"OntologyGeneratorAgent"` and `"OntologyValidatorAgent"`.
- Generator max_iterations: 50. Validator max_iterations: 100.
- Model default: `"github_copilot/claude-sonnet-4.5"`.
- `master_instruction.md` section title: "ASHRAE 223P Code Generation Protocol" — placed after the Visual Verification Protocol section.
- Do NOT import from `sub_agents/_223p/exit_tools.py` in the new agents.

### Claude's Discretion

- No explicit discretion areas specified.

### Deferred Ideas (OUT OF SCOPE)

- Phase 10: Neo4j + Graph tab — docker-compose Neo4j service, loading ontology.ttl, wiring Graph tab.
- Skills refactor — converting sub-agents to ADK skills after they work.
</user_constraints>

---

## Summary

Phase 9 is a well-defined wiring task. The code source of truth is already in the repo: `_223p/generator/agent.py` and `_223p/validator/agent.py` are exact structural templates. The new agents `ontology_generator/agent.py` and `ontology_validator/agent.py` copy that pattern but (a) use new class names to avoid collision, (b) use per-agent exit tools that write to `ToolContext.state`, and (c) are registered in `create_master_agent.py` via the existing `subagents` parameter.

The ADK `LoopWrapper` terminates exclusively via `actions.escalate = True` (confirmed in the exit tools source: "ADK's `LoopAgent._run_async_impl` stops the loop exclusively via `event.actions.escalate`"). The `is_loop_finished` method on `LoopWrapper` is called only on loop-back, not after escalation. This means `checkpoint_code` (which does NOT set `escalate = True`) safely allows the validator loop to continue iterating.

The frontend state system is already wired: `ThoughtsContext` exposes a `data: Record<string, unknown>` that is synced from `/session_state` endpoint. `StateWindow.tsx` reads `data` via `useThoughts()`. `CodeWindow.tsx` follows the identical pattern, reading `data.ontology_code_snapshots` from the same hook. Adding a `'code'` tab requires three changes: the TypeScript union type in two files plus one new component.

**Primary recommendation:** Mirror `_223p/generator/agent.py` exactly for the new generator, mirror `_223p/validator/agent.py` for the new validator, add per-agent `exit_tools.py` with the snapshot logic, register both via `subagents` parameter in `create_master_agent.py`, update `master_instruction.md`, then add the Code tab.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `google-adk` | (project-pinned) | LoopWrapper, LlmAgent, ToolContext, AgentTool | Already in use; all existing sub-agents use it |
| `google.genai.types` | (project-pinned) | GenerateContentConfig, temperature=0.0 | Already used by all sub-agents |
| `lucide-react` | ^0.555.0 (package.json) | Code2 icon for the Code tab | Already in package.json |
| React + Next.js 16 | (project-pinned) | Frontend component framework | Project stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `utils.callback_utils` | local | `shared_model_callback`, `shared_before_model_callback` | Used by all sub-agents |
| `utils.models` | local | `get_adk_model` | Converts model string to ADK model |
| `utils.prompt_utils` | local | `load_prompt_instruction` | Loads .md prompt files |
| `sub_agents._223p.tool` | local | All shared ontology tools (read/write/execute/inspect) | Import into new agents, do not duplicate |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flat sub-agents (decided) | SequentialAgent wrapper | Flat is simpler to swap, no wrapper state leakage |
| `checkpoint_code` non-escalating | Bake into `write_ontology` | `write_ontology` is shared; explicit tool is auditable |

**Installation:** No new packages needed. All dependencies are already in the project.

---

## Architecture Patterns

### Recommended Project Structure
```
agent/sub_agents/
├── ontology_generator/
│   ├── __init__.py          # exports OntologyGeneratorAgent
│   ├── agent.py             # LoopWrapper + LlmAgent (mirrors _223p/generator/agent.py)
│   ├── exit_tools.py        # exit_generator_success, exit_generator_failure
│   └── prompt.md            # copied from _223p/generator/prompt.md as starting point
├── ontology_validator/
│   ├── __init__.py          # exports OntologyValidatorAgent
│   ├── agent.py             # LoopWrapper + LlmAgent (mirrors _223p/validator/agent.py)
│   ├── exit_tools.py        # checkpoint_code, exit_validator_success, exit_validator_failure
│   └── prompt.md            # copied from _223p/validator/prompt.md, updated for checkpoint_code
mapper/src/app/page/components/
└── CodeWindow.tsx           # new component
```

### Pattern 1: Sub-agent as AgentTool (how master calls sub-agents)

**What:** `MasterLlmAgent.__init__` wraps each sub-agent in `AgentTool(agent=sa)` and appends to the master's tools list. The master LLM sees each sub-agent as a callable tool named by the LoopWrapper's `name` parameter.

**When to use:** Any LoopWrapper sub-agent that the master needs to delegate to by name.

**Example (from `level_3_master_main_llm.py`):**
```python
# Source: agent/master_architecture/level_3_master_main_llm.py lines 42-43
default_tools = [ingest_category_files_tool, load_artifacts, exit_loop_level_2, ...]
agent_tools = [AgentTool(agent=sa) for sa in (subagents or [])]
final_tools = default_tools + (tools or []) + agent_tools
```

The master sees the tool name `"OntologyGeneratorAgent"` and `"OntologyValidatorAgent"` exactly as specified in the LoopWrapper `name` parameter. The `description` parameter on the LoopWrapper is what the master uses to decide when to call each.

**Sub-agent registration in `create_master_agent.py` (current state — `subagents` defaults to None):**
```python
# Source: agent/master_architecture/create_master_agent.py line 37
def create_master_agent(session_id: str, model_name: str, subagents: List[LoopAgent] = None) -> LlmAgent:
```

Phase 9 populates this from `main.py` or directly in `create_master_agent.py` by importing and instantiating the new agents.

### Pattern 2: LoopWrapper agent structure (the exact template to follow)

**What:** A public `LoopWrapper` subclass wraps a private `LlmAgent` subclass. The `name` on the `LoopWrapper` is what the master sees.

**Example (from `bacnet/agent.py` — the simplest existing example):**
```python
# Source: agent/sub_agents/bacnet/agent.py
class BacnetLlmAgent(LoopWrapper):
    def __init__(self, model_name: str, ...):
        internal_agent = BacnetAgentInternal(model_name=model_name, ...)
        super().__init__(
            name="BacnetAgent",
            agent=internal_agent,
            description="Extracts BACnet technical metadata.",
            max_iterations=20
        )
```

The ontology agents follow the same pattern. The only differences from the `_223p` agents are the class names (`OntologyGeneratorAgent` / `OntologyGeneratorInternal`) and the exit tool imports.

### Pattern 3: ToolContext.state list appending (the checkpoint_code pattern)

**What:** ADK `ToolContext.state` is a dict backed by the session store. Lists can be read, mutated, and written back. The reliable pattern is read-copy-append-write.

**Confirmed approach (from `_223p/exit_tools.py` which already reads/writes scalar state):**
```python
# Source: agent/sub_agents/_223p/exit_tools.py lines 54-58
tool_context.state["ONTOLOGY_GENERATION_SUCCESS"] = True
tool_context.state["EXIT_LEVEL_4"] = True
tool_context.actions.escalate = True
```

For list appending in `checkpoint_code`:
```python
def checkpoint_code(tool_context: ToolContext, code: str) -> dict:
    """Appends a Fix N snapshot. Does NOT escalate — validator loop continues."""
    iteration = tool_context.state.get("ontology_code_iteration_count", 0)
    snapshots = list(tool_context.state.get("ontology_code_snapshots", []))
    snapshots.append({
        "label": f"Fix {iteration}",
        "code": code,
        "iteration": iteration,
        "status": "fix"
    })
    tool_context.state["ontology_code_snapshots"] = snapshots
    tool_context.state["ontology_code_iteration_count"] = iteration + 1
    return {"status": "snapshot_saved", "iteration": iteration}
    # NOTE: No tool_context.actions.escalate here — loop continues
```

**Critical:** ADK state dict mutation is in-place safe per tool call. The read-copy-write pattern (not `list.append()` directly on state value) avoids the risk of the state reference being replaced mid-operation.

### Pattern 4: Exit tool — generator success (appends Initial snapshot)

```python
def exit_generator_success(tool_context: ToolContext, code: str, summary: str) -> dict:
    snapshots = list(tool_context.state.get("ontology_code_snapshots", []))
    snapshots.append({"label": "Initial", "code": code, "iteration": 0, "status": "generated"})
    tool_context.state["ontology_code_snapshots"] = snapshots
    tool_context.state["ontology_code_iteration_count"] = 0
    tool_context.state["ONTOLOGY_GENERATION_SUCCESS"] = True
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "summary": summary}
```

### Pattern 5: Exit tool — validator success (patch last snapshot)

```python
def exit_validator_success(tool_context: ToolContext, code: str, summary: str) -> dict:
    # First save the final version as a snapshot
    checkpoint_code(tool_context, code)  # internal call
    # Patch the last snapshot to "Final"/"validated"
    snapshots = list(tool_context.state.get("ontology_code_snapshots", []))
    if snapshots:
        snapshots[-1]["label"] = "Final"
        snapshots[-1]["status"] = "validated"
        tool_context.state["ontology_code_snapshots"] = snapshots
    tool_context.state["ONTOLOGY_VALIDATION_SUCCESS"] = True
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "summary": summary}
```

### Pattern 6: Frontend Code tab (following StateWindow.tsx pattern)

**What:** `CodeWindow.tsx` reads `data.ontology_code_snapshots` from `useThoughts()`. The `data` object is `Record<string, unknown>` from `ThoughtsContext.tsx` and is populated via `syncData()` which merges `/session_state` polling results.

**State flow confirmed:** `/session_state` endpoint in `main.py` merges ADK session state + `GLOBAL_SESSION_STORE` and returns as JSON. Frontend polls this endpoint. `ThoughtsContext.syncData()` merges new keys into `data`. `CodeWindow.tsx` accesses `data.ontology_code_snapshots` typed as `SnapshotEntry[] | undefined`.

```tsx
// Source pattern: mapper/src/app/page/components/StateWindow.tsx
const { data } = useThoughts();
const snapshots = (data?.ontology_code_snapshots ?? []) as SnapshotEntry[];
```

**Version selector defaults to last snapshot (index `snapshots.length - 1`):**
```tsx
const [selectedIdx, setSelectedIdx] = useState<number>(snapshots.length > 0 ? snapshots.length - 1 : 0);
// Re-sync when new snapshots arrive (auto-advance to latest):
useEffect(() => {
    setSelectedIdx(snapshots.length > 0 ? snapshots.length - 1 : 0);
}, [snapshots.length]);
```

### Anti-Patterns to Avoid

- **Importing from `_223p/exit_tools.py`:** The new agents must have their own `exit_tools.py`. The `_223p` folder is untouched.
- **Using `SequentialAgent`:** The master sequences the two agents itself via its LLM instruction.
- **Setting `escalate = True` in `checkpoint_code`:** This would terminate the validator loop. The tool must return without setting escalate.
- **Direct `tool_context.state["ontology_code_snapshots"].append()`:** Mutating the live state reference directly may not persist. Always read-copy-write.
- **Collision on `EXIT_LEVEL_4` flag between generator and validator:** The generator sets it to `True` on exit. The existing `_223p` sequential agent reset it before running the validator (confirmed in docstring). For the master-sequences approach, the master delegates to the validator only after generator completes — the `EXIT_LEVEL_4` flag is reset by `LoopWrapper._default_termination()` which sets `state["EXIT_LEVEL_4"] = False` after reading it. Confirmed in `loop_wrapper.py` lines 35-36.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent-to-tool wrapping | Custom delegation mechanism | `AgentTool(agent=sa)` from `google.adk.tools` | Already used by all sub-agents via `level_3_master_main_llm.py` |
| Loop termination | Custom exit signal system | `tool_context.actions.escalate = True` + `LoopWrapper` | Already proven by all existing agents |
| State persistence | Custom DB or file | `ToolContext.state[key] = value` | ADK session state — already wired into frontend polling |
| Model resolution | Manual model string parsing | `get_adk_model(model_name)` from `utils.models` | Already used everywhere |
| Prompt loading | `open()` file reads | `load_prompt_instruction(relative_path)` from `utils.prompt_utils` | Already used everywhere |
| Tool deduplication | Custom set logic | `{t.__name__ if hasattr(t, '__name__') else str(t): t for t in all_tools}` | Established pattern in all agents |
| Code highlighting | Custom syntax highlighter | `<pre><code>` block (no external lib needed) | No highlighting library in `package.json`; plain preformatted block is the right default |

**Key insight:** Every mechanism needed already exists and is proven in the current codebase. This phase is wiring, not invention.

---

## Common Pitfalls

### Pitfall 1: Name collision between new agents and `_223p` agents
**What goes wrong:** Python import system picks up the wrong class if names collide. The `_223p/generator/agent.py` exports `OntologyLlmAgent` and `OntologyLlmAgentInternal`. If the new `ontology_generator/agent.py` uses the same class names, tests and runtime imports become ambiguous.
**Why it happens:** Both files are in `sub_agents/` subtree; both get imported.
**How to avoid:** New agents MUST use distinct class names: `OntologyGeneratorAgent` (LoopWrapper) and `OntologyGeneratorInternal` (LlmAgent). Validator: `OntologyValidatorAgent` and `OntologyValidatorInternal`.
**Warning signs:** `ImportError` or `AttributeError` mentioning unexpected class sources at startup.

### Pitfall 2: `checkpoint_code` accidentally escalating the validator loop
**What goes wrong:** If `tool_context.actions.escalate = True` is set inside `checkpoint_code`, the validator loop terminates after the first fix, not after validation succeeds.
**Why it happens:** Copy-paste from exit tool patterns that do escalate.
**How to avoid:** `checkpoint_code` must return a plain dict with no escalation. Only `exit_validator_success` and `exit_validator_failure` escalate.
**Warning signs:** Validator runs for only 1 iteration despite errors remaining.

### Pitfall 3: `EXIT_LEVEL_4` flag not reset between generator and validator runs
**What goes wrong:** Generator sets `EXIT_LEVEL_4 = True`. LoopWrapper resets it to `False` when it reads it (line 35-36 of `loop_wrapper.py`). But if the validator's LoopWrapper reads a stale `True` before the generator's flag is consumed, the validator terminates immediately.
**Why it happens:** Race condition in flag lifecycle if LoopWrapper's `is_loop_finished` is somehow called before reset.
**How to avoid:** Confirmed in `loop_wrapper.py`: `state["EXIT_LEVEL_4"] = False` is set immediately when `True` is found. The master delegates to validator only after generator has fully completed (escalated and returned). By that point the flag has been reset. No extra action needed.
**Warning signs:** Validator exits with 0 iterations completed.

### Pitfall 4: Frontend type union not updated in both files
**What goes wrong:** Adding `'code'` to the union type in `AgentNavbar.tsx` but not in `YourMainContent.tsx` (or vice versa) causes a TypeScript error.
**Why it happens:** The tab union type `'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts'` is defined in two places — the `AgentNavbarProps.activeTab` type and the `useState` type in `YourMainContent.tsx`.
**How to avoid:** Update both files in the same task. The union type appears on lines 11-12 of `AgentNavbar.tsx` and line 34 of `YourMainContent.tsx`.
**Warning signs:** TypeScript build error `Type '"code"' is not assignable to type '...'`.

### Pitfall 5: `main.py` does not pass `subagents` to `create_master_agent`
**What goes wrong:** New agents are instantiated in `create_master_agent.py` but the call site in `main.py` line 61 is `create_master_agent(session_id=session_id, model_name=SHARED_ADK_MODEL)` with no `subagents` argument.
**Why it happens:** `subagents` defaults to `None` — the parameter exists but no existing call site populates it.
**How to avoid:** Two approaches are valid: (a) instantiate the sub-agents inside `create_master_agent.py` directly (no change to `main.py` needed), or (b) pass them from `main.py`. The cleaner approach for this project is (a) — instantiate inside `create_master_agent`.
**Warning signs:** Master agent has no `OntologyGeneratorAgent` or `OntologyValidatorAgent` tools available at runtime.

### Pitfall 6: No syntax highlighting library available
**What goes wrong:** Planner assumes a library like `react-syntax-highlighter` or `prism-react-renderer` is available.
**Why it happens:** Assumption without checking `package.json`.
**How to avoid:** `package.json` has NO syntax highlighting library. `CodeWindow.tsx` must use `<pre><code>` with Tailwind styling only (monospace font, overflow-x scroll). Do not add a new dependency for Phase 9.
**Warning signs:** Build failure for missing module.

---

## Code Examples

### How the master calls a sub-agent by name

```typescript
// The master LLM sees each LoopWrapper as a tool.
// The name the master uses to call it equals the LoopWrapper `name` parameter.
// Source: level_3_master_main_llm.py lines 42-43
agent_tools = [AgentTool(agent=sa) for sa in (subagents or [])]
```

The master instruction must say: "delegate to `OntologyGeneratorAgent`" and "delegate to `OntologyValidatorAgent`" — using the exact LoopWrapper `name` values.

### New agent wiring in create_master_agent.py

```python
# Source: agent/master_architecture/create_master_agent.py (to be modified)
from sub_agents.ontology_generator.agent import OntologyGeneratorAgent
from sub_agents.ontology_validator.agent import OntologyValidatorAgent

def create_master_agent(session_id: str, model_name: str, subagents: List[LoopAgent] = None) -> LlmAgent:
    # ... existing code ...
    ontology_subagents = [
        OntologyGeneratorAgent(model_name=model_name),
        OntologyValidatorAgent(model_name=model_name),
    ]
    all_subagents = (subagents or []) + ontology_subagents
    master_agent = MasterLlmAgent(
        model_name=model_name,
        subagents=all_subagents,   # was: subagents=subagents
        tools=[skill_tools] + task_tools,
        session_id=session_id
    )
```

### Frontend: reading ontology snapshots from state

```tsx
// Source: pattern from mapper/src/app/page/components/StateWindow.tsx
import { useThoughts } from '../../../context/ThoughtsContext';

interface SnapshotEntry {
    label: string;
    code: string;
    iteration: number;
    status: 'generated' | 'fix' | 'validated';
}

export function CodeWindow() {
    const { data } = useThoughts();
    const snapshots = (data?.ontology_code_snapshots ?? []) as SnapshotEntry[];
    const [selectedIdx, setSelectedIdx] = useState(snapshots.length > 0 ? snapshots.length - 1 : 0);

    useEffect(() => {
        setSelectedIdx(snapshots.length > 0 ? snapshots.length - 1 : 0);
    }, [snapshots.length]);

    if (snapshots.length === 0) {
        return <StatusPlaceholder title="No ontology code generated yet" ... />;
    }
    // ... pill row + <pre><code> display
}
```

### AgentNavbar.tsx tab addition (exact lines to change)

Current type (line 11-12):
```typescript
activeTab: 'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts';
```
Add `| 'code'` to both occurrences.

Current navItems array (lines 22-32): add `{ id: 'code', label: 'Code', icon: Code2 }`.

Import `Code2` from `lucide-react` (not currently imported in `AgentNavbar.tsx`; current imports are `Eye, Edit3, BarChart2, Brain, Folder, Wrench, Database, Package`).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `SequentialAgent` wrapper for 223P pipeline | Master LLM sequences two flat `LoopWrapper` sub-agents | Phase 9 decision | Simpler; no wrapper state issues |
| Single exit tool for all 223P agents | Per-agent exit tools with snapshot logic | Phase 9 design | Clean separation; no cross-agent flag leakage |
| No code visibility in frontend | `ontology_code_snapshots` list in state, rendered in Code tab | Phase 9 | Full version history visible to user |

**Deprecated/outdated:**
- The `_223p/agent.py` `Ontology223PSequentialAgent` class is superseded for the master-integrated flow. It remains valid for the standalone runner only.
- `exit_loop_generator_success` in `_223p/exit_tools.py` does NOT accept a `code:` parameter — the new `exit_generator_success` in `ontology_generator/exit_tools.py` DOES. Do not confuse them.

---

## Open Questions

1. **Should the validator prompt be updated to instruct calling `checkpoint_code` after each `write_ontology`?**
   - What we know: The validator prompt (`_223p/validator/prompt.md`) currently says to call `write_ontology` and loop. It does not mention snapshotting.
   - What's unclear: The LLM may not call `checkpoint_code` unless the prompt explicitly instructs it.
   - Recommendation: The new `ontology_validator/prompt.md` must include: "After each successful `write_ontology` call, immediately call `checkpoint_code` with the same code string to save a version snapshot."

2. **Does `load_prompt_instruction` path resolution work for new sub-agent folders?**
   - What we know: `load_prompt_instruction` takes a path string relative to `agent/`. It is used as `load_prompt_instruction("sub_agents/_223p/generator/prompt.md")`.
   - What's unclear: Whether the function resolves relative to `agent/` root or the calling module.
   - Recommendation: Use `load_prompt_instruction("sub_agents/ontology_generator/prompt.md")` following the exact same pattern. This is LOW risk.

---

## Validation Architecture

`workflow.nyquist_validation` key is absent from `.planning/config.json` (only `_auto_chain_active` is present) — treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (detected in agent/.venv; existing tests in `agent/tests/`) |
| Config file | none detected at agent root (tests run with `pytest agent/tests/`) |
| Quick run command | `cd agent && uv run pytest tests/ -x -q` |
| Full suite command | `cd agent && uv run pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P9-01 | `OntologyGeneratorAgent` is a LoopWrapper with correct name/description/max_iterations | unit | `pytest tests/test_ontology_generator_agent.py -x` | Wave 0 |
| P9-02 | `OntologyValidatorAgent` is a LoopWrapper with correct name/description/max_iterations | unit | `pytest tests/test_ontology_validator_agent.py -x` | Wave 0 |
| P9-03 | `exit_generator_success` appends Initial snapshot and sets ONTOLOGY_GENERATION_SUCCESS=True | unit | `pytest tests/test_ontology_generator_exit_tools.py -x` | Wave 0 |
| P9-04 | `checkpoint_code` appends Fix N snapshot, increments counter, does NOT escalate | unit | `pytest tests/test_ontology_validator_exit_tools.py::test_checkpoint_code -x` | Wave 0 |
| P9-05 | `exit_validator_success` patches last snapshot to "Final"/"validated" and escalates | unit | `pytest tests/test_ontology_validator_exit_tools.py::test_exit_validator_success -x` | Wave 0 |
| P9-06 | `create_master_agent` includes OntologyGeneratorAgent and OntologyValidatorAgent as AgentTools | unit | `pytest tests/test_create_master_agent.py -x` | Wave 0 |
| P9-07 | Frontend Code tab renders with placeholder when snapshots empty | manual | n/a | manual-only |
| P9-08 | Frontend Code tab renders all snapshot labels and displays selected code | manual | n/a | manual-only |

### Sampling Rate
- **Per task commit:** `cd agent && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd agent && uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent/tests/test_ontology_generator_agent.py` — covers P9-01
- [ ] `agent/tests/test_ontology_validator_agent.py` — covers P9-02
- [ ] `agent/tests/test_ontology_generator_exit_tools.py` — covers P9-03
- [ ] `agent/tests/test_ontology_validator_exit_tools.py` — covers P9-04, P9-05
- [ ] `agent/tests/test_create_master_agent.py` — covers P9-06 (check if partial version exists from Phase 8)

---

## Sources

### Primary (HIGH confidence)
- `agent/sub_agents/_223p/generator/agent.py` — exact structural template for new generator agent
- `agent/sub_agents/_223p/validator/agent.py` — exact structural template for new validator agent
- `agent/sub_agents/_223p/exit_tools.py` — canonical exit tool pattern; includes ADK escalation docstring
- `agent/sub_agents/loop_agents/loop_wrapper.py` — `is_loop_finished`, `EXIT_LEVEL_4` flag reset confirmed
- `agent/master_architecture/level_3_master_main_llm.py` — `AgentTool` wrapping, `subagents` parameter
- `agent/master_architecture/create_master_agent.py` — `subagents: List[LoopAgent] = None` parameter
- `agent/sub_agents/bacnet/agent.py` — simplest sub-agent example for structural reference
- `mapper/src/app/page/components/StateWindow.tsx` — `useThoughts()` / `data` pattern
- `mapper/src/app/page/components/AgentNavbar.tsx` — exact tab union type and navItems array to extend
- `mapper/src/app/page/components/YourMainContent.tsx` — `renderContent()` switch to extend
- `mapper/src/context/ThoughtsContext.tsx` — `data: Record<string, unknown>`, `syncData()` shape
- `mapper/package.json` — confirms NO syntax highlighting library present
- `agent/main.py` — confirms `create_master_agent` call site uses `subagents` defaulting to None

### Secondary (MEDIUM confidence)
- N/A — all critical findings come from direct source code inspection

### Tertiary (LOW confidence)
- N/A

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed from existing code, no new dependencies
- Architecture: HIGH — all patterns verified from live source files
- Pitfalls: HIGH — specific line numbers and behaviors confirmed in source
- Frontend: HIGH — ThoughtsContext data flow, union types, and component patterns confirmed

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable codebase; only invalidated by major ADK version change or frontend refactor)
