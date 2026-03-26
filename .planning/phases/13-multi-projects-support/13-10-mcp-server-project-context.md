# 13-10 — MCP Server System Context

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-01` (env vars externalized), `13-05` (system grid IDs are known per system)
**See also:** `13-09` (agent system context — handled separately via `ToolContext.state`)

---

> [!WARNING]
> ## ⚠️ MCP Server Is Currently Unused by the Agent
>
> As of 2026-03-25, **the live agent service does not connect to the MCP server at runtime.**
>
> - The master agent instantiates `OntologyGeneratorAgent` and `OntologyValidatorAgent` with
>   **no MCP toolset**. Both agents read grid state via `read_internal_grid` — a local Python
>   function — and write ontology files to disk.
> - The **only** path that still connects to the MCP server is the standalone CLI runner
>   `sub_agents/_223p/run.py`, which is never triggered by the frontend or the ADK service.
> - The frontend (`mapper/`) has **no direct communication** with the MCP server.
>
> **Recommended action before starting any milestone:**
> 1. Confirm whether the MCP server is intended to be kept, reduced, or fully removed.
> 2. If retired, replace this task with a clean-up ticket.
> 3. If kept, the milestones below remain valid.

---

## Overview

The MCP server (`mcp_server/`) initialises all manager classes at startup with a single static set of Graphivac coordinates from `mcp.env`. This means all tool calls target the same Graphivac grid for the lifetime of the process.

In the new model:
- A **Graphivac Grid** corresponds to one **System** (not a project).
- `GRAPHIVAC_GRID_ID` in `mcp.env` must be set to the **active system's** `graphivac_grid_id`.
- `GRAPHIVAC_PROJECT_ID` in `mcp.env` must be set to the **active project's** `graphivac_project_id`.
- `GRAPHIVAC_ORG_ID` in `mcp.env` continues to be the **deployment-wide organisation ID** — a constant that never changes.

---

## Current Architecture

```
mcp_server/server/main.py
│
├── load_dotenv("mcp.env")
│
├── ORG_ID     = os.getenv("GRAPHIVAC_ORG_ID")     ← deployment constant
├── PROJECT_ID = os.getenv("GRAPHIVAC_PROJECT_ID") ← active project's graphivac_project_id
├── GRID_ID    = os.getenv("GRAPHIVAC_GRID_ID")    ← active system's graphivac_grid_id
│
├── duct_manager   = DuctManager(ORG_ID, PROJECT_ID, GRID_ID, ...)   ← singleton
└── ...
```

---

## Phase 13 Decision: Static Configuration with Operator Guidance

**Full dynamic per-request grid targeting is deferred.** The Phase 13 constraint is:

> The MCP server targets one Graphivac grid (= one SI-Mapper **system**) per deployment. Switching to a different system requires updating `GRAPHIVAC_GRID_ID` (and possibly `GRAPHIVAC_PROJECT_ID`) in `mcp.env` and restarting the MCP server container.

`GRAPHIVAC_ORG_ID` never needs to change — it is deployment-wide and constant.

---

## Changes for Phase 13

### Change 1 — Externalize `mcp.env` and document the system concept

**Steps:**
1. Create `mcp_server/server/mcp.env.example` documenting every variable.
2. Confirm `mcp_server/server/mcp.env` is in `.gitignore`.
3. Update `mcp_server/server/README.md` to explain that `GRAPHIVAC_GRID_ID` maps to a **system's** grid and `GRAPHIVAC_PROJECT_ID` maps to the **project's** Graphivac project.

**Variables to document in `mcp.env.example`:**
```dotenv
# Graphivac API base URL
GRAPHIVAC_BASE_URL=https://graphivac.hvac.io

# Graphivac organisation ID — deployment-wide constant, never changes
GRAPHIVAC_ORG_ID=public

# Graphivac project ID — corresponds to the active SI-Mapper project's graphivac_project_id
# Find this in the project's project.json or the SI-Mapper project management page.
GRAPHIVAC_PROJECT_ID=P-j8QIvTGH7p

# Graphivac grid ID — corresponds to the active SI-Mapper system's graphivac_grid_id
# Find this in the system's system.json or the SI-Mapper project management page.
# Change this value and restart the MCP server when switching systems.
GRAPHIVAC_GRID_ID=G-LAiRS3mgp6

