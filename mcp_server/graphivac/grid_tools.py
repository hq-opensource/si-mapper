from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from mcp_server.graphivac.grid_manager import GridManager

def register_grid_tools(mcp: FastMCP, manager: GridManager):
    """
    Registers grid management tools with the MCP server.
    """

    @mcp.tool("read_grid")
    def read_grid() -> ToolResult:
        """
        Retrieves the current state of the grid as a list of components.
        """
        result = manager.read_grid()
        return ToolResult(
            content=[TextContent(type="text", text="Grid read successfully.")],
            structured_content={"components": result}
        )

    @mcp.tool("delete_grid")
    def delete_grid() -> ToolResult:
        """
        Deletes the current grid.
        """
        result = manager.delete_grid()
        return ToolResult(
            content=[TextContent(type="text", text="Grid deleted successfully.")],
            structured_content={"result": result}
        )
