# Phase 13 — Deferred Items

Items that were explicitly considered during Phase 13 planning but are out of scope for this phase. Each entry records **what** was deferred, **why**, and **what a future implementation would require**.

---

## D-01 — Dynamic Per-Request Grid Targeting in the MCP Server

**Deferred from:** `13-08`
**Category:** Architecture

### What was deferred

Making the MCP server target different Graphivac grids on a per-tool-call basis, so that switching projects in the UI instantly affects all MCP canvas operations without a server restart.

### Why deferred

The MCP server initialises all manager classes (`DuctManager`, `PipeManager`, `GridManager`, etc.) as **singletons at startup** with a fixed set of Graphivac coordinates. The current MCP protocol (as used via FastMCP) does not provide a standard mechanism for injecting per-call context (such as `grid_id`) outside of explicit tool parameters.

Implementing dynamic targeting would require:

1. **Manager refactor**: change every manager class to accept `grid_id` (and optionally `org_id`, `project_id`) as method-level parameters rather than constructor arguments.
2. **Tool parameter additions**: every registered MCP tool would need a `grid_id` parameter, making the tool surface more complex for the AI caller.
3. **Protocol evaluation**: determine whether FastMCP / the MCP protocol supports per-call metadata injection (e.g. HTTP headers, session context) as an alternative to explicit parameters.
4. **State propagation**: the active project's grid ID would need to travel from the frontend → agent session → MCP tool call on every invocation. This crosses three process boundaries.

The risk of introducing subtle bugs across the full MCP tool surface during Phase 13 outweighs the benefit, given that single-project deployments are still the primary use case.

### Phase 13 mitigation

- The MCP server targets one grid per deployment, configured via `GRAPHIVAC_GRID_ID` in `mcp.env`.
- Switching projects requires updating this variable and restarting the MCP container.
- A `/config` health endpoint and a frontend mismatch warning banner (see `13-08`) make the manual process safe and observable.

### What a future phase would require

- Evaluate FastMCP's support for per-session or per-request context.
- Refactor `DuctManager`, `PipeManager`, `GridManager`, `PipeManager`, `CustomManager`, `ElectricManager`, `MetadataManager` to accept `grid_id` as a call-time argument.
- Update all tool registrations in `duct_tools.py`, `pipe_tools.py`, `grid_tools.py`, etc.
- Update the agent's internal grid → Graphivac sync flow to pass the active project's `grid_id` at call time.
- Remove the mismatch warning banner (no longer needed once switching is instant).

---

## D-02 — Mid-Session Project Switching for the Agent

**Deferred from:** `13-07`
**Category:** UX / Agent Architecture

### What was deferred

Allowing the user to switch the active project while an agent session is already in progress, with the agent immediately picking up the new project context for its next task.

### Why deferred

The ADK agent (`agent/main.py`) is created once per session in `create_app()`. The model name (`model_name` parameter to `create_master_agent`) is fixed at session creation time. If the user switches to a project that uses a different `ai_model_name`, the agent continues to use the old model until the session is restarted.

For CopilotKit state values that are read at tool call time (Graphivac grid IDs, folder paths), mid-session switching works correctly — the updated `active_project` in state is read on the next tool call. The model selection is the only session-fixed value.

### Phase 13 mitigation

- Graphivac coordinates and folder paths switch immediately (read from state at call time).
- Model switching requires a page refresh to start a new session.
- The project selector UI (see `13-06`) can display a note: "Model changes take effect on the next session."

### What a future phase would require

- Evaluate whether ADK supports hot-swapping the model mid-session.
- Alternatively, trigger a clean session restart (disconnect + reconnect CopilotKit) when the user switches to a project with a different model.

---

## D-03 — Graphivac Grid Deletion via API

**Deferred from:** `13-05`
**Category:** Graphivac API

### What was deferred

Automatically deleting the Graphivac grid when a SI-MAPPER project is deleted via `DELETE /api/projects/[id]`.

### Why deferred

The Graphivac REST API's support for grid deletion was not confirmed at planning time. The `mcp_server/graphivac/api.json` file must be inspected to verify whether a `DELETE /orgs/:org/projects/:proj/grids/:grid` endpoint exists and what its behaviour is.

### Phase 13 mitigation

- The `deleteGrid` function in `mapper/src/lib/graphivac-client.ts` (see `13-05`) logs a warning and resolves normally if the DELETE endpoint is unavailable or returns 404.
- Deleting a SI-MAPPER project leaves an orphaned Graphivac grid that the operator must clean up manually via the Graphivac UI.
- The `13-04` delete route documents this limitation in its response (e.g. a `warnings` field in the JSON body).

### What a future phase would require

- Confirm the Graphivac DELETE endpoint from `api.json` or Graphivac documentation.
- Implement `deleteGrid` fully once the endpoint is confirmed.
- Remove the orphaned-grid warning from the delete response.

