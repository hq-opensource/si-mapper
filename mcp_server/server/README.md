# SI-MAPPER Model Context Protocol Server

This project implements the Model Context Protocol (MCP) Server for the SI-MAPPER Agent. It exposes multiple sets of tools for the SI-MAPPER system.

## Architecture

This server is designed with a modern and high-performance stack that ensures compatibility with the latest MCP standards:

*   **Protocol**: **Streamable HTTP**. This next-generation transport protocol replaces standard SSE/HTTP patterns, offering a robust single-endpoint (`/mcp`) communication channel.
*   **Core Framework**: **FastMCP**. Tools are defined using the developer-friendly `FastMCP` decorators (`@mcp.tool`), simplifying input schema generation and validation.
*   **Web Server**: **Starlette**. The `FastMCP` instance is wrapped in a `StreamableHTTPSessionManager` and exposed via a Starlette ASGI application. This is required to support the Streamable HTTP transport explicitly.
*   **ASGI Server**: **Uvicorn**. A lightning-fast ASGI server that runs the Starlette application.
*   **Package Management**: **uv**. We use `uv` for extremely fast and reliable dependency management, available both locally and inside the Docker container.
*   **Runtime**: **Python 3.12**.

## Quick Start (Docker)

The easiest way to run the server is using Docker. The container is optimized with `uv` and `python:3.12-slim`.

### 1. Build the Image

Run this command from the **project root** (one level up from this directory):

```bash
docker build --no-cache -t si-mapper-mcp -f mcp_server/server/Dockerfile .
```

### 2. Run the Container

Start the server on port 8080. Ensure you provide the required environment variables (e.g., via an `mcp.env` file).

```bash
docker run -d \
  -p 8080:8080 \
  --env-file mcp_server/server/mcp.env \
  --name si-mapper-mcp \
  si-mapper-mcp
```

The server will be available at: `http://localhost:8080/mcp`

## Debugging with MCP Inspector

The **MCP Inspector** is a developer tool for testing and debugging. Since this server uses **Streamable HTTP**, the inspection workflow involves running the server first, then connecting the inspector to it.

### 1. Start the Server
Ensure your SI-MAPPER MCP Server is running.
*   **Docker**: Use the command above.
*   **Local**: `uv run server/main.py`
*   **URL**: `http://localhost:8080/mcp`

### 2. Start the Inspector
you can run the inspector using `npx` or Docker.

**Option A: Using npx (Node.js)**
```bash
npx @modelcontextprotocol/inspector
```

**Option B: Using Docker**
```bash
docker run --rm --network host ghcr.io/modelcontextprotocol/inspector:latest
```
*Note: `--network host` is required to allow the inspector to access `localhost:8080`.*

### 3. Connect

1.  Open the Inspector UI (usually available at `http://localhost:6274`).
2.  Select **Streamable HTTP** as the transport.
3.  Enter the URL: `http://localhost:8080/mcp`.
4.  Click **Connect**.

Alternatively, after starting the inspector, click this link to auto-configure:
[Open Inspector for SI-MAPPER](http://localhost:6274/?transport=streamable-http&serverUrl=http://localhost:8080/mcp)

## Local Development

If you prefer to run locally without Docker:

1.  **Install uv** (if not installed): `pip install uv`
2.  **Install dependencies**:
    ```bash
    cd mcp_server
    uv sync
    ```
3.  **Run the server**:
    ```bash
    uv run server/main.py
    ```

## Project Structure

*   `server/`: Core server configuration, `main.py` entry point, and Dockerfile.
*   `graphivac/`: Tool definitions organized by domain (`duct_tools.py`, `pipe_tools.py`, `custom_tools.py`).
