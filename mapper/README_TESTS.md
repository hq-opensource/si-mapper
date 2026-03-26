# Testing — `mapper`

This document explains how to run, filter, and understand the test suite for the `mapper` Next.js application.

---

## Prerequisites

Install dependencies from the `mapper` folder (only needed once):

```bash
pnpm install
```

---

## Running the tests

All commands must be run from the **`mapper/`** directory.

### Run the full suite

```bash
pnpm test
```

### Run without coverage output (faster)

```bash
pnpm test --no-coverage
```

### Run in watch mode (re-runs on file save)

```bash
pnpm test:watch
```

---

## Filtering tests

### By file name (substring match)

```bash
# Only the graphivac client tests
pnpm test --testPathPatterns="graphivac-client"

# Only the API route tests
pnpm test --testPathPatterns="api/projects/__tests__"

# Only the storage layer tests
pnpm test --testPathPatterns="lib/__tests__/projects"

# Only the file-upload/delete route tests
pnpm test --testPathPatterns="files-route"
```

### By test name (substring match on `describe` / `test` titles)

```bash
# Only tests whose name contains "DELETE"
pnpm test --testNamePattern="DELETE"

# Only "409" conflict tests
pnpm test --testNamePattern="409"
```

---

## Test files

| File | What it covers | Approach |
|---|---|---|
| `src/lib/__tests__/projects.test.ts` | `lib/projects.ts` — all Project & System CRUD, path-traversal guards | Real temp directory, no mocks |
| `src/lib/__tests__/graphivac-client.test.ts` | `lib/graphivac-client.ts` — all 5 Graphivac API client functions | `global.fetch` spy, no real HTTP |
| `src/app/api/projects/__tests__/route.test.ts` | `GET` + `POST /api/projects` | `lib/projects` + `lib/graphivac-client` mocked |
| `src/app/api/projects/__tests__/id-route.test.ts` | `GET` + `PATCH` + `DELETE /api/projects/[id]` | `lib/projects` + `lib/graphivac-client` mocked |
| `src/app/api/projects/__tests__/systems-route.test.ts` | `GET` + `POST /api/projects/[id]/systems` | `lib/projects` + `lib/graphivac-client` mocked |
| `src/app/api/projects/__tests__/sysid-route.test.ts` | `GET` + `PATCH` + `DELETE /api/projects/[id]/systems/[sysId]` | `lib/projects` + `lib/graphivac-client` mocked |
| `src/app/api/projects/__tests__/files-route.test.ts` | `GET` + `POST /files` and `DELETE /files/[filename]` | Real temp directory, only `lib/projects` mocked |
| `src/app/api/graph/route.test.ts` | `GET /api/graph` — Neo4j graph query route | `neo4j-driver` mocked |

**Total: 8 suites, 106 tests.**

---

## Test strategy by layer

### Storage layer (`lib/projects.ts`)
Pure file-system tests using a real temporary directory created in `os.tmpdir()`. The `PROJECTS_FOLDER` environment variable is pointed at this temp dir before the module is loaded. No mocks — every read and write hits actual disk.

### Graphivac client (`lib/graphivac-client.ts`)
`global.fetch` is spied on per-test using `jest.spyOn`. A `mockResponse(status, body)` helper returns a minimal fetch-compatible object. No real HTTP calls are made. Each test sets `GRAPHIVAC_BASE_URL` and `GRAPHIVAC_ORG_ID` in `process.env` and cleans them up in `afterEach`.

### API route handlers (`app/api/projects/`)
Route handler functions are imported directly and called with a constructed `NextRequest`. Dependencies are mocked with `jest.mock`:

- `@/lib/projects` — all storage functions replaced by `jest.fn()`
- `@/lib/graphivac-client` — all client functions replaced by `jest.fn()`

Tests assert on the `Response.status` and the JSON body. `jest.resetAllMocks()` runs before each test so return values are always set explicitly.

### File routes (`/files`, `/files/[filename]`)
A hybrid approach: `@/lib/projects` is mocked (including `systemDir`, which is made to return a real temp directory). Actual `fs/promises` calls run against that temp dir, so upload, list, overwrite, and delete operations are exercised against real files.

---

## Configuration

| Setting | Value | File |
|---|---|---|
| Test runner | Jest 30 | `jest.config.js` |
| Transformer | `ts-jest` | `jest.config.js` |
| Environment | `node` | `jest.config.js` |
| Path alias | `@/` → `src/` | `jest.config.js` → `moduleNameMapper` |
| Test file glob | `**/*.test.ts`, `**/*.test.tsx` | `jest.config.js` → `testMatch` |

---

## Notes on `console.error` output

Several tests deliberately trigger error paths (502 Graphivac failures, 500 disk errors, etc.). The route handlers log these with `console.error` before returning the error response. This output is **expected** and does not indicate a failing test — only a `FAIL` line in the summary does.

To suppress it during a run:

```bash
pnpm test --silent
```

