# Phase 23: Add Cypher Query Tool for Neo4j Agent Exploration - Research

**Researched:** 2026-04-03
**Domain:** Neo4j Python driver, Cypher introspection, ADK BaseTool, concurrent thread pool
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool set — 4 tools total**

1. `execute_cypher(query: str)` — Single Cypher query. Always returns the Neo4j error on failure so the agent can fix its syntax and retry. No HITL gate.

2. `execute_cypher_batch(queries: list[str])` — Fires multiple queries in parallel via a Python thread pool (same session pool Neo4j driver already manages). Returns a list of per-query results in the same structure as the single tool. Parallel execution means Neo4j must support concurrent reads — it does; each thread opens its own session.

3. `get_graph_schema()` — Runs background introspection queries (`CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()` or `CALL db.schema.visualization()`) and returns available labels, relationship types, and property keys. Agent calls this before writing substantive queries to understand graph shape.

4. `search_graph_entities(keyword: str)` — Fuzzy keyword search over node labels and relationship types currently in the graph. Bridges human language ("fan", "temperature") to formal ASHRAE 223P URIs. Returns matching labels/types.

**Result structure — same for all tools**

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

Batch tool response: a list of the above structure, one entry per query, preserving query order.

**Parallel execution mechanism**

`execute_cypher_batch` uses `concurrent.futures.ThreadPoolExecutor` — each thread calls `driver.execute_query()` on a shared driver instance. Results reordered to match input query order before returning.

**Safety and HITL**

- Read queries: freely callable, no HITL gate.
- Write queries: no hard block. Master instruction will include: "If a Cypher query modifies the graph, ask the human for confirmation before executing."
- File to update: `agent/master_architecture/prompts/master_instruction.md`

**Module location**

New file: `agent/tools/neo4j_query_tools.py` — all 4 tools in one module.
All 4 tools registered in `agent/master_architecture/create_master_agent.py` `task_tools`.

### Claude's Discretion

- Exact thread pool size (default to min(len(queries), 8) or fixed 4)
- Exact introspection queries used in `get_graph_schema`
- Row limit for large result sets (suggest cap at 500 rows with a `truncated: true` flag)
- Whether to expose `parameters` arg for parameterized queries (start without, add if needed)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 23 adds four Cypher query tools that give the master agent read access to the live Neo4j graph. The tools live in a new module `agent/tools/neo4j_query_tools.py` following the `BaseTool` pattern already established by `load_ttl_to_neo4j_tool.py`. No new Python dependencies are required — the `neo4j` package (currently 6.1.0) is already installed in the venv.

The key technical insight is that `GraphDatabase.driver()` objects are thread-safe per official Neo4j docs. Calling `driver.execute_query()` from multiple `ThreadPoolExecutor` threads simultaneously is safe because `execute_query` internally manages its own session per call, not shared across threads. This makes the batch tool's parallel design sound without any special locking.

The introspection queries for `get_graph_schema` use the standard Neo4j built-in procedures (`CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()`). Because this project uses n10s with `handleVocabUris: 'IGNORE'`, all RDF namespace prefixes are preserved verbatim as label/property prefixes (e.g., `ashrae223__TemperatureSensor`, `ns0__hasValue`). The schema tool must surface these prefixed names raw so the agent can form correct Cypher queries.

