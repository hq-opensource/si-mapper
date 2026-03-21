# Phase 10: TTL to Neo4j Database Integration with Frontend Graph Visualization — Research

**Researched:** 2026-03-21
**Domain:** Neo4j + Neosemantics (RDF/TTL import), @react-sigma/core (Sigma.js WebGL graph), Next.js API route, Python ADK BaseTool
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Graph visualization: **Sigma.js** (`@react-sigma/core`) + **ForceAtlas2** layout (`graphology-layout-forceatlas2`)
- Database: **Neo4j 5 + Neosemantics plugin** (`n10s.rdf.import.fetch` for TTL import)
- Import strategy: **wipe + reimport** on each call (no append, no merge, clean state)
- New master agent tool: `load_ttl_to_neo4j` following `BaseTool` subclass pattern
- API route: `GET /api/graph` returning `{ nodes: [...], edges: [...] }`
- Docker: port mapping `7474:7474`, `7687:7687`, profile `graph`, added to existing `docker-compose.yml`
- Node interactions: hover → floating info card (bottom-right), click → lock card + highlight connections + dim others, drag → reposition
- Zoom-triggered label visibility using node degree as size/importance metric
- Node label = RDF local name (namespace stripped)
- Node color-coded by `rdf:type`; size scales with degree
- Edge labels = RDF predicate local name; directed arrows; zoom-triggered visibility
- Frontend layout: full-screen Sigma canvas with overlaid toolbar (zoom in/out, reset, FA2 run/pause)

### Claude's Discretion
- Exact ForceAtlas2 parameter tuning (gravity, scaling ratio, barnesHut optimization)
- Color palette assignment for specific RDF types (planner should look at actual 223P TTL types)
- Neosemantics configuration: `handleVocabUris` value and uniqueness constraints
- Neo4j indexing strategy for query performance

### Deferred Ideas (OUT OF SCOPE)
- Phase 11: ADK agent queries Neo4j via MCP Toolbox
- Graph filtering / search UI in the Graph tab
- Multiple TTL versions side-by-side comparison
- Neo4j Browser iframe (explicitly rejected)
</user_constraints>

---

## Summary

Phase 10 integrates four components: a Neo4j Docker service (with Neosemantics plugin for RDF/TTL import), a Python `BaseTool` subclass that wipes and reimports `ontology.ttl`, a Next.js API route that queries Neo4j and serves graph data, and a `GraphWindow.tsx` React component using Sigma.js WebGL rendering with ForceAtlas2 layout.

All technology choices are locked by the user. The stack is well-established and the library versions are current. The critical integration concern is file access: the Python agent tool must pass the TTL file to Neo4j via either a Docker-mounted volume path (`file:///`) or via the `n10s.rdf.import.inline` procedure with the file contents as a string. Using `inline` avoids the volume-mount complexity and is the recommended approach for this architecture.

The `@react-sigma/core` v5.0.6 officially supports React 19, confirmed via NPM peer dependencies. All three packages (`@react-sigma/core`, `@react-sigma/layout-forceatlas2`, `graphology`) are compatible with the existing Next.js 16 / React 19.2 project.

**Primary recommendation:** Use `n10s.rdf.import.inline` (not `.fetch`) for the Python tool to avoid Docker volume mapping complexity. The tool reads the TTL file contents as a Python string and passes them directly to Neo4j via Cypher.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@react-sigma/core` | 5.0.6 | React wrapper for Sigma.js WebGL graph rendering | Official React integration; supports React 19; SigmaContainer + hooks |
| `sigma` | 3.0.2 | WebGL graph renderer (peer dep, auto-installed) | Sigma.js v3 is the current major; nodeReducer/edgeReducer for interactivity |
| `graphology` | 0.26.0 | Graph data structure (peer dep, auto-installed) | Required by sigma; MultiDirectedGraph for directed RDF edges |
| `@react-sigma/layout-forceatlas2` | 5.0.6 | ForceAtlas2 Web Worker layout integration for react-sigma | Provides `useWorkerLayoutForceAtlas2` hook + start/stop/kill/isRunning |
| `graphology-layout-forceatlas2` | 0.10.1 | ForceAtlas2 algorithm (peer dep of layout pkg) | The actual algorithm; runs in a Web Worker via layout package |
| `neo4j-driver` | 6.0.1 | Official Neo4j JavaScript driver for Next.js API route | Bolt protocol; `driver.executeQuery()` returns typed records |
| `neo4j` (Python) | ≥5.x | Official Neo4j Python driver for agent tool | `pip install neo4j`; `GraphDatabase.driver()` + `execute_query()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@react-sigma/layout-core` | 5.0.6 | Required peer dep of layout-forceatlas2 | Installed automatically; provides layout hook infrastructure |
| `graphology-utils` | bundled | Node degree computation (`degree()`) | Used in GraphWindow for sizing nodes by connectivity |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@react-sigma/layout-forceatlas2` | `graphology-layout-forceatlas2` directly | Worker package handles Web Worker lifecycle; direct requires manual worker management |
| `n10s.rdf.import.inline` | `n10s.rdf.import.fetch` with `file:///` | `fetch` requires Docker volume mount + container-internal path; `inline` is self-contained |

