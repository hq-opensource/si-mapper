import os
import sys
import asyncio
from typing import Any, Dict, List, Callable

from edn_format import Keyword

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.graphivac_api import GraphivacAPI # noqa
from mcp_server.graphivac.utils.edn_to_mutable import edn_to_mutable # noqa
from mcp_server.graphivac.utils.logging_config import configure_logging # noqa
from mcp_server.graphivac.utils.grid_status import read_grid as read_grid_util

logger = configure_logging()

class CustomManager:
    def __init__(self, org_id: str, project_id: str, grid_id: str, grid_title: str, font_configs: Dict[str, Any], base_url: str):
        self.api = GraphivacAPI(org_id, project_id, grid_id, grid_title, font_configs, base_url)
        self.lock = asyncio.Lock()

    def _ensure_comps_exists(self, mutable_grid: Dict[Keyword, Any], k_comps: Keyword) -> Dict[Keyword, Any]:
        # Check if comps exists and is mutable
        if k_comps in mutable_grid:
            pass # It exists
        else:
            logger.debug("'comps' keyword not found. Initializing empty comps map.")
            mutable_grid[k_comps] = {}
        return mutable_grid

    async def _wrap_tool_execution(self, tool_name: str, action: Callable[[], Any]) -> Dict[str, Any]:
        """
        Wraps a tool action to return a structured response with status and grid states.
        """
        response = {
            "tool_status": "success",
            "grid_before": [],
            "grid_after": []
        }

        try:
            # 1. Capture Grid Before (read-only, outside lock)
            try:
                response["grid_before"] = read_grid_util(self.api)
            except Exception as e:
                logger.error(f"Error reading grid BEFORE {tool_name}: {e}")

            # 2. Execute Action (serialized with lock, non-blocking)
            async with self.lock:
                await asyncio.to_thread(action)

            # 3. Capture Grid After (read-only, outside lock)
            try:
                response["grid_after"] = read_grid_util(self.api)
            except Exception as e:
                logger.error(f"Error reading grid AFTER {tool_name}: {e}")

        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            response["tool_status"] = f"fail: {str(e)}"
            try:
                response["grid_after"] = read_grid_util(self.api)
            except:
                pass

        return response

    # --- ROOM BASEBOARD ---

    async def create_room_baseboard(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE ROOM BASEBOARD: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "user.room.baseboard",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return await self._wrap_tool_execution(f"create_room_baseboard {name}", action)

    async def delete_room_baseboard(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE ROOM BASEBOARD: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            k_obj = Keyword("obj")
            k_name = Keyword("name")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)
            comps = mutable_grid[k_comps]
            keys_to_remove = []

            for key, value in comps.items():
                if isinstance(key, (tuple, list)) and len(key) > 0 and key[0] == k_obj:
                    is_match = False
                    if len(key) > 1 and key[1] == name:
                        is_match = True
                    elif isinstance(value, dict) and value.get(k_name) == name:
                        is_match = True

                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "user.room.baseboard"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete room baseboard named {name}. Item not found.")
                raise Exception(f"Room Baseboard named {name} not found.")

            for k in keys_to_remove:
                del comps[k]

            self.api.update_grid_edn(mutable_grid)

        return await self._wrap_tool_execution(f"delete_room_baseboard {name}", action)

    # --- PIPE CHILLER ---

    async def create_pipe_chiller(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE PIPE CHILLER: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "user.pipe.chiller",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return await self._wrap_tool_execution(f"create_pipe_chiller {name}", action)

    async def delete_pipe_chiller(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE PIPE CHILLER: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            k_obj = Keyword("obj")
            k_name = Keyword("name")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)
            comps = mutable_grid[k_comps]
            keys_to_remove = []

            for key, value in comps.items():
                if isinstance(key, (tuple, list)) and len(key) > 0 and key[0] == k_obj:
                    is_match = False
                    if len(key) > 1 and key[1] == name:
                        is_match = True
                    elif isinstance(value, dict) and value.get(k_name) == name:
                        is_match = True

                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "user.pipe.chiller"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete pipe chiller named {name}. Item not found.")
                raise Exception(f"Pipe Chiller named {name} not found.")

            for k in keys_to_remove:
                del comps[k]

            self.api.update_grid_edn(mutable_grid)

        return await self._wrap_tool_execution(f"delete_pipe_chiller {name}", action)
