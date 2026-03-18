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

from mcp_server.graphivac.duct_manager import DuctManager #noqa


def register_duct_tools(mcp_instance: FastMCP, duct_manager: DuctManager):
    """
    Registers all duct-related MCP tools.
    """

    @mcp_instance.tool
    async def create_duct(name: str, start_coord: List[int], end_coord: List[int]) -> ToolResult:
        """Creates a main air duct between two coordinate points.
        The start_coord input refers to the starting point of the duct, the place where the air is entering the duct.
        The end_coord input refers to the ending point of the duct, the place where the air is going out from the duct."""
        result = await duct_manager.create_duct(name, start_coord, end_coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_ducts_batch(ducts: Dict[str, Any]) -> ToolResult:
        """Creates multiple air ducts in a single batch operation.
        Input should be a dictionary where keys are duct names and values are dicts with 'start' and 'end' coordinates.
        Example: {"duct1": {"start": [0,0], "end": [10,0]}, "duct2": {"start": [10,0], "end": [10,10]}}
        It also supports nested keys 'horizontal_ducts' or 'vertical_ducts'."""
        result = await duct_manager.create_ducts_batch(ducts)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct(name: str) -> ToolResult:
        """Deletes a main air duct by name."""
        result = await duct_manager.delete_duct(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_cooling_coil(name: str, coord: List[int]) -> ToolResult:
        """Adds a cooling coil to the duct system at specific coordinates."""
        result = await duct_manager.create_cooling_coil(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_cooling_coil(name: str) -> ToolResult:
        """Deletes a cooling coil by name."""
        result = await duct_manager.delete_cooling_coil(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_heating_coil(name: str, coord: List[int]) -> ToolResult:
        """Adds a heating coil to the duct system at specific coordinates."""
        result = await duct_manager.create_heating_coil(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_heating_coil(name: str) -> ToolResult:
        """Deletes a heating coil by name."""
        result = await duct_manager.delete_heating_coil(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_fan(name: str, coord: List[int], rotation: int = 0) -> ToolResult:
        """Adds a fan to the duct system at specific coordinates with optional rotation (default 0)."""
        result = await duct_manager.create_fan(name, coord, rotation)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_fan(name: str) -> ToolResult:
        """Deletes a fan by name."""
        result = await duct_manager.delete_fan(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_filter(name: str, coord: List[int]) -> ToolResult:
        """Adds a filter to the duct system at specific coordinates."""
        result = await duct_manager.create_filter(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_filter(name: str) -> ToolResult:
        """Deletes a filter by name."""
        result = await duct_manager.delete_filter(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_damper(name: str, coord: List[int], rotation: int = 0) -> ToolResult:
        """Adds a damper to the duct system at specific coordinates with optional rotation (default 0)."""
        result = await duct_manager.create_damper(name, coord, rotation)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_damper(name: str) -> ToolResult:
        """Deletes a damper by name."""
        result = await duct_manager.delete_damper(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_thermal_wheel(name: str, coord: List[int]) -> ToolResult:
        """Adds a thermal wheel (heat recovery) to the duct system at specific coordinates."""
        result = await duct_manager.create_thermal_wheel(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_thermal_wheel(name: str) -> ToolResult:
        """Deletes a thermal wheel by name."""
        result = await duct_manager.delete_thermal_wheel(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_humidifier(name: str, coord: List[int]) -> ToolResult:
        """Adds a humidifier to the duct system at specific coordinates."""
        result = await duct_manager.create_humidifier(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_humidifier(name: str) -> ToolResult:
        """Deletes a humidifier by name."""
        result = await duct_manager.delete_humidifier(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    # --- DUCT SENSORS ---

    @mcp_instance.tool
    async def create_duct_sensor_enthalpy(name: str, coord: List[int]) -> ToolResult:
        """Adds an enthalpy sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_enthalpy(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_enthalpy(name: str) -> ToolResult:
        """Deletes an enthalpy sensor by name."""
        result = await duct_manager.delete_sensor_enthalpy(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_duct_sensor_temperature(name: str, coord: List[int]) -> ToolResult:
        """Adds a temperature sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_temperature(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_temperature(name: str) -> ToolResult:
        """Deletes a temperature sensor by name."""
        result = await duct_manager.delete_sensor_temperature(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_duct_sensor_differential_pressure(name: str, coord: List[int]) -> ToolResult:
        """Adds a differential pressure sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_differential_pressure(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_differential_pressure(name: str) -> ToolResult:
        """Deletes a differential pressure sensor by name."""
        result = await duct_manager.delete_sensor_differential_pressure(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_duct_sensor_humidity(name: str, coord: List[int]) -> ToolResult:
        """Adds a humidity sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_humidity(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_humidity(name: str) -> ToolResult:
        """Deletes a humidity sensor by name."""
        result = await duct_manager.delete_sensor_humidity(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_duct_sensor_flow(name: str, coord: List[int]) -> ToolResult:
        """Adds a flow sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_flow(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_flow(name: str) -> ToolResult:
        """Deletes a flow sensor by name."""
        result = await duct_manager.delete_sensor_flow(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_duct_sensor_low_limit(name: str, coord: List[int]) -> ToolResult:
        """Adds a low limit sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_low_limit(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_low_limit(name: str) -> ToolResult:
        """Deletes a low limit sensor by name."""
        result = await duct_manager.delete_sensor_low_limit(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def create_duct_sensor_static_pressure(name: str, coord: List[int]) -> ToolResult:
        """Adds a static pressure sensor to the duct system at specific coordinates."""
        result = await duct_manager.create_sensor_static_pressure(name, coord)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )

    @mcp_instance.tool
    async def delete_duct_sensor_static_pressure(name: str) -> ToolResult:
        """Deletes a static pressure sensor by name."""
        result = await duct_manager.delete_sensor_static_pressure(name)
        return ToolResult(
            content=[TextContent(type="text", text=result["tool_status"])],
            structured_content=result
        )
