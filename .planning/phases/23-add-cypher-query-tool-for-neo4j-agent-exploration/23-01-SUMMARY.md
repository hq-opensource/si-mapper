---
phase: 23-add-cypher-query-tool-for-neo4j-agent-exploration
plan: "01"
subsystem: database
tags: [neo4j, cypher, baseTool, ThreadPoolExecutor, graph-query]

requires:
  - phase: 10-ttl-to-neo4j-database-integration
    provides: Neo4j Docker service, LoadTtlToNeo4jTool, BaseTool + GraphDatabase pattern

provides:
  - ExecuteCypherTool (single query, 500-row cap, truncated flag, {query,result,error,truncated})
  - ExecuteCypherBatchTool (ThreadPoolExecutor parallel batch, ordered results, partial failure)
  - GetGraphSchemaTool (Neo4j labels + relationship_types + property_keys introspection)
  - SearchGraphEntitiesTool (case-insensitive keyword substring match on labels and rel types)
  - 15 unit tests for all 4 tools

affects:
  - master agent create_master_agent.py (next step: wire tools in)
  - skill-ontology-generation, skill-ontology-validation (agents can now query live Neo4j graph)

tech-stack:
  added: []
  patterns:
    - _run_query module-level helper (thread-safe, used by both execute_cypher and batch)
    - _get_neo4j_config() helper centralises env var reading for all 4 tools
    - ThreadPoolExecutor inside `with driver:` block for batch parallelism
    - future_to_index dict pattern for preserving query order in as_completed loop
    - ROW_LIMIT = 500 module constant controlling result cap
    - Module-level singletons for all 4 tools (BaseTool pattern from phase 10)

key-files:
  created:
    - agent/tools/neo4j_query_tools.py
    - agent/tests/test_neo4j_query_tools.py
  modified: []

key-decisions:
  - "_run_query is a module-level function (not method) so ThreadPoolExecutor workers can call it without holding a class reference"
  - "ThreadPoolExecutor is created INSIDE `with driver:` block to ensure driver stays open while threads execute"
  - "future_to_index maps Future -> original query index to restore ordered results from as_completed (unordered)"
  - "ROW_LIMIT constant (500) shared between execute_cypher and _run_query helper — no duplication"
  - "Empty queries list in batch returns {status: success, results: []} without creating a driver or thread pool"

patterns-established:
  - "Thread-safe query execution: _run_query catches all exceptions and returns {query, result: null, error: str}"
  - "Batch parallelism: ThreadPoolExecutor inside context manager, future_to_index for ordered assembly"
  - "Schema introspection: CALL db.labels() / db.relationshipTypes() / db.propertyKeys() pattern"

requirements-completed: [P23-01, P23-02, P23-03, P23-04, P23-05]

duration: 2min
completed: 2026-04-04
---

# Phase 23 Plan 01: Add Cypher Query Tool for Neo4j Agent Exploration Summary

**4 BaseTool Cypher query tools (execute_cypher, execute_cypher_batch, get_graph_schema, search_graph_entities) with ThreadPoolExecutor batch parallelism, 500-row cap, and 15 unit tests — all green.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-04T11:51:04Z
- **Completed:** 2026-04-04T11:53:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Implemented all 4 Cypher query tools following the BaseTool pattern from phase 10
- Execute-cypher caps results at 500 rows with a `truncated` flag; error path returns `{query, result: null, error: str}`
- Batch tool uses ThreadPoolExecutor with `future_to_index` dict pattern to guarantee ordering despite `as_completed` non-determinism; partial failures reported per-query
- Schema and search tools run the `CALL db.labels()` / `CALL db.relationshipTypes()` / `CALL db.propertyKeys()` introspection queries
- 15 unit tests — all pass including thread-safe `side_effect` function (not list) for batch mocking

## Task Commits

Each task was committed atomically:

1. **Task 1: Create neo4j_query_tools.py with all 4 tools + tests** - `fcd0554` (feat)

## Files Created/Modified

- `agent/tools/neo4j_query_tools.py` - 4 BaseTool subclasses + module-level singletons + ROW_LIMIT constant + _run_query + _get_neo4j_config helpers
- `agent/tests/test_neo4j_query_tools.py` - 15 unit tests across 4 test classes (TDD)

## Decisions Made

- `_run_query` is module-level (not a class method) so `ThreadPoolExecutor` workers can invoke it without holding a class reference — avoids serialisation issues.
- `ThreadPoolExecutor` is instantiated INSIDE the `with GraphDatabase.driver(...)` context to ensure the driver remains open while threads execute queries.
- `future_to_index` maps each `Future` to its original position in the queries list; `as_completed` fires futures in completion order, so index is needed to reassemble ordered results.
- Batch mock uses a `side_effect` function keyed on query string instead of a side_effect list, which is not thread-safe across concurrent threads.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Tools connect to Neo4j via the same `NEO4J_BOLT_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` environment variables already used by `load_ttl_to_neo4j_tool`.

## Next Phase Readiness

All 4 tools are implemented and tested. Next step (not in this plan) is to wire the singletons into `create_master_agent.py` as task tools.

---
*Phase: 23-add-cypher-query-tool-for-neo4j-agent-exploration*
*Completed: 2026-04-04*

## Self-Check: PASSED

- FOUND: agent/tools/neo4j_query_tools.py
- FOUND: agent/tests/test_neo4j_query_tools.py
- FOUND: .planning/phases/23-add-cypher-query-tool-for-neo4j-agent-exploration/23-01-SUMMARY.md
- FOUND: commit fcd0554
