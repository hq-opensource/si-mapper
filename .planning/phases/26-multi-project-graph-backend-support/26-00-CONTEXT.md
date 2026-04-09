# Phase 26: Multi-Project Graph Backend Support — Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

The current graph backend is Neo4j with the Neosemantics (n10s) plugin.  Each
HVAC *system* is mapped to its own Neo4j **database** (`CREATE DATABASE`) so
that ontology graphs stay isolated across multi-project/multi-system deployments.
`CREATE DATABASE` is an Enterprise-only feature; the Community Edition
supports only one fixed database named `"neo4j"`.

This phase introduces a single **`GRAPH_BACKEND`** environment variable that
selects one of three operational modes.  The switch is read by both the Python
agent backend and the Next.js frontend API.  No mode requires a code change;
operators just flip the variable in their env file.

The three modes form a migration ladder:

| Mode | Value | Description |
|---|---|---|
| 1 | `neo4j_single` | Neo4j Community Edition.  One shared `neo4j` database for all systems.  DB name choice is disabled; the per-system `neo4j_db_name` field is ignored. |
| 2 | `neo4j_prefix` | Neo4j Community Edition.  One shared `neo4j` database; each system's nodes are tagged with `_graph_ns = <system_id>` so they can be filtered independently.  No `CREATE DATABASE` ever issued. |
| 3 | `graphdb` | Ontotext GraphDB Free.  Each system maps to a GraphDB *repository* (= their term for a named database).  Completely new, independent tools implement import and SPARQL querying. |

Operators can add further modes in the future (e.g. `neo4j_enterprise`,
`stardog`) by extending the resolver functions introduced in Step 1 without
touching the tool business logic.

</domain>

<decisions>
## Implementation Decisions

### Switch placement

The `GRAPH_BACKEND` variable is read server-side only.  It is **never**
prefixed `NEXT_PUBLIC_` and is never exposed to the browser.  Both services
need it:

- **Agent** (`agent/`) — controls which tools are active and how
  `project_utils.py` resolves database/repository names.
- **Frontend API** (`mapper/`) — controls which branch of
  `/api/graph/route.ts` handles the GET request.

### Default value

`neo4j_single` — the safest default; works with Community Edition out of the
box and makes the existing ontology graph visible in the Graph tab without any
Docker Enterprise license.

### Mode 1 — `neo4j_single`

- `get_neo4j_db_name()` in `project_utils.py` returns the hard-coded string
  `"neo4j"` regardless of `active_system.neo4j_db_name`.
- `load_ttl_to_neo4j_tool.py` skips the `SHOW DATABASES` / `CREATE DATABASE`
  block entirely and goes straight to wipe → n10s init → import.
- Frontend `/api/graph/route.ts` ignores the `?db=` query param and always
  passes `database: "neo4j"` to the driver.
- Env examples updated with `GRAPH_BACKEND=neo4j_single` and a comment
  explaining the three valid values.

### Mode 2 — `neo4j_prefix`

- All systems share the single `neo4j` database.
- After the n10s `import.inline()` call, a post-import Cypher statement
  stamps every newly-imported node with the system namespace:
  ```cypher
  MATCH (n) WHERE NOT EXISTS(n._graph_ns)
  SET n._graph_ns = $ns
  ```
- Wipe is namespace-scoped:
  ```cypher
  MATCH (n {_graph_ns: $ns}) DETACH DELETE n
  ```
- `get_graph_schema` and Cypher query tools pass the namespace to the agent
  via an additional `graph_namespace` field in their responses.  The master
  instruction gets a new rule instructing the agent to always add
  `n._graph_ns = "<namespace>"` filters.
- Frontend `/api/graph/route.ts` queries the single `neo4j` DB and filters
  `WHERE n._graph_ns = $ns` using the system ID passed as a `?ns=` query param.

### Mode 3 — `graphdb`

- **New, independent tools** — no modification to any existing Neo4j tool:
  - `agent/tools/load_ttl_to_graphdb_tool.py`
  - `agent/tools/graphdb_query_tools.py` (4 SPARQL tools)
- GraphDB repositories (one per system) replace Neo4j databases.  Created via
  the GraphDB REST Admin API (`POST /rest/repositories`).
- TTL files uploaded directly to the SPARQL update endpoint — no n10s plugin
  needed.
- `project_utils.py` gets a new `get_graphdb_repository()` function reading
  `active_system.graphdb_repository`.
- **UI approach for visualization** — Option B (recommended): a new branch in
  `/api/graph/route.ts` that queries GraphDB's SPARQL endpoint server-side and
  returns the **same `{nodes, edges}` JSON shape** already consumed by the
  existing `GraphWindow.tsx` / Sigma.js component.  Zero frontend component
  changes required.  The `GRAPHDB_REST_URL` server-side env var points to the
  GraphDB container.  An optional `GRAPHDB_PUBLIC_URL` (browser-reachable) can
  be surfaced as a "Open in GraphDB Workbench" link.
- New `graphdb` Docker Compose profile / service using `ontotext/graphdb`.
- `System` data model gains `graphdb_repository?: string` field; auto-set to
  `system.id` at creation time (mirrors existing `neo4j_db_name` pattern).
- `create_master_agent.py` conditionally registers graphdb tools when
  `GRAPH_BACKEND=graphdb`; Neo4j tools are registered for the other two modes.
