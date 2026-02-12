# Technology Stack

**Analysis Date:** 2026-02-09

## Languages
- Python (>=3.10) - Primary for Agents and MCP Server
- TypeScript/JavaScript - Primary for Mapper Frontend

## Runtime
- Environments: Node.js (Frontend), Python (Backend)
- Package Managers: `uv` (Python), `pnpm` (TypeScript)

## Frameworks
- **Core (Backend):** FastAPI (Agent API and MCP Server), Pydantic
- **Core (Frontend):** Next.js, React
- **Testing:** Pytest (Backend)
- **Build/Dev:** Docker Compose for multi-container orchestration

## Key Dependencies
- `google-genai` & `google-adk`: Integration with Google's Gemini models
- `mcp`: Implementation of Model Context Protocol
- `psycopg`: Postgres database interaction
- `fastapi` & `uvicorn`: API development and serving
- `httpx` & `requests`: HTTP client libraries

## Configuration
- `.env` files for environment variables (Google API Key, Database credentials)
- `pyproject.toml` for Python project configuration and dependencies
- `package.json` and `tsconfig.json` for TypeScript/Frontend configuration
- `docker-compose.yml` for orchestration of services

## Platform Requirements
- **Development:** Docker, Docker Compose, Python 3.10+, Node.js/PNPM
- **Production:** Docker-ready environment (e.g., Cloud Run, EC2)