**Installation (mapper):**
```bash
cd mapper
pnpm add @react-sigma/core @react-sigma/layout-forceatlas2 @react-sigma/layout-core sigma graphology graphology-layout-forceatlas2 neo4j-driver
```

**Installation (agent — add to pyproject.toml):**
```toml
"neo4j>=5.0.0",
```
Then: `cd agent && uv sync`

**Version verification (confirmed 2026-03-21 via npm registry):**
```
@react-sigma/core        → 5.0.6  (peer: react ^18 || ^19, sigma ^3.0.2, graphology ^0.26.0)
sigma                    → 3.0.2
graphology               → 0.26.0
@react-sigma/layout-forceatlas2 → 5.0.6
graphology-layout-forceatlas2   → 0.10.1
neo4j-driver             → 6.0.1
```

---

## Architecture Patterns

### Recommended Project Structure
```
docker-compose.yml                          # Add neo4j service with graph profile
neo4j/
└── neo4j.env                               # NEO4J_AUTH, bolt URI for agent tool

agent/
└── master_architecture/
    └── tools/
        └── load_ttl_to_neo4j_tool.py       # New BaseTool subclass

mapper/src/app/
├── api/graph/route.ts                      # GET /api/graph → {nodes, edges}
└── page/components/
    └── GraphWindow.tsx                     # SigmaContainer + ForceAtlas2 + interactions
```

### Pattern 1: Neo4j Service in docker-compose.yml

**What:** Add a `neo4j` service under the `graph` profile with Neosemantics pre-installed via `NEO4J_PLUGINS`.
**When to use:** Always for Phase 10.

```yaml
# Source: Official Neo4j Docker documentation (neo4j.com/docs/operations-manual/current/docker/plugins/)
  neo4j:
    image: neo4j:5
    container_name: neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    env_file:
      - neo4j/neo4j.env
    environment:
      NEO4J_PLUGINS: '["n10s"]'
    volumes:
      - neo4j_data:/data
    profiles:
      - graph

volumes:
  neo4j_data:
```

`neo4j/neo4j.env`:
```
NEO4J_AUTH=neo4j/neo4j_password
```

**CRITICAL:** `NEO4J_PLUGINS` (not `NEO4JLABS_PLUGINS`) is the current env var for Neo4j 5. The old `NEO4JLABS_PLUGINS` is deprecated.

### Pattern 2: Neosemantics Init + Wipe + Import (Cypher)

**What:** The exact sequence of Cypher operations the Python tool runs via `execute_query`.
**When to use:** Every `load_ttl_to_neo4j` call.

```cypher
-- Step 1: Wipe all existing RDF data
MATCH (n) DETACH DELETE n;

-- Step 2: Drop existing n10s config and constraint (if exists)
CALL n10s.graphconfig.drop() YIELD configExisted;
DROP CONSTRAINT n10s_unique_uri IF EXISTS;

-- Step 3: Recreate constraint (required by n10s)
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

-- Step 4: Initialize graph config
CALL n10s.graphconfig.init({handleVocabUris: 'IGNORE'});

-- Step 5: Import TTL inline
CALL n10s.rdf.import.inline($ttl_content, 'Turtle')
YIELD terminationStatus, triplesLoaded, triplesParsed
RETURN terminationStatus, triplesLoaded, triplesParsed;
```

