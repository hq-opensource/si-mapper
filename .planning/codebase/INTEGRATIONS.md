# External Integrations

**Analysis Date:** 2026-02-09

## APIs & External Services
- **Google Gemini API:** Primary LLM and Multimodal (vision) provider for agent reasoning and image recognition.
- **Graphivac API/Public Graph:** External service for hosting and visualizing HVAC graph data. Accessible at `graphivac.hvac.io`.
- **Model Context Protocol (MCP):** Used as a standardized interface to interact with internal and external tools.

## Data Storage
- **Postgres Database:** Used for task tracking, agent state persistence, and managing tool data. Hosted via Docker (`toolbox_postgres`, `db_postgres`).
- **File System:** Local storage for drawing images and generated artifacts.

## Authentication & Identity
- **API Keys:** Managed via `GOOGLE_API_KEY` for Gemini access.
- **Database Auth:** Basic user/password authentication for Postgres services.

## Monitoring & Observability
- **Logs:** Centralized logging to `app_run.log` for debugging agent behavior.
- **MCP Inspector:** Tool for debugging and inspecting MCP server interactions. Available at `localhost:6274` when deployed.
- **Portainer:** Container management and monitoring UI at `localhost:9000`.

## CI/CD & Deployment
- **Docker Compose:** Orchestrates the multi-container environment (Agent, MCP, Database, Tools).
- **Profiles:** `build`, `deploy`, and `tools` profiles used to manage different lifecycle stages.

## Environment Configuration
- Uses `.env` files for secret management.
- Configuration is largely driven by `docker-compose.yml` and Python `dotenv`.

## Webhooks & Callbacks
- **MCP Streamable HTTP:** Transport layer for agent-tool communication.
