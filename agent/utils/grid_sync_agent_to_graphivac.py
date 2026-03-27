"""
Sync Out: Push agent's internal_grid to Graphivac via a single REST PUT.

_run_sync_out is called from shared_model_callback (callback_utils.py) on
every final model response (no pending tool calls). It is not a standalone
ADK callback — it is embedded in the shared model callback so it runs before
that callback returns and short-circuits the ADK callback chain.
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

# Use the named app logger so messages appear regardless of root logger level
import importlib
try:
    _lc = importlib.import_module("utils.logging_config")
    logger = _lc.configure_logging()
except Exception:
    logger = logging.getLogger(__name__)


def _put_grid_to_graphivac(raw_edn_grid: dict, state=None) -> int:
    """Synchronous helper: PUTs the full grid EDN to Graphivac. Returns status code.

    state is forwarded from the callback context so this helper can apply the
    state-first pattern for project_id and grid_id (13-09).  Accepts any
    mapping (dict, ADK State, etc.); pass None to fall back to env vars only.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id   = os.getenv("GRAPHIVAC_ORG_ID", "")
    # State-first: prefer IDs injected by the frontend; fall back to env vars
    active_project = (state or {}).get("active_project") or {}
    active_system  = (state or {}).get("active_system") or {}
    project_id = active_project.get("graphivac_project_id") or os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = active_system.get("graphivac_grid_id")     or os.getenv("GRAPHIVAC_GRID_ID", "")

    url = f"{base_url}/api/v1/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    data = edn_format.dumps(raw_edn_grid)
    response = requests.put(url, headers={"Content-Type": "application/edn"}, data=data, timeout=15)
    response.raise_for_status()
    return response.status_code


async def _run_sync_out(callback_context: CallbackContext) -> Optional[types.Content]:
    """Core sync-out logic: rebuild comps from internal_grid and PUT to Graphivac."""
    if not callback_context.state.get("_updated_grid"):
        return None

    internal_grid = callback_context.state.get("internal_grid", {"components": []})
    raw_edn_str = callback_context.state.get("_raw_edn_grid", "")
    n = len(internal_grid.get("components", []))

    if not raw_edn_str:
        print("[SYNC-OUT] WARNING: _raw_edn_grid is empty — skipping PUT", flush=True)
        return None

    try:
        raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))
    except Exception as e:
        print(f"[SYNC-OUT] ERROR parsing _raw_edn_grid: {e}", flush=True)
        return None

    try:
        new_comps = internal_grid_to_edn_comps(internal_grid)
        raw_edn_grid[Keyword("comps")] = new_comps
    except Exception as e:
        print(f"[SYNC-OUT] ERROR building EDN comps: {e}", flush=True)
        return None

    last_error = None
    for attempt in range(2):
        try:
            status = await asyncio.to_thread(
                _put_grid_to_graphivac, raw_edn_grid, callback_context.state
            )
            callback_context.state["_updated_grid"] = False
            print(f"[SYNC-OUT] PUT {n} component(s) → HTTP {status}", flush=True)
            return None
        except Exception as e:
            last_error = e
            if attempt == 0:
                print(f"[SYNC-OUT] PUT attempt 1 failed, retrying: {e}", flush=True)

    error_msg = (
        "SYNC ERROR: Failed to write grid to Graphivac after retry. "
        "Grid state is diverged. Stop all grid operations. "
        f"Last error: {last_error}"
    )
    print(f"[SYNC-OUT] UNRECOVERABLE: {error_msg}", flush=True)
    return types.Content(parts=[types.Part(text=error_msg)])
