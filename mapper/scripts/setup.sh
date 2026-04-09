#!/bin/bash
set -e

# Setup Agent
echo "[1/3] Setting up Agent..."
pushd "$(dirname "$0")/../../agent"
uv sync
popd

# Setup MCP Server
echo "[2/3] Setting up MCP Server..."
pushd "$(dirname "$0")/../../mcp_server"
uv sync
popd

echo ""
echo "[3/3] Done."
echo "All Python environments synchronized successfully."
