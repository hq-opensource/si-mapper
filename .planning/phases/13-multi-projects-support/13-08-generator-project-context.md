# 13-08 — Agent Project Context Awareness

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-07` (active project is in CopilotKit state before the agent can read it)
**See also:** `13-09` (MCP server project context — handled separately)

---

## Overview

The agentic backend (`agent/`) currently has its Graphivac grid identity and file paths baked in as static environment variables loaded at startup. This means:
- The agent always talks to the same Graphivac grid, regardless of which project the user selected.
- Agent file access (skill loading, ontology output paths) is not scoped to any project folder.
- Switching projects in the UI has no effect on the agent's behaviour.

This task makes the **agent** project-context-aware by:

1. Reading the active project record from `ToolContext.state` (injected by the frontend via CopilotKit — see `13-07`).
2. Using the active project's `graphivac_grid_id`, `graphivac_org_id`, `graphivac_project_id`, and `folder_path` instead of the static env vars wherever the agent interacts with Graphivac or the file system.
3. Scoping the agent's file-system access to the active project's folder on disk.
4. Using the active project's `ai_model_name` as the model for that session.

> The MCP server has a separate, more constrained treatment of multi-project support due to its architecture — see `13-09`.

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
These must instead read from `tool_context.state["active_project"]` when available, falling back to env vars for backwards compatibility.

### Agent model selection (`agent/main.py`)

```python
SHARED_ADK_MODEL = os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")
```
This is used globally. The active project's `ai_model_name` should override it per-session.

### Agent file access (skills, ontology output)

Skills that read from the file system (e.g. `skill-read-code`, the 223P ontology output at `223p/ttl/ontology.ttl`) are currently not project-scoped. For multi-project support, the agent must write/read ontology output to/from `{PROJECTS_FOLDER}/{project.folder_path}/`.

---

## Approach: Project Context via `ToolContext.state`

The frontend injects `active_project` into the CopilotKit agent state (see `13-07`). In the ADK agent, state is accessible via `tool_context.state` inside any tool function. The pattern is:

```python
def sync_graphivac_to_agent(tool_context: ToolContext) -> dict:
    active_project = tool_context.state.get("active_project")
    if active_project:
        grid_id    = active_project["graphivac_grid_id"]
        org_id     = active_project["graphivac_org_id"]
        project_id = active_project["graphivac_project_id"]
        base_url   = active_project.get("graphivac_base_url") or os.getenv("GRAPHIVAC_BASE_URL", "")
    else:
        # Fall back to env vars (backwards-compatible dev mode)
        grid_id    = os.getenv("GRAPHIVAC_GRID_ID", "")
        org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
        project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
        base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")
