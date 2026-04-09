"""
Tool: sync_agent_to_graphivac

Pushes the agent's internal_grid to Graphivac via a REST PUT.
The agent calls this tool explicitly when it decides the grid state is ready
to be persisted — typically after completing a batch of modifications.
"""

import asyncio
import logging
import os

import edn_format
import requests
from edn_format import Keyword
from google.adk.tools import ToolContext

from utils.edn_to_mutable import edn_to_mutable
from utils.grid_edn_translator import internal_grid_to_edn_comps
from utils.project_utils import get_graphivac_project_id, get_graphivac_grid_id

logger = logging.getLogger(__name__)


def _put_grid_to_graphivac(raw_edn_grid: dict, project_id: str = "", grid_id: str = "") -> int:
    """Synchronous helper: PUTs the full grid EDN to Graphivac. Returns status code.

    project_id / grid_id are resolved by the caller from state (state-first) and
    passed in here so this pure-sync helper stays stateless.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id   = os.getenv("GRAPHIVAC_ORG_ID", "")
    # Fall back to env vars when caller did not supply values
    if not project_id:
        project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    if not grid_id:
        grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    url = f"{base_url}/api/v1/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    data = edn_format.dumps(raw_edn_grid)
    response = requests.put(url, headers={"Content-Type": "application/edn"}, data=data, timeout=15)
    response.raise_for_status()
    return response.status_code


async def sync_agent_to_graphivac(tool_context: ToolContext) -> dict:
    """
    Persists the current internal_grid to Graphivac.

    Call this tool after you have finished modifying components in the grid
    and want to save the changes. The tool reads the current internal_grid
    from state, converts it to EDN format, and PUTs it to Graphivac.

    Returns a dict with 'status' ('ok' or 'error') and a 'message'.
    """
    state = tool_context.state

    if not state.get("_updated_grid"):
        return "No pending grid changes to sync. Internal grid state of the agent is already up to date."

    # State-first: prefer IDs injected by the frontend (13-09).
    project_id = get_graphivac_project_id(tool_context)
    grid_id    = get_graphivac_grid_id(tool_context)

    internal_grid = state.get("internal_grid", {"components": []})
    raw_edn_str = state.get("_raw_edn_grid", "")
    n = len(internal_grid.get("components", []))

    if not raw_edn_str:
        return "SYNC-OUT FAILED: raw EDN grid is empty. Call sync_graphivac_to_agent first to load the grid."

    try:
        raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))
    except Exception as e:
        return f"SYNC-OUT FAILED: could not parse EDN grid: {e}"

    try:
        new_comps = internal_grid_to_edn_comps(internal_grid)
        raw_edn_grid[Keyword("comps")] = new_comps
    except Exception as e:
        return f"SYNC-OUT FAILED: could not build EDN components: {e}"

    last_error = None
    for attempt in range(2):
        try:
            http_status = await asyncio.to_thread(
                _put_grid_to_graphivac, raw_edn_grid, project_id, grid_id
            )
            state["_updated_grid"] = False
            logger.info(f"[SYNC-OUT] PUT {n} component(s) → HTTP {http_status}")
            return f"Grid synchronized to Graphivac. {n} component(s) saved successfully."
        except Exception as e:
            last_error = e
            if attempt == 0:
                logger.warning(f"[SYNC-OUT] PUT attempt 1 failed, retrying: {e}")

    return (
        f"SYNC-OUT FAILED after 2 attempts. Grid state is diverged — stop all grid operations. "
        f"Error: {last_error}"
    )
