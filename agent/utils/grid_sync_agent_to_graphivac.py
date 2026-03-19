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


def _put_grid_to_graphivac(raw_edn_grid: dict) -> tuple:
    """
    Synchronous helper: PUTs the full grid EDN to GraphyVAC.
    Returns (status_code, response_text) for logging.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    print(f"[SYNC-OUT] PUT URL: {url}", flush=True)

    headers = {"Content-Type": "application/edn"}
    data = edn_format.dumps(raw_edn_grid)
    print(f"[SYNC-OUT] PUT body length: {len(data)} chars, first 200: {data[:200]}", flush=True)

    response = requests.put(url, headers=headers, data=data, timeout=15)
    print(f"[SYNC-OUT] PUT response: {response.status_code} — {response.text[:300]}", flush=True)
    response.raise_for_status()
    return response.status_code, response.text


async def sync_agent_to_graphivac_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    after_agent_callback: Rebuilds full comps from internal_grid,
    replaces the comps key in _raw_edn_grid, and PUTs the entire grid
    to GraphyVAC in a single REST call. No diffing. No MCP.
    """
    print("[SYNC-OUT] after_agent_callback entered", flush=True)

    # Log all state keys so we can see what's present
    state_keys = list(callback_context.state.keys()) if hasattr(callback_context.state, "keys") else "not dict-like"
    print(f"[SYNC-OUT] state keys: {state_keys}", flush=True)

    internal_grid = callback_context.state.get("internal_grid", {"components": []})
    n_components = len(internal_grid.get("components", []))
    print(f"[SYNC-OUT] internal_grid has {n_components} components", flush=True)
    if n_components > 0:
        names = [c.get("name") for c in internal_grid["components"]]
        print(f"[SYNC-OUT] component names: {names}", flush=True)

    raw_edn_str = callback_context.state.get("_raw_edn_grid", "")
    print(f"[SYNC-OUT] _raw_edn_grid type={type(raw_edn_str).__name__} len={len(raw_edn_str) if isinstance(raw_edn_str, str) else 'N/A'}", flush=True)

    if not raw_edn_str:
        print("[SYNC-OUT] WARNING: _raw_edn_grid is empty — skipping PUT", flush=True)
        logger.warning("grid_sync_agent_to_graphivac: No _raw_edn_grid in state — skipping PUT")
        return None

    try:
        # Re-parse the stored EDN string into a mutable dict with Keyword keys.
        # We store as a string in state to avoid Keyword objects breaking JSON serialization.
        print("[SYNC-OUT] Parsing stored EDN string...", flush=True)
        raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))
        print(f"[SYNC-OUT] Parsed EDN keys: {[str(k) for k in raw_edn_grid.keys()]}", flush=True)
    except Exception as e:
        print(f"[SYNC-OUT] ERROR parsing _raw_edn_grid: {e}", flush=True)
        logger.error(f"grid_sync_agent_to_graphivac: Failed to parse _raw_edn_grid: {e}")
        return None

    try:
        # Rebuild comps from internal_grid
        print("[SYNC-OUT] Translating internal_grid to EDN comps...", flush=True)
        new_comps = internal_grid_to_edn_comps(internal_grid)
        print(f"[SYNC-OUT] EDN comps built: {len(new_comps)} entries", flush=True)
        raw_edn_grid[Keyword("comps")] = new_comps
    except Exception as e:
        print(f"[SYNC-OUT] ERROR translating internal_grid to EDN comps: {e}", flush=True)
        logger.error(f"grid_sync_agent_to_graphivac: Failed to build EDN comps: {e}")
        return None

    print(f"[SYNC-OUT] Attempting PUT with {n_components} components...", flush=True)
    logger.info(f"grid_sync_agent_to_graphivac: Rebuilding {n_components} components into EDN and PUTting to GraphyVAC")

    # Attempt PUT with one retry
    last_error = None
    for attempt in range(2):
        try:
            status, _ = await asyncio.to_thread(_put_grid_to_graphivac, raw_edn_grid)
            print(f"[SYNC-OUT] PUT successful (HTTP {status})", flush=True)
            logger.info("grid_sync_agent_to_graphivac: PUT successful")
            return None
        except Exception as e:
            last_error = e
            print(f"[SYNC-OUT] PUT attempt {attempt + 1} failed: {e}", flush=True)
            if attempt == 0:
                logger.warning(f"grid_sync_agent_to_graphivac: PUT failed (attempt 1), retrying: {e}")

    # Both attempts failed — return error Content to agent
    error_msg = (
        "SYNC ERROR: Failed to write grid to GraphyVAC after retry. "
        "Grid state is diverged. Stop all grid operations. "
        f"Last error: {last_error}"
    )
    print(f"[SYNC-OUT] UNRECOVERABLE: {error_msg}", flush=True)
    logger.warning(f"grid_sync_agent_to_graphivac: {error_msg}")
    return types.Content(
        parts=[types.Part(text=error_msg)]
    )
