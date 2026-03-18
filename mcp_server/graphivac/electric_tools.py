
import os
import sys
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.electric_manager import ElectricManager #noqa

def register_electric_tools(mcp_instance: FastMCP, electric_manager: ElectricManager):
    """
    Registers all electric-related MCP tools.
    """

    @mcp_instance.tool
    async def create_variable_frequency_drive(name: str, coord: list[int]) -> ToolResult:
        """Adds a Variable Frequency Drive (VFD) to the system at specific coordinates."""
        result = await electric_manager.create_variable_frequency_drive(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_variable_frequency_drive(name: str) -> ToolResult:
        """Deletes a Variable Frequency Drive (VFD) by name."""
        result = await electric_manager.delete_variable_frequency_drive(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )
