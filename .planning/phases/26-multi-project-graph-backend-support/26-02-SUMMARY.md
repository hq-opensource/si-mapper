---
phase: 26-multi-project-graph-backend-support
plan: 02
title: "neo4j_prefix mode — namespace-scoped multi-system on Community Edition"
status: completed
completed_at: 2026-04-10
wave: 2
depends_on: [26-01]
---

## Summary

Implemented the `neo4j_prefix` backend mode across the full agent + frontend
stack.  All systems share the single `"neo4j"` Community Edition database; each
system's nodes are tagged with two namespace properties:
- `_graph_ns_system` — system ID; used for per-system isolation (wipe, query, visualise).
- `_graph_ns_project` — project ID; stamped for forward-compatible project-level filtering.

## Changes Made

### Task 1 — `agent/utils/project_utils.py`
- Added `get_graph_system_namespace(tool_context) -> str | None`:
  - Returns `None` for any backend other than `neo4j_prefix`.
  - Returns `active_system.id` (stripped) when backend is `neo4j_prefix`.
  - Raises `ValueError` when backend is `neo4j_prefix` but `active_system.id` is absent.
- Added `get_graph_project_namespace(tool_context) -> str | None`:
  - Returns `None` for any backend other than `neo4j_prefix`.
  - Returns `active_project.id` (stripped) when backend is `neo4j_prefix`.
  - Raises `ValueError` when backend is `neo4j_prefix` but `active_project.id` is absent.

### Task 2 — `agent/tools/load_ttl_to_neo4j_tool.py`
- Added `get_graph_system_namespace` and `get_graph_project_namespace` to import line.
- Added `ns_system` and `ns_project` after `db_name` resolution.
- **Wipe block** (Community Edition path) is now namespace-aware:
  - `neo4j_prefix`: `MATCH (n {_graph_ns_system: $ns}) DETACH DELETE n` — only this system's nodes.
  - `neo4j_single`: `MATCH (n) DETACH DELETE n` — full wipe.
  - n10s config drop and constraint drop only run in `neo4j_single` mode.
- **n10s init block** guards re-initialisation:
  - `neo4j_single` / enterprise: safe full reinit.
  - `neo4j_prefix`: idempotent `IF NOT EXISTS` create with `try/except` guard.
- **Step 6b** (new): after `import.inline`, stamps all unstamped nodes:
  - `MATCH (n) WHERE n._graph_ns_system IS NULL SET n._graph_ns_system = $ns_system`
  - `MATCH (n) WHERE n._graph_ns_project IS NULL SET n._graph_ns_project = $ns_project`
- Success log includes `(ns_system: <ns>)` and `(ns_project: <ns>)` when prefix mode is active.

### Task 3 — `agent/tools/neo4j_query_tools.py`
- Added `get_graph_backend, get_graph_system_namespace, get_graph_project_namespace` to import.
- `GetGraphSchemaTool.run_async` now returns three additional fields:
  - `"graph_backend"`: current backend string.
  - `"graph_namespace_system"`: system ID in prefix mode, `None` otherwise (use for Cypher filtering).
  - `"graph_namespace_project"`: project ID in prefix mode, `None` otherwise (informational).

### Task 4 — `mapper/src/app/api/graph/route.ts`
- Added `const ns` resolver: reads `?ns=` param in `neo4j_prefix` mode, `null` otherwise.
- Node query conditionally adds `{_graph_ns_system: $ns}` filter when `ns` is set.
- Edge query conditionally adds `{_graph_ns_system: $ns}` on both endpoints.
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
- Mandates `_graph_ns_system` filter on every Cypher `MATCH` clause in prefix mode.
- References `graph_namespace_system` field from `get_graph_schema` response.
- Documents `_graph_ns_project` / `graph_namespace_project` as informational (no filtering required).

## Verification Results

All plan verification checks passed:

| Check | Result |
|---|---|
| `_graph_ns_system` in `load_ttl_to_neo4j_tool.py` (wipe + stamp) | ✅ |
| `_graph_ns_project` in `load_ttl_to_neo4j_tool.py` (stamp) | ✅ |
| `graph_namespace_system` in `neo4j_query_tools.py` | ✅ |
| `graph_namespace_project` in `neo4j_query_tools.py` | ✅ |
| `_graph_ns_system` in `route.ts` (node + edge queries) | ✅ |
| `graph_namespace` in `page.tsx` (type + 2× assembly) | ✅ |
| `neo4j_prefix` in `master_instruction.md` | ✅ |

## Success Criteria Status

| Criterion | Status |
|---|---|
| Wipe in prefix mode deletes only `{_graph_ns_system}` nodes | ✅ |
| Imported nodes stamped with `_graph_ns_system` post-import | ✅ |
| Imported nodes stamped with `_graph_ns_project` post-import | ✅ |
| `get_graph_schema` surfaces `graph_backend` + `graph_namespace_system` + `graph_namespace_project` | ✅ |
| Frontend graph API filters by `_graph_ns_system` when `ns` param present | ✅ |
| Agent instructions mandate `_graph_ns_system` filters in prefix mode | ✅ |
| `neo4j_single` mode behaviour completely unchanged (ns=null guards) | ✅ |

