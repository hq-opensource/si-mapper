# Phase 23: Add Cypher Query Tool for Neo4j Agent Exploration - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Give the master agent tools to write and execute Cypher queries against the running Neo4j container. The agent uses the TTL file as prior knowledge, inspects the live graph schema, and issues queries to answer analytical questions about the building's HVAC system. The graph is read from; no write workflows are introduced here.

</domain>

<decisions>
## Implementation Decisions

### Tool set — 4 tools total

1. **`execute_cypher(query: str)`** — Single Cypher query. Always returns the Neo4j error on failure so the agent can fix its syntax and retry. No HITL gate.

2. **`execute_cypher_batch(queries: list[str])`** — Fires multiple queries in parallel via a Python thread pool (same session pool Neo4j driver already manages). Returns a list of per-query results in the same structure as the single tool. Parallel execution means Neo4j must support concurrent reads — it does; each thread opens its own session.

3. **`get_graph_schema()`** — Runs background introspection queries (`CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()` or `CALL db.schema.visualization()`) and returns available labels, relationship types, and property keys. Agent calls this before writing substantive queries to understand graph shape.

4. **`search_graph_entities(keyword: str)`** — Fuzzy keyword search over node labels and relationship types currently in the graph. Bridges human language ("fan", "temperature") to formal ASHRAE 223P URIs. Returns matching labels/types.

### Result structure — same for all tools

Single query response:
```json
{
  "query": "<cypher string>",
  "result": [<list of record dicts>],
  "error": null
}
```
On failure:
```json
{
  "query": "<cypher string>",
  "result": null,
  "error": "<Neo4j error message>"
}
```

Batch tool response: a list of the above structure, one entry per query, preserving query order. Agent can inspect which queries succeeded vs. failed individually.

### Parallel execution mechanism

`execute_cypher_batch` uses `concurrent.futures.ThreadPoolExecutor` — each thread calls `driver.execute_query()` on a shared driver instance (thread-safe per neo4j Python driver docs). Results are collected with `futures.as_completed()` or `executor.map()` and reordered to match input query order before returning.

### Safety and HITL

- Read queries (`MATCH`, `CALL db.*`, schema queries): freely callable, no HITL gate.
- Write queries (`CREATE`, `MERGE`, `DELETE`, `SET`): no hard block, but the master agent instruction will include a rule: *"If a Cypher query modifies the graph, ask the human for confirmation before executing."* Agent is expected to only read in normal operation.
- File location for agent instruction update: `agent/master_architecture/master_instruction.md`.

### Module location

New file: `agent/tools/neo4j_query_tools.py` — houses all 4 tools. Follows existing pattern (no separate sub-package needed for 4 tools).

All 4 tools registered in `agent/master_architecture/create_master_agent.py` `task_tools`.

### Claude's Discretion
- Exact thread pool size (default to min(len(queries), 8) or fixed 4)
- Exact introspection queries used in `get_graph_schema`
- Row limit for large result sets (suggest cap at 500 rows with a `truncated: true` flag)
- Whether to expose `parameters` arg for parameterized queries (start without, add if needed)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Neo4j tool (pattern to follow)
- `agent/tools/load_ttl_to_neo4j_tool.py` — Connection config, driver pattern, env vars (`NEO4J_BOLT_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`), `BaseTool`/`run_async` pattern

### Agent wiring
- `agent/master_architecture/create_master_agent.py` — Where to register new tools in `task_tools`
- `agent/master_architecture/master_instruction.md` — Where to add Neo4j Query Protocol section (Cypher write-gate instruction)

### Neo4j driver thread safety
- neo4j Python driver is thread-safe at the driver level; each `execute_query` call acquires its own session from the connection pool — safe for `ThreadPoolExecutor`

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LoadTtlToNeo4jTool` in `agent/tools/load_ttl_to_neo4j_tool.py`: driver instantiation pattern (`GraphDatabase.driver(uri, auth=(user, password))`), env var resolution, `BaseTool` subclass with `_get_declaration()` + `run_async()` — new tools copy this exactly
- `neo4j` package already installed in `.venv` (no new dependencies needed)
- `exit_tools.py`, `internal_grid_tools.py` — examples of multi-function tool modules

### Established Patterns
- All tools return `dict[str, Any]` with a `"status"` key (`"success"` / `"error"`)
- `FunctionDeclaration` with `types.Schema` for ADK tool registration
- Module-level singleton export: `load_ttl_to_neo4j_tool = LoadTtlToNeo4jTool()` — same for new tools

### Integration Points
- `create_master_agent.py`: import new module, add tool singletons to `task_tools` list
- `master_instruction.md`: add "Neo4j Query Protocol" section with Cypher write-gate rule

</code_context>

<specifics>
## Specific Ideas

- Agent asked for this tool itself (via session log) — it already understands the ASHRAE 223P RDF-in-Neo4j structure (namespaced labels like `ashrae223__TemperatureSensor`, relationships like `ashrae223__observes`)
- n10s imports with `handleVocabUris: 'IGNORE'` → namespace prefixes are preserved as label/property prefixes (e.g., `ns0__hasValue`) — `get_graph_schema` must surface these so agent can form correct queries
- User wants agent to be able to self-explore: fire 4-5 queries at once, read the results, and build more sophisticated follow-up queries

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 23-add-cypher-query-tool-for-neo4j-agent-exploration*
*Context gathered: 2026-04-04*
