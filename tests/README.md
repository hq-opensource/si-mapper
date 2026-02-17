# Grid Reading Verification Tests

This folder contains scripts to verify the integration between the Agent, the MCP Server, and the Graphivac API.

## Prerequisites

The full-stack test requires the MCP server to be running.

```powershell
# Start the server (from project root)
cd mcp_server
uv run server/main.py
```

---

## 1. Logic Verification (`test_read_grid.py`)

This test verifies the internal Python logic of the `GridManager` and its ability to communicate with the Graphivac API. It bypasses the MCP network protocol.

**Run command (from project root):**
```powershell
.\mcp_server\.venv\Scripts\python.exe tests/test_read_grid.py
```

- **Environment**: Uses `mcp_server` dependencies.
- **Verification**: Checks if the grid configured in `mcp_server/server/mcp.env` is reachable and parses components correctly.

---

## 2. Full-Stack Agent Verification (`verify_mcp_adk_v2.py`)

This test simulates a real AI agent's behavior. It connects to the running MCP server over HTTP and calls the `read_grid` tool using the actual transport layer used by the agent.

**Run command (from project root):**
```powershell
.\agent\.venv\Scripts\python.exe tests/verify_mcp_adk_v2.py
```

- **Environment**: Uses `agent` dependencies (specifically `google-adk`).
- **Prerequisite**: MCP Server must be running on `http://localhost:8080`.
- **Verification**: Confirms that the agent can successfully call the tool and receive structured component data via the MCP protocol.
