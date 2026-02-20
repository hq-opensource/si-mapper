from typing import Dict, Any
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from mcp_server.graphivac.metadata_manager import MetadataManager

def register_metadata_tools(mcp: FastMCP, manager: MetadataManager):
    """
    Registers metadata-related tools with the MCP server.
    """

    @mcp.tool("write_metadata")
    def write_metadata(equipment_name: str, metadata: Dict[str, Any]) -> ToolResult:
        """
        Adds or updates technical metadata for a specific equipment found on the grid.
        The data is saved as a JSON string in the component's ':custom-fields' property.
        
        Args:
            equipment_name: The unique name of the equipment (e.g., 'AHU-1').
            metadata: A dictionary of technical data (e.g., {'bacnet': 'AL-23', 'control': 'FRE2'}).
        """
        result = manager.write_metadata(equipment_name, metadata)
        return ToolResult(
            content=[TextContent(type="text", text=f"Metadata update for {equipment_name}: {result['tool_status']}")],
            structured_content=result
        )

    @mcp.tool("read_metadata")
    def read_metadata(equipment_name: str) -> ToolResult:
        """
        Retrieves the technical metadata for a specific equipment from its ':custom-fields' property.
        
        Args:
            equipment_name: The unique name of the equipment (e.g., 'AHU-1').
        """
        try:
            metadata = manager.read_metadata(equipment_name)
            return ToolResult(
                content=[TextContent(type="text", text=f"Metadata for {equipment_name} retrieved successfully.")],
                structured_content={"metadata": metadata}
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Error reading metadata for {equipment_name}: {str(e)}")],
                is_error=True
            )

    @mcp.tool("delete_metadata")
    def delete_metadata(equipment_name: str) -> ToolResult:
        """
        Deletes the technical metadata (the ':custom-fields' property) for a specific equipment.
        
        Args:
            equipment_name: The unique name of the equipment (e.g., 'AHU-1').
        """
        result = manager.delete_metadata(equipment_name)
        return ToolResult(
            content=[TextContent(type="text", text=f"Metadata deletion for {equipment_name}: {result['tool_status']}")],
            structured_content=result
        )

    @mcp.tool("write_metadata_batch")
    def write_metadata_batch(updates: Dict[str, Dict[str, Any]]) -> ToolResult:
        """
        Updates technical metadata for multiple equipment items in a single transaction.
        
        Args:
            updates: A dictionary where keys are equipment names (e.g., 'AHU-1') 
                     and values are technical metadata dictionaries (e.g., {'control': {...}}).
        """
        result = manager.write_metadata_batch(updates)
        return ToolResult(
            content=[TextContent(type="text", text=f"Batch metadata update processed {result['processed']} items.")],
            structured_content=result
        )