**Key insight on `handleVocabUris: 'IGNORE'`:** This strips namespaces and keeps only local names (e.g., `Fan-SF1`, `hasConnectionPoint`). This aligns with the CONTEXT.md requirement for "RDF local name" display. Do NOT use `'KEEP'` (stores full URIs as labels) or `'SHORTEN'` (creates `ns0__localName` patterns).

### Pattern 3: Python BaseTool Subclass — load_ttl_to_neo4j

**What:** Follows the exact `CaptureFrontendStateTool` pattern from Phase 8.
**When to use:** New master agent tool, registered in `create_master_agent.py`.

```python
# Source: agent/master_architecture/tools/capture_frontend_state_tool.py (Phase 8 pattern)
from google.adk.tools import BaseTool, ToolContext
from google.genai import types
from typing_extensions import override
import os
from neo4j import GraphDatabase
from pathlib import Path

class LoadTtlToNeo4jTool(BaseTool):
    def __init__(self):
        super().__init__(
            name='load_ttl_to_neo4j',
            description='Wipes Neo4j and reimports the current ontology.ttl file. Returns node_count and relationship_count.',
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        )

    @override
    async def run_async(self, *, args: dict, tool_context: ToolContext) -> dict:
        ttl_path = Path(__file__).resolve().parents[3] / "sub_agents" / "_223p" / "ttl" / "ontology.ttl"
        if not ttl_path.exists():
            return {"status": "error", "message": f"ontology.ttl not found at {ttl_path}"}

        ttl_content = ttl_path.read_text(encoding="utf-8")

        uri = os.getenv("NEO4J_BOLT_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j_password")

        try:
            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                # ... wipe + init + import sequence
                records, _, _ = driver.execute_query(
                    "CALL n10s.rdf.import.inline($ttl_content, 'Turtle') YIELD triplesLoaded RETURN triplesLoaded",
                    {"ttl_content": ttl_content},
                )
                triples = records[0]["triplesLoaded"] if records else 0
            return {"status": "success", "triples_loaded": triples}
        except Exception as e:
            return {"status": "error", "message": str(e)}

load_ttl_to_neo4j_tool = LoadTtlToNeo4jTool()
```

### Pattern 4: Next.js API Route — GET /api/graph

**What:** Connects to Neo4j via Bolt, runs Cypher to get all nodes and relationships, transforms to `{nodes, edges}`.
**File:** `mapper/src/app/api/graph/route.ts`

```typescript
// Source: neo4j.com/docs/javascript-manual/current/
import { NextResponse } from 'next/server';
import neo4j from 'neo4j-driver';

const driver = neo4j.driver(
    process.env.NEO4J_BOLT_URI ?? 'bolt://localhost:7687',
    neo4j.auth.basic(
        process.env.NEO4J_USER ?? 'neo4j',
        process.env.NEO4J_PASSWORD ?? 'neo4j_password'
    )
);

export async function GET() {
    try {
        const { records: nodeRecords } = await driver.executeQuery(
            'MATCH (n) RETURN n.uri AS uri, labels(n) AS labels, properties(n) AS props'
        );
        const { records: edgeRecords } = await driver.executeQuery(
            'MATCH (a)-[r]->(b) RETURN a.uri AS source, b.uri AS target, type(r) AS label, r.uri AS id'
        );

        const nodes = nodeRecords.map(r => ({
            id: r.get('uri'),
            label: localName(r.get('uri')),
            type: (r.get('labels') as string[])[0] ?? 'Resource',
            properties: r.get('props'),
        }));

        const edges = edgeRecords.map((r, i) => ({
            id: r.get('id') ?? `edge-${i}`,
            source: r.get('source'),
            target: r.get('target'),
            label: r.get('label'),
        }));

        return NextResponse.json({ nodes, edges });
    } catch (e) {
        return NextResponse.json({ error: String(e) }, { status: 500 });
    }
}

function localName(uri: string): string {
    const hash = uri?.lastIndexOf('#');
    const slash = uri?.lastIndexOf('/');
    const pos = Math.max(hash ?? -1, slash ?? -1);
    return pos >= 0 ? uri.slice(pos + 1) : uri ?? '';
}
```

