# MCP Server

> [!WARNING]
> **Deprecated.** This MCP server is no longer used by the `agent` or `mapper` services and is not deployed as part of the standard stack. It is kept here for reference only and will be removed in a future release. Do not add new features or dependencies against this module.

This directory contains the Model Context Protocol (MCP) server implementation for the Graphivac HVAC Agent.

## Structure

- `server/`: Contains the core server application code and configuration.
- `graphivac/`: Contains the Graphivac-specific tools and managers.

## Setup & Running

> **💡 Recommended Setup:** For the easiest setup, run `pnpm install` in the **mapper directory**. This will automatically handle the Python environment and dependencies for you. See the [Mapper README](../mapper/README.md) for details.

### Manual Setup
To start the MCP server independently, run the following from this directory:

```bash
uv sync
uv run server/main.py
```

The server will start on `http://localhost:8080`.

## Configuration

This server uses `server/mcp.env` for its internal configuration (Graphivac API IDs). This file is tracked in Git as it contains project-wide public IDs, not secret keys.

Secret keys or local overrides should be placed in a `.env` file in the `mcp_server` root directory, which is ignored by Git.

## Running Tests

To run the verification tests:

```bash
uv run graphivac/test.py
```
