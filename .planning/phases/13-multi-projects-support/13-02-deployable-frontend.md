# 13-02 — Deployable Frontend

**Phase:** 13 — Multi-Project Support
**Status:** Completed
**Updated:** 2026-03-25
**Depends on:** `13-01` (environment variables must be externalized before the Docker image is useful)

---

## Overview

The `mapper/` Next.js frontend currently has no Docker image and is absent from `docker-compose.yml`. Running the stack in production requires a developer to install Node.js, pnpm, and manually run `pnpm build && pnpm start` on the host.

This task packages the frontend as a self-contained Docker image that:
- Builds the Next.js app at image-build time using the project's documented build process (`pnpm install && pnpm build`).
- Excludes unnecessary build artifacts, source files, and development dependencies from the final image.
- Mounts the `uploads/` folder as a Docker volume so uploaded files persist across container restarts and rebuilds.
- Accepts all runtime configuration (service URLs, credentials) via environment variables — not baked-in values.
- Is wired into the root `docker-compose.yml` under the `deploy` profile, consistent with the existing MCP server service.

---

## Current State

| Aspect | Current Situation |
|---|---|
| `mapper/Dockerfile` | Does not exist |
| `docker-compose.yml` — frontend service | Absent; only `si-mapper-mcp`, `mcp-inspector`, `portainer`, and `neo4j` are defined |
| Frontend build process | Documented in root `README.md`: `cd mapper && pnpm install && pnpm build && pnpm start` |
| `uploads/` folder | Used by the file manager API (`/api/files`) for project file storage; currently lives on the host |
| Environment variables | Hardcoded in source (see `13-01`); Docker image is useless without `13-01` complete |

---

## Motivation

- **Reproducible deployments**: Any host with Docker installed can run the full stack with a single `docker compose up --profile deploy`.
- **Isolation**: The frontend process runs in its own container with a pinned Node version, independent of whatever is installed on the host.
- **Portability**: The image can be pushed to a registry and deployed on any server or CI environment.
- **Consistency with existing services**: The MCP server already ships with a `Dockerfile` and a `deploy` profile entry in `docker-compose.yml`. The frontend should follow the same pattern.

---

## Implementation Plan

### Milestone 1 — Create `mapper/Dockerfile`

**Goal:** A multi-stage Docker image that produces a lean production artifact.

**Design decisions:**
- Use official `node:20-alpine` as the base image (small footprint, matches recommended LTS).
- Multi-stage build:
  1. **`deps` stage** — Install all dependencies with pnpm.
  2. **`builder` stage** — Copy source, run `pnpm build`.
  3. **`runner` stage** — Copy only the built output (`.next/standalone` or `.next/` + `public/`) and production node_modules. Start with `node server.js` (Next.js standalone output) or `pnpm start`.
- Enable Next.js [standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output) (`output: 'standalone'` in `next.config.ts`) to minimise the image size — only the files actually needed to run are copied.
- The `uploads/` directory is **not** copied into the image; it is provided as a Docker volume at runtime.

**Steps:**
1. Add `output: 'standalone'` to `mapper/next.config.ts`.
2. Create `mapper/.dockerignore` to exclude:
   - `node_modules/`
   - `.next/`
   - `uploads/`
   - `.env.local`, `.env`
   - `*.log`, `coverage/`, `.git/`
   - `pnpm-lock.yaml` (will be regenerated inside the build stage using the locked versions from lockfile — keep it!)

   > **Correction:** `pnpm-lock.yaml` **must** be included so that `pnpm install --frozen-lockfile` produces a deterministic install. Exclude everything except source and lock files.

3. Create `mapper/Dockerfile` with the three-stage structure described above.

**`mapper/Dockerfile` outline:**
```dockerfile
# ── Stage 1: Install dependencies ──────────────────────────────────────────
FROM node:20-alpine AS deps
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile --prod=false

# ── Stage 2: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# ── Stage 3: Runtime image ──────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Standalone output bundles only what is needed
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# uploads/ will be mounted as a volume — create the mount point
RUN mkdir -p /app/uploads

EXPOSE 3000
CMD ["node", "server.js"]
```

**Files to create/modify:**
- `mapper/Dockerfile` _(new)_
- `mapper/.dockerignore` _(new)_
- `mapper/next.config.ts` _(add `output: 'standalone'`)_

---

### Milestone 2 — Create Frontend Environment File Template

**Goal:** A `mapper/docker.env.example` file that Docker Compose can reference as `env_file:`. This mirrors the pattern of `mcp_server/server/mcp.env`.

**Steps:**
1. Create `mapper/docker.env.example` listing all variables needed at runtime (derived from `13-01`).
2. Document that operators copy this file to `mapper/docker.env` and fill in real values before running `docker compose up`.
3. Add `mapper/docker.env` to the root `.gitignore`.

**Variables in `mapper/frontend.env.example`:**
```dotenv
# Agent backend (FastAPI / ADK) — must be reachable from the Docker network
AGENT_BACKEND_URL=http://si-mapper-agent:8001

# Agent backend — must be reachable from the browser (use public host/port)
NEXT_PUBLIC_AGENT_BACKEND_URL=http://localhost:8001

# Graphivac grid URL for the active project (without query parameters)
NEXT_PUBLIC_GRAPHIVAC_GRID_URL=https://graphivac.hvac.io/o/public/p/XXXXXXXX/g/XXXXXXXX

# Projects folder — must match the container-side path of the volume mount below
# Default matches the docker-compose.yml volume: ./mapper/uploads:/app/uploads
PROJECTS_FOLDER=/app/uploads

# Neo4j connection (server-side only)
NEO4J_BOLT_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
```

