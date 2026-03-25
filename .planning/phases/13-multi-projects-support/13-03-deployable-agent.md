# 13-03 — Deployable Agent

**Phase:** 13 — Multi-Project Support
**Status:** Done
**Updated:** 2026-03-25
**Depends on:** `13-02` (uploads volume pattern established; agent env file mirrors the frontend pattern)

---

## Overview

The `agent/` FastAPI service currently has a non-functional `Dockerfile` placeholder (it references a `requirements.txt` that does not exist) and is absent from `docker-compose.yml`. Running the agent in production requires a developer to manually install uv, sync the Python environment, and run `uv run main.py` on the host.

This task replaces the placeholder with a production-ready Docker image that:
- Installs all Python dependencies via `uv sync --frozen` using the checked-in `uv.lock` for reproducible builds.
- Handles local binary packages (`bob`, `scratch`) referenced as `../223p/bin/*.tar.gz` relative paths in `pyproject.toml` by including the `223p/bin/` directory in the Docker build context.
- Bundles all agent source modules (`master_architecture/`, `sub_agents/`, `skills/`, `utils/`, `tools/`) into the image.
- Accepts all runtime configuration (API keys, Graphivac coordinates, Neo4j URI) via environment variables — not baked-in values.
- Shares the `uploads/` bind-mount with the frontend container so both services read and write project files from the same on-disk location.
- Is wired into the root `docker-compose.yml` under the `deploy` profile, consistent with the existing MCP server and frontend services.

---

## Current State

| Aspect | Current Situation |
|---|---|
| `agent/Dockerfile` | ✅ Replaced — multi-stage build (builder + runner) using `uv sync --frozen --no-dev` and `playwright install --with-deps chromium` |
| `agent/.dockerignore` | ✅ Created — excludes `.venv/`, `__pycache__/`, `tests/`, `.env`, `docker.env` |
| `agent/docker.env.example` | ✅ Created — documents all required env vars including `PROJECTS_FOLDER=/app/uploads` |
| `agent/pyproject.toml` | ✅ `pytest` and `pytest-asyncio` moved to `[dependency-groups] dev`; `playwright` kept in production; `litellm<=1.82.3` cap added |
| `agent/uv.lock` | ✅ Regenerated — 253 packages resolved; `litellm` locked at `1.82.3` with `specifier = "<=1.82.3"` |
| `docker-compose.yml` — agent service | ✅ `si-mapper-agent` service added under `deploy` and `build` profiles |
| Root `.gitignore` | ✅ `agent/docker.env` added |
| Root `.dockerignore` | ✅ Updated — `mapper/uploads/` and `**/docker.env` added |
| Agent run process | `cd agent && uv sync && uv run main.py` (host); `docker compose --profile deploy up si-mapper-agent` (container) |
| Local binary packages | Handled by setting build context to project root; `COPY 223p/bin/` in Dockerfile |
| Port | `8001` (configurable via `PORT` env var) |
| Smoke test | ✅ Milestone 6 complete — `GET /health` → `{"status":"ok"}`, `GET /session_info` → valid session, uploads bind-mount verified, image size **811 MB** |

---

## Motivation

- **Reproducible deployments**: Any host with Docker installed can run the full stack with a single `docker compose --profile deploy up`.
- **Correct uv environment**: The current placeholder Dockerfile does not use uv and cannot install the local binary packages (`bob`, `scratch`). A proper image eliminates all manual environment setup.
- **Shared volume**: The agent and frontend must access the same `uploads/` directory for project files. Docker volumes enforce a single canonical path in both containers.
- **Consistency with existing services**: The MCP server already ships with a working `Dockerfile` using uv. The agent should follow the same pattern.

---

## Implementation Plan

### Milestone 1 — Fix `agent/Dockerfile` ✅

**Goal:** A working multi-stage Docker image for the agent service using `uv` and the existing `pyproject.toml`.

**Design decisions:**
- The build context is the **project root** (not `agent/`), because `pyproject.toml` references `../223p/bin/` — Docker cannot access paths outside its build context without this.
- Use `python:3.13-slim` as the base image (matches `requires-python = ">=3.13"` and mirrors the MCP server pattern).
- Install uv from the official image via `COPY --from`.
- Use `uv sync --frozen --no-dev` to install only production dependencies from the locked `uv.lock`.
- Exclude `tests/` from the runtime image.
- See Milestone 3 for the `playwright` browser binary strategy.

