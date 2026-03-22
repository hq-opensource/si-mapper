---
phase: 10-ttl-to-neo4j-database-integration-with-frontend-graph-visualization
plan: 01
subsystem: database
tags: [neo4j, neosemantics, n10s, docker, ttl, rdf, ontology, python, google-adk]

# Dependency graph
requires:
  - phase: 09-ontology-subagents
    provides: OntologyValidatorAgent that produces ontology.ttl — the source file loaded by this tool
provides:
  - Neo4j Docker service with Neosemantics (n10s) plugin, graph profile, port 7474/7687
  - LoadTtlToNeo4jTool — BaseTool that wipes Neo4j and reimports ontology.ttl via n10s.rdf.import.inline
  - load_ttl_to_neo4j_tool registered in master agent task_tools list
  - Neo4j Import Protocol section in master_instruction.md with explicit HITL gate
  - neo4j/neo4j.env credentials file
affects: [10-02, 10-03, 10-04, frontend-graph-visualization]

# Tech tracking
tech-stack:
  added: [neo4j Python driver (neo4j>=5.0.0 / installed as neo4j==6.1.0), Neo4j 5 Docker image with n10s plugin]
  patterns: [BaseTool subclass pattern (LoadTtlToNeo4jTool mirrors CaptureFrontendStateTool), full wipe-and-reimport Cypher sequence, Path mock chain using recursive __truediv__ for reliable test isolation]

key-files:
  created:
    - neo4j/neo4j.env
    - agent/master_architecture/tools/load_ttl_to_neo4j_tool.py
    - agent/tests/test_load_ttl_to_neo4j_tool.py
  modified:
    - docker-compose.yml
    - agent/pyproject.toml
    - agent/uv.lock
    - agent/master_architecture/create_master_agent.py
    - agent/master_architecture/prompts/master_instruction.md

key-decisions:
  - "neo4j Docker service uses NEO4J_PLUGINS (not deprecated NEO4JLABS_PLUGINS) for Neo4j 5 compatibility"
  - "graph profile isolates Neo4j from deploy/tools profiles — must run docker compose --profile graph up"
  - "load_ttl_to_neo4j is HITL-gated — Do NOT auto-trigger; waits for explicit human instruction"
  - "Path mock chain uses recursive __truediv__ returning the same leaf mock to handle multi-segment / chains in tests"
  - "Cypher sequence: wipe -> drop config -> drop constraint -> create constraint -> init config -> import -> count (8 queries total)"

patterns-established:
  - "Path mock for multi-segment chains: set __truediv__ on both root and leaf to return the same leaf MagicMock"
  - "execute_query side_effect list for ordered Neo4j call verification"

requirements-completed: [P10-01, P10-02, P10-05]

# Metrics
duration: 7min
completed: 2026-03-22
---

# Phase 10 Plan 01: Neo4j Docker + LoadTtlToNeo4jTool Summary

**Neo4j 5 service with Neosemantics n10s plugin wired to master agent via LoadTtlToNeo4jTool, enabling wipe-and-reimport of ontology.ttl with explicit HITL gate**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-03-22T13:30:00Z
- **Completed:** 2026-03-22T13:37:21Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Neo4j 5 Docker service defined with Neosemantics (n10s) plugin, graph profile, and standard port mapping (7474/7687)
- LoadTtlToNeo4jTool implements full 8-query Cypher sequence: wipe, drop config, drop constraint, create constraint, init config, import inline, count nodes, count rels
- 4 unit tests pass with fully mocked Neo4j driver and Path (no live service required)
- Tool registered in create_master_agent.py task_tools; Neo4j Import Protocol added to master_instruction.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Docker Neo4j service + credentials + Python dependency** - `5a2e789` (chore)
2. **TDD RED: failing tests** - `b36921e` (test)
3. **Task 2: LoadTtlToNeo4jTool + tests + registration + protocol** - `c1b9144` (feat)

_Note: TDD task has two commits (test RED → feat GREEN)_

## Files Created/Modified
- `neo4j/neo4j.env` - Neo4j credentials (NEO4J_AUTH=neo4j/neo4j_password)
- `docker-compose.yml` - Added neo4j service with n10s plugin, graph profile, neo4j_data volume
- `agent/pyproject.toml` - Added neo4j>=5.0.0 dependency
- `agent/master_architecture/tools/load_ttl_to_neo4j_tool.py` - LoadTtlToNeo4jTool BaseTool subclass
- `agent/tests/test_load_ttl_to_neo4j_tool.py` - 4 unit tests with mocked driver and Path
- `agent/master_architecture/create_master_agent.py` - Added load_ttl_to_neo4j_tool import and registration
- `agent/master_architecture/prompts/master_instruction.md` - Added Neo4j Import Protocol section

## Decisions Made
- Used `NEO4J_PLUGINS` (not `NEO4JLABS_PLUGINS`) — the latter is deprecated in Neo4j 5.
- Neo4j service uses `graph` profile to keep it isolated from always-on services.
- `load_ttl_to_neo4j` is explicitly HITL-gated to prevent accidental wipe of graph database.
- Path mock for tests: `__truediv__` on both root and leaf returns the same leaf mock, handling the 4-segment `/` chain in the tool's TTL path resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Path mock chain for multi-segment path resolution in tests**
- **Found during:** Task 2 TDD GREEN phase
- **Issue:** Original test used `mock_path_instance.__truediv__ = MagicMock(return_value=mock_ttl_path)` but subsequent `/` calls on `mock_ttl_path` returned fresh MagicMocks, so `ttl_path.exists()` was not controlled. test_missing_ttl_file connected to real Neo4j instead of returning early.
- **Fix:** Extracted `_make_path_mock()` helper that sets `mock_ttl_path.__truediv__ = MagicMock(return_value=mock_ttl_path)` (recursive) and `mock_path_root.__truediv__ = MagicMock(return_value=mock_ttl_path)`. Full chain now always resolves to the same controllable leaf.
- **Files modified:** agent/tests/test_load_ttl_to_neo4j_tool.py
- **Verification:** All 4 tests pass in 1.6s without any network activity
- **Committed in:** c1b9144 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in test mock chain)
**Impact on plan:** Fix was necessary for test correctness. No scope creep.

## Issues Encountered
- Path mock chain wasn't propagating `exists()` control through 4 `/` segments — resolved by making every link in the chain return the same terminal mock object.

## User Setup Required
To start Neo4j: `docker compose --profile graph up -d neo4j`

The master agent will provide this command automatically when `load_ttl_to_neo4j` returns a connection error.

## Next Phase Readiness
- Neo4j infrastructure ready for plan 10-02 (graph API endpoint) and 10-03 (frontend graph tab)
- LoadTtlToNeo4jTool is fully tested and registered — master agent can call it on human request
- Neo4j not running by default (graph profile) — must be started explicitly before use

---
*Phase: 10-ttl-to-neo4j-database-integration-with-frontend-graph-visualization*
*Completed: 2026-03-22*

## Self-Check: PASSED

All created files exist on disk. All task commits verified in git log.
