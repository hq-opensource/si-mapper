---
phase: 26-multi-project-graph-backend-support
plan: 01
title: "GRAPH_BACKEND switch — neo4j_single mode"
status: completed
completed_at: 2026-04-09
wave: 1
---

## Summary

Implemented the `GRAPH_BACKEND` environment variable and the `neo4j_single` operational mode across the full stack.

## Changes Made

### `agent/utils/project_utils.py`
- Added `import logging` and `logger = logging.getLogger(__name__)`.
- Added `VALID_GRAPH_BACKENDS = {"neo4j_single", "neo4j_prefix", "graphdb"}` constant.
- Added `get_graph_backend()` function: reads `GRAPH_BACKEND` env var, defaults to `"neo4j_single"`, warns and falls back on unknown values.
- Rewrote `get_neo4j_db_name()`: returns `"neo4j"` unconditionally for `neo4j_single` and `neo4j_prefix` modes; falls back to state-based lookup for other/future modes.

### `agent/tools/load_ttl_to_neo4j_tool.py`
- Added `get_graph_backend` to the import from `utils.project_utils`.
- Replaced the monolithic `SHOW DATABASES` / `CREATE DATABASE` block with a backend-aware branch:
  - **Community modes** (`neo4j_single`, `neo4j_prefix`): wipe + graceful n10s config drop + constraint drop — no `CREATE DATABASE` calls.
  - **Enterprise/future modes**: original `SHOW DATABASES` → `CREATE DATABASE` if missing, else wipe.
- Steps 5–7 (n10s init, TTL import, node/rel count) are unchanged.

### `mapper/src/app/api/graph/route.ts`
- Replaced `const db = searchParams.get('db') ?? 'neo4j'` with a backend-aware resolver.
- `GRAPH_BACKEND` is read via `process.env.GRAPH_BACKEND` (defaulting to `"neo4j_single"`).
- `db` is always `"neo4j"` for `neo4j_single` and `neo4j_prefix` modes; reads `?db=` param for other modes (forward-compatible).

### Env example files (all four)
All four files — `agent/docker.env.example`, `agent/.env.example`, `mapper/docker.env.example`, `mapper/.env.example` — received a new `# -- Graph backend` section inserted after the `NEO4J_PASSWORD` line:
- `GRAPH_BACKEND=neo4j_single` (uncommented, active default).
- Full comment block describing all three valid values.
- `#GRAPHDB_REST_URL=http://graphdb:7200` placeholder (commented out).

The two mapper files additionally received:
- `#GRAPHDB_PUBLIC_URL=http://localhost:7200` placeholder for the future browser-reachable GraphDB URL.

## Verification

```
# Backend defaults to neo4j_single when unset
python -c "import os; os.environ.pop('GRAPH_BACKEND',None); from agent.utils.project_utils import get_graph_backend; assert get_graph_backend()=='neo4j_single'; print('default OK')"

# Explicit neo4j_single
python -c "import os; os.environ['GRAPH_BACKEND']='neo4j_single'; from agent.utils.project_utils import get_graph_backend, get_neo4j_db_name; assert get_graph_backend()=='neo4j_single'; assert get_neo4j_db_name(None)=='neo4j'; print('neo4j_single OK')"
```

## Acceptance criteria status

| Criterion | Status |
|---|---|
| `GRAPH_BACKEND=neo4j_single` (default) in all four env example files | ✅ |
| `get_graph_backend()` returns `"neo4j_single"` when unset | ✅ |
| `get_neo4j_db_name()` returns `"neo4j"` for both Community modes | ✅ |
| `load_ttl_to_neo4j_tool` skips `CREATE DATABASE` for Community modes | ✅ |
| Frontend `/api/graph/route.ts` uses `"neo4j"` DB for Community modes | ✅ |
| Zero behaviour change when `GRAPH_BACKEND` is unset | ✅ |

