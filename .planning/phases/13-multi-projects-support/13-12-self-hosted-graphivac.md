# 13-12 — Self-Hosted Graphivac

**Phase:** 13 — Multi-Project Support
**Status:** Not started
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

Three separate services each hold their own `GRAPHIVAC_BASE_URL`, pointing to the same cloud instance in different formats:

| Service | Env file | `GRAPHIVAC_BASE_URL` value | Format |
|---|---|---|---|
| **MCP server** | `mcp_server/server/mcp.env` | `https://graphivac.hvac.io/api/v1` | Includes `/api/v1` |
| **Agent** | `agent/docker.env` | `https://graphivac.hvac.io/api/v1` | Includes `/api/v1` |
| **Mapper** (server-side) | `mapper/docker.env` | `https://graphivac.hvac.io` | Base host only |
| **Mapper** (client-side) | `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` | Full static iframe URL (per-grid) | One fixed URL |

The **existing inconsistency** — MCP server and agent include `/api/v1` in the base URL while the mapper does not — must be resolved as part of this step (see *URL Normalization* below).

All services share: `GRAPHIVAC_ORG_ID=public`.

---

## Two-URL Problem: Server-Side vs. Client-Side

When Graphivac runs in Docker, two distinct URL bases are required:

| Use | Network path | Example value |
|---|---|---|
| **Server-to-Graphivac** — API calls from mapper API routes, MCP server, and agent | Container DNS (internal) | `http://graphivac:8888` |
| **Browser-to-Graphivac** — iframe `src`, must be reachable from the end-user's browser | Public hostname | `http://localhost:8888` or `https://graphivac.example.com` |

Using the container-internal URL (`http://graphivac:8888`) as the iframe `src` fails silently — the browser cannot resolve container DNS.

### Solution: two env vars

| Env var | Who reads it | Purpose |
|---|---|---|
| `GRAPHIVAC_BASE_URL` | Server-side only (mapper API routes, agent, MCP server) | Internal API calls. Set to container DNS in Docker. |
| `GRAPHIVAC_PUBLIC_BASE_URL` | `/api/config` route → client components | Public iframe base URL. Set to the browser-reachable hostname. |

For the **cloud deployment**, both values are identical (`https://graphivac.hvac.io`).  
For a **self-hosted Docker deployment**:
- `GRAPHIVAC_BASE_URL=http://graphivac:8888` (server-to-server)
- `GRAPHIVAC_PUBLIC_BASE_URL=http://localhost:8888` (or `https://graphivac.acme.com`)

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
- Any agent tool that reads `GRAPHIVAC_BASE_URL` and passes it to `GraphivacAPI` — no code change needed there; `GraphivacAPI` is the only place that constructs URLs

---

## Dynamic Iframe URL — Replacing the Static `NEXT_PUBLIC_GRAPHIVAC_GRID_URL`

`NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is currently a full static URL pointing to a single fixed grid. With multi-project support (`13-07`, `13-08`), each system has its own `graphivac_project_id` and `graphivac_grid_id`. A single env var cannot serve all systems.

The correct pattern is to construct the iframe URL from its parts at runtime:

```
{graphivacBaseUrl}/o/{graphivacOrgId}/p/{activeProject.graphivac_project_id}/g/{activeSystem.graphivac_grid_id}?mode=editor&init-zoom=t
```

Where:
- `graphivacBaseUrl` and `graphivacOrgId` come from `/api/config` (fetched once on page load)
- `activeProject.graphivac_project_id` and `activeSystem.graphivac_grid_id` come from `WorkspaceContext`

This eliminates `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` entirely and makes the canvas URL always track the selected system. The `ExternalPageIframe` component receives a dynamically constructed `src` prop from `YourMainContent`.

> **Note:** The `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` env var and its Docker Compose ARG should be removed from `mapper/Dockerfile`, `docker-compose.yml`, `mapper/.env.example`, and `mapper/docker.env.example` as part of this step.

---

## Changes Required

### 1. `graphivac/Dockerfile` — new Graphivac Docker image

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

EXPOSE 8888

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8888/api/v1/orgs/public || exit 1

CMD ["java", "-jar", "graphivac-server.jar", "8888"]
```

**Design decisions:**
- `eclipse-temurin:21-jre-alpine` — official Adoptium JRE, minimal footprint, Java 21 LTS.
- Port `8888` — avoids collision with the mapper (`3000`), agent (`8001`), and MCP server (`8080`).
- The JAR is downloaded at **image-build time** from `hvac.io` via a `RUN curl` step. The version is parameterised with `ARG GRAPHIVAC_VERSION` so upgrading requires only a version bump and a rebuild.
- `/data` is the working directory mounted as a volume. Graphivac writes org/project/grid configuration into this directory. It must survive container restarts and image upgrades.

