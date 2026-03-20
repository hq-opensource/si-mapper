# Phase 6: Refactor Graphivac API - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesign the agent↔Graphivac communication architecture. Instead of the agent calling MCP tools that immediately write to Graphivac (long round-trip: vision → tool params → API call → read_grid), the agent writes to an internal state (ADK ToolContext.state) using a simplified tool layer. A standalone sync service watches that internal state and calls the existing MCP server to replicate it in Graphivac in real time.

The MCP server itself is NOT modified. The existing Graphivac API client and manager/tool layer stay intact.

</domain>

<decisions>
## Implementation Decisions

### Internal state format
- Agent-friendly JSON stored in ADK `ToolContext.state` under a dedicated key (e.g., `"internal_grid"`)
- Schema: `{"components": [{"type": "...", "id": "...", "name": "...", "x": ..., "y": ..., ...}]}` Analyze schema for ducts, because ducts have start and end coordinates, while the other equipments don't require a start and end.
- Component types and schema must match the current MCP tool signatures (ducts, pipes, equipment) so the sync service can translate directly to MCP calls
- IDs, names, and coordinates are mandatory fields on every component entry

### Agent tool interface (new internal-state layer)
- Replicate the existing MCP tool surface, but writing to `ToolContext.state` instead of calling Graphivac
- Support both single-element and batch operations (add/delete)
- Read back from internal state at any time (agent self-corrects: "I found 3 fans but image shows 5 → add 2 more")
- Flexible CRUD: add one, add batch, delete one, delete batch
- Tool schema is authoritative for the component standard — must align with what the sync service reads

### Sync service
- Standalone Python service (separate from MCP server and Next.js frontend)
- Polls `ToolContext.state["internal_grid"]` on a fixed interval
- Diffs current state against last-synced state to identify new/changed/deleted components. Where is saved the last state? 
- For each diff, calls the corresponding MCP server tool (e.g., `create_duct`, `create_cooling_coil`) using the existing MCP server endpoint
- MCP server's internal queuing logic handles rate control — sync service does not need its own queue
- Mirrors the existing "50 agent test" pattern that already drives the MCP server programmatically

### What is NOT changing
- `mcp_server/graphivac/graphivac_api.py` — left as-is
- All existing managers and tools — left as-is
- MCP server routing and queuing — left as-is
- `agent/tools/state_tools.py` — the new internal-state tools extend this existing pattern 

### Claude's Discretion
- Initial "internal_grid" state? For the initial internal grid state, you should use the MCP server to check the existing grid state, and use that grid state as the initial state for the "internal_grid" state.
- Poll interval duration (start with a reasonable default, tune later) , each 2 seconds.
- Diff algorithm implementation details
- Whether to persist last-synced state in a file for crash recovery, yes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing tool surface to mirror
- `mcp_server/graphivac/duct_tools.py` — Tool signatures for ducts/equipment (create_duct, create_ducts_batch, delete_duct, create_cooling_coil, etc.)
- `mcp_server/graphivac/pipe_tools.py` — Pipe tool signatures
- `mcp_server/graphivac/grid_tools.py` — read_grid, delete_grid
- `mcp_server/graphivac/electric_tools.py` — Electrical component tool signatures
- `mcp_server/graphivac/custom_tools.py` — Custom component tool signatures
- `mcp_server/graphivac/metadata_tools.py` — Metadata tool signatures

### Existing state pattern to extend
- `agent/tools/state_tools.py` — save_agent_state / get_agent_state using ToolContext.state; new internal-grid tools follow the same pattern

### MCP server entry point (for sync service to target)
- `mcp_server/server/main.py` — Manager instantiation and tool registration; sync service connects here

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/tools/state_tools.py`: Existing ToolContext.state read/write pattern — new internal-grid tools extend this directly
- `mcp_server/graphivac/duct_manager.py`: `create_ducts_batch` already accepts a dict of multiple ducts — batch schema reference
- `mcp_server/server/main.py`: Manager + tool registration pattern — sync service instantiates managers the same way

### Established Patterns
- All MCP tools return `ToolResult` with `tool_status` in `structured_content` — sync service should check this field
- Managers use `asyncio.Lock` for concurrency safety — MCP server's queuing is already in place
- `save_agent_state` stores to `tool_context.state["treated"]` — new internal grid state goes to `tool_context.state["internal_grid"]`

### Integration Points
- Sync service connects to MCP server via its HTTP endpoint (same as agent does via MCP protocol)
- Agent's new tools are registered alongside existing tools in the agent's tool list
- Internal state key `"internal_grid"` must be readable by the sync service outside the agent's turn context (check ADK session storage API)

</code_context>

<specifics>
## Specific Ideas

- The sync service is architecturally similar to the existing "50 agents test" — a programmatic MCP client that drives the server without being the agent itself
- Agent self-correction flow: agent reads `internal_grid`, notices missing components vs. source image, calls add_component (single or batch) to patch the gap
- The user explicitly wants the highest accuracy possible: if the image has 3 fans and 5 dampers, the final state must have exactly 3 fans and 5 dampers — the flexible read/add/delete interface exists to support iterative correction

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-refactor-graphivac-api*
*Context gathered: 2026-03-18*
