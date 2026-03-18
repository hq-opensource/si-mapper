import logging
from typing import List, Dict, Any, Optional
from google.adk.tools.mcp_tool.mcp_session_manager import streamablehttp_client
from mcp import ClientSession

logger = logging.getLogger("sync_service.mcp_client")


class McpSyncClient:
    """Calls MCP server tools via streamablehttp to create/delete components in GraphyVAC."""

    def __init__(self, mcp_url: str = "http://localhost:8080/mcp/"):
        self.mcp_url = mcp_url

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Open a session, call one tool, close. Mirrors test_create_50_fans.py pattern."""
        async with streamablehttp_client(url=self.mcp_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                # result.content is a list of TextContent; extract text
                text = result.content[0].text if result.content else ""
                logger.info(f"MCP call {tool_name}({arguments}) -> {text}")
                return {"tool_name": tool_name, "status": text}

    async def create_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Map a component dict to the correct MCP create_* tool call."""
        comp_type = component["type"]
        name = component["name"]

        # Line types: duct, pipe — use start_coord, end_coord
        if comp_type in ("duct", "pipe"):
            tool_name = f"create_{comp_type}"
            args = {"name": name, "start_coord": component["start"], "end_coord": component["end"]}
        # Rotation types: fan, damper — include rotation
        elif comp_type in ("fan", "damper"):
            tool_name = f"create_{comp_type}"
            args = {"name": name, "coord": component["coord"], "rotation": component.get("rotation", 0)}
        # All other coord types
        else:
            tool_name = f"create_{comp_type}"
            args = {"name": name, "coord": component["coord"]}

        return await self.call_tool(tool_name, args)

    async def delete_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Map a component dict to the correct MCP delete_* tool call."""
        tool_name = f"delete_{component['type']}"
        return await self.call_tool(tool_name, {"name": component["name"]})
