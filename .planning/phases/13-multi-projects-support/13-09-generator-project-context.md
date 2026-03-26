# 13-09 — Agent System Context Awareness

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-07` (active project and system are in CopilotKit state before the agent can read them)
**See also:** `13-10` (MCP server project context — handled separately)

---

## Overview

The agentic backend (`agent/`) currently has its Graphivac grid identity and file paths baked in as static environment variables loaded at startup. This means:
- The agent always talks to the same Graphivac grid, regardless of which project and system the user selected.
- Agent file access is not scoped to any system folder.
- Switching projects or systems in the UI has no effect on the agent's behaviour.

This task makes the **agent** system-context-aware by:

1. Reading the active project and active system from `ToolContext.state` (injected by the frontend via CopilotKit — see `13-07`).
2. Using the active system's `graphivac_grid_id` and the active project's `graphivac_project_id` when interacting with Graphivac.
3. Scoping all file-system access to the active system's folder on disk.
4. Using the active system's `ai_model_name` as the model for that session.

> The Graphivac organisation (`GRAPHIVAC_ORG_ID`) is **always read from the agent's own env var** — it is never sent from the frontend and never stored in state.

> The MCP server has a separate treatment — see `13-10`.

---

## State Shape (from `13-07`)

The frontend injects the following into `tool_context.state`:

```python
{
  "active_project": {
    "id": "proj-abc123",
    "name": "Building A",
    "folder_path": "proj-abc123",
    "graphivac_project_id": "P-j8QIvTGH7p",
  },
  "active_system": {
    "id": "sys-aaa111",
    "name": "Chilled Water Plant",
    "folder_path": "sys-aaa111",          # relative to project folder
    "graphivac_grid_id": "G-LAiRS3mgp6",
    "ai_model_name": "gemini-3.1-pro",
  }
}
```

Note what is **absent** from state:
- `graphivac_org_id` — the agent reads it from `GRAPHIVAC_ORG_ID` env var.

---

## Current Static Configuration — What Needs to Change

### Agent Graphivac tools (`agent/tools/`)

Both `sync_graphivac_to_agent_tool.py` and `sync_graphivac_tool.py` read:
```python
base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")
org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
grid_id    = os.getenv("GRAPHIVAC_GRID_ID", "")
```

These must instead read from `tool_context.state` when available:

```python
def sync_graphivac_to_agent(tool_context: ToolContext) -> dict:
    active_project = tool_context.state.get("active_project") or {}
    active_system  = tool_context.state.get("active_system") or {}

    # Org ID is always from env — never from state
    org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
    base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")

    # Project and grid IDs: prefer state, fall back to env for dev compatibility
    project_id = active_project.get("graphivac_project_id") or os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = active_system.get("graphivac_grid_id")     or os.getenv("GRAPHIVAC_GRID_ID", "")
```

This pattern:
- Requires **no breaking change** — when `active_project` / `active_system` are absent (old clients, tests), env vars continue to work.
- Does not require restarting the agent when switching systems.
- `org_id` is **always** from env — state never carries it.

---

## Changes Required

### 1. `agent/tools/sync_graphivac_to_agent_tool.py`

Replace hardcoded env var reads with the state-first pattern for `project_id` and `grid_id`.
`org_id` and `base_url` remain env-only.

---

### 2. `agent/tools/sync_graphivac_tool.py`

Same pattern.

---

### 3. `agent/master_architecture/create_master_agent.py`

The AI model should be read from `active_system.ai_model_name` when available, falling back to `SHARED_ADK_MODEL` env var.

```python
model_name = (
    tool_context.state.get("active_system", {}).get("ai_model_name")
    or os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")
)
```

Because the agent is created once per session, the model is fixed for the session. If the user switches systems mid-session, the next session picks up the new model (Graphivac and file-path changes apply immediately via state).

---

### 4. Scope file-system access to the system folder

Agent tools that read/write files must resolve paths relative to the **active system's folder** (not the project root).

**Absolute path of the active system's folder:**
```
{PROJECTS_FOLDER}/{active_project.folder_path}/{active_system.folder_path}/
```

**Key paths to scope:**

| Current path | Scoped path |
|---|---|
| `223p/ttl/ontology.ttl` | `{PROJECTS_FOLDER}/{proj_folder}/{sys_folder}/ontology.ttl` |
| `223p/ontology.py` | `{PROJECTS_FOLDER}/{proj_folder}/{sys_folder}/ontology.py` |

**Approach:** Add a `get_system_path(tool_context, relative: str) -> str` helper.

```python
# agent/utils/project_utils.py

