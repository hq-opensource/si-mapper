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

logger = logging.getLogger(__name__)


def _put_grid_to_graphivac(raw_edn_grid: dict) -> int:
    """Synchronous helper: PUTs the full grid EDN to Graphivac. Returns status code."""
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
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
        return {"status": "ok", "message": "No pending grid changes to sync."}

    internal_grid = state.get("internal_grid", {"components": []})
    raw_edn_str = state.get("_raw_edn_grid", "")
    n = len(internal_grid.get("components", []))

    if not raw_edn_str:
        return {"status": "error", "message": "_raw_edn_grid is empty — cannot sync."}

    try:
        raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse _raw_edn_grid: {e}"}

    try:
        new_comps = internal_grid_to_edn_comps(internal_grid)
        raw_edn_grid[Keyword("comps")] = new_comps
    except Exception as e:
        return {"status": "error", "message": f"Failed to build EDN comps: {e}"}

    last_error = None
    for attempt in range(2):
        try:
            status = await asyncio.to_thread(_put_grid_to_graphivac, raw_edn_grid)
            state["_updated_grid"] = False
            logger.info(f"[SYNC-OUT] PUT {n} component(s) → HTTP {status}")
            return {"status": "ok", "message": f"Synced {n} component(s) to Graphivac (HTTP {status})."}
        except Exception as e:
            last_error = e
            if attempt == 0:
                logger.warning(f"[SYNC-OUT] PUT attempt 1 failed, retrying: {e}")

    error_msg = (
        f"Failed to write grid to Graphivac after 2 attempts. "
        f"Grid state is diverged. Stop all grid operations. "
        f"Last error: {last_error}"
    )
    logger.error(f"[SYNC-OUT] UNRECOVERABLE: {error_msg}")
    return {"status": "error", "message": error_msg}
