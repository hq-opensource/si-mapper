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

## 🐳 Docker Deployment

The full stack can be run as Docker containers using the `deploy` profile. All services are defined in `docker-compose.yml` at the project root.

### Services

| Service | Container | Host port | Description |
| :--- | :--- | :--- | :--- |
| `si-mapper-frontend` | `si-mapper-frontend` | `3001` | Next.js UI |
| `si-mapper-agent` | `si-mapper-agent` | `8001` | LLM orchestration agent (FastAPI) |
| `si-mapper-mcp` | `si-mapper-mcp` | `8080` | MCP server |
| `graphivac` | `si-mapper-graphivac` | `3000` | HVAC grid editor |
| `portainer` | `portainer` | `9000` | Container management UI |

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
docker compose --profile deploy up
```

The frontend is available at **http://localhost:3001**.

### Useful commands

```bash
# Start in the background
docker compose --profile deploy up -d

# View logs for a specific service
docker compose logs -f si-mapper-frontend
docker compose logs -f si-mapper-agent

# Rebuild a single service after a code change
docker compose build si-mapper-frontend
docker compose --profile deploy up si-mapper-frontend

docker compose build si-mapper-agent
docker compose --profile deploy up si-mapper-agent

# Stop all services
docker compose --profile deploy down
```

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
