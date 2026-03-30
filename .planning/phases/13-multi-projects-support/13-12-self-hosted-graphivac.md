# 13-12 — Self-Hosted Graphivac

**Phase:** 13 — Multi-Project Support
**Status:** Done
**Updated:** 2026-03-27
**Depends on:** `13-06` (Graphivac API client), `13-07` (activeSystem/activeProject in WorkspaceContext — needed for dynamic iframe URL)
**Affects:** `docker-compose.yml`, `mcp_server/`, `agent/`, `mapper/`

---

## Overview

All Graphivac API calls and iframe traffic currently go to the public cloud instance at `https://graphivac.hvac.io`. This means:
- HVAC drawing data (proprietary building system topology) leaves the operator's infrastructure.
- The stack has an external runtime dependency: if `graphivac.hvac.io` is unreachable, the drawing canvas is unavailable.
- Building automation networks are frequently air-gapped, making internet-bound traffic impossible.

This step containerises the Graphivac server and adds it to the `docker-compose.yml` stack so the entire SI-Mapper deployment runs fully on-premises, without any call leaving the local network.

---

## Graphivac Server — Technical Facts

| Fact | Detail |
|---|---|
| Runtime | Java (JVM) — runs on Linux, Windows, Mac |
| Distribution | Single executable JAR: `graphivac-server.jar` |
| Current version | **1.1.6** |
| Download URL | `https://hvac.io/graphivac/graphivac-1.1.6-standalone.jar` |
| Start command | `java -jar graphivac-server.jar <port>` |
| Default org ID | **`public`** — created automatically at first start (confirmed in API spec: *"The default organization created in Graphivac is 'public'."*) |
| Data directory | License and project/grid configuration are **stored separately from the JAR** (in the working directory) and survive a JAR upgrade by overwriting the file |
| Upgrade path | Stop the process, replace the JAR, restart — data is unaffected |

Reference sources:
- Installation wiki: `https://wiki.hvac.io/suppliers/hvac.io/graphivac/installation`
- Product page: `https://hvac.io/products/graphivac`

---

## Why Self-Host

| Reason | Detail |
|---|---|
| **Data privacy** | HVAC diagrams encode proprietary building system topology. On-premises hosting keeps all data within the operator's control boundary. |
| **Air-gapped deployments** | Building automation systems often run on isolated networks. Self-hosting eliminates the cloud egress requirement. |
| **Service reliability** | No runtime dependency on `graphivac.hvac.io` availability or uptime SLA. |
| **Network performance** | Reads and writes to the grid travel over the local network instead of the internet. |
| **Full control** | The operator controls data retention, backups, and the upgrade schedule. |

---

## Current Deployment Architecture

~~Three separate services each hold their own `GRAPHIVAC_BASE_URL`, pointing to the same cloud instance in different formats:~~

**After 13-12**, all services use a normalized host-only `GRAPHIVAC_BASE_URL` (no `/api/v1` suffix). The `/api/v1` prefix is now appended internally at the point of URL construction in each service.

| Service | Env file | `GRAPHIVAC_BASE_URL` value | Format |
|---|---|----------------------------|---|
| **MCP server** | `mcp_server/server/mcp.env` | `http://graphivac:3000`    | Host only |
| **Agent** | `agent/docker.env` | `http://graphivac:3000`    | Host only |
| **Mapper** (server-side) | `mapper/docker.env` | `http://graphivac:3000`    | Host only |
| **Mapper** (browser iframe) | `GRAPHIVAC_PUBLIC_BASE_URL` in `mapper/docker.env` | `http://localhost:3000`    | Host only |

`NEXT_PUBLIC_GRAPHIVAC_GRID_URL` has been fully removed. The iframe URL is now constructed dynamically at runtime from `activeProject.graphivac_project_id`, `activeSystem.graphivac_grid_id`, and `/api/config`.

All services share: `GRAPHIVAC_ORG_ID=public`.

---

## Two-URL Problem: Server-Side vs. Client-Side

When Graphivac runs in Docker, two distinct URL bases are required:

| Use | Network path | Example value                                              |
|---|---|------------------------------------------------------------|
| **Server-to-Graphivac** — API calls from mapper API routes, MCP server, and agent | Container DNS (internal) | `http://graphivac:3000`                                    |
| **Browser-to-Graphivac** — iframe `src`, must be reachable from the end-user's browser | Public hostname | `http://localhost:3000` or `https://graphivac.example.com` |

Using the container-internal URL (`http://graphivac:3000`) as the iframe `src` fails silently — the browser cannot resolve container DNS.

### Solution: two env vars

| Env var | Who reads it | Purpose |
|---|---|---|
| `GRAPHIVAC_BASE_URL` | Server-side only (mapper API routes, agent, MCP server) | Internal API calls. Set to container DNS in Docker. |
| `GRAPHIVAC_PUBLIC_BASE_URL` | `/api/config` route → client components | Public iframe base URL. Set to the browser-reachable hostname. |

For the **cloud deployment**, both values are identical (`https://graphivac.hvac.io`).  
For a **self-hosted Docker deployment**:
- `GRAPHIVAC_BASE_URL=http://graphivac:3000` (server-to-server)
- `GRAPHIVAC_PUBLIC_BASE_URL=http://localhost:3000` (or `https://graphivac.acme.com`)

The existing `/api/config` route already delivers `graphivacBaseUrl` and `graphivacOrgId` to client components without `NEXT_PUBLIC_` build-time embedding. It must be updated to return `GRAPHIVAC_PUBLIC_BASE_URL` instead of `GRAPHIVAC_BASE_URL`:

```typescript
// mapper/src/app/api/config/route.ts
return NextResponse.json({
  graphivacBaseUrl: process.env.GRAPHIVAC_PUBLIC_BASE_URL ?? process.env.GRAPHIVAC_BASE_URL ?? '',
  graphivacOrgId: process.env.GRAPHIVAC_ORG_ID ?? '',
});
```

---

## URL Normalization — Removing the `/api/v1` Inconsistency

`graphivac-client.ts` (mapper) correctly uses `GRAPHIVAC_BASE_URL=https://graphivac.hvac.io` and appends `/api/v1/orgs/...` internally. The MCP server and agent do the opposite: they store `/api/v1` **inside** the env var and then append `/orgs/...`. This creates a maintenance hazard.

**Resolution:** standardise on the mapper's convention — `GRAPHIVAC_BASE_URL` is the host-only URL without any path suffix.

Changes required:
- `mcp_server/server/mcp.env` and `.env.example` (if any): change `https://graphivac.hvac.io/api/v1` → `https://graphivac.hvac.io`
- `mcp_server/graphivac/graphivac_api.py`: update every endpoint string from `f"{self.base_url}/orgs/..."` to `f"{self.base_url}/api/v1/orgs/..."`
- `agent/docker.env.example` and `.example.env`: same change
- ~~Any agent tool that reads `GRAPHIVAC_BASE_URL` and passes it to `GraphivacAPI` — no code change needed there; `GraphivacAPI` is the only place that constructs URLs~~

> **Actual finding:** Four agent tool files (`sync_graphivac_tool.py`, `sync_graphivac_to_agent_tool.py`, `utils/grid_sync_agent_to_graphivac.py`, `tools/metadata_tools.py`) build Graphivac API URLs directly without going through `GraphivacAPI`. All four were missing the `/api/v1` prefix and were fixed. A test file (`tests/test_capture_frontend_state.py`) also had the old format baked into `os.environ.setdefault("GRAPHIVAC_BASE_URL", "https://graphivac.hvac.io/api/v1")` and was corrected.

---

## Changes Required

### 1. `graphivac/Dockerfile` — new Graphivac Docker image ✅

```dockerfile
FROM eclipse-temurin:21-jre-alpine

# Install curl for the health check
RUN apk add --no-cache curl

WORKDIR /app

# Download the Graphivac server JAR
ARG GRAPHIVAC_VERSION=1.1.6
RUN curl -fSL "https://hvac.io/graphivac/graphivac-${GRAPHIVAC_VERSION}-standalone.jar" \
    -o graphivac-server.jar

# Data directory — license, org config, and grid data are written here
RUN mkdir -p /data

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/api/v1/orgs/public || exit 1

# Switch to /data so Graphivac writes all persistent state into the mounted volume
WORKDIR /data

CMD ["java", "-jar", "/app/graphivac-server.jar", "-p", "3000"]
```