**Note on driver module-level singleton:** In Next.js, the driver is created at module level in a route handler. This is fine for `route.ts` (server-side only). Do not create a new driver per request — reuse the singleton.

### Pattern 5: GraphWindow.tsx — SigmaContainer + ForceAtlas2 + Interactions

**What:** Full-screen Sigma.js canvas with ForceAtlas2 layout, zoom-triggered labels, hover/click node interactions.
**File:** `mapper/src/app/page/components/GraphWindow.tsx`

```typescript
// Source: sim51.github.io/react-sigma/docs/ + npm peer dependency verification
"use client";
import { SigmaContainer, useLoadGraph, useSigma } from "@react-sigma/core";
import { useWorkerLayoutForceAtlas2 } from "@react-sigma/layout-forceatlas2";
import { MultiDirectedGraph } from "graphology";
import "@react-sigma/core/lib/style.css";
import { useEffect, useState } from "react";

// LoadGraph: child component inside SigmaContainer
function GraphLoader({ nodes, edges }: GraphData) {
    const loadGraph = useLoadGraph();
    const { start, stop, isRunning } = useWorkerLayoutForceAtlas2({
        settings: { gravity: 1, scalingRatio: 10, barnesHutOptimize: true }
    });

    useEffect(() => {
        const graph = new MultiDirectedGraph();
        nodes.forEach(n => graph.addNode(n.id, {
            label: n.label,
            size: 5 + Math.log(1 + degree),   // degree added after graph built
            color: TYPE_COLORS[n.type] ?? '#999',
            x: Math.random(), y: Math.random(), // initial positions required by FA2
        }));
        edges.forEach(e => graph.addEdge(e.source, e.target, { label: e.label, type: 'arrow' }));
        loadGraph(graph);
        start();                                // FA2 runs immediately on mount
    }, [nodes, edges]);
    // ...
}
```

**CRITICAL: Initial positions required.** ForceAtlas2 requires `x` and `y` attributes on every node before it can run. Use `Math.random()` or circular layout as seeds.

**CSS import is mandatory:** `import "@react-sigma/core/lib/style.css"` — without this the container has no dimensions and Sigma renders invisible.

### Pattern 6: Hover/Click Interactions via Sigma Reducers

**What:** `nodeReducer` and `edgeReducer` are registered on `SigmaContainer`'s `settings` prop and called for every render frame. They inspect React state (`hoveredNode`, `clickedNode`) to modify rendered appearance without touching the underlying graphology graph.

```typescript
// Source: sigmajs.org/docs/advanced/customization/ + sim51 examples
const settings = {
    nodeReducer: (node, data) => {
        if (clickedNode && node !== clickedNode && !neighbors.has(node)) {
            return { ...data, color: '#e0e0e0', size: data.size * 0.6 };
        }
        if (node === hoveredNode || node === clickedNode) {
            return { ...data, highlighted: true };
        }
        return data;
    },
    edgeReducer: (edge, data) => {
        if (clickedNode) {
            const [src, tgt] = sigma.getGraph().extremities(edge);
            if (src !== clickedNode && tgt !== clickedNode) {
                return { ...data, hidden: true };
            }
        }
        return data;
    },
};
```

Events are registered via the `useSigma` hook inside a child component:

```typescript
const sigma = useSigma();
sigma.on('enterNode', ({ node }) => setHoveredNode(node));
sigma.on('leaveNode', () => setHoveredNode(null));
sigma.on('clickNode', ({ node }) => setClickedNode(prev => prev === node ? null : node));
```

### Anti-Patterns to Avoid

