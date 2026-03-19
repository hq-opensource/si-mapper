"""
Sync Out: Push agent's internal_grid to GraphyVAC via a single REST PUT.
"""

import asyncio
import logging
import os
from typing import Optional

import edn_format
import requests
from edn_format import Keyword
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from utils.edn_to_mutable import edn_to_mutable
from utils.grid_edn_translator import internal_grid_to_edn_comps

logger = logging.getLogger(__name__)


def _put_grid_to_graphivac(raw_edn_grid: dict) -> None:
    """Synchronous helper: PUTs the full grid EDN to GraphyVAC."""
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    headers = {"Content-Type": "application/edn"}
    data = edn_format.dumps(raw_edn_grid)
    response = requests.put(url, headers=headers, data=data, timeout=15)
    response.raise_for_status()


async def sync_agent_to_graphivac_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    after_agent_callback: Rebuilds full comps from internal_grid,
    replaces the comps key in _raw_edn_grid, and PUTs the entire grid
    to GraphyVAC in a single REST call. No diffing. No MCP.
    """
    internal_grid = callback_context.state.get("internal_grid", {"components": []})
    raw_edn_str = callback_context.state.get("_raw_edn_grid", "")

    if not raw_edn_str:
        logger.warning("grid_sync_agent_to_graphivac: No _raw_edn_grid in state — skipping PUT")
        return None

    # Re-parse the stored EDN string into a mutable dict with Keyword keys.
    # We store as a string in state to avoid Keyword objects breaking JSON serialization.
    raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))

    # Rebuild comps from internal_grid
    new_comps = internal_grid_to_edn_comps(internal_grid)
    raw_edn_grid[Keyword("comps")] = new_comps

    n = len(internal_grid.get("components", []))
    logger.info(f"grid_sync_agent_to_graphivac: Rebuilding {n} components into EDN and PUTting to GraphyVAC")

    # Attempt PUT with one retry
    last_error = None
    for attempt in range(2):
        try:
            await asyncio.to_thread(_put_grid_to_graphivac, raw_edn_grid)
            logger.info("grid_sync_agent_to_graphivac: PUT successful")
            return None
        except Exception as e:
            last_error = e
            if attempt == 0:
                logger.warning(f"grid_sync_agent_to_graphivac: PUT failed (attempt 1), retrying: {e}")

    # Both attempts failed — return error Content to agent
    error_msg = (
        "SYNC ERROR: Failed to write grid to GraphyVAC after retry. "
        "Grid state is diverged. Stop all grid operations. "
        f"Last error: {last_error}"
    )
    logger.warning(f"grid_sync_agent_to_graphivac: {error_msg}")
    return types.Content(
        parts=[types.Part(text=error_msg)]
    )
