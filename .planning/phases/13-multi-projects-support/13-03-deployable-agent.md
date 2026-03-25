# 13-03 — Deployable Agent

**Phase:** 13 — Multi-Project Support
**Status:** Not started
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
| `agent/Dockerfile` | Exists but is a non-functional placeholder (`COPY requirements.txt .` — that file does not exist; only copies `main.py`) |
| `docker-compose.yml` — agent service | Absent |
| Agent run process | Documented in `agent/README.md`: `cd agent && uv sync && uv run main.py` |
| Local binary packages | `pyproject.toml` references `../223p/bin/bob-0.99.8.tar.gz` and `../223p/bin/scratch-0.2.tar.gz` as local path dependencies |
| Port | Agent starts on port `8001` (configurable via `PORT` env var, defaulting to `8001` in `main.py`) |
| `uploads/` dependency | Agent will need `PROJECTS_FOLDER=/app/uploads` to match the container-side volume mount |

---

## Motivation

- **Reproducible deployments**: Any host with Docker installed can run the full stack with a single `docker compose --profile deploy up`.
- **Correct uv environment**: The current placeholder Dockerfile does not use uv and cannot install the local binary packages (`bob`, `scratch`). A proper image eliminates all manual environment setup.
- **Shared volume**: The agent and frontend must access the same `uploads/` directory for project files. Docker volumes enforce a single canonical path in both containers.
- **Consistency with existing services**: The MCP server already ships with a working `Dockerfile` using uv. The agent should follow the same pattern.

---

## Implementation Plan

### Milestone 1 — Fix `agent/Dockerfile`

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

**`agent/Dockerfile` outline:**