- **Creating driver per request:** Create `neo4j.driver()` once at module scope in the API route. Re-creating per request causes connection pool exhaustion.
- **Running FA2 without initial positions:** ForceAtlas2 throws if `x` or `y` is missing. Always seed with random positions before calling `start()`.
- **Forgetting CSS import:** `@react-sigma/core/lib/style.css` is required. The container has no height without it, so Sigma renders invisibly.
- **Using `n10s.rdf.import.fetch` with `file:///`:** This requires the TTL file to be inside the Neo4j Docker container's filesystem. Use `n10s.rdf.import.inline` instead to pass content as a string parameter from Python.
- **Not creating uniqueness constraint before n10s.graphconfig.init:** n10s requires `CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE` to exist before `graphconfig.init` or any import.
- **Using `NEO4JLABS_PLUGINS` in docker-compose.yml:** This is the deprecated name. Use `NEO4J_PLUGINS` for Neo4j 5.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebGL graph rendering | Custom canvas/SVG graph | `sigma` v3 + `@react-sigma/core` | WebGL batch rendering; handles 10k+ nodes without frame drops |
| Force-directed layout | Custom spring simulation | `graphology-layout-forceatlas2` + `@react-sigma/layout-forceatlas2` | Runs in Web Worker; FA2 is proven for knowledge graphs |
| RDF/TTL → Neo4j parsing | Custom Turtle parser + Cypher inserts | `n10s.rdf.import.inline` | n10s handles blank nodes, namespace mapping, literal types, OWL axioms |
| Node degree calculation | `graph.neighbors(node).length` | `graph.degree(node)` | graphology built-in; O(1) lookup |
| Neo4j connection pooling | Custom HTTP client to Neo4j | `neo4j-driver` / `neo4j` Python pkg | Official drivers handle Bolt protocol, connection pooling, retry logic |

**Key insight:** Sigma.js + graphology is the graph visualization equivalent of "use the framework" — the nodeReducer/edgeReducer system makes hover/click highlighting a 10-line pattern instead of a custom rendering engine.

---

## Common Pitfalls

### Pitfall 1: n10s graphconfig already exists on reimport
**What goes wrong:** Second call to `load_ttl_to_neo4j` fails with "GraphConfig already exists" because the first run initialized it and wipe+delete only removed Resource nodes, not the config node.
**Why it happens:** `n10s.graphconfig.init` creates a `_n10s_GraphConfig` node. `MATCH (n) DETACH DELETE n` deletes it too, but the constraint still exists — or vice versa depending on order.
**How to avoid:** Use `CALL n10s.graphconfig.drop()` (which handles missing config gracefully) before re-initializing. Then recreate the constraint. Run in this order: `MATCH (n) DETACH DELETE n` → `n10s.graphconfig.drop()` → `DROP CONSTRAINT n10s_unique_uri IF EXISTS` → `CREATE CONSTRAINT` → `n10s.graphconfig.init` → `n10s.rdf.import.inline`.
**Warning signs:** `Neo.ClientError.Procedure.ProcedureCallFailed` with "GraphConfig already exists" message.

### Pitfall 2: ForceAtlas2 never settles (graph animates forever)
**What goes wrong:** FA2 keeps running and the graph never stabilizes; node positions jitter continuously.
**Why it happens:** Default FA2 settings don't have automatic stopping criteria. The `useWorkerLayoutForceAtlas2` hook runs indefinitely until `stop()` is called.
**How to avoid:** Use `isRunning` from the hook to display a "stop" button. Optionally set a timer to auto-stop after N seconds (e.g., 5s). Parameters: lower `gravity` values (0.5–2) tend to stabilize faster; `barnesHutOptimize: true` speeds convergence.
**Warning signs:** CPU stays at >10% after graph is loaded.

### Pitfall 3: `localName()` stripping fails for blank node URIs
**What goes wrong:** Blank nodes in the RDF (e.g., `_:b0`) don't have a `#` or `/` separator; `localName()` returns the empty string or the full blank node ID.
**Why it happens:** n10s with `handleVocabUris: 'IGNORE'` may create node records without a `uri` property for blank nodes.
**How to avoid:** In the API route's `localName()` function, add a fallback: return `uri ?? 'Resource'`. In the Cypher query, use `coalesce(n.uri, toString(id(n)))` as the node ID.
**Warning signs:** Blank or `undefined` node labels in the graph display.