**Primary recommendation:** Copy the `LoadTtlToNeo4jTool` `BaseTool` pattern exactly. Use module-level driver creation inside `run_async` (same pattern as existing tool — create+close per call to avoid stale connections). Use `ThreadPoolExecutor(max_workers=min(len(queries), 8))` for the batch tool. Cap result rows at 500 with a `truncated` flag.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| neo4j | 6.1.0 | Neo4j Python driver — Bolt protocol, execute_query, thread-safe driver | Already installed; used by load_ttl_to_neo4j_tool |
| concurrent.futures | stdlib | ThreadPoolExecutor for parallel batch queries | No new dependency; stdlib since Python 3.2 |
| google-adk | (project version) | BaseTool, ToolContext, FunctionDeclaration for agent tool registration | Project standard |
| google.genai.types | (project version) | types.Schema, types.Type for tool declaration parameters | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| neo4j.exceptions | 6.1.0 | ServiceUnavailable, CypherSyntaxError, etc. for typed error handling | Error reporting to agent |
| neo4j.RoutingControl | 6.1.0 | READ vs WRITE routing hint for execute_query | Use RoutingControl.READ for all schema and query tools |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ThreadPoolExecutor | asyncio + AsyncGraphDatabase | asyncio would require run_async to be structured differently; thread pool is simpler given existing sync driver pattern |
| driver.execute_query | session-per-query explicit session management | execute_query handles session lifecycle internally; simpler and thread-safe |

**Installation:**

No new packages needed. `neo4j>=5.0.0` is already in `agent/pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure

```
agent/tools/
├── neo4j_query_tools.py        # NEW: all 4 Cypher query tools
├── load_ttl_to_neo4j_tool.py   # EXISTING: pattern to copy
└── ...

agent/tests/
├── test_neo4j_query_tools.py   # NEW: unit tests for all 4 tools
└── ...

agent/master_architecture/
├── create_master_agent.py      # MODIFY: import + register 4 tools
└── prompts/
    └── master_instruction.md   # MODIFY: add Neo4j Query Protocol section
```

### Pattern 1: BaseTool with module-level singleton

Each tool is a `BaseTool` subclass. Module exports a singleton instance. Matches every existing tool in the project.

```python
# Source: agent/tools/load_ttl_to_neo4j_tool.py (project reference)
from google.adk.tools import BaseTool, ToolContext
from google.genai import types
from neo4j import GraphDatabase
import os

class ExecuteCypherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="execute_cypher",
            description="Execute a single Cypher query against the Neo4j graph...",
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="Cypher query string"),
                },
                required=["query"],
            ),
        )

    @override
    async def run_async(self, *, args: dict, tool_context: ToolContext) -> dict:
        query = args.get("query", "")
        uri = os.getenv("NEO4J_BOLT_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j_password")
        try:
            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                records, _, _ = driver.execute_query(query, database_="neo4j")
                result = [dict(r) for r in records]
            return {"query": query, "result": result, "error": None}
        except Exception as e:
            return {"query": query, "result": None, "error": str(e)}

execute_cypher_tool = ExecuteCypherTool()
```

### Pattern 2: Row cap with truncated flag

```python
# Apply after collecting records from execute_query
ROW_LIMIT = 500

def _cap_result(records: list, query: str) -> dict:
    truncated = len(records) > ROW_LIMIT
    return {
        "query": query,
        "result": records[:ROW_LIMIT],
        "error": None,
        "truncated": truncated,
    }
```

### Pattern 3: Batch with ThreadPoolExecutor preserving order

```python
# Source: concurrent.futures stdlib pattern
from concurrent.futures import ThreadPoolExecutor, as_completed

def _run_single(driver, query: str, database: str) -> dict:
    try:
        records, _, _ = driver.execute_query(query, database_=database)
        result = [dict(r) for r in records]
        return {"query": query, "result": result[:ROW_LIMIT], "error": None,
                "truncated": len(result) > ROW_LIMIT}
    except Exception as e:
        return {"query": query, "result": None, "error": str(e)}

# In run_async:
with GraphDatabase.driver(uri, auth=(user, password)) as driver:
    max_workers = min(len(queries), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_single, driver, q, "neo4j"): i
                   for i, q in enumerate(queries)}
        ordered = [None] * len(queries)
        for future in as_completed(futures):
            idx = futures[future]
            ordered[idx] = future.result()