```dockerfile
# ── Stage 1: Install dependencies ──────────────────────────────────────────
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

# Install production dependencies via uv
WORKDIR /app/agent
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Runtime image ──────────────────────────────────────────────────
FROM python:3.13-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/agent
ENV PORT=8001

WORKDIR /app

# Copy uv (needed to run the venv's Python cleanly)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy 223p binary packages (required at install/import time)
COPY 223p/bin/ ./223p/bin/

# Copy the virtual environment from the builder stage
COPY --from=builder /app/agent/.venv ./agent/.venv

# Copy all agent source code
COPY agent/ ./agent/

# Remove test files from the runtime image
RUN rm -rf /app/agent/tests/

# Create the uploads mount point
RUN mkdir -p /app/uploads

WORKDIR /app/agent
EXPOSE 8001
CMD [".venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

> **`docker-compose.yml` note:** The build context must be `.` (project root) and the Dockerfile path must be set explicitly to `agent/Dockerfile`. See Milestone 5.

**Files to create/modify:**
- `agent/Dockerfile` _(replace placeholder)_

---

### Milestone 2 — Create `agent/.dockerignore`

**Goal:** Exclude unnecessary files from the Docker build context to keep the build fast and avoid leaking secrets.

**`agent/.dockerignore` content:**

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

> **Note on root-level `.dockerignore`:** Since the build context is the project root, a root-level `.dockerignore` should also be created (or updated) to exclude the large frontend artefacts (`mapper/node_modules/`, `mapper/.next/`, `mapper/uploads/`) from the agent build context. Without this, Docker sends the entire repository to the daemon on each build.

**Files to create:**
- `agent/.dockerignore` _(new)_

---

### Milestone 3 — Handle the `playwright` Dependency

**Goal:** Resolve the Playwright dependency without bloating the image with Chromium or breaking the build.

**Context:** `agent/pyproject.toml` lists `playwright>=1.40.0` as a dependency. Playwright requires browser binaries (`playwright install`) that are typically 200–400 MB. If Playwright is not used in production code paths, it should be moved to a dev dependency group.

**Steps:**
1. Search the agent codebase for `playwright` imports to determine whether it is used in production or only in tests.
2. **If Playwright is only used in tests** (most likely): move it to a `[dependency-groups]` dev group in `pyproject.toml`:
   ```toml
   [dependency-groups]
   dev = [
     "playwright>=1.40.0",
   ]
   ```
   `uv sync --frozen --no-dev` will then exclude it from the Docker image.
3. **If Playwright is required in production:** add a browser installation step to the builder stage:
   ```dockerfile
   RUN .venv/bin/playwright install --with-deps chromium
   ```
   Then copy the browser cache directory to the runner stage. Document the resulting image size increase.
4. Run `uv lock` after modifying `pyproject.toml` to update `uv.lock`.

**Files to potentially modify:**
- `agent/pyproject.toml` _(move playwright to dev group if unused in production)_
- `agent/Dockerfile` _(add playwright install step only if needed in production)_

---

### Milestone 4 — Create `agent/docker.env.example`

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

**Files to create:**
- `agent/docker.env.example` _(new)_

---

### Milestone 5 — Add Agent Service to `docker-compose.yml`

**Goal:** Running `docker compose --profile deploy up` starts the agent container alongside the frontend and MCP server.

**Steps:**
1. Add a `si-mapper-agent` service to `docker-compose.yml`:
   ```yaml
   si-mapper-agent:
     build:
       context: .
       dockerfile: agent/Dockerfile
     image: si-mapper-agent:latest
     container_name: si-mapper-agent
     ports:
       - "8001:8001"
     env_file:
       - agent/docker.env
     volumes:
       - ./mapper/uploads:/app/uploads
     profiles:
       - deploy
       - build
   ```
2. The `uploads/` bind-mount (`./mapper/uploads:/app/uploads`) matches the frontend service, ensuring both containers share the same project files directory.
3. Add `agent/docker.env` to the root `.gitignore` so the operator-populated secrets file is never committed.

**Files to modify:**
- `docker-compose.yml` _(add `si-mapper-agent` service)_

---

### Milestone 6 — Build & Smoke Test

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

---

## Acceptance Criteria

- [ ] `agent/Dockerfile` exists and produces a working image when built with `docker compose build si-mapper-agent` from the project root.
- [ ] `agent/.dockerignore` exists and excludes `.venv/`, `__pycache__/`, `tests/`, `.env`, `docker.env`.
- [ ] `agent/docker.env.example` documents all required environment variables, including `PROJECTS_FOLDER`.
- [ ] `docker-compose.yml` includes a `si-mapper-agent` service under the `deploy` profile with `context: .` and `dockerfile: agent/Dockerfile`.
- [ ] The build context is set to the project root so `223p/bin/` is accessible during the Docker build.
- [ ] `uv sync --frozen --no-dev` is used for dependency installation (deterministic, no dev deps).
- [ ] The `playwright` dependency is either excluded from the production image (moved to a dev group) or handled with explicit browser binary installation — and the decision is documented.
- [ ] The `uploads/` bind-mount (`./mapper/uploads:/app/uploads`) matches the frontend container mount target, and `PROJECTS_FOLDER=/app/uploads` is documented in `docker.env.example`.
- [ ] `GET /health` returns `{"status": "ok"}` when the container is running.
- [ ] `agent/docker.env` is listed in the root `.gitignore`.
- [ ] The final image size is noted in the milestone review (target: < 500 MB without Playwright browsers).

---

## Notes & Decisions

- **Build context at project root**: This is an unusual but necessary choice because `pyproject.toml` references `../223p/bin/` — Docker cannot follow relative paths outside its build context. Setting `context: .` and `dockerfile: agent/Dockerfile` is the correct solution and is already supported by Docker Compose.
- **Shared `uploads/` volume**: The agent and frontend both need access to project files. Using the same bind-mount (`./mapper/uploads:/app/uploads`) in both services ensures files written by one are immediately visible to the other. `PROJECTS_FOLDER=/app/uploads` must be set consistently in both `mapper/docker.env` and `agent/docker.env`.
- **No Playwright browsers by default**: Playwright browser binaries add 200–400 MB to the image. If Playwright is only a test dependency, moving it to a `[dependency-groups] dev` group in `pyproject.toml` keeps the production image lean. This matches the pattern already used by the frontend (`pnpm install --ignore-scripts` in `13-02`).
- **Port 8001**: The agent listens on port `8001` by default (configurable via `PORT` env var). This does not conflict with the MCP server (port `8080`) or the frontend (port `3000`).
- **`uv sync` vs `pip install`**: `uv sync --frozen` uses the exact versions in `uv.lock` for deterministic builds — the same philosophy as `pnpm install --frozen-lockfile` on the frontend side.
- **Dual agent URLs in `mapper/docker.env`**: The frontend's `AGENT_BACKEND_URL` (server-to-server, uses Docker service name `si-mapper-agent`) and `NEXT_PUBLIC_AGENT_BACKEND_URL` (browser-to-server, uses the host's exposed port `http://localhost:8001`) must both be set correctly. This mirrors the dual-URL pattern documented in `13-02`.
- **`PYTHONPATH=/app/agent`**: All agent module imports (e.g. `from master_architecture.create_master_agent import ...`) use top-level package names relative to the `agent/` directory. Setting `PYTHONPATH` ensures Python resolves these correctly inside the container.

