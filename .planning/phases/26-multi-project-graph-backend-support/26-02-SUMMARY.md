---
phase: 26-multi-project-graph-backend-support
plan: 02
title: "neo4j_prefix mode — namespace-scoped multi-system on Community Edition"
status: completed
completed_at: 2026-04-09
wave: 2
depends_on: [26-01]
---

## Summary

Implemented the `neo4j_prefix` backend mode across the full agent + frontend
stack.  All systems share the single `"neo4j"` Community Edition database; each
system's nodes are tagged with `_graph_ns = <system_id>` to provide per-system
isolation without `CREATE DATABASE`.

## Changes Made

### Task 1 — `agent/utils/project_utils.py`
- Updated module docstring state-shape comment to include `graph_namespace`.
- Added `get_graph_namespace(tool_context) -> str | None`:
  - Returns `None` for any backend other than `neo4j_prefix`.
  - Returns `active_system.id` (stripped) when backend is `neo4j_prefix`.
  - Raises `ValueError` when backend is `neo4j_prefix` but `active_system.id` is absent.

### Task 2 — `agent/tools/load_ttl_to_neo4j_tool.py`
- Added `get_graph_namespace` to import line.
- Added `ns = get_graph_namespace(tool_context)` after `db_name` resolution.
- **Wipe block** (Community Edition path) is now namespace-aware:
  - `neo4j_prefix`: `MATCH (n {_graph_ns: $ns}) DETACH DELETE n` — only this system's nodes.
  - `neo4j_single`: `MATCH (n) DETACH DELETE n` — full wipe.
  - n10s config drop and constraint drop only run in `neo4j_single` mode.
- **n10s init block** guards re-initialisation:
  - `neo4j_single` / enterprise: safe full reinit.
  - `neo4j_prefix`: idempotent `IF NOT EXISTS` create with `try/except` guard.
- **Step 6b** (new): after `import.inline`, stamps all unstamped nodes:
  `MATCH (n) WHERE n._graph_ns IS NULL SET n._graph_ns = $ns`
- Success log includes `(namespace: <ns>)` when prefix mode is active.

### Task 3 — `agent/tools/neo4j_query_tools.py`
- Added `get_graph_backend, get_graph_namespace` to import.
- `GetGraphSchemaTool.run_async` now returns two additional fields:
  - `"graph_backend"`: current backend string.
  - `"graph_namespace"`: system ID in prefix mode, `None` otherwise.

### Task 4 — `mapper/src/app/api/graph/route.ts`
- Added `const ns` resolver: reads `?ns=` param in `neo4j_prefix` mode, `null` otherwise.
- Node query conditionally adds `{_graph_ns: $ns}` filter when `ns` is set.
- Edge query conditionally adds `{_graph_ns: $ns}` on both endpoints.
- Parameters object is `{ ns }` when ns is set, `{}` otherwise — `neo4j_single` path is unchanged.

### Task 5 — Frontend state
- **`mapper/src/types/index.ts`**: Added JSDoc comment on `System.neo4j_db_name` explaining `graph_namespace` derivation.
- **`mapper/src/lib/projects.ts`**: Same JSDoc added to server-side `System` interface.
- **`mapper/src/app/page.tsx`**:
  - `AgentState.active_system` type extended with `graph_namespace: string`.
  - `combinedState` assembly: `graph_namespace: activeSystem.id` added.
  - `useEffect` re-stamp: `graph_namespace: activeSystem.id` added.
- **`mapper/src/app/page/components/GraphWindow.tsx`**:
  - Fetch URL updated to `?db=${db}&ns=${ns}` (always passes system ID).
  - `useEffect` dependency changed from `activeSystem?.neo4j_db_name` → `activeSystem?.id`.

### Task 6 — `agent/master_architecture/prompts/master_instruction.md`
- Added `### neo4j_prefix Mode — Namespace Filtering Rule` section inside the Neo4j Query Protocol block.
- Mandates `_graph_ns` filter on every Cypher `MATCH` clause in prefix mode.
- References `graph_namespace` field from `get_graph_schema` response.

## Verification Results

All plan verification checks passed:

| Check | Result |
|---|---|
| `_graph_ns` in `load_ttl_to_neo4j_tool.py` (wipe + stamp) | ✅ lines 89, 147, 150 |
| `graph_namespace` in `neo4j_query_tools.py` | ✅ lines 22, 244, 253 |
| `_graph_ns` in `route.ts` (node + edge queries) | ✅ lines 50, 61 |
| `graph_namespace` in `page.tsx` (type + 2× assembly) | ✅ lines 39, 153, 178 |
| `neo4j_prefix` in `master_instruction.md` | ✅ lines 114, 116 |

Runtime import test (all symbols):
```
TEST 1 PASS: default -> neo4j_single, db=neo4j, ns=None
TEST 2 PASS: neo4j_prefix -> db=neo4j, ns=sys-abc123
TEST 3 PASS: raised ValueError as expected
```

## Success Criteria Status

| Criterion | Status |
|---|---|
| Wipe in prefix mode deletes only `{_graph_ns}` nodes | ✅ |
| Imported nodes stamped with `_graph_ns` post-import | ✅ |
| `get_graph_schema` surfaces `graph_backend` + `graph_namespace` | ✅ |
| Frontend graph API filters by namespace when `ns` param present | ✅ |
| Agent instructions mandate `_graph_ns` filters in prefix mode | ✅ |
| `neo4j_single` mode behaviour completely unchanged (ns=null guards) | ✅ |