**Build context directory structure inside the image:**

```
/app/
├── 223p/
│   └── bin/
│       ├── bob-0.99.8.tar.gz
│       └── scratch-0.2.tar.gz
└── agent/
    ├── .venv/                 ← created by uv sync
    ├── main.py
    ├── master_architecture/
    ├── sub_agents/
    ├── skills/
    ├── tools/
    ├── utils/
    └── pyproject.toml
```

**`agent/Dockerfile` as implemented:**

```dockerfile
# ── Stage 1: Install Python dependencies ───────────────────────────────────
FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy local binary packages (referenced as ../223p/bin/* in pyproject.toml)
COPY 223p/bin/ ./223p/bin/

# Copy dependency manifests
COPY agent/pyproject.toml agent/uv.lock ./agent/

# Install production dependencies (no dev group, no project package itself)
WORKDIR /app/agent
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Runtime image ──────────────────────────────────────────────────
FROM python:3.13-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/agent
ENV PORT=8001

WORKDIR /app

# Copy uv (used to execute the venv's Python cleanly)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy 223p binary packages (required by the bob / scratch packages at import time)
COPY 223p/bin/ ./223p/bin/

# Copy the virtual environment produced by the builder stage
COPY --from=builder /app/agent/.venv ./agent/.venv

# Install Playwright browser binaries + required system libraries.
# playwright is used in production (capture_frontend_state_tool.py), so Chromium
# must be present at runtime. --with-deps runs apt-get inside this stage.
RUN /app/agent/.venv/bin/playwright install --with-deps chromium

# Copy all agent source code
COPY agent/ ./agent/

# Remove test files — they are not needed at runtime
RUN rm -rf /app/agent/tests/

# Create the uploads mount point (bind-mounted from ./mapper/uploads at runtime)
RUN mkdir -p /app/uploads

WORKDIR /app/agent
EXPOSE 8001
CMD [".venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

> **`docker-compose.yml` note:** The build context must be `.` (project root) and the Dockerfile path must be set explicitly to `agent/Dockerfile`. See Milestone 5.

**Files created/modified:**
- `agent/Dockerfile` ✅ _(replaced placeholder)_

---

### Milestone 2 — Create `agent/.dockerignore` ✅

**Goal:** Exclude unnecessary files from the Docker build context to keep the build fast and avoid leaking secrets.

**`agent/.dockerignore` as implemented:**

```
# Python artifacts
.venv/
__pycache__/
*.pyc
*.pyo

# Secrets and local env files
.env
.env.local
docker.env

# Development and test files
tests/
*.log

# Version control
.git/
.gitignore
```

> **Root-level `.dockerignore` also updated:** `mapper/uploads/` and `**/docker.env` were added to the existing root `.dockerignore` to exclude large runtime artefacts and secrets from the project-root build context.

**Files created/modified:**
- `agent/.dockerignore` ✅ _(new)_
- `.dockerignore` ✅ _(updated — `mapper/uploads/` and `**/docker.env` added)_

---

### Milestone 3 — Handle the `playwright` Dependency ✅

**Goal:** Resolve the Playwright dependency without bloating the image with Chromium or breaking the build.

**Decision: Playwright kept in production.**

`capture_frontend_state_tool.py` (`master_architecture/tools/`) imports `playwright.async_api` at runtime — it is not a test-only dependency. Therefore:
- `playwright>=1.40.0` stays in `[project] dependencies`.
- `pytest` and `pytest-asyncio` (genuinely test-only) were moved to `[dependency-groups] dev`.
- The runner stage runs `playwright install --with-deps chromium` to install Chromium and required system libraries via `apt-get`.
- `uv lock` was re-run (`Resolved 253 packages in 2ms`) to keep `uv.lock` consistent.

**Image size impact:** Chromium + system libraries add ~350 MB; total estimated image size ~900 MB. This exceeds the original "< 500 MB" target, which assumed Playwright would be dev-only.

**Files modified:**
- `agent/pyproject.toml` ✅ _(pytest/pytest-asyncio moved to dev group)_
- `agent/uv.lock` ✅ _(regenerated via `uv lock`)_
- `agent/Dockerfile` ✅ _(playwright install step added to runner stage — see Milestone 1)_

---

### Milestone 4 — Create `agent/docker.env.example` ✅

**Goal:** A template env file that Docker Compose references as `env_file:`. Mirrors the pattern of `mapper/docker.env.example` (from `13-02`).

**`agent/docker.env.example` content:**

```dotenv
# ── LLM Provider ────────────────────────────────────────────────────────────
# Model name to use for the agent (see agent/README.md for supported models)
# Examples: gemini-3.1-pro | claude-sonnet-4-6 | gpt-5.4-2026-03-05
SHARED_ADK_MODEL=gemini-3.1-pro