### Pitfall 4: Neo4j container not ready when agent tool runs
**What goes wrong:** `load_ttl_to_neo4j` runs immediately after `docker compose --profile graph up -d` and fails with connection refused.
**Why it happens:** Neo4j takes 10–30 seconds to start, initialize, and load the n10s plugin.
**How to avoid:** In the Python tool, wrap the `GraphDatabase.driver()` call with a retry loop (3 attempts, 5-second delay) with clear error message. Or document in master_instruction.md that the agent should wait for Neo4j to be ready.
**Warning signs:** `ServiceUnavailable: Unable to retrieve routing information` error.

### Pitfall 5: react-sigma CSS not imported causes invisible graph
**What goes wrong:** `GraphWindow` renders but shows a blank white area; no error in console.
**Why it happens:** SigmaContainer has `height: 0` without the CSS import.
**How to avoid:** Add `import "@react-sigma/core/lib/style.css"` at the top of `GraphWindow.tsx`. Set explicit `style={{ height: "100%", width: "100%" }}` on `SigmaContainer`.
**Warning signs:** React DevTools shows `sigma-container` div with height 0.

### Pitfall 6: Neo4j driver singleton in Next.js dev mode (hot reload)
**What goes wrong:** Multiple driver instances created on hot reload exhaust connection pool.
**Why it happens:** Next.js dev server re-evaluates modules on hot reload, creating new driver instances each time.
**How to avoid:** Use `global` caching pattern in `route.ts`: check `(global as any)._neo4jDriver` before creating a new driver.
**Warning signs:** `Neo4jError: Connection pool full` in dev mode.

---

## Code Examples

Verified patterns from official sources:

### Neo4j Docker Compose Service (with Neosemantics)
```yaml
# Source: neo4j.com/docs/operations-manual/current/docker/plugins/ (2026-03)
  neo4j:
    image: neo4j:5
    container_name: neo4j
    ports:
      - "7474:7474"   # HTTP browser
      - "7687:7687"   # Bolt
    env_file:
      - neo4j/neo4j.env
    environment:
      NEO4J_PLUGINS: '["n10s"]'
    volumes:
      - neo4j_data:/data
    profiles:
      - graph
```

### Neosemantics Full Wipe + Reimport Sequence
```cypher
-- Source: neo4j.com/labs/neosemantics/4.3/import/ + n10s community docs
MATCH (n) DETACH DELETE n;
CALL n10s.graphconfig.drop() YIELD configExisted RETURN configExisted;
DROP CONSTRAINT n10s_unique_uri IF EXISTS;
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
CALL n10s.graphconfig.init({handleVocabUris: 'IGNORE'});
CALL n10s.rdf.import.inline($ttl_content, 'Turtle')
  YIELD terminationStatus, triplesLoaded, triplesParsed, namespaces
  RETURN terminationStatus, triplesLoaded, triplesParsed;
```

### SigmaContainer with Directed Graph and ForceAtlas2
```typescript
// Source: sim51.github.io/react-sigma/docs/ + npm peer dependency verification (2026-03)
import { SigmaContainer } from "@react-sigma/core";
import { useWorkerLayoutForceAtlas2 } from "@react-sigma/layout-forceatlas2";
import { MultiDirectedGraph } from "graphology";
import "@react-sigma/core/lib/style.css";

// Inside a child of SigmaContainer:
const { start, stop, kill, isRunning } = useWorkerLayoutForceAtlas2({
    settings: {
        gravity: 1,
        scalingRatio: 10,
        barnesHutOptimize: true,
        barnesHutTheta: 0.5,
        slowDown: 3,
    }
});

// Wrap:
<SigmaContainer
    graph={MultiDirectedGraph}
    style={{ height: "100%", width: "100%" }}
    settings={{ renderEdgeLabels: true, defaultEdgeType: "arrow" }}
>
    <GraphLoader nodes={nodes} edges={edges} />
</SigmaContainer>
```