> **Upgrade path:** bump `GRAPHIVAC_VERSION` build arg → `docker compose build graphivac` → `docker compose up -d graphivac`. The `/data` volume is untouched.

### 2. `docker-compose.yml` — add `graphivac` service

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
      - "8888:8888"
    volumes:
      - graphivac_data:/data
    profiles:
      - deploy
      - build
```

Add `graphivac_data` to the top-level `volumes:` block.

The service is placed before the MCP server and agent so the dependency order is clear. Both the MCP server and agent depend on Graphivac being reachable, but Docker Compose `depends_on` is not strictly needed — the services perform their own retry/connection logic.

### 3. Env var updates — MCP server

`mcp_server/server/mcp.env` (and the equivalent example file, if it exists):

```dotenv
# Base URL of the Graphivac server (no /api/v1 suffix — appended internally).
# Self-hosted Docker: http://graphivac:8888
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_BASE_URL=http://graphivac:8888
```

`mcp_server/graphivac/graphivac_api.py` — update all endpoint strings:

```python
# Before (old inconsistent format)
endpoint = f"/orgs/{self.org_id}/projects/{self.project_id}/grids/{self.grid_id}"

# After (normalized — base URL no longer includes /api/v1)
endpoint = f"/api/v1/orgs/{self.org_id}/projects/{self.project_id}/grids/{self.grid_id}"
```

This one-line change in `graphivac_api.py` covers all six methods (`get_grid_info_edn`, `update_grid_edn`, `get_all_grids`, etc.) — each builds its URL the same way via `f"{self.base_url}{endpoint}"`.

### 4. Env var updates — Agent

`agent/docker.env.example` and `agent/.example.env`:

```dotenv
# Base URL of the Graphivac server (no /api/v1 suffix).
# Self-hosted Docker: http://graphivac:8888
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_BASE_URL=http://graphivac:8888
```

No code changes in the agent — it passes `GRAPHIVAC_BASE_URL` directly to `GraphivacAPI`, which now handles the `/api/v1` prefix.

### 5. Env var updates — Mapper (server-side)

`mapper/docker.env.example` and `mapper/.env.example`:

```dotenv
# Internal (server-to-server) URL of Graphivac.
# Self-hosted Docker: http://graphivac:8888
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_BASE_URL=http://graphivac:8888

# Public (browser-reachable) URL of Graphivac.
# Self-hosted Docker: http://localhost:8888  (or https://graphivac.acme.com)
# Cloud: https://graphivac.hvac.io
GRAPHIVAC_PUBLIC_BASE_URL=http://localhost:8888

# Remove NEXT_PUBLIC_GRAPHIVAC_GRID_URL — replaced by dynamic URL construction.
```

### 6. `mapper/src/app/api/config/route.ts` — return `GRAPHIVAC_PUBLIC_BASE_URL`

```typescript
return NextResponse.json({
  graphivacBaseUrl: process.env.GRAPHIVAC_PUBLIC_BASE_URL
    ?? process.env.GRAPHIVAC_BASE_URL   // fallback keeps cloud deployments working without a second var
    ?? '',
  graphivacOrgId: process.env.GRAPHIVAC_ORG_ID ?? '',
});
```

The fallback to `GRAPHIVAC_BASE_URL` means cloud deployments that have only one variable set continue to work without any config change.

### 7. `mapper/src/app/page/components/YourMainContent.tsx` — dynamic iframe URL

Replace the two hardcoded `https://graphivac.hvac.io/...` strings with a URL constructed from context:

```tsx
// At the top of the component, read config from context or /api/config
const { activeProject, activeSystem, graphivacConfig } = useWorkspace();

// Construct the Graphivac iframe URL for the active system
function buildGraphivacUrl(mode: 'editor' | 'view'): string {
  if (!graphivacConfig?.graphivacBaseUrl || !activeProject || !activeSystem) return '';
  const { graphivacBaseUrl, graphivacOrgId } = graphivacConfig;
  const projId = activeProject.graphivac_project_id;
  const gridId = activeSystem.graphivac_grid_id;
  const modeParam = mode === 'view' ? 'iframe=t&init-zoom=t' : 'mode=editor&init-zoom=t';
  return `${graphivacBaseUrl}/o/${graphivacOrgId}/p/${projId}/g/${gridId}?${modeParam}`;
}

// Usage
case 'edit':
  return <ExternalPageIframe src={buildGraphivacUrl('editor')} />;
case 'view':
  return <ExternalPageIframe src={buildGraphivacUrl('view')} />;
```