- `master_instruction.md` gets two new protocol sections:
  *GraphDB Import Protocol* and *SPARQL Query Protocol*, activated when mode
  is `graphdb`.

### Env var additions per mode

**All modes (both services):**
```
GRAPH_BACKEND=neo4j_single   # neo4j_single | neo4j_prefix | graphdb
```

**Mode 3 only — agent `docker.env.example` / `.env.example`:**
```
GRAPHDB_REST_URL=http://graphdb:7200
```

**Mode 3 only — mapper `docker.env.example` / `.env.example`:**
```
GRAPHDB_REST_URL=http://graphdb:7200
GRAPHDB_PUBLIC_URL=http://localhost:7200
```

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Graph backend — existing files
- `agent/tools/load_ttl_to_neo4j_tool.py` — current import tool (pattern to extend / guard)
- `agent/tools/neo4j_query_tools.py` — current Cypher query tools (pattern to extend / guard)
- `agent/utils/project_utils.py` — `get_neo4j_db_name()` resolver (primary modification target in Steps 1 & 2)
- `mapper/src/app/api/graph/route.ts` — frontend graph API route (modification target in all 3 steps)

### Data model
- `mapper/src/lib/projects.ts` — `System` interface (`neo4j_db_name` field; add `graphdb_repository` in Step 3)
- `mapper/src/types/index.ts` — same `System` type mirror
- `mapper/src/app/page.tsx` — where `active_system` is assembled and sent to agent state

### Env files (both services)
- `agent/docker.env.example` — Docker runtime env template
- `agent/.env.example` — Local dev env template
- `mapper/docker.env.example` — Docker runtime env template
- `mapper/.env.example` (= `.env.local` template) — Local dev env template

### Docker
- `docker-compose.yml` — add `graphdb` service in Step 3

### Agent wiring
- `agent/master_architecture/create_master_agent.py` — tool registration (Step 3)
- `agent/master_architecture/prompts/master_instruction.md` — protocol sections

### GraphDB REST API (Step 3)
- Create repository: `POST /rest/repositories` with JSON body
- Check repository: `GET /rest/repositories/{id}`
- Clear repository: `DELETE /repositories/{id}/statements`
- Upload TTL: `POST /repositories/{id}/statements` with `Content-Type: text/turtle`
- SPARQL query: `GET /repositories/{id}?query=<encoded SPARQL>`

</canonical_refs>

<code_context>
## Existing Code Insights

### `get_neo4j_db_name()` — current implementation
```python
# agent/utils/project_utils.py
def get_neo4j_db_name(tool_context) -> str:
    if tool_context is not None:
        active_system = tool_context.state.get("active_system") or {}
        db_name = active_system.get("neo4j_db_name", "")
        if db_name:
            return db_name
    raise ValueError(
        "Neo4j database name not found. "
        "Ensure 'neo4j_db_name' is set on the active system in the tool context."
    )
```

### `load_ttl_to_neo4j_tool.py` — CREATE DATABASE block (Enterprise-only, to be guarded)
```python
# Step 1: Create the database if it does not yet exist
existing, _, _ = driver.execute_query(
    "SHOW DATABASES YIELD name WHERE name = $name RETURN name",
    {"name": db_name},
    database_="system",
)
db_exists = len(existing) > 0
if not db_exists:
    driver.execute_query(f"CREATE DATABASE `{db_name}`", database_="system")
```

### Frontend `/api/graph/route.ts` — db param usage
```typescript
const db = searchParams.get('db') ?? 'neo4j';
// ... all queries use { database: db }
```

### System type (projects.ts)
```typescript
export interface System {
  id: string;
  name: string;
  folder_path: string;
  graphivac_grid_id: string;
  neo4j_db_name?: string;       // per-system Neo4j DB (Enterprise mode)
  // graphdb_repository?: string  // to be added in Step 3
  thread_id?: string;
  sessions?: Session[];
  created_at: string;
  updated_at: string;
}
```

### active_system shape sent to agent (page.tsx)
```typescript
active_system: activeSystem ? {
  id: activeSystem.id,
  name: activeSystem.name,
  folder_path: activeSystem.folder_path,
  graphivac_grid_id: activeSystem.graphivac_grid_id,
  neo4j_db_name: activeSystem.neo4j_db_name,
  // graphdb_repository: activeSystem.graphdb_repository  // Step 3
} : null,
```

</code_context>

<deferred>
## Deferred Ideas

- **`neo4j_enterprise`** fourth mode — identical to existing behavior (per-system `CREATE DATABASE`).  Deferred; can be added by naming the current code path and registering it behind `neo4j_enterprise`.
- **Stardog / Apache Jena Fuseki** — additional SPARQL triplestore backends.  Same architecture as `graphdb` mode; deferred until GraphDB is validated.
- **OWL reasoning in GraphDB** — GraphDB supports optional OWL/RDFS inference. Deferred; can be toggled via a repository config flag in Step 3 without code changes.
- **Incremental TTL import** (add/remove triples) — all three modes currently do wipe-and-reimport.  A delta-import strategy is deferred to a future phase.

</deferred>

---

*Phase: 26-multi-project-graph-backend-support*
*Context gathered: 2026-04-09*

