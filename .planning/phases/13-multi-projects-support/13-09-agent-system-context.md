# 13-09 — Agent System Context Awareness

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-26
**Depends on:** `13-07` (active project and system are in CopilotKit state before the agent can read them)
**See also:** `13-99` (MCP server project context — handled separately)

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

> The MCP server has a separate treatment — see `13-99`.

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

### 2b. `agent/tools/metadata_tools.py`

`write_metadata` and `write_metadata_batch` both accept `ToolContext` but delegate to the private `_graphivac_url()` helper, which reads project and grid IDs purely from env vars:

```python
def _graphivac_url() -> str:
    base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = os.getenv("GRAPHIVAC_GRID_ID", "")
    return f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
```

**Fix:** pass `tool_context` to `_graphivac_url` (or inline the URL construction inside each tool) and apply the same state-first pattern:

```python
def _graphivac_url(tool_context: ToolContext) -> str:
    active_project = tool_context.state.get("active_project") or {}
    active_system  = tool_context.state.get("active_system") or {}
    base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = active_project.get("graphivac_project_id") or os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = active_system.get("graphivac_grid_id")     or os.getenv("GRAPHIVAC_GRID_ID", "")
    return f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
```

This affects the BACnet and control metadata written by the bacnet, control and electricity sub-agents via the master agent's `write_metadata` / `write_metadata_batch` tools.

---

### 2c. Non-ontology sub-agents — no further changes needed

The following sub-agents do **not** require individual changes beyond what is covered by §2b and §4c:

| Sub-agent | What it does | Covered by |
|---|---|---|
| `bacnet/` | Reads uploads → extracts BACnet points → master writes metadata | §2b (`metadata_tools.py`), §4c (`ingest_category_tool.py`) |
| `control/` | Reads uploads → extracts control logic → master writes metadata | §2b, §4c |
| `electricity/` | Reads uploads → extracts electrical data → master writes metadata | §2b, §4c |
| `equipment/` | Reads uploads → places HVAC equipment on grid | §4c |
| `horizontal_ducts/` | Reads uploads → draws horizontal ducts | §4c |
| `vertical_ducts/` | Reads uploads → draws vertical ducts | §4c |

These agents use only:
- `ingest_category_files_tool` — reads from `mapper/uploads/` → fixed once in §4c
- `load_artifacts` — ADK built-in, no project-specific I/O
- `update_step` / `update_status` / `update_state` — state-only, no file I/O
- `exit_loop_level_4` — loop control only

Their Graphivac output flows through the **master agent's** `write_metadata` / `write_metadata_batch` tools, fixed in §2b. The sub-agents themselves are not aware of Graphivac coordinates.

---

### 2d. `agent/utils/grid_sync_agent_to_graphivac.py` ⚠️ Critical

This file is **the most critical gap**. It is not an explicit tool — it is the **background auto-sync** invoked from the model callback (`callback_utils.py`) on every final model response. It silently PUTs the internal grid to Graphivac using a private helper that reads project and grid IDs purely from env vars:

```python
def _put_grid_to_graphivac(raw_edn_grid: dict) -> int:
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = os.getenv("GRAPHIVAC_GRID_ID", "")
    ...
```

Because this runs automatically after every LLM turn (not just when the agent explicitly calls a sync tool), **even if `sync_graphivac_tool.py` and `metadata_tools.py` are fixed, the background push will still go to the env-var grid**. This would corrupt the wrong project's data silently.

**Fix:** `_run_sync_out` already has access to `callback_context.state`, which carries `active_project` and `active_system`. Pass `callback_context.state` to `_put_grid_to_graphivac` and apply the state-first pattern:

```python
def _put_grid_to_graphivac(raw_edn_grid: dict, state: dict) -> int:
    active_project = state.get("active_project") or {}
    active_system  = state.get("active_system") or {}
    base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = active_project.get("graphivac_project_id") or os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = active_system.get("graphivac_grid_id")     or os.getenv("GRAPHIVAC_GRID_ID", "")
    ...
```

---

### 2e. `agent/master_architecture/tools/capture_frontend_state_tool.py`

Builds the Graphivac canvas view URL and saves screenshots to disk using hardcoded env vars and a hardcoded path. Has `ToolContext` available but does not use it.