`graphivacConfig` is fetched once by `WorkspaceContext` from `/api/config` and stored in context, consistent with how `AGENT_BACKEND_URL` is handled.

### 8. `WorkspaceContext` — add `graphivacConfig`

`WorkspaceContext` already fetches configuration on mount. Extend it to also load Graphivac config from `/api/config`:

```typescript
interface GraphivacConfig {
  graphivacBaseUrl: string;
  graphivacOrgId: string;
}

// New field in context
graphivacConfig: GraphivacConfig | null;
```

On mount, one `fetch('/api/config')` populates `graphivacConfig`. The call is cheap (no network egress — served by Next.js) and needed only once per page load.

### 9. Remove `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` references

Once the dynamic URL is in place, remove:
- `mapper/Dockerfile` — `ARG NEXT_PUBLIC_GRAPHIVAC_GRID_URL` and `ENV NEXT_PUBLIC_GRAPHIVAC_GRID_URL=...` lines
- `docker-compose.yml` — `NEXT_PUBLIC_GRAPHIVAC_GRID_URL:` build arg under `si-mapper-frontend`
- `mapper/.env.example` and `mapper/docker.env.example` — the var and its comments
- Any type definitions or default references to the var in source code

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

### Milestone 1 — Docker container (no env var changes)

**Goal:** Run a self-hosted Graphivac instance. Confirm it is reachable and the API works.

**Steps:**
1. Create `graphivac/` directory and `graphivac/Dockerfile`.
2. Build the image: `docker compose --profile build build graphivac`.
3. Start it: `docker compose --profile deploy up graphivac`.
4. Verify health check: `curl http://localhost:8888/api/v1/orgs/public`.
5. Verify the UI is reachable in a browser: `http://localhost:8888/o/public`.
6. Add `graphivac_data` named volume and confirm data persists across a container restart.

---

### Milestone 2 — URL normalization (MCP server + agent)

**Goal:** Standardise `GRAPHIVAC_BASE_URL` to host-only format (no `/api/v1` suffix) across all Python services.

**Steps:**
1. Update `mcp_server/graphivac/graphivac_api.py` — prepend `/api/v1` to all endpoint strings.
2. Update `mcp_server/server/mcp.env` — remove `/api/v1` from the URL value.
3. Update `agent/docker.env.example` and `agent/.example.env` — same change.
4. Run `tests/test_read_grid.py` and `tests/test_integration_grid_sync.py` to confirm no regression.
5. Update `.env.example` files for developers.

---

### Milestone 3 — Two-URL split (mapper)

**Goal:** Separate `GRAPHIVAC_BASE_URL` (server-to-server) from `GRAPHIVAC_PUBLIC_BASE_URL` (browser-to-Graphivac).

**Steps:**
1. Update `mapper/src/app/api/config/route.ts` — return `GRAPHIVAC_PUBLIC_BASE_URL ?? GRAPHIVAC_BASE_URL`.
2. Add `GRAPHIVAC_PUBLIC_BASE_URL` to `mapper/.env.example` and `mapper/docker.env.example`.
3. Update `docker-compose.yml` — pass `GRAPHIVAC_PUBLIC_BASE_URL` through to the `si-mapper-frontend` service via `env_file`.
4. Confirm: `GET /api/config` returns `http://localhost:8888` (the browser-reachable URL).

---

### Milestone 4 — Dynamic iframe URL (mapper frontend)

**Goal:** Replace both hardcoded Graphivac URL strings in `YourMainContent.tsx` with a URL built from `activeProject`, `activeSystem`, and `/api/config`.

**Steps:**
1. Add `graphivacConfig: GraphivacConfig | null` to `WorkspaceContext`. Fetch from `/api/config` on mount.
2. Add `buildGraphivacUrl(mode)` helper in `YourMainContent.tsx`.
3. Replace `src="https://graphivac.hvac.io/..."` with `src={buildGraphivacUrl('editor')}` and `src={buildGraphivacUrl('view')}`.
4. Remove `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` from all env files, `mapper/Dockerfile`, and `docker-compose.yml`.
5. Test: switch active system → confirm the iframe `src` changes to the new system's grid URL.
6. Test: `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is not set → confirm no error and the placeholder appears when `activeSystem` is null.

---

## Acceptance Criteria

**Container (Milestone 1):**
- [ ] `docker compose --profile deploy up graphivac` starts successfully.
- [ ] The health check passes: `GET /api/v1/orgs/public` returns 200.
- [ ] The Graphivac UI is accessible at `http://localhost:8888` from a browser.
- [ ] Data survives container restart (`docker compose restart graphivac`).
- [ ] Data survives an image upgrade (rebuild + recreate) — no grid data lost.