return {"status": "success", "results": ordered}
```

### Pattern 4: Schema introspection queries

```cypher
-- Labels (node types)
CALL db.labels() YIELD label RETURN collect(label) AS labels

-- Relationship types
CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationship_types

-- Property keys
CALL db.propertyKeys() YIELD propertyKey RETURN collect(propertyKey) AS property_keys
```

Note: `CALL db.schema.visualization()` is available but returns graph objects rather than plain lists — harder to serialize. The three separate `CALL db.*()` queries returning collected lists are simpler and more serialization-friendly.

### Pattern 5: Fuzzy keyword search for search_graph_entities

```python
# Filter labels and relationship types whose lowercase contains the keyword
keyword_lower = keyword.lower()
matching_labels = [l for l in all_labels if keyword_lower in l.lower()]
matching_rels = [r for r in all_rel_types if keyword_lower in r.lower()]
return {
    "status": "success",
    "keyword": keyword,
    "matching_labels": matching_labels,
    "matching_relationship_types": matching_rels,
}
```

### Pattern 6: Tool registration in create_master_agent.py

```python
# Source: agent/master_architecture/create_master_agent.py (project reference)
from tools.neo4j_query_tools import (
    execute_cypher_tool,
    execute_cypher_batch_tool,
    get_graph_schema_tool,
    search_graph_entities_tool,
)

task_tools = [
    # ... existing tools ...
    load_ttl_to_neo4j_tool,
    execute_cypher_tool,
    execute_cypher_batch_tool,
    get_graph_schema_tool,
    search_graph_entities_tool,
]
```

### Pattern 7: Master instruction section (Neo4j Query Protocol)

Append after the existing "Neo4j Import Protocol" section:

```markdown
## Neo4j Query Protocol

The agent may query the Neo4j graph directly using the Cypher query tools.

**Read queries** (`MATCH`, `CALL db.*`, schema queries): freely callable without HITL.

**Write queries** (`CREATE`, `MERGE`, `DELETE`, `SET`, `REMOVE`): **Do NOT execute write queries without explicit human confirmation.** If a query you are about to execute modifies the graph, stop and ask the human for permission before calling `execute_cypher` or `execute_cypher_batch`.

**Recommended exploration sequence:**
1. Call `get_graph_schema` to understand available labels, relationship types, and property keys.
2. Call `search_graph_entities` with human-language terms to find relevant ASHRAE 223P labels.
3. Call `execute_cypher` for individual analytical queries.
4. Call `execute_cypher_batch` when you want to fire 4-5 queries in parallel.

