"""
Grid synchronization: Pulls the live GraphyVAC grid into the agent's 
internal state (ToolContext.state["internal_grid"]) at the start of every turn.
"""

import asyncio
import logging
import os
import uuid
import json
import requests
from typing import Optional
from edn_format import Keyword
from edn_format.immutable_list import ImmutableList
import edn_format
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger(__name__)


def _fetch_and_parse_grid() -> dict:
    """
    Synchronous helper: fetches the current grid from GraphyVAC via REST and
    returns a dict ready to store as internal_grid.

    Returns {"components": [...]} on success or {"components": []} on any error.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    if not all([base_url, org_id, project_id, grid_id]):
        logger.warning("GraphyVAC env vars not fully set — internal_grid starts empty")
        return {"components": []}

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    try:
        response = requests.get(url, headers={"Accept": "application/edn"}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not reach GraphyVAC to seed grid: {e} — starting empty")
        return {"components": []}

    try:
        edn_data = edn_format.loads(response.text)
    except Exception as e:
        logger.warning(f"Could not parse grid EDN response: {e} — starting empty")
        return {"components": []}

    comps_map = edn_data.get(Keyword("comps"), {})
    components = []

    for key, value in comps_map.items():
        # Key format: (Keyword("duct"|"obj"), "component-name")
        if not (isinstance(key, (list, tuple, ImmutableList)) and len(key) == 2):
            continue

        obj_type_kw, obj_name = key
        obj_type = obj_type_kw.name if isinstance(obj_type_kw, Keyword) else str(obj_type_kw)
        comp_id = str(uuid.uuid4())[:8]

        if obj_type == "duct":
            n1 = value.get(Keyword("n1"), {})
            n2 = value.get(Keyword("n2"), {})
            pos1 = n1.get(Keyword("pos"), [0, 0])
            pos2 = n2.get(Keyword("pos"), [0, 0])
            components.append({
                "id": comp_id,
                "type": "duct",
                "name": obj_name,
                "start": list(pos1),
                "end": list(pos2),
            })

        elif obj_type == "obj":
            symbol = value.get(Keyword("symbol"))
            comp_type = symbol.name if isinstance(symbol, Keyword) else str(symbol)
            pos = value.get(Keyword("pos"), [0, 0])
            rotation = value.get(Keyword("rotation"), 0)

            comp: dict = {
                "id": comp_id,
                "type": comp_type,
                "name": obj_name,
                "coord": list(pos),
            }
            if comp_type in {"fan", "damper"}:
                comp["rotation"] = int(rotation) if rotation else 0
            components.append(comp)

    return {"components": components}


async def sync_graphivac_to_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    before_agent_callback: seeds internal_grid from the live GraphyVAC grid
    at the start of every agent turn.

    This ensures the agent always has the latest user modifications from the frontend.
    Also saves a snapshot to help diffing in the after_agent_callback.
    """
    try:
        grid = await asyncio.to_thread(_fetch_and_parse_grid)
        # 1. Update the active grid state (Source of Truth for Tools)
        callback_context.state["internal_grid"] = grid

        # 2. Save a snapshot for the 'after' sync diff (Initial State)
        callback_context.state["_initial_grid_snapshot"] = json.loads(json.dumps(grid))

        n = len(grid["components"])
        logger.info(f"grid_sync_graphivac_to_agent: Synchronized {n} components into agent memory")
    except Exception as e:
        logger.error(f"grid_sync_graphivac_to_agent: Sync failed, starting empty: {e}")
        if "internal_grid" not in callback_context.state:
            callback_context.state["internal_grid"] = {"components": []}

    return None