**Issue 1 — Graphivac URL:**
```python
project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
grid_id    = os.getenv("GRAPHIVAC_GRID_ID", "")
view_url = f"{site_url}/o/{org_id}/p/{project_id}/g/{grid_id}?iframe=t&init-zoom=t"
```
Apply same state-first pattern using `tool_context.state`.

**Issue 2 — Snapshot save path:**
```python
snapshots_dir = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "snapshots"
```
Scope to the active project's folder: `{PROJECTS_FOLDER}/{proj_folder}/uploads/snapshots/`. Fall back to `mapper/uploads/snapshots/` when no active project is in state.

---

### 2f. `agent/master_architecture/tools/load_ttl_to_neo4j_tool.py`

Reads the TTL file from a hardcoded path that points to the old shared uploads location:

```python
ttl_path = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "ttl" / "latest_ontology.ttl"
```

This must be updated to read from the same path the ontology validator writes to — the active system's TTL output folder:

```python
# Preferred: system-scoped TTL (written by ontology validator)
ttl_path = get_system_path(tool_context, os.path.join("ttl", "ontology.ttl"))
# Fallback: legacy shared uploads path
if not Path(ttl_path).exists():
    ttl_path = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "ttl" / "latest_ontology.ttl"
```

---

### 2g. `agent/master_architecture/tools/ingest_category_tool.py` — duplicate

There are **two copies** of `IngestCategoryFilesTool` with identical `mapper/uploads/` hardcoding:
- `agent/sub_agents/tools/ingest_category_tool.py` — used by all sub-agents
- `agent/master_architecture/tools/ingest_category_tool.py` — used by the master LLM agent

Both need the same uploads-path scoping fix described in §4c. Consider consolidating them into a single shared module to avoid the divergence recurring.

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
| `223p/src/ontology.py` | `{PROJECTS_FOLDER}/{proj_folder}/{sys_folder}/src/ontology.py` |
| `223p/ttl/ontology.ttl` | `{PROJECTS_FOLDER}/{proj_folder}/{sys_folder}/ttl/ontology.ttl` |

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

#### 4a. Primary file: `agent/sub_agents/_223p/tool.py`

This is the **central file** where the ontology file paths are computed as module-level constants at import time:

```python
ONTOLOGY_FILE  = os.path.join(_PROJECT_ROOT, "223p", "src", "ontology.py")
TTL_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "223p", "ttl")
```

All three ontology functions (`read_ontology`, `write_ontology`, `execute_ontology`) reference these constants directly. Since module-level constants cannot read `ToolContext`, the functions must be updated to accept `tool_context: ToolContext` and resolve paths at call time via `get_system_path`:

```python
def write_ontology(content: str, tool_context: ToolContext) -> str:
    ontology_file = get_system_path(tool_context, os.path.join("src", "ontology.py"))
    ...

def read_ontology(tool_context: ToolContext) -> str:
    ontology_file = get_system_path(tool_context, os.path.join("src", "ontology.py"))
    ...

def execute_ontology(tool_context: ToolContext) -> str:
    ontology_file = get_system_path(tool_context, os.path.join("src", "ontology.py"))
    ttl_output_dir = get_system_path(tool_context, "ttl")
    ...
```

The module-level `ONTOLOGY_FILE` and `TTL_OUTPUT_DIR` constants can be kept as fallbacks (for code that imports them directly) but should no longer be used by the three tool functions.

#### 4b. Sub-agent files to verify after `tool.py` is updated

Because all ontology file I/O flows through `_223p/tool.py`, updating that file is sufficient for both the standalone sub-agents **and** the pipeline sub-agents. However, the following files should still be verified to ensure they pass `tool_context` correctly when calling the updated functions:

**Standalone sub-agents** (used by `create_master_agent.py`):
- `agent/sub_agents/ontology_generator/agent.py`
- `agent/sub_agents/ontology_validator/agent.py`

**Pipeline sub-agents** (used by `sub_agents/_223p/agent.py` — the `Ontology223PSequentialAgent`):
- `agent/sub_agents/_223p/generator/agent.py`
- `agent/sub_agents/_223p/validator/agent.py`
- `agent/sub_agents/_223p/agent.py` — has a hardcoded `_PIPELINE_MODEL`; see Milestone 3.

Both execution paths (standalone and pipeline) call the same `_223p/tool.py` functions, so fixing `tool.py` covers all four agent files at once. The per-agent verification is to confirm `tool_context` is threaded through correctly.

