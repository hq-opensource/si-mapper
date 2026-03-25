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

> **Docker deployments** — pass variables via the `environment:` or `env_file:` keys in `docker-compose.yml` instead of using `.env.local`.

| Variable | Side | Description |
|---|---|---|
| `AGENT_BACKEND_URL` | Server | Full base URL of the ADK agent FastAPI server |
| `PROJECTS_FOLDER` | Server | Absolute path to the projects root folder (matches Docker volume mount) |
| `NEO4J_BOLT_URI` | Server | Neo4j Bolt connection URI |
| `NEO4J_USER` | Server | Neo4j username |
| `NEO4J_PASSWORD` | Server | Neo4j password |
| `NEXT_PUBLIC_AGENT_BACKEND_URL` | Client | Agent polling URL (must be reachable from the browser) |
| `NEXT_PUBLIC_GRAPHIVAC_GRID_URL` | Client | Graphivac grid base URL (leave empty to show a placeholder) |

## Available Scripts
- `dev` - Starts the UI, Agent, and MCP server concurrently in development mode.
- `dev:debug` - Starts development servers with debug logging enabled.
- `dev:ui` - Starts only the Next.js UI server.
- `dev:agent` - Starts only the ADK agent server.
- `dev:mcp` - Starts only the MCP server.
- `build` - Builds the Next.js application for production.
- `start` - Starts the production server.
- `lint` - Runs ESLint for code linting.