# Grid display title (used in PUT requests)
GRAPHIVAC_GRID_TITLE=Chilled Water Plant
```

**Files to create/modify:**
- `mcp_server/server/mcp.env.example` _(new)_
- `mcp_server/server/README.md`

---

### Change 2 — Add a `/config` health endpoint

**Steps:**
1. Add `GET /config` to the Starlette app in `mcp_server/server/main.py`.
2. Returns the currently loaded Graphivac coordinates:
   ```json
   {
     "graphivac_base_url": "https://graphivac.hvac.io",
     "graphivac_org_id": "public",
     "graphivac_project_id": "P-j8QIvTGH7p",
     "graphivac_grid_id": "G-LAiRS3mgp6",
     "graphivac_grid_title": "Chilled Water Plant"
   }
   ```
3. The frontend calls this endpoint and compares `graphivac_grid_id` against `activeSystem.graphivac_grid_id`. If they differ, a warning banner is shown.

**Files to modify:**
- `mcp_server/server/main.py`

---

### Change 3 — Frontend mismatch warning

When the active system's grid ID does not match the MCP server's configured grid ID, the user must be informed.

**Steps:**
1. In `AgentNavbar.tsx` (or a dedicated `McpStatusBanner.tsx`), poll `GET {MCP_SERVER_URL}/config` every 30 seconds.
2. Compare returned `graphivac_grid_id` with `activeSystem.graphivac_grid_id`.
3. If they differ, show a persistent warning:
   > ⚠️ The MCP server is configured for a different system grid (`G-XXXXXX`). Canvas tools will write to the wrong system. Update `GRAPHIVAC_GRID_ID` in `mcp.env` and restart the MCP server.

**New env var:**

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_MCP_SERVER_URL` | `http://localhost:8080` | Public URL of the MCP server |

**Files to modify:**
- `mapper/src/app/page/components/AgentNavbar.tsx` _(or new `McpStatusBanner.tsx`)_
- `mapper/.env.example`
- `mapper/frontend.env.example`

---

### Change 4 — Document the restart procedure

Add to `mcp_server/server/README.md`:

```markdown
## Switching Systems

The MCP server targets one Graphivac grid (one SI-Mapper system) at a time.

To switch the active system:

1. Find the new system's `graphivac_grid_id` in the SI-Mapper project management page
   (or in `system.json` under `PROJECTS_FOLDER/{project}/{system}/`).
2. If the new system is in a different project, also update `GRAPHIVAC_PROJECT_ID`
   to the new project's `graphivac_project_id`.
3. `GRAPHIVAC_ORG_ID` never needs to change — it is deployment-wide.
4. Update `mcp_server/server/mcp.env` with the new values.
5. Restart the MCP server:
   - Dev: stop and re-run `uv run server/main.py`
   - Docker: `docker compose restart si-mapper-mcp`
6. The frontend will detect the update via the `/config` health endpoint and clear
   the mismatch warning automatically.
```

---

## Deferred: Dynamic Per-Request Grid Targeting

**Recorded in `deferred-items.md`.**

True dynamic multi-system support would require:
1. Changing every manager class to accept `grid_id` as a method-level parameter.
2. Updating every tool registration to accept `grid_id` as a parameter.
3. Evaluating whether FastMCP supports per-call context injection.
4. Propagating the active system's grid ID from the frontend → agent session → MCP tool call.

---

## Implementation Plan

### Milestone 1 — `mcp.env.example` and README update

**Steps:**
1. Create `mcp_server/server/mcp.env.example` with all variables documented, using system/project terminology.
2. Add "Switching Systems" section to `mcp_server/server/README.md`.

---

### Milestone 2 — `/config` health endpoint

**Steps:**
1. Add `GET /config` to `mcp_server/server/main.py`.
2. Add CORS header (inherits blanket CORS middleware).
3. Test: `curl http://localhost:8080/config`.

---

### Milestone 3 — Frontend mismatch warning

**Steps:**
1. Add `NEXT_PUBLIC_MCP_SERVER_URL` to `mapper/.env.example` and `mapper/frontend.env.example`.
2. Create `mapper/src/app/page/components/McpStatusBanner.tsx` — polls `/config`, compares `graphivac_grid_id` with `activeSystem.graphivac_grid_id`.
3. Include in `AgentNavbar.tsx`.

---

## Acceptance Criteria

- [ ] `mcp_server/server/mcp.env.example` documents all variables, clarifying that `GRAPHIVAC_GRID_ID` is a system's grid and `GRAPHIVAC_PROJECT_ID` is a project's Graphivac project.
- [ ] `mcp.env.example` notes that `GRAPHIVAC_ORG_ID` is a deployment constant and never changes.
- [ ] `mcp_server/server/README.md` includes a "Switching Systems" section with step-by-step restart instructions.
- [ ] `GET /config` is available and returns the current coordinates as JSON.
- [ ] The frontend shows a warning when `activeSystem.graphivac_grid_id` does not match the MCP server's `graphivac_grid_id`.
- [ ] The warning banner uses the word "system" (not "project") to match the SI-Mapper terminology.
- [ ] `NEXT_PUBLIC_MCP_SERVER_URL` is documented in both `.env.example` files.
- [ ] Dynamic per-request grid targeting is documented as a deferred item.

---

## Notes & Decisions

- **Terminology update**: the previous spec used "project" loosely for what is now called a "system" (grid). All documentation in this task uses the correct terms: system = grid, project = Graphivac project.
- **`GRAPHIVAC_ORG_ID` is deployment-constant**: it is documented as such in `mcp.env.example` and operators are explicitly told it never needs to change.
- **The mismatch warning compares against `activeSystem`**: now that systems are the granular unit of work, the comparison is against the active system's grid, not the active project.
- **Restart-by-operator is acceptable for Phase 13**: see `13-00` for rationale.
