#!/bin/bash
set -e

# Setup Agent
echo "[1/2] Setting up Agent..."
pushd "$(dirname "$0")/../../agent"
uv sync
popd

# Setup MCP Server
echo "[2/2] Setting up MCP Server..."
pushd "$(dirname "$0")/../../mcp_server"
uv sync
popd

echo ""
echo "All Python environments synchronized successfully."