**Important:** n10s imports with `handleVocabUris: 'IGNORE'` — all namespace prefixes are preserved verbatim (e.g., `ashrae223__TemperatureSensor`, `ns0__hasValue`). Use the exact label/property strings returned by `get_graph_schema` in your queries.
```

### Anti-Patterns to Avoid

- **Sharing a session across threads:** Only the `driver` object is thread-safe. Sessions are not. `execute_query` handles its own session internally — never pass a session between threads.
- **Returning raw Neo4j Record objects:** Always `dict(r)` each record before returning; Neo4j `Record` objects are not JSON-serializable.
- **Omitting error field in success response:** All four tools must always include the `error` key (set to `null` on success) for consistent agent parsing.
- **Long-lived driver in a module-level singleton:** The existing project pattern creates the driver inside `run_async` using a `with` block. Follow this; do not create a module-level driver singleton that persists between calls (stale connection risk after Neo4j restart).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parallel query execution | Custom threading with queue | `concurrent.futures.ThreadPoolExecutor` | Handles exceptions, future ordering, worker limits, cleanup |
| Neo4j session management | Manual session open/close per thread | `driver.execute_query()` | execute_query handles session lifecycle; thread-safe at driver level |
| Schema discovery | Manual MATCH queries on all nodes | `CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()` | Built-in Neo4j procedures; always current; faster |
| Keyword fuzzy match | Levenshtein/regex engine | Simple `keyword in label.lower()` substring match | Sufficient for bridging human terms to ASHRAE URIs; no extra library |
| Row serialization | Custom Record-to-dict converters | `dict(r)` on each Neo4j `Record` | The driver's `Record` class supports dict conversion natively |

**Key insight:** The Neo4j Python driver already handles connection pooling, session lifecycle, and thread-safe execution. The tools are thin wrappers, not infrastructure builders.

---

## Common Pitfalls

### Pitfall 1: Neo4j Record is not JSON-serializable

**What goes wrong:** Returning raw `records` from `execute_query` — the tool returns `Record` objects which cannot be JSON-serialized, causing an ADK serialization error.
**Why it happens:** `driver.execute_query` returns `EagerResult` with a `.records` list of `Record` objects.
**How to avoid:** Always convert: `result = [dict(r) for r in records]` before building the return dict.
**Warning signs:** TypeError about JSON serialization during tool return; ADK logs showing serialization failure.

### Pitfall 2: n10s label format surprises the agent

**What goes wrong:** Agent writes `MATCH (n:TemperatureSensor)` and gets zero results.
**Why it happens:** n10s with `handleVocabUris: 'IGNORE'` keeps full namespace prefixes — the actual label is `ashrae223__TemperatureSensor`. The agent doesn't know this without first calling `get_graph_schema`.
**How to avoid:** `get_graph_schema` returns raw label strings from `CALL db.labels()`. Master instruction must remind the agent to call `get_graph_schema` first and use the exact label strings returned.
**Warning signs:** Queries returning empty results despite data being present.

### Pitfall 3: Driver closed while ThreadPoolExecutor futures are still running

**What goes wrong:** The `with GraphDatabase.driver(...)` context manager closes the driver before `ThreadPoolExecutor` threads finish their `execute_query` calls.
**Why it happens:** If the `with driver` block exits before the thread pool's `__exit__`, threads get a closed driver.
**How to avoid:** The `with ThreadPoolExecutor(...)` block must be nested *inside* the `with GraphDatabase.driver(...)` block. The executor's `__exit__` (which waits for all futures) runs before the driver's `__exit__`.
**Warning signs:** `ServiceUnavailable` or `DriverClosed` errors in batch queries.

### Pitfall 4: Batch result order not preserved

**What goes wrong:** Results returned in completion order (fastest query first), not input order — agent can't match results back to queries.
**Why it happens:** `as_completed()` yields futures as they complete, not in submission order.
**How to avoid:** Track input index via `futures = {pool.submit(...): i for i, q in enumerate(queries)}`. Build `ordered = [None] * len(queries)` and assign by index.
**Warning signs:** Agent reports confusion about which result belongs to which query.

### Pitfall 5: CALL db.schema.visualization() serialization complexity

**What goes wrong:** Using `CALL db.schema.visualization()` instead of the three separate `CALL db.*()` procedures — returns node/relationship graph objects that are not flat lists.
**Why it happens:** The visualization procedure is designed for rendering, not data extraction.
**How to avoid:** Use `CALL db.labels()`, `CALL db.relationshipTypes()`, and `CALL db.propertyKeys()` separately. Each yields a single column of strings that serializes cleanly.

### Pitfall 6: FunctionDeclaration for list parameter (batch tool)

**What goes wrong:** Declaring `queries` as `types.Type.STRING` when it must be `types.Type.ARRAY` with `items` specified.
**Why it happens:** Copying the single-query tool declaration without adjusting the parameter type.
**How to avoid:**
```python
"queries": types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(type=types.Type.STRING),
    description="List of Cypher query strings to execute in parallel",
),
```

---

## Code Examples

### execute_cypher — single query (verified pattern)

```python
# Source: neo4j Python driver 6.1.0 + project load_ttl_to_neo4j_tool.py pattern
async def run_async(self, *, args: dict, tool_context: ToolContext) -> dict:
    query = args.get("query", "")
    if not query:
        return {"query": query, "result": None, "error": "query is required"}
    uri = os.getenv("NEO4J_BOLT_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j_password")
    try:
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            records, _, _ = driver.execute_query(query, database_="neo4j")
            rows = [dict(r) for r in records]
        truncated = len(rows) > ROW_LIMIT
        return {
            "query": query,
            "result": rows[:ROW_LIMIT],
            "error": None,
            "truncated": truncated,
        }
    except Exception as e:
        return {"query": query, "result": None, "error": str(e)}
