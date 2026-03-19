"""
Sync Out: Push agent's local grid modifications to GraphyVAC via MCP.
"""

import logging
import os
import json
from typing import Optional, Dict, Any, List, Tuple
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

# Use existing MCP client logic for pushing
from google.adk.tools.mcp_tool.mcp_session_manager import streamablehttp_client
from mcp import ClientSession

logger = logging.getLogger(__name__)

# --- Low Level MCP Client ---

async def call_mcp_tool(mcp_url: str, tool_name: str, arguments: Dict[str, Any]) -> str:
    """Invokes an MCP tool directly via streamable HTTP."""
    try:
        async with streamablehttp_client(url=mcp_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                # First content item should be TextContent
                return result.content[0].text if result.content else "No result text"
    except Exception as e:
        logger.error(f"MCP Call Failed: {tool_name}({arguments}) -> {e}")
        return f"Error: {e}"

# --- Diffing & Pushing ---

async def sync_agent_to_graphivac_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    after_agent_callback: Diffs current grid state (potentially modified by agent)
    against the Turn-Initial state, and pushes deletions/creates to GraphyVAC.

    Ensures the UI stays in sync with agent tool actions.
    """
    current_grid = callback_context.state.get("internal_grid", {"components": []})
    initial_grid = callback_context.state.get("_initial_grid_snapshot", {"components": []})

    curr_comps = {c["name"]: c for c in current_grid.get("components", [])}
    init_comps = {c["name"]: c for c in initial_grid.get("components", [])}

    curr_names = set(curr_comps.keys())
    init_names = set(init_comps.keys())

    to_create = [curr_comps[n] for n in (curr_names - init_names)]
    to_delete = [init_comps[n] for n in (init_names - curr_names)]

    if not to_create and not to_delete:
        logger.debug("grid_sync_agent_to_graphivac: No changes to push to GraphyVAC")
        return None

    logger.info(f"grid_sync_agent_to_graphivac: Syncing {len(to_create)} additions and {len(to_delete)} deletions out to GraphyVAC")

    mcp_url = os.getenv("MCP_URL", "http://localhost:8080/mcp/")

    # Process Deletions First (avoid name conflicts)
    for comp in to_delete:
        tool_name = f"delete_{comp['type']}"
        await call_mcp_tool(mcp_url, tool_name, {"name": comp["name"]})

    # Process Creations
    for comp in to_create:
        comp_type = comp["type"]
        name = comp["name"]

        # Map current schema to specialized create tools
        if comp_type in ("duct", "pipe"):
            tool_name = f"create_{comp_type}"
            args = {"name": name, "start_coord": comp["start"], "end_coord": comp["end"]}
        elif comp_type in ("fan", "damper"):
            tool_name = f"create_{comp_type}"
            args = {"name": name, "coord": comp["coord"], "rotation": comp.get("rotation", 0)}
        else:
            tool_name = f"create_{comp_type}"
            args = {"name": name, "coord": comp["coord"]}

        await call_mcp_tool(mcp_url, tool_name, args)

    logger.info("grid_sync_agent_to_graphivac: Sync-Out complete")
    return None
