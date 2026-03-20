"""
Tool: sync_graphivac_to_agent

Pulls the live Graphivac grid into the agent's internal state.
The agent calls this tool explicitly when it wants to refresh its view of
the grid — typically at the start of a task or before reading grid data.
"""

import asyncio
import logging
import os

import edn_format
import requests
from edn_format import Keyword
from google.adk.tools import ToolContext

from utils.edn_to_mutable import edn_to_mutable
from utils.grid_edn_translator import edn_comps_to_internal_grid

logger = logging.getLogger(__name__)


def _fetch_and_parse_grid() -> tuple:
    """
    Synchronous helper: fetches the current grid from Graphivac via REST.
    Returns (internal_grid, edn_text) on success or ({"components": []}, "") on error.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    if not all([base_url, org_id, project_id, grid_id]):
        raise ValueError("Graphivac env vars not fully set (GRAPHIVAC_BASE_URL, GRAPHIVAC_ORG_ID, GRAPHIVAC_PROJECT_ID, GRAPHIVAC_GRID_ID).")

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    response = requests.get(url, headers={"Accept": "application/edn"}, timeout=10)
    response.raise_for_status()

    edn_text = response.text
    edn_data = edn_format.loads(edn_text)
    raw_edn_grid = edn_to_mutable(edn_data)

    comps_map = raw_edn_grid.get(Keyword("comps"), {})
    internal_grid = edn_comps_to_internal_grid(comps_map)

    return internal_grid, edn_text


async def sync_graphivac_to_agent(tool_context: ToolContext) -> dict:
    """
    Fetches the current grid from Graphivac and loads it into the agent's internal state.

    Call this tool before reading or modifying grid components to ensure you are
    working with the latest data. It overwrites any in-memory grid state with the
    live version from Graphivac and resets the pending-changes flag.

    Returns a plain string confirming success or describing the failure.
    """
    try:
        internal_grid, raw_edn_text = await asyncio.to_thread(_fetch_and_parse_grid)
    except Exception as e:
        logger.error(f"[SYNC-IN] Failed to fetch grid from Graphivac: {e}")
        if "internal_grid" not in tool_context.state:
            tool_context.state["internal_grid"] = {"components": []}
        if "_raw_edn_grid" not in tool_context.state:
            tool_context.state["_raw_edn_grid"] = ""
        return f"SYNC-IN FAILED: {e}. Internal grid was not updated."

    tool_context.state["internal_grid"] = internal_grid
    tool_context.state["_raw_edn_grid"] = raw_edn_text
    tool_context.state["_updated_grid"] = False

    n = len(internal_grid.get("components", []))
    logger.info(f"[SYNC-IN] Fetched {n} component(s) from Graphivac → internal_grid reset")
    return f"Agent's internal grid is now synchronized with Graphivac ({n} components)."