```

### get_graph_schema — three separate CALL procedures

```python
# Source: Neo4j built-in procedures (verified in official docs)
with GraphDatabase.driver(uri, auth=(user, password)) as driver:
    label_records, _, _ = driver.execute_query(
        "CALL db.labels() YIELD label RETURN collect(label) AS labels",
        database_="neo4j",
    )
    rel_records, _, _ = driver.execute_query(
        "CALL db.relationshipTypes() YIELD relationshipType "
        "RETURN collect(relationshipType) AS relationship_types",
        database_="neo4j",
    )
    prop_records, _, _ = driver.execute_query(
        "CALL db.propertyKeys() YIELD propertyKey "
        "RETURN collect(propertyKey) AS property_keys",
        database_="neo4j",
    )
labels = label_records[0]["labels"] if label_records else []
rel_types = rel_records[0]["relationship_types"] if rel_records else []
prop_keys = prop_records[0]["property_keys"] if prop_records else []
return {
    "status": "success",
    "labels": labels,
    "relationship_types": rel_types,
    "property_keys": prop_keys,
}
```

### execute_cypher_batch — ThreadPoolExecutor with ordered results

```python
# Source: Python stdlib concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

def _run_query(driver, query: str) -> dict:
    try:
        records, _, _ = driver.execute_query(query, database_="neo4j")
        rows = [dict(r) for r in records]
        truncated = len(rows) > ROW_LIMIT
        return {"query": query, "result": rows[:ROW_LIMIT],
                "error": None, "truncated": truncated}
    except Exception as e:
        return {"query": query, "result": None, "error": str(e)}

# Inside run_async:
queries = args.get("queries", [])
with GraphDatabase.driver(uri, auth=(user, password)) as driver:
    max_workers = min(len(queries), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {pool.submit(_run_query, driver, q): i
                         for i, q in enumerate(queries)}
        ordered = [None] * len(queries)
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            ordered[idx] = future.result()
return {"status": "success", "results": ordered}
```

### FunctionDeclaration for list parameter

```python
# Source: google.genai.types pattern from project
parameters=types.Schema(
    type=types.Type.OBJECT,
    properties={
        "queries": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="List of Cypher query strings to run in parallel",
        ),
    },
    required=["queries"],
),
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NEO4JLABS_PLUGINS env var | NEO4J_PLUGINS | Neo4j 5 | Decision 10-01: already implemented |
| n10s void procedures with YIELD | Omit YIELD for void procedures | Neo4j 5 + n10s | Decision 10-04: already implemented |
| CALL db.schema() (deprecated) | CALL db.labels() + db.relationshipTypes() + db.propertyKeys() | Neo4j 4.x | Separate procedures return plain lists; visualization() is for rendering |

**Deprecated/outdated:**
- `NEO4JLABS_PLUGINS`: already removed in this project (Decision 10-01).
- `CALL db.schema()`: deprecated; use the three separate CALL db.* procedures.

---

## Open Questions

1. **RoutingControl.READ for schema queries**
   - What we know: `driver.execute_query` defaults to `routing_=RoutingControl.WRITE`. For read-only queries, passing `routing_=RoutingControl.READ` is more efficient in a clustered Neo4j but makes no functional difference on a single-node container.
   - What's unclear: Whether the local Docker Neo4j container cares about routing hints.
   - Recommendation: Pass `routing_=RoutingControl.READ` for all 4 tools for correctness; it's a no-op for single-node but correct for future scale.

