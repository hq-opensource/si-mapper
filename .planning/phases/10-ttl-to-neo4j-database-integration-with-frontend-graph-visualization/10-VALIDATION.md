---
phase: 10
slug: ttl-to-neo4j-database-integration-with-frontend-graph-visualization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python agent tool) + Jest/Vitest (Next.js frontend) |
| **Config file** | `agent/pyproject.toml` (pytest) / `mapper/package.json` (jest) |
| **Quick run command** | `cd agent && uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x -q` |
| **Full suite command** | `cd agent && uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x -q && cd ../mapper && npm test -- --passWithNoTests` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent && uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x -q`
- **After every plan wave:** Run full suite command above
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | Docker/Neo4j | manual | `docker compose --profile graph up -d neo4j` | N/A | pending |
| 10-01-02 | 01 | 1 | Python tool | unit | `cd agent && uv run pytest tests/test_load_ttl_to_neo4j_tool.py -x -q` | W0 (Plan 01 Task 2 creates) | pending |
| 10-02-01 | 02 | 1 | npm deps | manual | `grep -q '"@react-sigma/core"' mapper/package.json` | N/A | pending |
| 10-02-02 | 02 | 1 | API route | unit | `cd mapper && npx jest --testPathPattern=graph/route.test` | W0 (Plan 02 Task 3 creates) | pending |
| 10-03-01 | 03 | 2 | GraphWindow | build | `cd mapper && npm run build 2>&1 | grep -v warning` | N/A | pending |
| 10-04-01 | 04 | 3 | E2E verify | manual | checkpoint:human-verify | N/A | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_load_ttl_to_neo4j_tool.py` — unit tests for LoadTtlToNeo4jTool (mocked neo4j driver) — created by Plan 01 Task 2
- [ ] `mapper/src/app/api/graph/route.test.ts` — unit tests for GET /api/graph route (mocked neo4j-driver) — created by Plan 02 Task 3

*Existing pytest and jest infrastructure already present — no new framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Neo4j starts with Neosemantics plugin loaded | Docker infra | Requires running Docker + browser | `docker compose --profile graph up -d neo4j` -> open `http://localhost:7474` -> verify n10s procedures exist with `CALL n10s.graphconfig.show()` |
| TTL imports into Neo4j correctly | End-to-end import | Requires live Neo4j + real TTL file | Call agent tool via master agent -> verify node/edge counts returned match expected ontology size |
| Graph renders in browser with nodes and edges | Frontend visual | No headless graph rendering test | Open Graph tab -> verify ForceAtlas2 layout runs -> verify nodes appear with color-coded types |
| Hover card shows node properties | Frontend interactive | No headless interaction test | Hover over node -> verify info card appears bottom-right with RDF type, label, degree |
| Click locks card + highlights connections | Frontend interactive | No headless interaction test | Click node -> card stays visible -> connected nodes highlighted |
| Drag repositions node | Frontend interactive | No headless interaction test | Click-hold-drag node to new position -> verify position updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