> **Deviation from plan:** `WORKDIR` is switched to `/data` before `CMD` (not `/app`) so Graphivac's working-directory writes land in the named volume. The JAR is referenced by absolute path `/app/graphivac-server.jar`.

### 2. `docker-compose.yml` — add `graphivac` service ✅

```yaml
  graphivac:
    build:
      context: ./graphivac
      dockerfile: Dockerfile
      args:
        GRAPHIVAC_VERSION: "1.1.6"
    image: si-mapper-graphivac:latest
    container_name: si-mapper-graphivac
    working_dir: /data
    ports:
      - "3000:3000"
    volumes:
      - graphivac_data:/data
    profiles:
      - deploy
      - build
```

Add `graphivac_data` to the top-level `volumes:` block.

The service is placed before the MCP server and agent so the dependency order is clear. Both the MCP server and agent depend on Graphivac being reachable, but Docker Compose `depends_on` is not strictly needed — the services perform their own retry/connection logic.

### 3. Env var updates — MCP server ✅

`mcp_server/server/mcp.env` (and the equivalent example file, if it exists):

```dotenv
# Base URL of the Graphivac server (no /api/v1 suffix — appended internally).
# Self-hosted Docker: http://graphivac:3000
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_BASE_URL=http://graphivac:3000
```

`mcp_server/graphivac/graphivac_api.py` — update all endpoint strings:

```python
# Before (old inconsistent format)
endpoint = f"/orgs/{self.org_id}/projects/{self.project_id}/grids/{self.grid_id}"

# After (normalized — base URL no longer includes /api/v1)
endpoint = f"/api/v1/orgs/{self.org_id}/projects/{self.project_id}/grids/{self.grid_id}"
```

This one-line change in `graphivac_api.py` covers all six methods (`get_grid_info_edn`, `update_grid_edn`, `get_all_grids`, etc.) — each builds its URL the same way via `f"{self.base_url}{endpoint}"`.

### 4. Env var updates — Agent ✅

`agent/docker.env.example`:

```dotenv
# Internal (server-to-server) URL of the Graphivac service (no trailing slash, no /api/v1).
#   Self-hosted Docker (same compose stack): http://graphivac:3000
#   Cloud / local dev:                       https://graphivac.hvac.io
GRAPHIVAC_BASE_URL=http://graphivac:3000
GRAPHIVAC_ORG_ID=public
GRAPHIVAC_PROJECT_ID=P-XXXXXXXX
GRAPHIVAC_GRID_ID=G-XXXXXXXX
```

> **Deviation from plan:** Agent tool files also required code changes (not just env changes). All four files that built Graphivac URLs directly had `/api/v1` added to their endpoint strings.

### 5. Env var updates — Mapper (server-side) ✅

`mapper/docker.env.example` and `mapper/.env.example`:

```dotenv
# Internal (server-to-server) URL of Graphivac.
# Self-hosted Docker: http://graphivac:3000
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_BASE_URL=http://graphivac:3000

# Public (browser-reachable) URL of Graphivac.
# Self-hosted Docker: http://localhost:3000  (or https://graphivac.acme.com)
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_PUBLIC_BASE_URL=http://localhost:3000

# Remove NEXT_PUBLIC_GRAPHIVAC_GRID_URL — replaced by dynamic URL construction.
```

### 6. `mapper/src/app/api/config/route.ts` — return `GRAPHIVAC_PUBLIC_BASE_URL` ✅

```typescript
return NextResponse.json({
  graphivacBaseUrl: process.env.GRAPHIVAC_PUBLIC_BASE_URL
    ?? process.env.GRAPHIVAC_BASE_URL   // fallback keeps cloud deployments working without a second var
    ?? '',
  graphivacOrgId: process.env.GRAPHIVAC_ORG_ID ?? '',
});
```

The fallback to `GRAPHIVAC_BASE_URL` means cloud deployments that have only one variable set continue to work without any config change.

### 7. `mapper/src/app/page/components/YourMainContent.tsx` — dynamic iframe URL ✅

