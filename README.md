# SI-MAPPER

SI-MAPPER is an AI Agent built using the **Google ADK** and **Ashrae 223P standard**. It transforms multimodal HVAC data into a semantic virtual twin, integrating BACnet, Modbus, and external databases for advanced diagnostics and optimization.

## 🚀 Quick Start

The project is structured with a Next.js frontend that orchestrates the backend services.

### 1. Prerequisites
- [Node.js](https://nodejs.org/) & [pnpm](https://pnpm.io/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### 2. Setup & Run (Development)
Navigate to the `mapper` folder to install dependencies and start the full system in development mode:

```bash
cd mapper
pnpm install
pnpm dev
```

This single `pnpm install` will automatically synchronize the Python environments for the Agent and MCP Server as well.

### 3. Setup & Run (Production/Optimized)
For a faster, more optimized experience, you can build the frontend and run the production server:

```bash
cd mapper
pnpm build
pnpm start
```

This will:
1.  **Build**: Optimize and minify the Next.js frontend assets.
2.  **Start**: Launch the production frontend along with the Agent and MCP Server backend processes.

---

## 🛠️ Independent Control

If you need to work on specific components independently:

| Component | Path | Tool | Command |
| :--- | :--- | :--- | :--- |
| **Frontend** | `/mapper` | pnpm | `pnpm dev:ui` |
| **Agent** | `/agent` | uv | `uv run main.py` |
| **MCP Server** | `/mcp_server` | uv | `uv run server/main.py` |

---

## ⚙️ Environment Variables

Each component manages its own set of environment variables. Copy the relevant example file, fill in your values, and the service will pick them up at startup — the same variables apply whether you are running locally or in Docker.

- **Frontend (mapper):** see [`mapper/README.md → Configuration`](mapper/README.md#configuration)
- **Agent:** see [`agent/README.md → Environment Variables`](agent/README.md#environment-variables)

> None of the env files (`*.env`, `*.env.local`, `docker.env`) are committed to source control — they are all gitignored.

---

## 🐳 Docker Deployment

All services are defined in `docker-compose.yml` at the project root and are grouped into **profiles** that let you start only the components you need.

### Profiles

| Profile | Purpose |
| :--- | :--- |
| `deploy` | Core application stack (frontend, agent, MCP server, Graphivac, MCP Inspector, Portainer) |
| `build` | Same as `deploy` but intended for CI image-build steps |
| `tools` | Optional tooling only (MCP Inspector, Portainer) — useful without starting the full app |
| `graph` | Neo4j graph database |

### Services

| Service | Container | Host port(s) | Profile | Description |
| :--- | :--- | :--- | :--- | :--- |
| `si-mapper-frontend` | `si-mapper-frontend` | `3000` | `deploy` | Next.js UI |
| `si-mapper-agent` | `si-mapper-agent` | `8001` | `deploy` | LLM orchestration agent (FastAPI) |
| `si-mapper-mcp` | `si-mapper-mcp` | `8080` | `deploy` | MCP server (FastMCP) |
| `graphivac` | `si-mapper-graphivac` | `8888` | `deploy` | Grid / diagram editor (Graphivac) |
| `mcp-inspector` | `mcp-inspector` | `6274`, `6277` | `deploy` / `tools` | MCP Inspector UI |
| `portainer` | `portainer` | `9000` | `deploy` / `tools` | Container management UI |
| `neo4j` | `neo4j` | `7474` (HTTP), `7687` (Bolt) | `graph` | Neo4j graph database |

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

### 1. Configure environment

**Root `.env`** — read automatically by Docker Compose before any build. Required for `NEXT_PUBLIC_*` variables that Next.js inlines into the JS bundle at build time:

```bash
cp .env.example .env
# edit .env — set NEXT_PUBLIC_GRAPHIVAC_GRID_URL and NEXT_PUBLIC_AGENT_BACKEND_URL
```

**`mapper/docker.env`** — runtime variables injected into the frontend container at startup:

```bash
cp mapper/docker.env.example mapper/docker.env
# edit mapper/docker.env — set AGENT_BACKEND_URL, PROJECTS_FOLDER, NEO4J_*, etc.
```

**`agent/docker.env`** — runtime variables injected into the agent container at startup:

```bash
cp agent/docker.env.example agent/docker.env
# edit agent/docker.env — set GOOGLE_API_KEY (or ANTHROPIC_API_KEY / OPENAI_API_KEY),
#   GITHUB_TOKEN (required by the read-code skill),
#   SHARED_ADK_MODEL, GRAPHIVAC_* values, and PROJECTS_FOLDER=/app/uploads
```

**`mcp_server/server/mcp.env`** — runtime variables for the MCP server:

```bash
cp mcp_server/server/mcp.env.example mcp_server/server/mcp.env
# edit mcp_server/server/mcp.env — set GRAPHIVAC_* values
```

> None of these files are committed to source control — they are all gitignored.

### 2. Build

```bash
docker compose build
```

### 3. Start

```bash
# Core application stack
docker compose --profile deploy up

# Also start the Neo4j graph database
docker compose --profile deploy --profile graph up
```

The frontend is available at **http://localhost:3000**.
The Graphivac editor is available at **http://localhost:8888**.

### Useful commands

```bash
# Start in the background
docker compose --profile deploy up -d

# Start only the optional tooling (MCP Inspector + Portainer) without the full app
docker compose --profile tools up -d

# View logs for a specific service
docker compose logs -f si-mapper-frontend
docker compose logs -f si-mapper-agent
docker compose logs -f si-mapper-graphivac

# Rebuild a single service after a code change
docker compose build si-mapper-frontend
docker compose --profile deploy up si-mapper-frontend

docker compose build si-mapper-agent
docker compose --profile deploy up si-mapper-agent

# Stop all services
docker compose --profile deploy down
```

---

## 🗄️ Restoring the Graphivac Data Volume

`restore_graphivac_volume.py` is a self-contained Python 3 utility (no third-party dependencies) that re-creates the `si-mapper_graphivac_data` Docker volume from an embedded snapshot (taken 2026-03-30). Use it to seed a fresh environment with the demo projects and grids.

### Usage

```bash
# 1. Write the snapshot files to ./graphivac-data/ for inspection (default)
python restore_graphivac_volume.py

# 2. Write locally AND push directly into the live Docker volume
python restore_graphivac_volume.py --to-volume

# 3. Push directly into the volume without keeping a local copy
python restore_graphivac_volume.py --to-volume --no-local

# 4. Target a different volume name
python restore_graphivac_volume.py --to-volume --volume my_other_volume

# 5. Write to a custom local directory instead of ./graphivac-data/
python restore_graphivac_volume.py --output-dir /path/to/output
```

### Options

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--to-volume` | off | Push the restored files into the Docker volume after writing them locally |
| `--volume NAME` | `si-mapper_graphivac_data` | Name of the Docker volume to restore into |
| `--no-local` | off | Skip the local staging directory; implies `--to-volume` |
| `--output-dir DIR` | `./graphivac-data` | Local directory to write the restored files into |

> **Requires Docker** when `--to-volume` or `--no-local` is used. The script spins up a temporary `alpine` container, copies the files in via `docker cp`, then removes the container.

---

# Tech Stack

- **Agent Framework**: [Agent Development Kit](https://google.github.io/adk-docs/)
- **Frontend**: [React](https://react.dev/)
- **Backend for the Agent**: [FastAPI](https://fastapi.tiangolo.com/)
- **Connection between the Agent and the Frontend**: [CopilotKit](https://docs.copilotkit.ai/)
- **MCP Server**: [FastMCP](https://gofastmcp.com/getting-started/welcome)
- **Containerization**: [Docker](https://www.docker.com/)
- **Container Orchestration**: [Docker Compose](https://docs.docker.com/compose/)
- **Ontology Standard**: [Ashrae 223P](https://docs.open223.info/)
- **Graph Database**: [Neo4j](https://neo4j.com/)
