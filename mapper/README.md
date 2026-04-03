# MAPPER Frontend

This is the frontend for the MAPPER project.

## Getting Started

> **🚀 One-Command Setup:** The easiest way to run the entire project is to execute `pnpm install` then `pnpm dev` in the **root directory**. This will start the UI, Agent, and MCP server concurrently. See the [Root README](../README.md) for details.

## Configuration

Environment-specific values (service URLs, credentials, paths) are managed through environment variables so that the same build can be deployed to different environments without touching source code.

- **Local dev:** copy `.env.example` → `.env.local` and fill in your values.
- **Docker:** copy `docker.env.example` → `docker.env` and fill in your values.

| Variable | Side | Default | Description |
| :--- | :---: | :--- | :--- |
| `AGENT_BACKEND_URL` | Server | `http://host.docker.internal:8001` | Internal (server-to-server) base URL of the ADK agent FastAPI service. |
| `NEXT_PUBLIC_AGENT_BACKEND_URL` | Client | `http://localhost:8001` | Browser-facing URL of the agent — must be reachable from the end-user's machine. |
| `PROJECTS_FOLDER` | Server | `/app/uploads` | Absolute path to the project-files root. Must match the Docker volume mount target. |
| `NEO4J_BOLT_URI` | Server | `bolt://neo4j:7687` | Neo4j Bolt connection URI. |
| `NEO4J_USER` | Server | `neo4j` | Neo4j username. |
| `NEO4J_PASSWORD` | Server | `neo4j_password` | Neo4j password. |
| `GRAPHIVAC_BASE_URL` | Server | `http://graphivac:3000` | Internal (server-to-server) Graphivac API base URL (no trailing slash). |
| `GRAPHIVAC_PUBLIC_BASE_URL` | Client | `http://localhost:8888` | Public (browser-reachable) Graphivac URL used for the embedded iframe. Falls back to `GRAPHIVAC_BASE_URL` if unset. |
| `GRAPHIVAC_ORG_ID` | Server | `public` | Graphivac organisation ID — deployment-wide constant. |
| `COPILOTKIT_DEV_CONSOLE` | Server | `false` | Set to `true` to show the CopilotKit dev console and announcement banners in the UI. |

## Docker Deployment

The frontend ships as a self-contained Docker image built with Next.js [standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output). It is wired into the root `docker-compose.yml` under the `deploy` profile alongside the agent and MCP server.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) installed on the host.
- All commands are run from the **project root** (one level above `mapper/`).

### 1 — Create the env file

```bash
cp mapper/docker.env.example mapper/docker.env
```

> See [Configuration](#configuration) above for the full list of variables and their defaults. `mapper/docker.env` is gitignored — never commit real credentials.

> **⚠️ `NEXT_PUBLIC_` variables are inlined at build time, not runtime.**
> Next.js bakes `NEXT_PUBLIC_*` values directly into the JavaScript bundle during `pnpm build`.
> `docker.env` is only injected when the container *starts* — too late for these variables.
> Define them in a **root-level `.env` file** instead (next to `docker-compose.yml`).
> Docker Compose reads it automatically before running any build:
> ```bash
> cp .env.example .env   # from the project root
> # edit .env and set NEXT_PUBLIC_GRAPHIVAC_GRID_URL and NEXT_PUBLIC_AGENT_BACKEND_URL
> docker compose build si-mapper-frontend
> ```
> Server-side variables (`AGENT_BACKEND_URL`, `PROJECTS_FOLDER`, etc.) do not have this
> constraint — they are read from `docker.env` at runtime as expected.

### 2 — Build the image

```bash
docker compose build si-mapper-frontend
```

### 3 — Start the service

```bash
# Frontend only
docker compose --profile deploy up si-mapper-frontend

# Full stack (frontend + agent + MCP server)
docker compose --profile deploy up
```

The frontend is available at **http://localhost:3000**.

### Ports & volumes

| Resource | Host | Container |
|---|---|---|
| HTTP | `3000` | `3000` |
| Project files | `./mapper/uploads/` | `/app/uploads/` |

The `uploads/` bind-mount is shared with the agent container (`si-mapper-agent`). Both services read and write project files through the same directory on the host. `PROJECTS_FOLDER=/app/uploads` in `docker.env` must match this mount target.

### Rebuilding after code changes

```bash
docker compose build si-mapper-frontend
docker compose --profile deploy up si-mapper-frontend
```

---

## Available Scripts
- `dev` - Starts the UI, Agent, and MCP server concurrently in development mode.
- `dev:debug` - Starts development servers with debug logging enabled.
- `dev:ui` - Starts only the Next.js UI server.
- `dev:agent` - Starts only the ADK agent server.
- `dev:mcp` - Starts only the MCP server.
- `build` - Builds the Next.js application for production.
- `start` - Starts the production server.
- `lint` - Runs ESLint for code linting.