#### 4c. `agent/sub_agents/tools/ingest_category_tool.py`

This tool reads uploaded files from `mapper/uploads/{category}/`, computed at call time relative to the repository root. In multi-project mode, each project or system has its own set of uploaded reference documents.

**Current behaviour:** path is always `<repo_root>/mapper/uploads/{category}/`.

**Required change:** resolve uploads relative to the active project:
```
{PROJECTS_FOLDER}/{active_project.folder_path}/uploads/{category}/
```

Use `get_system_path` or a simpler `get_project_path` helper (one level up, without the system folder, since uploads are per-project not per-system). Fall back to `mapper/uploads/{category}` when no active project is in state, preserving dev compatibility.

> **Decision needed:** confirm whether uploads are per-project or per-system before implementing. The scoping level (project vs. system) determines whether to use `get_project_path` or `get_system_path`.

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
3. Update `metadata_tools.py` — pass `tool_context` to `_graphivac_url` and apply the same state-first pattern.
4. **Update `utils/grid_sync_agent_to_graphivac.py` ⚠️** — pass `callback_context.state` to `_put_grid_to_graphivac` and apply state-first for `project_id` and `grid_id`. This is the background auto-sync triggered after every LLM turn; if not fixed, it will silently push data to the wrong Graphivac grid.
5. Update `master_architecture/tools/capture_frontend_state_tool.py` — state-first for `project_id` and `grid_id` when building the view URL.
6. Test: set `active_system` in the frontend with a different `grid_id`, trigger sync, a metadata write, and a screenshot capture — confirm the correct grid is used in all cases.

---

### Milestone 2 — `get_system_path` helper and scoped file access

**Steps:**
1. Create `agent/utils/project_utils.py` with `get_system_path(tool_context, relative)`.
2. Update `agent/sub_agents/_223p/tool.py` — the **primary change**: make `read_ontology`, `write_ontology`, and `execute_ontology` accept `tool_context: ToolContext` and resolve paths via `get_system_path` instead of the module-level `ONTOLOGY_FILE` / `TTL_OUTPUT_DIR` constants.
3. Verify all four agent files pass `tool_context` through correctly when calling those functions:
   - `agent/sub_agents/ontology_generator/agent.py` (standalone)
   - `agent/sub_agents/ontology_validator/agent.py` (standalone)
   - `agent/sub_agents/_223p/generator/agent.py` (pipeline)
   - `agent/sub_agents/_223p/validator/agent.py` (pipeline)
4. Update `agent/master_architecture/tools/load_ttl_to_neo4j_tool.py` — resolve the TTL path via `get_system_path(tool_context, "ttl/ontology.ttl")`; fall back to `mapper/uploads/ttl/latest_ontology.ttl` for backward compatibility.
5. Update `agent/master_architecture/tools/capture_frontend_state_tool.py` — scope the snapshot save path to the active project's uploads folder.
6. Update **both** `ingest_category_tool.py` copies — resolve the uploads directory from `active_project.folder_path` (pending decision on project vs. system scoping from §2g):
   - `agent/sub_agents/tools/ingest_category_tool.py`
   - `agent/master_architecture/tools/ingest_category_tool.py`
   Consider consolidating them into one shared module.
7. Confirm ontology files land in `PROJECTS_FOLDER/{proj}/{sys}/src/ontology.py` and `PROJECTS_FOLDER/{proj}/{sys}/ttl/ontology.ttl`.

---

### Milestone 3 — Per-system model selection

**Steps:**
1. In `agent/main.py`, read `active_system.ai_model_name` from initial state; pass to `create_master_agent` as `model_name`.
2. Fall back to `SHARED_ADK_MODEL` env var if absent.
3. In `agent/sub_agents/_223p/agent.py`, ensure `_PIPELINE_MODEL` / `_STANDALONE_DEFAULT_MODEL` are also overridable by the injected `model_name` (they already accept it as a constructor parameter — confirm no hardcoded fallback silently wins).

---

### Milestone 4 — Master instruction update

**Steps:**
1. Add "System Context" section to `master_instruction.md`.
2. Instruct the agent to check for both `active_project` and `active_system` and ask the user if either is null.

> **Runtime model switching (live swap without agent restart) is out of scope for this step — see `13-10`.**

---

## Acceptance Criteria