**URL normalization (Milestone 2):**
- [ ] `GRAPHIVAC_BASE_URL` in MCP server and agent env files contains no `/api/v1` suffix.
- [ ] `mcp_server/graphivac/graphivac_api.py` prepends `/api/v1` to every endpoint string.
- [ ] Integration tests pass against both the self-hosted container and the cloud instance.

**Two-URL split (Milestone 3):**
- [ ] `GET /api/config` returns `GRAPHIVAC_PUBLIC_BASE_URL` (not `GRAPHIVAC_BASE_URL`) for `graphivacBaseUrl`.
- [ ] Fallback: if only `GRAPHIVAC_BASE_URL` is set, `/api/config` returns that value.
- [ ] `GRAPHIVAC_PUBLIC_BASE_URL` is documented in `mapper/.env.example`.

**Dynamic iframe URL (Milestone 4):**
- [ ] No hardcoded `graphivac.hvac.io` strings remain in `YourMainContent.tsx` or any other component.
- [ ] `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is removed from all env example files, `Dockerfile`, and `docker-compose.yml`.
- [ ] Switching the active system updates the iframe `src` to that system's grid.
- [ ] When no system is selected, the iframe shows the "No grid URL configured" placeholder.
- [ ] URL pattern: `{graphivacPublicBaseUrl}/o/{orgId}/p/{projectId}/g/{gridId}?mode=editor&init-zoom=t`.

---

## Notes & Decisions

- **Default org is always `public`** — this is not a project-specific default; it is Graphivac's fixed built-in org name. `GRAPHIVAC_ORG_ID=public` is correct for both cloud and self-hosted deployments and never needs to change.
- **JAR is downloaded at build time, not bundled** — including a 50+ MB JAR in the repository would be inappropriate. The `Dockerfile` downloads it from `hvac.io` during `docker compose build`. Teams in air-gapped environments should pre-pull the image or mirror the JAR to an internal artifact registry.
- **Upgrade by bumping `GRAPHIVAC_VERSION`** — the `ARG GRAPHIVAC_VERSION=1.1.6` build argument makes version upgrades a one-line diff in `docker-compose.yml` or the `Dockerfile`. No data migration is expected between Graphivac versions (data is stored as files in `/data`).
- **`GRAPHIVAC_PUBLIC_BASE_URL` defaults to `GRAPHIVAC_BASE_URL`** — this keeps existing deployments (cloud or single-host) working with zero config change. Only Docker deployments where the internal and external addresses differ need to set both variables.
- **`eclipse-temurin:21-jre-alpine` is the recommended base** — it is the official Adoptium JRE image, uses Java 21 LTS, and has a minimal Alpine footprint (~130 MB). Graphivac requires Java 8 or higher per the wiki; Java 21 is backwards compatible.
- **No authentication layer in scope** — Graphivac's public org is accessible without authentication by design (the cloud `graphivac.hvac.io` uses the same approach). If access control is needed, it should be enforced at the network/reverse-proxy level outside the scope of this step.
- **Port `8888` chosen** to avoid conflicts with mapper (`3000`), agent (`8001`), and MCP server (`8080`). It is configurable by changing the `CMD` argument and the port mapping in `docker-compose.yml`.
- **`NEXT_PUBLIC_GRAPHIVAC_GRID_URL` is fully deprecated** — it was always a workaround for the single-grid era. The dynamic URL construction introduced in Milestone 4 is the correct multi-system approach, consistent with how the mapper already handles project and system selection.
- **The dynamic URL depends on `13-07`** — `activeProject.graphivac_project_id` and `activeSystem.graphivac_grid_id` are fields introduced in `13-07`. Milestone 4 should be attempted only after `13-07` is complete. Milestones 1–3 are independent of `13-07`.
- **Cloud deployments are unaffected** — operators using the public `graphivac.hvac.io` instance do not need to change anything except removing `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` and adding `GRAPHIVAC_PUBLIC_BASE_URL` (which defaults to `GRAPHIVAC_BASE_URL`). All other changes are additive or internal.