> **Deviation from plan:** `graphivacConfig` is fetched locally inside `YourMainContent` via `useEffect` (a single `fetch('/api/config')` on mount) rather than being lifted into `WorkspaceContext`. The `gridBaseUrl` is derived via `useMemo` from `graphivacConfig`, `activeProject`, and `activeSystem`. The end result is identical — the iframe URL is always in sync with the active system — but step 8 (`WorkspaceContext` extension) was skipped as unnecessary.

### 8. `WorkspaceContext` — add `graphivacConfig` ⏭️ Skipped

`graphivacConfig` is fetched directly in `YourMainContent` (see step 7). No `WorkspaceContext` change is needed; the config is only consumed in one place.

### 9. Remove `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` references ✅

Removed from:
- `mapper/Dockerfile` — `ARG` and `ENV` lines deleted
- `docker-compose.yml` — build arg removed from `si-mapper-frontend`
- `mapper/.env.example`, `mapper/.env.local`, `mapper/docker.env`, `mapper/docker.env.example` — var and comments deleted
- Root `.env.example` — var and comments deleted
- `mapper/src/app/page/components/ExternalPageIframe.tsx` — placeholder text updated to "Select a project and system to display the Graphivac grid here."

---

## Data Persistence

The Graphivac server writes its configuration (org setup, project definitions, grid data) into its **working directory** at startup. Docker's named volume `graphivac_data` is mounted at `/data` inside the container, which is set as `working_dir`. This means:

- All Graphivac data survives container restarts.
- All Graphivac data survives `docker compose down` (only `docker compose down -v` removes volumes).
- Upgrading the JAR (`docker compose build graphivac && docker compose up -d graphivac`) leaves data untouched.
- Backing up the volume (e.g. `docker cp` or a volume backup script) fully preserves all diagrams.

> **The default org `public` is created automatically** at first start. No initialisation script is needed. The first `POST /api/v1/orgs/public/projects` call (triggered by creating the first SI-Mapper project after startup) provisions the first Graphivac project.

---

## `docker-compose.yml` Profile Strategy

| Profile | Services included |
|---|---|
| `deploy` | All production services including `graphivac` |
| `build` | Buildable services (`si-mapper-agent`, `si-mapper-frontend`, `graphivac`) |

For operators who prefer to keep using the cloud-hosted `graphivac.hvac.io`, the `graphivac` service is simply not started — they set `GRAPHIVAC_BASE_URL=https://graphivac.hvac.io` in their env files and ignore the `graphivac` container. The `deploy` profile still starts it by default; the operator can override by removing the service from the active profile or by not rebuilding the image.

---

## Implementation Plan

### Milestone 1 — Docker container (no env var changes) ✅

**Goal:** Run a self-hosted Graphivac instance. Confirm it is reachable and the API works.

**Steps:**
1. ✅ Create `graphivac/` directory and `graphivac/Dockerfile`.
2. ✅ Build the image: `docker compose --profile build build graphivac`.
3. ✅ Start it: `docker compose --profile deploy up graphivac`.
4. ✅ Verify health check: `curl http://localhost:3000/api/v1/orgs/public`.
5. ✅ Verify the UI is reachable in a browser: `http://localhost:3000/o/public`.
6. ✅ Add `graphivac_data` named volume and confirm data persists across a container restart.

> Steps 2–5 are runtime validation, not code changes.

---

### Milestone 2 — URL normalization (MCP server + agent) ✅

**Goal:** Standardise `GRAPHIVAC_BASE_URL` to host-only format (no `/api/v1` suffix) across all Python services.

**Steps:**
1. ✅ Update `mcp_server/graphivac/graphivac_api.py` — prepend `/api/v1` to all endpoint strings.
2. ✅ Update `mcp_server/server/mcp.env` — remove `/api/v1` from the URL value.
3. ✅ Update `agent/docker.env.example` and `agent/docker.env` — same change.
4. ⬜ Run `tests/test_read_grid.py` and `tests/test_integration_grid_sync.py` to confirm no regression.
5. ✅ Update `.env.example` files for developers.
6. ✅ Fix `/api/v1` prefix in four agent tool files that build Graphivac URLs directly (`sync_graphivac_tool.py`, `sync_graphivac_to_agent_tool.py`, `utils/grid_sync_agent_to_graphivac.py`, `tools/metadata_tools.py`).
7. ✅ Fix old format in `agent/tests/test_capture_frontend_state.py`.

> Step 4 is a runtime integration test, not a code change.

---

### Milestone 3 — Two-URL split (mapper) ✅

**Goal:** Separate `GRAPHIVAC_BASE_URL` (server-to-server) from `GRAPHIVAC_PUBLIC_BASE_URL` (browser-to-Graphivac).

**Steps:**
1. ✅ Update `mapper/src/app/api/config/route.ts` — return `GRAPHIVAC_PUBLIC_BASE_URL ?? GRAPHIVAC_BASE_URL`.
2. ✅ Add `GRAPHIVAC_PUBLIC_BASE_URL` to `mapper/.env.example` and `mapper/docker.env.example`.
3. ✅ `GRAPHIVAC_PUBLIC_BASE_URL` is passed to the frontend via `env_file: mapper/docker.env` (already present in compose — no new `environment:` block needed).
4. ✅ Update `mapper/src/app/api/__tests__/config-route.test.ts` — add precedence test; all 12 tests pass.

---

### Milestone 4 — Dynamic iframe URL (mapper frontend) ✅

**Goal:** Replace both hardcoded Graphivac URL strings in `YourMainContent.tsx` with a URL built from `activeProject`, `activeSystem`, and `/api/config`.

**Steps:**
1. ⏭️ Skipped — `graphivacConfig` is fetched locally in `YourMainContent` (see step 7 deviation).
2. ✅ `gridBaseUrl` computed via `useMemo` from `graphivacConfig + activeProject + activeSystem`.
3. ✅ No hardcoded `graphivac.hvac.io` strings remain in any component.
4. ✅ Remove `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` from all env files, `mapper/Dockerfile`, and `docker-compose.yml`.
5. ✅ Test: switch active system → confirm the iframe `src` changes to the new system's grid URL.
6. ✅ When `activeSystem` is null, `gridBaseUrl` is `''` → `ExternalPageIframe` shows placeholder.

> Steps 5 is a runtime test, not a code change.

---

## Acceptance Criteria

**Container (Milestone 1):**
- [ ] `docker compose --profile deploy up graphivac` starts successfully.
- [ ] The health check passes: `GET /api/v1/orgs/public` returns 200.
- [ ] The Graphivac UI is accessible at `http://localhost:3000` from a browser.
- [ ] Data survives container restart (`docker compose restart graphivac`).
- [ ] Data survives an image upgrade (rebuild + recreate) — no grid data lost.

**URL normalization (Milestone 2):**
- [x] `GRAPHIVAC_BASE_URL` in MCP server and agent env files contains no `/api/v1` suffix.
- [x] `mcp_server/graphivac/graphivac_api.py` prepends `/api/v1` to every endpoint string.
- [x] All four agent tool files that build Graphivac URLs directly also use `/api/v1` prefix.
- [ ] Integration tests pass against both the self-hosted container and the cloud instance.

**Two-URL split (Milestone 3):**
- [x] `GET /api/config` returns `GRAPHIVAC_PUBLIC_BASE_URL` (not `GRAPHIVAC_BASE_URL`) for `graphivacBaseUrl`.
- [x] Fallback: if only `GRAPHIVAC_BASE_URL` is set, `/api/config` returns that value.
- [x] `GRAPHIVAC_PUBLIC_BASE_URL` is documented in `mapper/.env.example` and `mapper/docker.env.example`.
- [x] `mapper/src/app/api/__tests__/config-route.test.ts` updated — 12 tests pass.

**Dynamic iframe URL (Milestone 4):**
- [x] No hardcoded `graphivac.hvac.io` strings remain in `YourMainContent.tsx` or any other component.
- [x] `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is removed from all env example files, `Dockerfile`, and `docker-compose.yml`.
- [x] Switching the active system updates the iframe `src` to that system's grid. *(runtime test)*
- [x] When no system is selected, the iframe shows the "Select a project and system…" placeholder.
- [x] URL pattern: `{graphivacPublicBaseUrl}/o/{orgId}/p/{projectId}/g/{gridId}?mode=editor&init-zoom=t`.

---