### Neo4j JavaScript Driver in Next.js API Route
```typescript
// Source: neo4j.com/docs/javascript-manual/current/ (driver v6)
import neo4j from 'neo4j-driver';

// Module-level singleton (dev-safe via global cache)
const globalWithDriver = global as typeof global & { _neo4jDriver?: ReturnType<typeof neo4j.driver> };
if (!globalWithDriver._neo4jDriver) {
    globalWithDriver._neo4jDriver = neo4j.driver(
        process.env.NEO4J_BOLT_URI ?? 'bolt://localhost:7687',
        neo4j.auth.basic(
            process.env.NEO4J_USER ?? 'neo4j',
            process.env.NEO4J_PASSWORD ?? 'neo4j_password'
        )
    );
}
const driver = globalWithDriver._neo4jDriver;

// Query pattern:
const { records } = await driver.executeQuery(
    'MATCH (n) RETURN n.uri AS uri, labels(n) AS labels, properties(n) AS props',
    {},
    { database: 'neo4j' }
);
```

### Python Neo4j Driver in BaseTool
```python
# Source: neo4j.com/docs/python-manual/current/ (driver v5+, pip install neo4j)
from neo4j import GraphDatabase

with GraphDatabase.driver(bolt_uri, auth=(user, password)) as driver:
    records, summary, keys = driver.execute_query(
        "CALL n10s.rdf.import.inline($ttl_content, 'Turtle') "
        "YIELD terminationStatus, triplesLoaded RETURN terminationStatus, triplesLoaded",
        {"ttl_content": ttl_content},
        database_="neo4j",
    )
    triples = records[0]["triplesLoaded"] if records else 0
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `NEO4JLABS_PLUGINS` | `NEO4J_PLUGINS` | Neo4j 5.x Docker image | Old var deprecated; use new one |
| `neo4j-driver` Python pkg | `neo4j` Python pkg | Driver v5 (2022) | `neo4j-driver` is now an alias with no updates |
| `react-sigma-v2` (npm) | `@react-sigma/core` (sim51) | 2022 rewrite | The `webvis-suite/react-sigma-v2` is abandoned; sim51's is the maintained fork |
| Manual Web Worker for FA2 | `@react-sigma/layout-forceatlas2` | v3 package | Worker lifecycle managed by the hook |
| `driver.session().run()` | `driver.executeQuery()` | Driver v5.x | New API auto-manages session/transaction/retry |

**Deprecated/outdated:**
- `react-sigma-v2` package: abandoned, do not use
- `NEO4JLABS_PLUGINS`: deprecated in Neo4j 5 Docker; replaced by `NEO4J_PLUGINS`
- `driver.session()` pattern: still works but `executeQuery()` is preferred for simple queries

---

## Open Questions

1. **`handleVocabUris` value for 223P ontology**
   - What we know: `'IGNORE'` keeps local names only (e.g., `Fan-SF1`); `'MAP'` creates readable names from prefixes; `'KEEP'` stores full URIs.
   - What's unclear: Whether the 223P ontology TTL uses blank nodes heavily (which `'IGNORE'` handles differently) — needs to be verified against actual `ontology.ttl` output from Phase 9.
   - Recommendation: Default to `'IGNORE'` in the planner; if blank node handling breaks imports, switch to `'MAP'`. Planner should flag this as a tuning decision.

2. **RDF type color palette**
   - What we know: Node color is coded by `rdf:type`; CONTEXT.md lists: Equipment=blue, Duct=green, ConnectionPoint=orange, System=purple.
   - What's unclear: The exact class names in the 223P TTL output (depends on Phase 9 generator); `ontology.ttl` doesn't exist yet.
   - Recommendation: Define a fallback palette with ~8 colors and a `TYPE_COLORS` map that defaults to gray for unknown types. Planner should mark the palette as "populate after Phase 9 is run once".

3. **Neo4j connectivity from Next.js dev server**
   - What we know: Docker compose maps `7687:7687`; Next.js connects via `bolt://localhost:7687`.
   - What's unclear: Whether the Next.js server (running outside Docker) can connect to the containerized Neo4j via `localhost:7687` in the project's WSL2 environment.
   - Recommendation: Use `bolt://localhost:7687` in `.env.local`. If WSL2 networking issues arise, use the container's actual IP. Document as a setup step.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio |
| Config file | `agent/pyproject.toml` (`asyncio_mode = "auto"`) |
| Quick run command | `cd agent && uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x` |
| Full suite command | `cd agent && uv run pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P10-01 | Neo4j Docker service starts with n10s plugin | smoke (manual) | `docker compose --profile graph up -d && docker exec neo4j cypher-shell "CALL n10s.graphconfig.list()"` | N/A — manual |
| P10-02 | `load_ttl_to_neo4j` tool: returns success dict with triples_loaded | unit (mocked Neo4j) | `uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x` | ❌ Wave 0 |
| P10-03 | `load_ttl_to_neo4j` tool: handles missing ontology.ttl gracefully | unit | `uv run pytest tests/test_load_ttl_to_neo4j_tool.py::test_missing_ttl -x` | ❌ Wave 0 |
| P10-04 | GET /api/graph returns `{nodes, edges}` from real Neo4j | integration (manual) | Manual: `curl http://localhost:3000/api/graph` | N/A — manual |
| P10-05 | GraphWindow renders SigmaContainer (smoke render test) | frontend smoke | Next.js build passes without TypeScript errors | N/A — build |

### Sampling Rate
- **Per task commit:** `cd agent && uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x`
- **Per wave merge:** `cd agent && uv run pytest tests/ -x`
- **Phase gate:** Full Python suite green + manual smoke (Neo4j up + `/api/graph` returns data + GraphWindow renders) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent/tests/test_load_ttl_to_neo4j_tool.py` — unit tests for LoadTtlToNeo4jTool (mocked neo4j driver + mocked TTL file)
- [ ] `neo4j/neo4j.env` — credentials file (needed for docker compose to start)

*(Frontend GraphWindow tests are not automated — visual inspection is the primary verification for graph rendering)*

---

## Sources

### Primary (HIGH confidence)
- npm registry (2026-03-21 live query) — `@react-sigma/core` 5.0.6, peer deps `react ^18 || ^19`, `sigma ^3.0.2`, `graphology ^0.26.0`
- npm registry (2026-03-21 live query) — `@react-sigma/layout-forceatlas2` 5.0.6, `graphology-layout-forceatlas2` 0.10.1, `neo4j-driver` 6.0.1
- [Neo4j Docker Plugins Documentation](https://neo4j.com/docs/operations-manual/current/docker/plugins/) — `NEO4J_PLUGINS` env var, docker compose syntax
- [Neosemantics Import Documentation](https://neo4j.com/labs/neosemantics/4.3/import/) — `n10s.rdf.import.inline`, `n10s.graphconfig.init`, `handleVocabUris` values
- [Neo4j JavaScript Driver Manual](https://neo4j.com/docs/javascript-manual/current/) — `driver.executeQuery()`, singleton pattern
- [Neo4j Python Driver Manual](https://neo4j.com/docs/python-manual/current/) — `pip install neo4j`, `GraphDatabase.driver()`, `execute_query()`
- [React Sigma Setup Guide](https://sim51.github.io/react-sigma/docs/start-setup/) — CSS import requirement, `SigmaContainer`, `useLoadGraph`
- [React Sigma Layouts](https://sim51.github.io/react-sigma/docs/example/layouts/) — `useWorkerLayoutForceAtlas2`, start/stop/kill/isRunning
- [Sigma.js Customization](https://www.sigmajs.org/docs/advanced/customization/) — `nodeReducer`, `edgeReducer` for interaction highlighting

### Secondary (MEDIUM confidence)
- [Neosemantics Getting Started Tutorial](https://neo4j.com/labs/neosemantics/tutorial/) — `CREATE CONSTRAINT n10s_unique_uri`, `n10s.graphconfig.init` sequence
- [Graphology ForceAtlas2 Docs](https://graphology.github.io/standard-library/layout-forceatlas2.html) — initial position requirement, parameter reference

### Tertiary (LOW confidence)
- Community reports about `NEO4JLABS_PLUGINS` deprecation — confirmed against official docs above (upgraded to HIGH)
- WSL2 localhost networking for Docker containers — project-specific, unverified

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified live against npm registry (2026-03-21)
- Architecture: HIGH — patterns verified against official docs; inline-vs-fetch recommendation verified against n10s docs
- Pitfalls: MEDIUM-HIGH — Pitfalls 1-3 verified against n10s docs and sigma patterns; Pitfalls 4-6 are community-confirmed patterns

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable ecosystem; Neo4j 5 + n10s are both stable releases)
