import os
import sys
from typing import List, Any, Dict

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.custom_manager import CustomManager #noqa


def register_custom_tools(mcp_instance: FastMCP, custom_manager: CustomManager):
    """
    Registers all custom element-related MCP tools.
    """

    @mcp_instance.tool
    async def create_room_baseboard(name: str, coord: List[int]) -> ToolResult:
        """Adds a custom room baseboard heater/unit to a room at specific coordinates."""
        result = await custom_manager.create_room_baseboard(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_room_baseboard(name: str) -> ToolResult:
        """Deletes a room baseboard by name."""
        result = await custom_manager.delete_room_baseboard(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_pipe_chiller(name: str, coord: List[int]) -> ToolResult:
        """Adds a custom pipe chiller unit at specific coordinates."""
        result = await custom_manager.create_pipe_chiller(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_pipe_chiller(name: str) -> ToolResult:
        """Deletes a pipe chiller by name."""
        result = await custom_manager.delete_pipe_chiller(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )
