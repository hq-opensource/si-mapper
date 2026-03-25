# 13-10 — MCP Server Project Context

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-25
**Depends on:** `13-01` (env vars externalized), `13-06` (Graphivac grid IDs are known per project)
**See also:** `13-09` (agent project context — handled separately via `ToolContext.state`)

---

> [!WARNING]
> ## ⚠️ MCP Server Is Currently Unused by the Agent
>
> As of 2026-03-25, **the live agent service does not connect to the MCP server at runtime.**
>
> - The master agent (`create_master_agent.py`) instantiates `OntologyGeneratorAgent` and
>   `OntologyValidatorAgent` with **no MCP toolset**. Both agents read grid state via
>   `read_internal_grid` — a local Python function — and write ontology files to disk.
> - The **only** path that still connects to the MCP server is the standalone CLI runner
>   `sub_agents/_223p/run.py`, which is never triggered by the frontend or the ADK service.
> - The frontend (`mapper/`) has **no direct communication** with the MCP server.
>
> **Consequence for this task:** All milestones in this document (the `/config` endpoint,
> the `McpStatusBanner` mismatch warning, the env-var documentation) may be **unnecessary**
> if the MCP server is formally retired or replaced by the internal grid tool pipeline.
>
> **Recommended action before starting any milestone:**
> 1. Confirm whether the MCP server is intended to be kept, reduced to a deployment-only
>    Graphivac canvas helper, or fully removed.
> 2. If the MCP server is retired, replace this task with a clean-up ticket (remove
>    `mcp_server/`, `dev:mcp` scripts, `mcp_utils.py`, and the `_223p` standalone runner).
> 3. If it is kept (e.g. for future canvas operations), the milestones below remain valid
>    but should be re-prioritised accordingly.

---

## Overview

The MCP server (`mcp_server/`) is a FastMCP/Starlette process that manages all Graphivac grid operations performed by the frontend canvas (draw ducts, place equipment, sync grids, etc.). It initialises all of its manager classes at **startup time** with a single static set of Graphivac coordinates loaded from `mcp.env`.

This singleton architecture means:
- All tool calls — no matter which project the user has selected in the UI — target the same Graphivac grid for the lifetime of the process.
- Switching projects in the UI has **no effect** on MCP server behaviour without an env change and a server restart.

This task defines the Phase 13 treatment of the MCP server, documents the architectural constraint as a known limitation, and specifies the concrete changes that bring partial multi-project awareness without requiring a full architectural overhaul.

---

## Current Architecture

```
mcp_server/server/main.py
│
├── load_dotenv("mcp.env")              # ← loads static Graphivac coords
│
├── ORG_ID     = os.getenv("GRAPHIVAC_ORG_ID")
├── PROJECT_ID = os.getenv("GRAPHIVAC_PROJECT_ID")
├── GRID_ID    = os.getenv("GRAPHIVAC_GRID_ID")
│
├── duct_manager   = DuctManager(ORG_ID, PROJECT_ID, GRID_ID, ...)   # ← singleton
├── pipe_manager   = PipeManager(ORG_ID, PROJECT_ID, GRID_ID, ...)
├── grid_manager   = GridManager(ORG_ID, PROJECT_ID, GRID_ID, ...)
├── ...
│
└── All registered tools call manager methods that use these fixed IDs
```

Every tool (`create_duct`, `read_grid`, `create_fan`, etc.) goes through a manager whose Graphivac coordinates are fixed at process startup.

---

## Phase 13 Decision: Static Configuration with Operator Guidance

**Full dynamic per-request grid targeting is deferred.** The Phase 13 constraint is:

> The MCP server targets one Graphivac grid per deployment. That grid must correspond to the active SI-MAPPER project. Switching to a different project requires updating `GRAPHIVAC_GRID_ID` in `mcp.env` and restarting the MCP server container.

This is acceptable for Phase 13 because:
- Single-project deployments (one team, one building) are the primary use case today.
- The agent's own Graphivac tools (`sync_graphivac_to_agent_tool.py`, `sync_graphivac_tool.py`) are fully dynamic (see `13-09`) — they read the correct grid from `ToolContext.state` per session.
- The MCP server tools are primarily used for **canvas rendering** (the frontend's View/Edit tabs embed Graphivac directly), which is already dynamically scoped to the project via the Graphivac iframe URL in `13-07`.

---

## Changes for Phase 13

Despite the static-config approach, several concrete improvements are still required.

### Change 1 — Externalize `mcp.env` Graphivac variables

Currently `mcp.env` contains values that are tied to a single project and committed to source control (or at least not explicitly treated as per-project configuration).

**Steps:**
1. Create `mcp_server/server/mcp.env.example` documenting every variable with its role and expected format. This mirrors the pattern established by `mapper/.env.example` in `13-01`.
2. Confirm `mcp_server/server/mcp.env` is in `.gitignore` (it holds real credentials/IDs).
3. Update `mcp_server/server/README.md` (or add a Configuration section) explaining that `GRAPHIVAC_GRID_ID` must be set to the target project's grid ID for the MCP server to talk to the correct grid.

**Variables to document in `mcp.env.example`:**
```dotenv
# Graphivac API base URL
GRAPHIVAC_BASE_URL=https://graphivac.hvac.io

# Graphivac organisation ID (shared across all projects in a deployment)
GRAPHIVAC_ORG_ID=public

# Graphivac project container ID (shared — holds all grids)
GRAPHIVAC_PROJECT_ID=P-j8QIvTGH7p

# Graphivac grid ID for the currently active SI-MAPPER project
# Change this value and restart the MCP server when switching projects.
GRAPHIVAC_GRID_ID=G-LAiRS3mgp6

# Grid display title (used in PUT requests)
GRAPHIVAC_GRID_TITLE=My HVAC Project
```

**Files to create/modify:**
- `mcp_server/server/mcp.env.example` _(new)_
- `mcp_server/server/README.md` _(add Configuration section)_

---

### Change 2 — Add a `/config` health endpoint

The MCP server exposes no endpoint that reveals which Graphivac grid it is currently configured for. This makes it impossible for the frontend to warn the user when the MCP server's grid differs from the active project's grid.

**Steps:**
1. Add a `GET /config` route to the Starlette app in `mcp_server/server/main.py`.
2. The route returns the currently loaded Graphivac coordinates (non-sensitive — grid IDs are not secrets):
   ```json
   {
     "graphivac_base_url": "https://graphivac.hvac.io",
     "graphivac_org_id": "public",
     "graphivac_project_id": "P-j8QIvTGH7p",
     "graphivac_grid_id": "G-LAiRS3mgp6",
     "graphivac_grid_title": "My HVAC Project"
   }
   ```
3. The frontend calls this endpoint on project switch and compares `graphivac_grid_id` against `activeProject.graphivac_grid_id`. If they differ, a warning banner is shown (see Change 3).

**Files to modify:**
- `mcp_server/server/main.py` _(add GET /config route to the Starlette routing table)_

---

### Change 3 — Frontend mismatch warning

When the active project's Graphivac grid ID does not match the MCP server's configured grid ID, the user must be informed — otherwise the agent's canvas tools will write to the wrong grid.

**Steps:**
1. In `mapper/src/app/page/components/AgentNavbar.tsx` (or a dedicated status component), add a polling effect that calls `GET {MCP_SERVER_URL}/config` every 30 seconds.
2. Compare the returned `graphivac_grid_id` with `activeProject.graphivac_grid_id`.
3. If they differ, show a persistent warning banner:
   > ⚠️ The MCP server is configured for a different project grid (`G-XXXXXX`). Canvas tools will write to the wrong grid. Update `GRAPHIVAC_GRID_ID` in `mcp.env` and restart the MCP server.
4. If they match, no banner is shown.

**New env var (client-side, for the frontend to know the MCP server URL):**

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_MCP_SERVER_URL` | `http://localhost:8080` | Public URL of the MCP server, used by the browser to call `/config` |

Add this to `mapper/.env.example` and `mapper/frontend.env.example`.

**Files to modify:**
- `mapper/src/app/page/components/AgentNavbar.tsx` _(or a new `McpStatusBanner.tsx`)_
- `mapper/.env.example`
- `mapper/frontend.env.example`

---

### Change 4 — Document the restart procedure

Add clear operator documentation so switching projects is a guided, low-friction process — even if it requires a restart.

**Content to add to `mcp_server/server/README.md`:**

```markdown
## Switching Projects

The MCP server targets one Graphivac grid at a time. To switch the active project:

1. Find the new project's `graphivac_grid_id` in the SI-MAPPER project selector (or in `project.json`).
2. Update `GRAPHIVAC_GRID_ID` in `mcp_server/server/mcp.env`.
3. Restart the MCP server:
   - Dev: stop and re-run `uv run server/main.py`
   - Docker: `docker compose restart si-mapper-mcp`
4. The frontend will automatically detect the update via the `/config` health endpoint and clear the mismatch warning.
```

**Files to modify:**
- `mcp_server/server/README.md`

---

## Deferred: Dynamic Per-Request Grid Targeting

The architectural change required for true dynamic multi-project support in the MCP server is:

**Replace singleton manager instances with per-request factory construction** — each tool call receives the `grid_id` as a parameter, constructs a scoped manager, executes the operation, and discards the manager.

This would require:
1. Changing every manager class to accept `grid_id` as a method parameter instead of a constructor argument.
2. Changing every tool registration to accept `grid_id` as an input parameter.
3. The frontend passing `grid_id` with every MCP tool call (not currently supported by the FastMCP/MCP protocol without custom metadata).
4. Evaluating whether the MCP protocol supports per-call context injection or whether a custom middleware layer is needed.

**Recorded as a deferred item in:** `deferred-items.md`

---

## Implementation Plan

### Milestone 1 — `mcp.env.example` and README documentation

**Steps:**
1. Create `mcp_server/server/mcp.env.example` with all variables documented.
2. Add a Configuration + Switching Projects section to `mcp_server/server/README.md`.
3. Confirm `mcp.env` is gitignored.

**Files to create/modify:**
- `mcp_server/server/mcp.env.example` _(new)_
- `mcp_server/server/README.md`

---

### Milestone 2 — `/config` health endpoint

**Steps:**
1. Add a `GET /config` Starlette route to `mcp_server/server/main.py` that returns the loaded `ORG_ID`, `PROJECT_ID`, `GRID_ID`, `GRID_TITLE`, `BASE_URL` as JSON.
2. Add CORS header to allow the frontend (on a different port) to call it.
3. Manual test: `curl http://localhost:8080/config` — confirm JSON response.

**Files to modify:**
- `mcp_server/server/main.py`

---

### Milestone 3 — Frontend mismatch warning

**Steps:**
1. Add `NEXT_PUBLIC_MCP_SERVER_URL` to `mapper/.env.example` and `mapper/frontend.env.example`.
2. Create `mapper/src/app/page/components/McpStatusBanner.tsx` — polls `/config`, compares grid IDs, renders the warning.
3. Include `McpStatusBanner` in `AgentNavbar.tsx` or the main layout.

**Files to create:**
- `mapper/src/app/page/components/McpStatusBanner.tsx`

**Files to modify:**
- `mapper/src/app/page/components/AgentNavbar.tsx`
- `mapper/.env.example`
- `mapper/frontend.env.example`

---

### Milestone 4 — Deferred items file

**Steps:**
1. Confirm `deferred-items.md` documents dynamic per-request MCP grid targeting as a primary deferred item with scope and rationale.

**Files to verify:**
- `.planning/phases/13-multi-projects-support/deferred-items.md`

---

## Acceptance Criteria

- [ ] `mcp_server/server/mcp.env.example` exists and documents all required variables including `GRAPHIVAC_GRID_ID`.
- [ ] `mcp_server/server/README.md` includes a "Switching Projects" section with restart instructions.
- [ ] `GET /config` endpoint is available on the MCP server and returns the current Graphivac coordinates as JSON.
- [ ] The frontend displays a warning banner when the MCP server's `graphivac_grid_id` does not match the active project's grid ID.
- [ ] The warning banner clears automatically when the MCP server is restarted with the correct `GRAPHIVAC_GRID_ID`.
- [ ] `NEXT_PUBLIC_MCP_SERVER_URL` is documented in both `.env.example` and `frontend.env.example`.
- [ ] Dynamic per-request grid targeting is documented as a deferred item.

---

## Notes & Decisions

- **Why not restart automatically?** The MCP server is a separate process (and Docker container in production). Restarting it from the Next.js frontend would require either a Docker socket mount (a significant security exposure) or a dedicated management API. The restart-by-operator approach is simpler and safer for Phase 13.
- **`/config` is not authenticated**: grid IDs are not sensitive — they appear in Graphivac iframe URLs already. The endpoint is safe to expose without auth.
- **CORS on `/config`**: the MCP server already includes a blanket CORS middleware (`allow_origins=["*"]`), so the `/config` route inherits this without extra config.
- **`McpStatusBanner` polling interval**: 30 seconds is sufficient — the user triggers a restart manually and waits a few seconds. There is no value in polling faster.
- **Relationship to `13-09`**: the agent's own Graphivac sync tools are fully dynamic (per `13-09`). The MCP server tools are used for canvas operations that the agent triggers via the internal grid → Graphivac sync flow. In practice, as long as both the MCP server and the agent target the same grid, everything is consistent. The mismatch warning catches the case where the operator forgot to restart the MCP server after switching projects.