**Graphivac tools (all must use state-first, env-var fallback):**
- [ ] `sync_graphivac_to_agent_tool.py` reads `graphivac_project_id` from `state["active_project"]` and `graphivac_grid_id` from `state["active_system"]` when present.
- [ ] `sync_graphivac_tool.py` applies the same pattern.
- [ ] `metadata_tools.py` — `_graphivac_url` accepts `tool_context` and applies the same state-first pattern; `write_metadata` and `write_metadata_batch` pass it through.
- [ ] `utils/grid_sync_agent_to_graphivac.py` — `_put_grid_to_graphivac` accepts `state` and uses state-first for `project_id` and `grid_id`. Background auto-sync never pushes to the env-var grid when a different grid is active in state.
- [ ] `master_architecture/tools/capture_frontend_state_tool.py` — view URL uses `project_id` and `grid_id` from state.
- [ ] `org_id` is **always** read from `GRAPHIVAC_ORG_ID` env var — never from state, in any of the above files.
- [ ] All tools fall back to env vars (`GRAPHIVAC_PROJECT_ID`, `GRAPHIVAC_GRID_ID`) when state keys are absent.

**File-system scoping:**
- [ ] `agent/utils/project_utils.py` exists with `get_system_path`.
- [ ] `agent/sub_agents/_223p/tool.py` — `read_ontology`, `write_ontology`, and `execute_ontology` accept `tool_context: ToolContext` and resolve file paths via `get_system_path` at call time (not from module-level constants).
- [ ] Both standalone sub-agents (`ontology_generator/`, `ontology_validator/`) and both pipeline sub-agents (`_223p/generator/`, `_223p/validator/`) pass `tool_context` through to those functions correctly.
- [ ] Ontology files land in `PROJECTS_FOLDER/{proj}/{sys}/src/ontology.py` and `PROJECTS_FOLDER/{proj}/{sys}/ttl/ontology.ttl` when the active system is set.
- [ ] `master_architecture/tools/load_ttl_to_neo4j_tool.py` reads the TTL from `PROJECTS_FOLDER/{proj}/{sys}/ttl/ontology.ttl` when the active system is set.
- [ ] `master_architecture/tools/capture_frontend_state_tool.py` saves screenshots to the active project's folder; falls back to `mapper/uploads/snapshots/` when no active project is in state.
- [ ] **Both** `ingest_category_tool.py` copies resolve the uploads directory from the active project state; fall back to `mapper/uploads/` when absent.

**Model selection:**
- [ ] The master agent's model is taken from `active_system.ai_model_name`, falling back to `SHARED_ADK_MODEL`.
- [ ] Runtime model switching (live swap) is handled in `13-10` — no acceptance criteria here.

**Instructions:**
- [ ] `master_instruction.md` instructs the agent to check for both `active_project` and `active_system` before starting any task.

---

## Notes & Decisions

- **`GRAPHIVAC_ORG_ID` is env-only, always**: this is the defining constraint from `13-00`. The agent never reads it from state, and the frontend never sends it. Any code path that currently passes `org_id` from outside env should be treated as a bug.
- **State-first, env-var fallback**: non-breaking. Old clients, tests, and direct agent invocations continue to work via env vars.
- **No agent restart on system switch**: Graphivac coordinates and folder paths switch immediately (read from state at call time). Only the model is session-fixed.
- **`PROJECTS_FOLDER` must be set for the agent process**: in dev it's the same host path as for the frontend. In Docker it's a shared volume mount.
- **Two-level path**: the system folder is nested inside the project folder. `get_system_path` handles both levels.
- **Background auto-sync is the highest-risk item**: `grid_sync_agent_to_graphivac.py` runs silently after every LLM turn. Must be fixed before any multi-project testing — a wrong `GRAPHIVAC_GRID_ID` env var would corrupt another project's canvas without any explicit tool call.
- **Two copies of `ingest_category_tool.py`**: `sub_agents/tools/` and `master_architecture/tools/` are identical. The fix should be applied to both, or they should be consolidated into `agent/utils/` and imported from one place.
- **MCP server is handled separately**: see `13-99`.
- **Runtime model switching**: the session-scoped model selection in Milestone 3 is sufficient for 13-09. True live swapping (`AgentHolder`, `POST /model`, `asyncio.Lock`) is deferred to `13-10`.