2. **dict(r) for nested types**
   - What we know: `dict(r)` works for flat record values (strings, ints, floats, booleans, None).
   - What's unclear: Records containing Neo4j `Node` or `Relationship` objects (from `RETURN n` style queries) may not serialize cleanly with a simple `dict(r)`.
   - Recommendation: For the current agent use case (analytical MATCH queries returning scalars), `dict(r)` is sufficient. Add a note in PLAN that if the agent issues `RETURN n` node-object queries, a deeper serializer may be needed.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `agent/pyproject.toml` (existing) |
| Quick run command | `python -m pytest agent/tests/test_neo4j_query_tools.py -v` |
| Full suite command | `python -m pytest agent/tests/ -v` |

### Phase Requirements to Test Map

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| execute_cypher returns success dict with query/result/error keys | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherTool::test_successful_query -x` | Wave 0 |
| execute_cypher returns error dict (not raises) on Cypher syntax error | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherTool::test_cypher_error -x` | Wave 0 |
| execute_cypher truncates results at 500 rows | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherTool::test_row_cap -x` | Wave 0 |
| execute_cypher_batch returns ordered results list | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherBatchTool::test_batch_ordered -x` | Wave 0 |
| execute_cypher_batch handles partial failure (one query fails) | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherBatchTool::test_batch_partial_failure -x` | Wave 0 |
| get_graph_schema returns labels/relationship_types/property_keys | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestGetGraphSchemaTool::test_schema_success -x` | Wave 0 |
| search_graph_entities returns case-insensitive substring matches | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestSearchGraphEntitiesTool::test_keyword_match -x` | Wave 0 |
| All 4 tools have correct FunctionDeclaration names | unit | `pytest agent/tests/test_neo4j_query_tools.py -k "declaration" -x` | Wave 0 |
| create_master_agent registers all 4 new tools | unit | `pytest agent/tests/test_create_master_agent.py -x` | exists |

### Sampling Rate

- **Per task commit:** `python -m pytest agent/tests/test_neo4j_query_tools.py -v`
- **Per wave merge:** `python -m pytest agent/tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `agent/tests/test_neo4j_query_tools.py` — covers all 4 tools (does not exist yet)

*(Existing test infrastructure covers all other requirements. The new test file is the only gap.)*

---

## Sources

### Primary (HIGH confidence)
- neo4j Python driver API docs (v6.1) — thread safety of Driver object confirmed: "neo4j.Driver objects are thread-safe"
- `agent/tools/load_ttl_to_neo4j_tool.py` — canonical project pattern for BaseTool + GraphDatabase.driver usage
- `agent/master_architecture/create_master_agent.py` — tool registration pattern
- `agent/tests/test_load_ttl_to_neo4j_tool.py` — test mocking pattern for neo4j driver
- Python stdlib `concurrent.futures` — ThreadPoolExecutor, as_completed

### Secondary (MEDIUM confidence)
- [Neo4j Concurrency docs](https://neo4j.com/docs/python-manual/current/concurrency/) — confirmed execute_query manages its own session internally
- [Neo4j API docs](https://neo4j.com/docs/api/python-driver/current/api.html) — Driver thread-safety statement
- Neo4j built-in procedures (`CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()`) — confirmed available via web search + Neo4j official knowledge base

### Tertiary (LOW confidence)
- None — all key claims verified from project source code or official docs.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — neo4j 6.1.0 confirmed in venv, existing tool confirms pattern
- Architecture: HIGH — direct inspection of existing tools, confirmed BaseTool API
- Pitfalls: HIGH — confirmed from existing project decisions (10-01, 10-04) + official driver docs
- Test patterns: HIGH — confirmed 4 existing neo4j tests pass, pytest 9.0.2 in use

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable neo4j driver API)
