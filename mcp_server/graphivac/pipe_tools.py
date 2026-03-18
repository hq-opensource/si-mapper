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

from mcp_server.graphivac.pipe_manager import PipeManager #noqa


def register_pipe_tools(mcp_instance: FastMCP, pipe_manager: PipeManager):
    """
    Registers all pipe-related MCP tools.
    """

    @mcp_instance.tool
    async def create_pipe(name: str, start_coord: List[int], end_coord: List[int]) -> ToolResult:
        """Creates a water/fluid pipe between two coordinate points.
        The start_coord input refers to the starting point of the pipe, the place where the fluid is entering the pipe.
        The end_coord input refers to the ending point of the pipe, the place where the fluid is going out from the pipe."""
        result = await pipe_manager.create_pipe(name, start_coord, end_coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_pipe(name: str) -> ToolResult:
        """Deletes a pipe by name."""
        result = await pipe_manager.delete_pipe(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_boiler(name: str, coord: List[int]) -> ToolResult:
        """Adds a boiler to the piping system at specific coordinates."""
        result = await pipe_manager.create_boiler(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_boiler(name: str) -> ToolResult:
        """Deletes a boiler by name."""
        result = await pipe_manager.delete_boiler(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_heat_pump(name: str, coord: List[int]) -> ToolResult:
        """Adds a heat pump to the piping system at specific coordinates."""
        result = await pipe_manager.create_heat_pump(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_heat_pump(name: str) -> ToolResult:
        """Deletes a heat pump by name."""
        result = await pipe_manager.delete_heat_pump(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_pump(name: str, coord: List[int]) -> ToolResult:
        """Adds a pump equipment (to pump fluids) to the piping system at specific coordinates."""
        result = await pipe_manager.create_pump(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_pump(name: str) -> ToolResult:
        """Deletes a pump equipment (to pump fluids) by name."""
        result = await pipe_manager.delete_pump(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_pipe_sensor_temperature(name: str, coord: List[int]) -> ToolResult:
        """Adds a temperature sensor to the piping system at specific coordinates."""
        result = await pipe_manager.create_sensor_temperature(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_pipe_sensor_temperature(name: str) -> ToolResult:
        """Deletes a temperature sensor from the piping system."""
        result = await pipe_manager.delete_sensor_temperature(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_valve_three_way(name: str, coord: List[int]) -> ToolResult:
        """Adds a three-way valve to the piping system at specific coordinates."""
        result = await pipe_manager.create_valve_three_way(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_valve_three_way(name: str) -> ToolResult:
        """Deletes a three-way valve by name."""
        result = await pipe_manager.delete_valve_three_way(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_valve_two_way(name: str, coord: List[int]) -> ToolResult:
        """Adds a two-way valve to the piping system at specific coordinates."""
        result = await pipe_manager.create_valve_two_way(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_valve_two_way(name: str) -> ToolResult:
        """Deletes a two-way valve by name."""
        result = await pipe_manager.delete_valve_two_way(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )
