@echo off
setlocal enabledelayedexpansion

REM Setup Agent
echo [1/2] Setting up Agent...
cd /d "%~dp0\..\..\agent"
call uv sync
if !errorlevel! neq 0 (
    echo Error setting up Agent.
    exit /b !errorlevel!
)

REM Setup MCP Server
echo [2/2] Setting up MCP Server...
cd /d "%~dp0\..\..\mcp_server"
call uv sync
if !errorlevel! neq 0 (
    echo Error setting up MCP Server.
    exit /b !errorlevel!
)

echo.
echo All Python environments synchronized successfully.
