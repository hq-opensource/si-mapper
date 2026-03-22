---
phase: 10
plan: "02"
subsystem: mapper/api
tags: [neo4j, sigma, graphology, api-route, jest, unit-tests]
dependency_graph:
  requires: []
  provides: [GET /api/graph endpoint, neo4j-driver singleton, graph JSON shape]
  affects: [10-03-PLAN.md (GraphWindow component consumes this API)]
tech_stack:
  added: [neo4j-driver@6.0.1, sigma@3.0.2, graphology@0.26.0, "@react-sigma/core@5.0.6", "@react-sigma/layout-core@5.0.6", "@react-sigma/layout-forceatlas2@5.0.6", graphology-layout-forceatlas2@0.10.1, jest@30.3.0, ts-jest@29.4.6]
  patterns: [Next.js App Router API route, Neo4j global singleton, RDF localName stripping, Jest module-level mock with globalThis bridge]
key_files:
  created:
    - mapper/src/app/api/graph/route.ts
    - mapper/src/app/api/graph/route.test.ts
    - mapper/jest.config.js
  modified:
    - mapper/package.json
    - mapper/pnpm-lock.yaml
decisions:
  - "Jest config uses .js extension (not .ts) to avoid ts-node dependency"
  - "Neo4j mock uses globalThis bridge to expose mock fn from hoisted jest.mock() factory, avoiding temporal dead zone caused by global driver singleton being created at import time"
  - "coalesce(n.uri, toString(id(n))) in Cypher handles blank nodes without uri property"
metrics:
  duration_seconds: 204
  completed_date: "2026-03-22"
  tasks_completed: 3
  files_changed: 5
---

# Phase 10 Plan 02: Install npm dependencies and create GET /api/graph API route with unit tests

Neo4j + Sigma.js packages installed, GET /api/graph route created with global driver singleton and RDF localName stripping, Jest configured with 2 passing unit tests.

## Tasks Completed

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Install npm dependencies for Sigma.js + neo4j-driver | 822b9cf | Done |
| 2 | Create GET /api/graph API route | ef2759f | Done |
| 3 | Create unit tests for GET /api/graph route | 87079ba | Done |

## What Was Built

### Task 1: npm Dependencies

Installed 7 production packages and 4 devDependencies:

**Production:** `@react-sigma/core@5.0.6`, `@react-sigma/layout-core@5.0.6`, `@react-sigma/layout-forceatlas2@5.0.6`, `sigma@3.0.2`, `graphology@0.26.0`, `graphology-layout-forceatlas2@0.10.1`, `neo4j-driver@6.0.1`

**Dev:** `jest@30.3.0`, `jest-environment-jsdom@30.3.0`, `@types/jest@30.0.0`, `ts-jest@29.4.6`

### Task 2: GET /api/graph Route

`mapper/src/app/api/graph/route.ts` implements:

- **Global driver singleton** cached on `globalThis._neo4jDriver` to prevent connection pool exhaustion on Next.js hot reload
- **Cypher queries** for all nodes (`coalesce(n.uri, toString(id(n)))` handles blank nodes) and all relationships
- **`localName()`** strips RDF namespace prefixes from URIs (handles both `#` and `/` separators)
- **Response shape**: `{ nodes: [{id, label, type, properties}], edges: [{id, source, target, label}] }`
- **Error handling**: catches Neo4j errors, logs them, returns `{ error: string }` with HTTP 500

### Task 3: Unit Tests

`mapper/src/app/api/graph/route.test.ts` with Jest + ts-jest:

- **Test 1:** `returns nodes and edges on success` — mocks two `executeQuery` calls (nodes + edges), verifies 200 response and correct node/edge shapes including `localName` stripping (`Fan-SF1` from full URI)
- **Test 2:** `returns 500 when Neo4j is unreachable` — mocks `executeQuery` rejection, verifies 500 status and error message

**Mock approach:** `jest.mock("neo4j-driver", ...)` factory exposes the mock fn via `globalThis.__neo4jMockExecuteQuery` to work around the temporal dead zone caused by the driver singleton being created at module import time.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Jest test infrastructure missing**
- **Found during:** Task 3
- **Issue:** No test framework existed in the project. The plan referenced running jest tests but neither jest nor ts-jest were installed.
- **Fix:** Installed jest@30.3.0, jest-environment-jsdom, @types/jest, ts-jest as devDependencies. Created jest.config.js.
- **Files modified:** mapper/package.json, mapper/pnpm-lock.yaml, mapper/jest.config.js
- **Commit:** 87079ba

**2. [Rule 1 - Bug] `const mockExecuteQuery` TDZ error in test mock**
- **Found during:** Task 3 first test run
- **Issue:** Jest hoists `jest.mock()` factories above `const` declarations, so referencing `mockExecuteQuery` inside the factory caused a "Cannot access before initialization" ReferenceError. This is a known Jest 30 TDZ limitation.
- **Fix:** Changed strategy to create the mock fn inside the factory and expose it via `globalThis.__neo4jMockExecuteQuery`, retrieved by a `getExecMock()` helper function.
- **Files modified:** mapper/src/app/api/graph/route.test.ts
- **Commit:** 87079ba

**3. [Rule 3 - Blocking] jest.config.ts requires ts-node (not installed)**
- **Found during:** Task 3 first test execution
- **Issue:** Jest 30 requires `ts-node` to parse TypeScript config files. ts-node was not installed.
- **Fix:** Replaced `jest.config.ts` with `jest.config.js` using `module.exports` — equivalent functionality without the ts-node dependency.
- **Files modified:** mapper/jest.config.js (replaced jest.config.ts)
- **Commit:** 87079ba

## Verification Results

```
sigma: PASS
neo4j: PASS
route: PASS
GET: PASS
tests: PASS
Test Suites: 1 passed, 1 total
Tests: 2 passed, 2 total
TSC: PASS
```

## Self-Check: PASSED
