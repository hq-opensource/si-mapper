# Phase 13 — Deferred Items

Items that were explicitly considered during Phase 13 planning but are out of scope for this phase. Each entry records **what** was deferred, **why**, and **what a future implementation would require**.

---

## D-01 — Dynamic Per-Request Grid Targeting in the MCP Server

**Deferred from:** `13-10`
**Category:** Architecture

### What was deferred

Making the MCP server target different Graphivac grids (= different SI-Mapper **systems**) on a per-tool-call basis, so that switching systems in the UI instantly affects all MCP canvas operations without a server restart.

### Why deferred

The MCP server initialises all manager classes (`DuctManager`, `PipeManager`, `GridManager`, etc.) as **singletons at startup** with a fixed set of Graphivac coordinates. The current MCP protocol does not provide a standard mechanism for injecting per-call context (such as `grid_id`) outside of explicit tool parameters.

Implementing dynamic targeting would require:

1. **Manager refactor**: change every manager class to accept `grid_id` (and `project_id`) as method-level parameters rather than constructor arguments.
2. **Tool parameter additions**: every registered MCP tool would need a `grid_id` parameter, making the tool surface more complex for the AI caller.
3. **Protocol evaluation**: determine whether FastMCP / the MCP protocol supports per-call metadata injection as an alternative to explicit parameters.
4. **State propagation**: the active system's grid ID would need to travel from the frontend → agent session → MCP tool call on every invocation. This crosses three process boundaries.

### Phase 13 mitigation

- The MCP server targets one system's grid per deployment, configured via `GRAPHIVAC_GRID_ID` in `mcp.env`.
- Switching systems requires updating `GRAPHIVAC_GRID_ID` (and `GRAPHIVAC_PROJECT_ID` if the project also changed) and restarting the MCP container.
- A `/config` health endpoint and a frontend mismatch warning banner (see `13-10`) make the manual process safe and observable.
- `GRAPHIVAC_ORG_ID` **never** needs to change — it is a deployment-wide constant.

### What a future phase would require

- Evaluate FastMCP's support for per-session or per-request context.
- Refactor all manager classes to accept `grid_id` as a call-time argument.
- Update all tool registrations in `duct_tools.py`, `pipe_tools.py`, `grid_tools.py`, etc.
- Update the agent's internal grid → Graphivac sync flow to pass the active system's `grid_id` at call time.
- Remove the mismatch warning banner (no longer needed once switching is instant).

---

## D-02 — Mid-Session System Switching for the Agent

**Deferred from:** `13-09`
**Category:** UX / Agent Architecture

### What was deferred

Allowing the user to switch the active system while an agent session is already in progress, with the agent immediately picking up the new system's model for its next task.

### Why deferred

The ADK agent is created once per session in `create_app()`. The model name is fixed at session creation time. If the user switches to a system with a different `ai_model_name`, the agent continues using the old model until the session is restarted.

For all other system-level values read at tool call time (Graphivac grid ID, folder path), mid-session switching works correctly — the updated `active_system` in state is read on the next tool call. The model is the only session-fixed value.

### Phase 13 mitigation

- Graphivac coordinates and folder paths switch immediately (read from state at call time).
- Model switching requires a page refresh to start a new session.
- The system selector UI can display a note: "Model changes take effect on the next session."

### What a future phase would require

- Evaluate whether ADK supports hot-swapping the model mid-session.
- Alternatively, trigger a clean session restart (disconnect + reconnect CopilotKit) when the user switches to a system with a different model.

---

## D-03 — Graphivac Grid and Project Deletion via API

**Deferred from:** `13-05`, `13-06`
**Category:** Graphivac API

### What was deferred

Automatically deleting the Graphivac Grid when a system is deleted, and the Graphivac Project when a project is deleted.

### Why deferred

The Graphivac REST API's support for grid and project deletion was not confirmed at planning time. `mcp_server/graphivac/api.json` must be inspected to verify whether `DELETE` endpoints exist for both resources.

### Phase 13 mitigation

- `deleteGrid` and `deleteGraphivacProject` in `mapper/src/lib/graphivac-client.ts` log a warning and resolve normally if the endpoint is unavailable or returns 404.
- Deleting a system or project may leave orphaned Graphivac Grids/Projects that the operator must clean up manually via the Graphivac UI.
- The delete API routes document this limitation in a `warnings` field in the JSON response.

### What a future phase would require

- Confirm `DELETE` endpoints from `api.json` or Graphivac documentation.
- Implement `deleteGrid` and `deleteGraphivacProject` fully once endpoints are confirmed.
- Remove the orphaned-resource warning from delete responses.

---

## D-04 — Agent Scoped to an Entire Project (Multi-System)

**Deferred from:** `13-09`
**Category:** Agent Architecture

### What was deferred

Allowing the agent to operate across all systems within a project simultaneously (e.g. cross-reference BACnet points from multiple systems, generate a multi-system ontology).

### Why deferred

The agent is currently scoped to a single active system. Cross-system operation requires the agent to manage multiple Graphivac grid connections, multiple file folder scopes, and potentially multiple models. This complexity is out of scope for Phase 13.

### Phase 13 mitigation

The agent works on one system at a time. Cross-system tasks must be performed by the user switching systems between agent sessions.

### What a future phase would require

- Extend the agent state to support a list of active systems.
- Add a multi-system path resolver (`get_project_path` at the project level).
- Allow the agent to call Graphivac tools parameterised with different grid IDs within the same session.
