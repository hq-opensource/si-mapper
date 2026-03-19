"""
Grid synchronization: Pulls the live GraphyVAC grid into the agent's internal state
using the EDN translator.
"""

import asyncio
import logging
import os
import requests
from typing import Optional

import edn_format
from edn_format import Keyword
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from utils.edn_to_mutable import edn_to_mutable
from utils.grid_edn_translator import edn_comps_to_internal_grid

logger = logging.getLogger(__name__)


def _fetch_and_parse_grid() -> tuple:
    """
    Synchronous helper: fetches the current grid from GraphyVAC via REST.
    Returns (internal_grid, edn_text) on success or ({"components": []}, "") on error.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    if not all([base_url, org_id, project_id, grid_id]):
        logger.warning("GraphyVAC env vars not fully set — internal_grid starts empty")
        return {"components": []}, ""

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    try:
        response = requests.get(url, headers={"Accept": "application/edn"}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not reach GraphyVAC to seed grid: {e} — starting empty")
        return {"components": []}, ""

    edn_text = response.text

    try:
        edn_data = edn_format.loads(edn_text)
    except Exception as e:
        logger.warning(f"Could not parse grid EDN response: {e} — starting empty")
        return {"components": []}, ""

    # Convert entire EDN to mutable Python types to extract comps
    raw_edn_grid = edn_to_mutable(edn_data)

    # Extract comps and translate to internal_grid
    comps_map = raw_edn_grid.get(Keyword("comps"), {})
    internal_grid = edn_comps_to_internal_grid(comps_map)

    # Return the raw EDN string (not the parsed dict) so it can be stored in state
    # without Keyword objects that break JSON serialization.
    return internal_grid, edn_text


async def sync_graphivac_to_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    before_agent_callback: seeds internal_grid from the live GraphyVAC grid
    at the start of every agent turn.

    Saves the raw EDN grid as _raw_edn_grid so after_callback can preserve
    non-comps metadata (title, font configs, etc.) in the PUT.
    """
    try:
        internal_grid, raw_edn_grid = await asyncio.to_thread(_fetch_and_parse_grid)
        callback_context.state["internal_grid"] = internal_grid
        # Store as EDN string (not parsed dict) — Keyword objects in a parsed dict
        # cannot be serialized to JSON by the ADK state layer.
        callback_context.state["_raw_edn_grid"] = raw_edn_grid

        n = len(internal_grid.get("components", []))
        logger.info(f"grid_sync_graphivac_to_agent: Synchronized {n} components into agent memory")
    except Exception as e:
        logger.error(f"grid_sync_graphivac_to_agent: Sync failed, starting empty: {e}")
        if "internal_grid" not in callback_context.state:
            callback_context.state["internal_grid"] = {"components": []}
        if "_raw_edn_grid" not in callback_context.state:
            callback_context.state["_raw_edn_grid"] = ""

    return None
