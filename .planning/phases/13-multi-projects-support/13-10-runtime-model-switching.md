# 13-10 — Runtime Model Switching

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-26
**Depends on:** `13-09` (session-scoped model selection must be in place first)
**See also:** `13-99` (MCP server project context)

---

## Overview

`13-09` Milestone 3 fixes the model at session creation time by reading `active_system.ai_model_name` from state. That covers the standard path: the model is chosen when the session starts and stays fixed for its duration.

This step covers the next level: **swapping the model on a live process without restarting the agent** — useful when:
- The user switches `active_system` mid-conversation to a system that uses a different model.
- An operator needs to change the model without a full service restart.
- A `POST /model` override is exposed to the frontend or an admin UI.

---

## Background — Why the Model Is Frozen

Every `LlmAgent` subclass calls `get_adk_model(model_name)` in `__init__` and passes the result to Pydantic's `super().__init__(model=...)`. Once constructed, the value is frozen. The active tree at startup is three nodes:

```
main.py  (SHARED_ADK_MODEL env var)
  └─► create_master_agent(model_name=...)
        ├─► MasterLlmAgent(model_name=...)          → get_adk_model() → frozen
        ├─► OntologyGeneratorAgent(model_name=...)  → get_adk_model() → frozen (own LLM loop)
        └─► OntologyValidatorAgent(model_name=...)  → get_adk_model() → frozen (own LLM loop)
```

Domain agents (BACnet, Control, Equipment, etc.) are implemented as **skills** (`SKILL.md` files in `SkillToolset`) and run on the master's own model — they are not instantiated as separate agents and are therefore unaffected by this problem.

| | Ontology agents | Domain agents (BACnet, Control, etc.) |
|---|---|---|
| **Mechanism** | Full `AgentTool` with their own LLM loop | `SKILL.md` markdown loaded into the master's `SkillToolset` |
| **Instantiated at startup?** | Yes — hardcoded inside `create_master_agent` | No — Python classes exist but are never wired in |
| **Own model?** | Yes — frozen at construction | No — run on the master's model |
| **Affected by model freeze?** | Yes | No |

> If the domain Python classes (`sub_agents/bacnet/agent.py`, etc.) are ever promoted from skills to full `AgentTool`s, they will become subject to the same freeze and must be added to the rebuild call at that time.

---

## Changes Required

### 1. `agent/main.py` — `ModelConfig` and `AgentHolder`

Replace the static `SHARED_ADK_MODEL` string variable with a mutable holder, and wrap the `ADKAgent` in an indirection object so FastAPI routes always delegate to the current instance:

```python
class ModelConfig:
    current: str = os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")

class AgentHolder:
    adk_agent: ADKAgent | None = None

model_config = ModelConfig()
holder = AgentHolder()
_rebuild_lock = asyncio.Lock()
```

### 2. `agent/main.py` — `rebuild_agent()` factory function

```python
def rebuild_agent(model_name: str, session_id: str) -> None:
    master = create_master_agent(session_id=session_id, model_name=model_name)
    holder.adk_agent = ADKAgent(
        adk_agent=master,
        app_name="si_mapper",
        user_id="demo_user",
        session_timeout_seconds=3600,
        execution_timeout_seconds=1800,
        tool_timeout_seconds=900,
        use_in_memory_services=True
    )
```

Call once at startup (equivalent to current behaviour — no regression):
```python
rebuild_agent(model_config.current, session_id)
```

All existing FastAPI handlers that reference `adk_agent` must be updated to reference `holder.adk_agent` instead.

### 3. `agent/main.py` — `POST /model` endpoint

```python
@app.post("/model")
async def set_model(model_name: str):
    async with _rebuild_lock:
        new_session_id = f"session-{uuid.uuid4().hex[:8]}"
        GLOBAL_SESSION_STORE[new_session_id] = {
            "detailed_equipment_dict": {},
            "completed_sub_agents": [],
            "python_code_snapshots": [],
            "ttl_code_snapshots": []
        }
        GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[new_session_id]
        model_config.current = model_name
        rebuild_agent(model_name, new_session_id)
    return {"status": "ok", "model": model_name, "session_id": new_session_id}
```

The lock ensures that if two requests race to change the model, the second waits for the first rebuild to complete.

---

## Trade-offs & Decisions

- **Session history is lost on swap**: `ADKAgent` holds `InMemorySessionManager` internally. Rebuilding it discards conversation history. This is an accepted trade-off — the swap is an operator action, not a mid-turn event.
- **In-flight requests**: requests in progress against the old `ADKAgent` will complete normally (Python keeps the old object alive until all references drop). New requests pick up the new instance immediately after the lock releases.
- **No changes to `create_master_agent`**: the factory already accepts `model_name` and propagates it to all three frozen nodes. The rebuild is fully covered by calling it again.
- **`/session_info` and `/session_state`**: both endpoints reference `session_id` and `adk_agent` — they must be updated to read from `holder.adk_agent` and a module-level `current_session_id` variable that `rebuild_agent` updates on each call.

---

## Implementation Plan

### Milestone 1 — `AgentHolder` indirection

**Steps:**
1. Introduce `ModelConfig`, `AgentHolder`, and `_rebuild_lock` in `main.py`.
2. Implement `rebuild_agent(model_name, session_id)`.
3. Replace the `create_app()` inline agent construction with a call to `rebuild_agent`.
4. Update all handlers (`/session_info`, `/session_state`, `add_adk_fastapi_endpoint`) to reference `holder.adk_agent` instead of a closed-over `adk_agent` variable.
5. Smoke-test: startup behaviour is identical to before.

---

### Milestone 2 — `POST /model` endpoint

**Steps:**
1. Add the `POST /model` endpoint with `asyncio.Lock` protection.
2. Test: call `POST /model` with a different model name; verify the next agent interaction uses the new model for `MasterLlmAgent`, `OntologyGeneratorAgent`, and `OntologyValidatorAgent`.
3. Test: call `POST /model` twice in rapid succession; verify no race condition.
4. Test: verify `/session_info` returns the new `session_id` after a swap.

---

## Acceptance Criteria

- [ ] `POST /model` endpoint exists and accepts a model name string; returns `{"status": "ok", "model": ..., "session_id": ...}`.
- [ ] After `POST /model`, the next agent interaction uses the new model across the entire active tree: `MasterLlmAgent`, `OntologyGeneratorAgent`, and `OntologyValidatorAgent`.
- [ ] `AgentHolder` indirection is in place — FastAPI routes never reference a stale `ADKAgent` after a swap.
- [ ] An `asyncio.Lock` guards the rebuild so concurrent `POST /model` calls are serialised, not dropped.
- [ ] `/session_info` returns the new `session_id` after a swap.
- [ ] Startup behaviour is unchanged — the initial `rebuild_agent` call is equivalent to the current inline construction.
- [ ] In-flight requests against the old agent complete normally; new requests use the new agent.

---

## Notes & Decisions

- **This step depends on `13-09` Milestone 3**: session-scoped model selection (`active_system.ai_model_name`) must be in place. The `POST /model` endpoint is the operator-level override on top of that.
- **Domain agent Python classes**: `sub_agents/bacnet/agent.py`, `sub_agents/equipment/agent.py`, etc. are currently orphaned (not wired in as `AgentTool`s). They are unaffected by this change. If they are ever promoted, they will need to be added to `rebuild_agent`.
- **Frontend integration**: the frontend should call `GET /session_info` after a system switch to pick up the new `session_id` if a model swap was triggered server-side.

