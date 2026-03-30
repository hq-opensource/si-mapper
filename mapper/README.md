# MAPPER Frontend

This is the frontend for the MAPPER project.

## Getting Started

> **🚀 One-Command Setup:** The easiest way to run the entire project is to execute `pnpm install` then `pnpm dev` in the **root directory**. This will start the UI, Agent, and MCP server concurrently. See the [Root README](../README.md) for details.

## Configuration

Environment-specific values (service URLs, credentials, paths) are managed through environment variables so that the same build can be deployed to different environments without touching source code.

1. Copy the reference template to a local override file (gitignored):
   ```bash
   cp .env.example .env.local
   ```
2. Edit `.env.local` and fill in the values for your environment.
3. See `.env.example` for the full list of variables, their defaults, and descriptions.

> **Docker deployments** — pass variables via `mapper/docker.env` instead of `.env.local`. See the [Docker Deployment](#docker-deployment) section below.

| Variable | Side | Description |
|---|---|---|
| `AGENT_BACKEND_URL` | Server | Full base URL of the ADK agent FastAPI server |
| `PROJECTS_FOLDER` | Server | Absolute path to the projects root folder (matches Docker volume mount) |
| `NEO4J_BOLT_URI` | Server | Neo4j Bolt connection URI |
| `NEO4J_USER` | Server | Neo4j username |
| `NEO4J_PASSWORD` | Server | Neo4j password |
| `NEXT_PUBLIC_AGENT_BACKEND_URL` | Client | Agent polling URL (must be reachable from the browser) |
| `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` | Client | Graphivac grid base URL (leave empty to show a placeholder) |

## Docker Deployment

The frontend ships as a self-contained Docker image built with Next.js [standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output). It is wired into the root `docker-compose.yml` under the `deploy` profile alongside the agent and MCP server.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) installed on the host.
- All commands are run from the **project root** (one level above `mapper/`).

### 1 — Create the env file

```bash
cp mapper/docker.env.example mapper/docker.env
```

Edit `mapper/docker.env`. Key variables:

| Variable | Example value | Notes |
|---|---|---|
| `AGENT_BACKEND_URL` | `http://si-mapper-agent:8001` | Server-to-server (Docker service name) |
| `NEXT_PUBLIC_AGENT_BACKEND_URL` | `http://localhost:8001` | Browser-to-server (host-exposed port) — see note below |
| `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` | `https://graphivac.hvac.io/o/public/p/P-.../g/G-...` | Graphivac iframe URL — see note below |
| `PROJECTS_FOLDER` | `/app/uploads` | Must match the volume mount target below |
| `NEO4J_BOLT_URI` | `bolt://neo4j:7687` | Use the Docker service name if Neo4j runs in Docker |

> `mapper/docker.env` is gitignored — never commit real credentials.

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

The frontend is available at **http://localhost:3001**.

### Ports & volumes

| Resource | Host | Container |
|---|---|---|
| HTTP | `3001` | `3000` |
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
