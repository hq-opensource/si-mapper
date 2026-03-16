#!/bin/bash
set -e

# Setup Agent
echo "[1/2] Setting up Agent..."
cd "$(dirname "$0")/../../agent"
uv sync

# Setup MCP Server
echo "[2/2] Setting up MCP Server..."
cd "$(dirname "$0")/../../mcp_server"
uv sync

echo ""
echo "All Python environments synchronized successfully."