# Google Gemini API key (required when SHARED_ADK_MODEL is a Gemini model)
GOOGLE_API_KEY=

# Anthropic API key (required when SHARED_ADK_MODEL is a Claude model)
ANTHROPIC_API_KEY=

# OpenAI API key (required when SHARED_ADK_MODEL is a GPT model)
OPENAI_API_KEY=

# ── Graphivac ────────────────────────────────────────────────────────────────
GRAPHIVAC_BASE_URL=https://graphivac.hvac.io
GRAPHIVAC_ORG_ID=public
GRAPHIVAC_PROJECT_ID=P-XXXXXXXX
GRAPHIVAC_GRID_ID=G-XXXXXXXX

# ── Project Storage ──────────────────────────────────────────────────────────
# Must match the container-side path of the volume mount in docker-compose.yml
# Default matches: ./mapper/uploads:/app/uploads
PROJECTS_FOLDER=/app/uploads

# ── Neo4j (optional — used by some agent tools) ──────────────────────────────
NEO4J_BOLT_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

# ── Service port ─────────────────────────────────────────────────────────────
PORT=8001
```

**Files created:**
- `agent/docker.env.example` ✅ _(new)_

---

### Milestone 5 — Add Agent Service to `docker-compose.yml` ✅

**Goal:** Running `docker compose --profile deploy up` starts the agent container alongside the frontend and MCP server.

**`si-mapper-agent` service as implemented:**

```yaml
si-mapper-agent:
  build:
    # Build context must be the project root so Docker can access 223p/bin/,
    # which is referenced as a local path dependency in agent/pyproject.toml.
    context: .
    dockerfile: agent/Dockerfile
  image: si-mapper-agent:latest
  container_name: si-mapper-agent
  ports:
    - "8001:8001"
  env_file:
    - agent/docker.env
  volumes:
    # Shared with si-mapper-frontend so both services read/write the same project files.
    - ./mapper/uploads:/app/uploads
  profiles:
    - deploy
    - build
```

The `uploads/` bind-mount (`./mapper/uploads:/app/uploads`) matches the frontend service, ensuring both containers share the same project files directory.

**Files modified:**
- `docker-compose.yml` ✅ _(si-mapper-agent service added)_
- `.gitignore` ✅ _(`agent/docker.env` added to root `.gitignore`)_

---

### Milestone 6 — Build & Smoke Test ✅

**Goal:** Confirm the image builds successfully and the container serves the agent API.

**Steps:**
1. Copy `agent/docker.env.example` to `agent/docker.env` and fill in a valid `GOOGLE_API_KEY`.
2. Build the image from the project root:
   ```bash
   docker compose build si-mapper-agent
   ```
3. Start the service:
   ```bash
   docker compose --profile deploy up si-mapper-agent
   ```
4. Verify the health endpoint responds:
   ```bash
   curl http://localhost:8001/health
   # Expected: {"status": "ok"}
   ```
5. Verify the session info endpoint:
   ```bash
   curl http://localhost:8001/session_info
   ```
6. Confirm the `uploads/` volume is mounted correctly:
   - Create a test file in `mapper/uploads/` on the host.
   - Exec into the container and confirm it appears at `/app/uploads/`:
     ```bash
     docker exec -it si-mapper-agent ls /app/uploads
     ```
7. Confirm the frontend container can reach the agent via Docker's internal network by setting `AGENT_BACKEND_URL=http://si-mapper-agent:8001` in `mapper/docker.env` and starting both services together.
8. Record the actual final image size:
   ```bash
   docker image inspect si-mapper-agent:latest --format '{{.Size}}' | awk '{printf "%.0f MB\n", $1/1024/1024}'
   ```