> **Note on dual agent URLs:** `AGENT_BACKEND_URL` is used server-to-server (container DNS name); `NEXT_PUBLIC_AGENT_BACKEND_URL` is used browser-to-server (must go via the host machine's exposed port).
>
> **Note on `PROJECTS_FOLDER`:** This server-side variable tells the Next.js file-manager API (`/api/files`) where to read and write project files inside the container. It must be kept in sync with the left-hand side of the `volumes:` bind-mount in `docker-compose.yml` — if you change the mount target you must also change this variable.

**Files to create:**
- `mapper/docker.env.example` _(new)_

---

### Milestone 3 — Add Frontend Service to `docker-compose.yml`

**Goal:** Running `docker compose --profile deploy up` starts the frontend container alongside the MCP server.

**Steps:**
1. Add a `si-mapper-frontend` service to `docker-compose.yml`:
   ```yaml
   si-mapper-frontend:
     build:
       context: ./mapper
       dockerfile: Dockerfile
     image: si-mapper-frontend:latest
     container_name: si-mapper-frontend
     ports:
       - "3000:3000"
     env_file:
       - mapper/docker.env
     volumes:
       - ./mapper/uploads:/app/uploads
     profiles:
       - deploy
       - build
   ```
2. Decide on network: follow existing services — some use `ports:` with `network_mode: host`, others use mapped ports. Use mapped ports (`3000:3000`) for the frontend to avoid conflicts with other services.
3. The `uploads/` bind-mount maps the host `mapper/uploads/` directory into the container, preserving files across rebuilds.

**Files to modify:**
- `docker-compose.yml` _(add `si-mapper-frontend` service)_

---

### Milestone 4 — Validate the Python Postinstall Hook

**Goal:** Confirm the `pnpm install` postinstall hook (which syncs Python environments via `scripts/setup.sh`) does not break inside Docker where Python/uv may not be installed.

**Context:** `mapper/package.json` defines a `postinstall` script that runs `./scripts/setup.sh || scripts\setup.bat`. This is appropriate for developer machines but should be skipped inside Docker (the Agent and MCP Server run in separate containers).

**Steps:**
1. Inspect `mapper/scripts/setup.sh` to understand what it does.
2. In the `Dockerfile` `deps` stage, set `SKIP_POSTINSTALL=1` or use `pnpm install --ignore-scripts` to bypass the Python setup script.
   - Alternatively, modify `package.json` to check the env var: `"postinstall": "[ -z \"$SKIP_POSTINSTALL\" ] && (./scripts/setup.sh || scripts\\setup.bat) || true"`.
3. Confirm the Docker build does not fail due to missing `uv` or Python.

**Files to potentially modify:**
- `mapper/Dockerfile` _(use `--ignore-scripts` or set env var)_
- `mapper/package.json` _(guard the postinstall script — optional approach)_

---

### Milestone 5 — Build & Smoke Test

**Goal:** Confirm the image builds successfully and the container serves the app.

**Steps:**
1. From the project root, build the image:
   ```bash
   docker compose build si-mapper-frontend
   ```
2. Bring up the service:
   ```bash
   docker compose --profile deploy up si-mapper-frontend
   ```
3. Open `http://localhost:3000` — confirm the UI loads.
4. Confirm the `uploads/` volume is mounted correctly:
   - Upload a file via the UI.
   - Stop and restart the container.
   - Confirm the file is still accessible.
5. Confirm environment variables are read (e.g. set `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` to a test value and verify the iframe src changes).

---

## Acceptance Criteria

- [x] `mapper/Dockerfile` exists and produces a working image with `docker build`.
- [x] `mapper/.dockerignore` exists and excludes `node_modules/`, `.next/`, `.env.local`, `uploads/`.
- [x] `mapper/next.config.ts` enables `output: 'standalone'`.
- [x] `mapper/docker.env.example` documents all required environment variables, including `PROJECTS_FOLDER`.
- [x] `docker-compose.yml` includes a `si-mapper-frontend` service under the `deploy` profile.
- [x] The `uploads/` directory is mounted as a bind-mount volume (not copied into the image), and `PROJECTS_FOLDER` in `frontend.env` matches the container-side mount path.
- [x] The Docker build does not invoke the Python postinstall script (no `uv`/Python required inside the image).
- [x] The final image size is reasonable (< 500 MB — standalone Next.js + Alpine Node baseline).
- [x] Running `docker compose --profile deploy up` starts the frontend and it is accessible at `http://localhost:3000`.
- [x] Files in `uploads/` persist across container restarts.

---

## Notes & Decisions

- **Standalone output**: Next.js `output: 'standalone'` traces and bundles only the files actually used at runtime. This typically reduces image size by 60–80% compared to copying all of `node_modules/`. It is the recommended approach for Docker deployments.
- **pnpm in Docker**: `corepack enable` is the cleanest way to get pnpm inside an Alpine Node image without pinning a specific pnpm version in the Dockerfile itself.
- **`uploads/` as bind-mount vs named volume**: A bind-mount (`./mapper/uploads:/app/uploads`) is chosen over a named volume because:
  - Files remain directly accessible on the host for debugging and backups.
  - The same `uploads/` directory is used by the dev server, avoiding duplication.
- **Agent container**: The `agent/` backend is not yet Dockerized as part of this phase. `AGENT_BACKEND_URL` in the frontend container therefore defaults to the host machine's agent process. If/when the agent is containerized, the service name will be used instead (e.g. `http://si-mapper-agent:8001`).
- **Build profile**: The service is placed under both `deploy` and `build` profiles, mirroring the `si-mapper-mcp` convention so `docker compose --profile build` can pre-build all images in CI without starting them.
