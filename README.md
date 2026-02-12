# SI-MAPPER

SI-MAPPER is an AI Agent built using the **Google ADK** and **Ashrae 223P standard**. It transforms multimodal HVAC data into a semantic virtual twin, integrating BACnet, Modbus, and external databases for advanced diagnostics and optimization.

## 🚀 Quick Start

The project is structured with a Next.js frontend that orchestrates the backend services.

### 1. Prerequisites
- [Node.js](https://nodejs.org/) & [pnpm](https://pnpm.io/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### 2. Setup & Run
Navigate to the `mapper` folder to install dependencies and start the full system:

```bash
cd mapper
pnpm install
pnpm dev
```

This single `pnpm install` will automatically synchronize the Python environments for the Agent and MCP Server as well.

---

## 🛠️ Independent Control

If you need to work on specific components independently:

| Component | Path | Tool | Command |
| :--- | :--- | :--- | :--- |
| **Frontend** | `/mapper` | pnpm | `pnpm dev:ui` |
| **Agent** | `/agent` | uv | `uv run main.py` |
| **MCP Server** | `/mcp_server` | uv | `uv run server/main.py` |


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
