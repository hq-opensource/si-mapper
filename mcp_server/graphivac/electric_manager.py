
import os
import sys
import re
from typing import Any, Dict, List, Callable

from edn_format import Keyword

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.graphivac_api import GraphivacAPI #noqa
from mcp_server.graphivac.utils.edn_to_mutable import edn_to_mutable #noqa
from mcp_server.graphivac.utils.logging_config import configure_logging #noqa

logger = configure_logging()

class ElectricManager:
    def __init__(self, org_id: str, project_id: str, grid_id: str, grid_title: str, font_configs: Dict[str, Any], base_url: str):
        self.api = GraphivacAPI(org_id, project_id, grid_id, grid_title, font_configs, base_url)

    def _ensure_comps_exists(self, mutable_grid: Dict[Keyword, Any], k_comps: Keyword) -> Dict[Keyword, Any]:
        # Check if comps exists and is mutable
        if k_comps in mutable_grid:
            pass # It exists
        else:
            logger.debug("'comps' keyword not found. Initializing empty comps map.")
            mutable_grid[k_comps] = {}
        return mutable_grid

    def _wrap_tool_execution(self, tool_name: str, action: Callable[[], Any]) -> Dict[str, Any]:
        tool_status = "success"
        try:
            logger.debug(f"Executing action for {tool_name}")
            action()
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            tool_status = f"fail: {str(e)}"
        
        return {"tool_status": tool_status}

    # --- VFD ---

    def create_variable_frequency_drive(self, name: str, coord: List[int]) -> Dict[str, Any]:
        """Creates a Variable Frequency Drive (VFD)."""
        def action():
            logger.debug(f"--- STARTING CREATE VFD: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "electric.vfd",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_variable_frequency_drive {name}", action)

    def delete_variable_frequency_drive(self, name: str) -> Dict[str, Any]:
        """Deletes a VFD by name."""
        def action():
            logger.debug(f"--- STARTING DELETE VFD: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "electric.vfd"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete VFD named {name}. Item not found.")
                raise Exception(f"VFD named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_variable_frequency_drive {name}", action)