```

This pattern:
- Requires **no breaking change** — when `active_project` is absent from state (old clients, tests), env vars continue to work.
- Does not require restarting the agent when switching projects — the state is per-session.
- Is consistent with how other state values (`detailed_equipment_dict`, `python_code_snapshots`, etc.) are read.

---

## Active Project State Shape (from `13-07`)

The frontend injects the following into `tool_context.state`:

```python
{
  "active_project": {
    "id": "proj-abc123",
    "name": "Building A — HVAC",
    "folder_path": "proj-abc123",         # relative to PROJECTS_FOLDER
    "graphivac_org_id": "public",
    "graphivac_project_id": "P-j8QIvTGH7p",
    "graphivac_grid_id": "G-LAiRS3mgp6",
    "ai_model_name": "gemini-3.1-pro",
  }
}
```

---

## Changes Required

### 1. `agent/tools/sync_graphivac_to_agent_tool.py`

Replace the four `os.getenv` calls with the state-first pattern shown above.

**Files to modify:**
- `agent/tools/sync_graphivac_to_agent_tool.py`

---

### 2. `agent/tools/sync_graphivac_tool.py`

Same pattern — replace static env var reads with `tool_context.state["active_project"]` fallback.

**Files to modify:**
- `agent/tools/sync_graphivac_tool.py`

---

### 3. `agent/master_architecture/create_master_agent.py`

The `SHARED_ADK_MODEL` env var is passed to `create_master_agent` as `model_name`. For multi-project support, the model should be read from `active_project.ai_model_name` if available.

**Approach:** Read the model from the initial state at session start and use it throughout the session.

**Steps:**
1. In `agent/main.py`, after the initial session state is created, check `tool_context.state.get("active_project", {}).get("ai_model_name")` and use it as `model_name` if present.
2. Because the agent is created once per session (in `create_app()`), the model is fixed for the session. If the user switches projects mid-session, the next session uses the new project's model.

**Files to modify:**
- `agent/main.py`
- `agent/master_architecture/create_master_agent.py` _(accept model_name override from state if needed)_

---

### 4. Scope file-system access to the project folder

Agent tools and sub-agents that read/write files on disk (ontology output, skill asset loading) must be scoped to the active project.

**Key paths to scope:**

| Current path | Scoped path |
|---|---|
| `223p/ttl/ontology.ttl` (ontology output) | `{PROJECTS_FOLDER}/{folder_path}/ontology.ttl` |
| `223p/ontology.py` (generated Python source) | `{PROJECTS_FOLDER}/{folder_path}/ontology.py` |

**Approach:**
- Add a `get_project_path(tool_context, relative: str) -> str` helper in `agent/utils/project_utils.py`.
- The helper resolves `active_project.folder_path` from state and joins it with `PROJECTS_FOLDER` (read from env var `PROJECTS_FOLDER`, defaulting to `agent/../mapper/uploads` for the dev setup).
- Sub-agents that write ontology files call this helper instead of using hardcoded relative paths.

**Files to create:**
- `agent/utils/project_utils.py`

**Files to modify:**
- `agent/sub_agents/ontology_generator/` _(exit tool: write to project path)_
- `agent/sub_agents/ontology_validator/` _(read/write from project folder)_

---

### 5. Update `master_instruction.md`

Add a section explaining to the master agent:
- It should always read `active_project` from state before any task.
- Graphivac tools automatically use the correct grid from state — no manual intervention needed.
- File outputs go to the project folder, resolved via `get_project_path`.
- If `active_project` is not in state, the agent should ask the user to select a project before proceeding.

**Files to modify:**
- `agent/master_architecture/prompts/master_instruction.md`

---

## Implementation Plan

### Milestone 1 — State-aware Graphivac tools

**Steps:**
1. Update `sync_graphivac_to_agent_tool.py` — state-first Graphivac coord reading with env var fallback.
2. Update `sync_graphivac_tool.py` — same.
3. Manual test: set `active_project` in the frontend to a project with a different `grid_id`, trigger `sync_graphivac_to_agent` — confirm the agent reads the correct grid.

**Files to modify:**
- `agent/tools/sync_graphivac_to_agent_tool.py`
- `agent/tools/sync_graphivac_tool.py`

---

### Milestone 2 — Per-project file paths

**Steps:**
1. Create `agent/utils/project_utils.py` with `get_project_path(tool_context, relative)`.
2. Update ontology generator and validator sub-agents to use `get_project_path` for all file writes.
3. Confirm ontology files land in the correct project subfolder.

**Files to create:**
- `agent/utils/project_utils.py`

**Files to modify:**
- `agent/sub_agents/ontology_generator/` _(exit tool: write to project path)_
- `agent/sub_agents/ontology_validator/` _(exit tool: write to project path)_

---

### Milestone 3 — Per-project model selection

**Steps:**
1. In `agent/main.py`, check `active_project.ai_model_name` in the initial state passed from the frontend at session start via CopilotKit.
2. Use it as `model_name` when calling `create_master_agent`.
3. If absent, fall back to `SHARED_ADK_MODEL` env var.

**Files to modify:**
- `agent/main.py`

---

### Milestone 4 — Master instruction update

**Steps:**
1. Add a "Project Context" section to `master_instruction.md` explaining the `active_project` state key and the expectation to check it before any task.
2. Instruct the agent to inform the user if `active_project` is null and ask them to select one.

**Files to modify:**
- `agent/master_architecture/prompts/master_instruction.md`

---

## Acceptance Criteria

- [ ] `sync_graphivac_to_agent_tool.py` reads Graphivac coords from `tool_context.state["active_project"]` when present.
- [ ] `sync_graphivac_tool.py` reads Graphivac coords from `tool_context.state["active_project"]` when present.
- [ ] Both tools fall back to env vars when `active_project` is not in state (backwards-compatible).
- [ ] `agent/utils/project_utils.py` exists with a `get_project_path` helper.
- [ ] Ontology generator and validator write output files into the active project's folder.
- [ ] The master agent's model is taken from `active_project.ai_model_name` when present, falling back to `SHARED_ADK_MODEL`.
- [ ] `master_instruction.md` instructs the agent to check for `active_project` before starting any task.

---

## Notes & Decisions

- **State-first, env-var fallback**: this pattern is non-breaking and follows the existing convention in the codebase (many tools already check state before falling back to defaults). No env var is removed.
- **No agent restart on project switch**: the agent session is created once when the frontend connects. If the user switches projects, the new `active_project` is sent to the agent via the CopilotKit state update mechanism. The agent reads the updated state on the next tool call — no restart needed.
- **`PROJECTS_FOLDER` in the agent**: the agent process runs from `agent/`, not `mapper/`. The `PROJECTS_FOLDER` env var must also be set for the agent process so `get_project_path` resolves correctly. In the dev setup, this is the same host path. In Docker, it would be a shared volume mount.
- **MCP server is handled separately**: the MCP server has a singleton architecture that requires a different approach. See `13-09`.