import os
import pathlib

def get_system_path(tool_context, relative: str) -> str:
    """
    Resolves a path relative to the active system's folder.
    Falls back to the repo root if no active system is in state.
    """
    projects_root = os.getenv("PROJECTS_FOLDER", "")
    active_project = tool_context.state.get("active_project") or {}
    active_system  = tool_context.state.get("active_system") or {}

    proj_folder = active_project.get("folder_path", "")
    sys_folder  = active_system.get("folder_path", "")

    if projects_root and proj_folder and sys_folder:
        return str(pathlib.Path(projects_root) / proj_folder / sys_folder / relative)

    # Fallback for dev/test without project context
    return relative
```

**Files to create:**
- `agent/utils/project_utils.py`

**Files to modify:**
- `agent/sub_agents/ontology_generator/` _(write ontology to system path)_
- `agent/sub_agents/ontology_validator/` _(read/write from system folder)_

---

### 5. Update `master_instruction.md`

Add a "System Context" section:
- The agent must read `active_project` and `active_system` from state before any task.
- Graphivac tools automatically use the correct project and grid IDs from state.
- File outputs go to the system folder via `get_system_path`.
- `graphivac_org_id` is never in state — the agent reads it from its own env var.
- If either `active_project` or `active_system` is null, ask the user to select a project and system before proceeding.

---

## Implementation Plan

### Milestone 1 — State-aware Graphivac tools

**Steps:**
1. Update `sync_graphivac_to_agent_tool.py` — state-first for `project_id` and `grid_id`; env-only for `org_id`.
2. Update `sync_graphivac_tool.py` — same.
3. Test: set `active_system` in the frontend with a different `grid_id`, trigger sync — confirm the correct grid is used.

---

### Milestone 2 — `get_system_path` helper and scoped file access

**Steps:**
1. Create `agent/utils/project_utils.py` with `get_system_path(tool_context, relative)`.
2. Update ontology generator and validator to use `get_system_path` for all file writes.
3. Confirm ontology files land in `PROJECTS_FOLDER/{proj}/{sys}/`.

---

### Milestone 3 — Per-system model selection

**Steps:**
1. In `agent/main.py`, read `active_system.ai_model_name` from initial state; pass to `create_master_agent` as `model_name`.
2. Fall back to `SHARED_ADK_MODEL` env var if absent.

---

### Milestone 4 — Master instruction update

**Steps:**
1. Add "System Context" section to `master_instruction.md`.
2. Instruct the agent to check for both `active_project` and `active_system` and ask the user if either is null.

---

## Acceptance Criteria

- [ ] `sync_graphivac_to_agent_tool.py` reads `graphivac_project_id` from `state["active_project"]` and `graphivac_grid_id` from `state["active_system"]` when present.
- [ ] `sync_graphivac_tool.py` applies the same pattern.
- [ ] `org_id` is **always** read from `GRAPHIVAC_ORG_ID` env var — never from state.
- [ ] Both tools fall back to env vars (`GRAPHIVAC_PROJECT_ID`, `GRAPHIVAC_GRID_ID`) when state keys are absent.
- [ ] `agent/utils/project_utils.py` exists with `get_system_path`.
- [ ] Ontology generator and validator write output into the active system's folder.
- [ ] The master agent's model is taken from `active_system.ai_model_name`, falling back to `SHARED_ADK_MODEL`.
- [ ] `master_instruction.md` instructs the agent to check for both `active_project` and `active_system` before starting any task.

---

## Notes & Decisions

- **`GRAPHIVAC_ORG_ID` is env-only, always**: this is the defining constraint from `13-00`. The agent never reads it from state, and the frontend never sends it. Any code path that currently passes `org_id` from outside env should be treated as a bug.
- **State-first, env-var fallback**: non-breaking. Old clients, tests, and direct agent invocations continue to work via env vars.
- **No agent restart on system switch**: Graphivac coordinates and folder paths switch immediately (read from state at call time). Only the model is session-fixed.
- **`PROJECTS_FOLDER` must be set for the agent process**: in dev it's the same host path as for the frontend. In Docker it's a shared volume mount.
- **Two-level path**: the system folder is nested inside the project folder. `get_system_path` handles both levels.
- **MCP server is handled separately**: see `13-10`.