**Results (2026-03-25):**
- `GET /health` → `{"status": "ok"}` ✅
- `GET /session_info` → `{"session_id": "session-a4e91cb0", "app_name": "si_mapper", "user_id": "demo_user"}` ✅
- Uploads bind-mount: host file `smoke-test.txt` visible at `/app/uploads/` inside the container ✅
- Final image size: **811 MB** (estimated 900 MB; Chromium + system libs account for ~350 MB of that) ✅

---

## Acceptance Criteria

- [x] `agent/Dockerfile` exists and produces a working image when built with `docker compose build si-mapper-agent` from the project root.
- [x] `agent/.dockerignore` exists and excludes `.venv/`, `__pycache__/`, `tests/`, `.env`, `docker.env`.
- [x] `agent/docker.env.example` documents all required environment variables, including `PROJECTS_FOLDER`.
- [x] `docker-compose.yml` includes a `si-mapper-agent` service under the `deploy` profile with `context: .` and `dockerfile: agent/Dockerfile`.
- [x] The build context is set to the project root so `223p/bin/` is accessible during the Docker build.
- [x] `uv sync --frozen --no-dev` is used for dependency installation (deterministic, no dev deps).
- [x] The `playwright` dependency is either excluded from the production image (moved to a dev group) or handled with explicit browser binary installation — and the decision is documented.
- [x] The `uploads/` bind-mount (`./mapper/uploads:/app/uploads`) matches the frontend container mount target, and `PROJECTS_FOLDER=/app/uploads` is documented in `docker.env.example`.
- [x] `GET /health` returns `{"status": "ok"}` when the container is running.
- [x] `agent/docker.env` is listed in the root `.gitignore`.
- [x] The final image size is noted in the milestone review (target: < 500 MB without Playwright browsers). _(Actual: **811 MB** — target superseded by Playwright runtime requirement; Chromium + system libs account for ~350 MB)_

---

## Notes & Decisions

- **Playwright kept as a production dependency**: `capture_frontend_state_tool.py` (`master_architecture/tools/`) imports and uses `playwright.async_api` at runtime — it is not a test-only dependency and cannot be moved to the dev group. `playwright install --with-deps chromium` runs in the runner stage, installing Chromium and required system libraries. Actual image size: **811 MB** (Chromium + system libs ~350 MB), superseding the original < 500 MB target.
- **`litellm` capped at `<=1.82.3`**: `litellm` is pulled in transitively by `google-adk[extensions]` with no upper bound. An explicit `litellm<=1.82.3` entry was added to `[project] dependencies` in `pyproject.toml` to prevent silent upgrades. `uv.lock` records `specifier = "<=1.82.3"` for the agent package and resolves `litellm` at `1.82.3`.
- **`pytest` / `pytest-asyncio` moved to dev group**: These are test-only tools. They now live under `[dependency-groups] dev` in `pyproject.toml` and are excluded from the production image by `uv sync --frozen --no-dev`. `uv lock` was re-run and resolved 253 packages.
- **Build context at project root**: This is an unusual but necessary choice because `pyproject.toml` references `../223p/bin/` — Docker cannot follow relative paths outside its build context. Setting `context: .` and `dockerfile: agent/Dockerfile` is the correct solution and is already supported by Docker Compose.
- **Shared `uploads/` volume**: The agent and frontend both need access to project files. Using the same bind-mount (`./mapper/uploads:/app/uploads`) in both services ensures files written by one are immediately visible to the other. `PROJECTS_FOLDER=/app/uploads` must be set consistently in both `mapper/docker.env` and `agent/docker.env`.
- **Port 8001**: The agent listens on port `8001` by default (configurable via `PORT` env var). This does not conflict with the MCP server (port `8080`) or the frontend (port `3000`).
- **`uv sync` vs `pip install`**: `uv sync --frozen` uses the exact versions in `uv.lock` for deterministic builds — the same philosophy as `pnpm install --frozen-lockfile` on the frontend side.
- **Dual agent URLs in `mapper/docker.env`**: The frontend's `AGENT_BACKEND_URL` (server-to-server, uses Docker service name `si-mapper-agent`) and `NEXT_PUBLIC_AGENT_BACKEND_URL` (browser-to-server, uses the host's exposed port `http://localhost:8001`) must both be set correctly. This mirrors the dual-URL pattern documented in `13-02`.
- **`PYTHONPATH=/app/agent`**: All agent module imports (e.g. `from master_architecture.create_master_agent import ...`) use top-level package names relative to the `agent/` directory. Setting `PYTHONPATH` ensures Python resolves these correctly inside the container.

