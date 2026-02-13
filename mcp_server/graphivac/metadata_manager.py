import os
import sys
import json
from typing import Any, Dict, List, Callable
from collections.abc import Mapping, Sequence

from edn_format import Keyword
from edn_format.immutable_list import ImmutableList

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.graphivac_api import GraphivacAPI
from mcp_server.graphivac.utils.edn_to_mutable import edn_to_mutable
from mcp_server.graphivac.utils.logging_config import configure_logging
from mcp_server.graphivac.utils.grid_status import read_grid as read_grid_util

logger = configure_logging()

class MetadataManager:
    def __init__(self, org_id: str, project_id: str, grid_id: str, grid_title: str, font_configs: Dict[str, Any], base_url: str):
        self.api = GraphivacAPI(org_id, project_id, grid_id, grid_title, font_configs, base_url)

    def _ensure_comps_exists(self, mutable_grid: Dict[Keyword, Any], k_comps: Keyword) -> Dict[Keyword, Any]:
        if k_comps not in mutable_grid:
            logger.debug("'comps' keyword not found. Initializing empty comps map.")
            mutable_grid[k_comps] = {}
        return mutable_grid

    def _wrap_tool_execution(self, tool_name: str, action: Callable[[], Any]) -> Dict[str, Any]:
        response = {
            "tool_status": "success",
            "grid_before": [],
            "grid_after": []
        }
        
        try:
            try:
                response["grid_before"] = read_grid_util(self.api)
            except Exception as e:
                logger.error(f"Error reading grid BEFORE {tool_name}: {e}")

            action()

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

    def _is_match(self, key, value, equipment_name, k_obj, k_name):
        """Helper to match equipment by name or ID in the complex EDN key/value structure."""
        if isinstance(key, (tuple, list, ImmutableList, Sequence)) and not isinstance(key, (str, bytes)):
            if len(key) > 0 and key[0] == k_obj:
                if len(key) > 1 and key[1] == equipment_name:
                    return True
        
        if isinstance(value, (dict, Mapping)) and value.get(k_name) == equipment_name:
            return True
            
        return False

    def write_metadata(self, equipment_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING WRITE METADATA TO: {equipment_name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            k_obj = Keyword("obj")
            k_name = Keyword("name")
            k_custom_fields = Keyword("custom-fields")
            
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)
            comps = mutable_grid[k_comps]
            
            found = False
            for key, value in comps.items():
                if self._is_match(key, value, equipment_name, k_obj, k_name):
                    if not isinstance(value, dict):
                        logger.warning(f"Component {equipment_name} is not a dictionary. Cannot write metadata.")
                        continue
                    
                    # Custom fields are stored as a map in EDN, which edn_to_mutable converts to a dict
                    current_metadata = value.get(k_custom_fields, {})
                    if not isinstance(current_metadata, dict):
                        logger.warning(f"Existing :custom-fields for {equipment_name} is not a dict. Resetting.")
                        current_metadata = {}
                    
                    # Merge new metadata (ensure keys/values are strings if needed, but EDN supports many types)
                    # For consistency with user's example, we'll keep them as they are passed
                    current_metadata.update(metadata)
                    
                    value[k_custom_fields] = current_metadata
                    found = True
                    break
            
            if not found:
                raise Exception(f"Equipment named '{equipment_name}' not found on the grid.")

            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"write_metadata {equipment_name}", action)

    def read_metadata(self, equipment_name: str) -> Dict[str, Any]:
        logger.debug(f"--- STARTING READ METADATA FOR: {equipment_name} ---")
        immutable_grid = self.api.get_grid_info_edn()
        k_comps = Keyword("comps")
        k_obj = Keyword("obj")
        k_name = Keyword("name")
        k_custom_fields = Keyword("custom-fields")
        
        comps = immutable_grid.get(k_comps, {})
        
        for key, value in comps.items():
            if self._is_match(key, value, equipment_name, k_obj, k_name):
                # value is likely an ImmutableMap here
                cf = value.get(k_custom_fields, {})
                # Use edn_to_mutable to ensure we return a clean Python dict
                from mcp_server.graphivac.utils.edn_to_mutable import edn_to_mutable
                return edn_to_mutable(cf)
        
        raise Exception(f"Equipment named '{equipment_name}' not found on the grid.")

    def delete_metadata(self, equipment_name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE METADATA FOR: {equipment_name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            k_obj = Keyword("obj")
            k_name = Keyword("name")
            k_custom_fields = Keyword("custom-fields")
            
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)
            comps = mutable_grid[k_comps]
            
            found = False
            for key, value in comps.items():
                if self._is_match(key, value, equipment_name, k_obj, k_name):
                    if k_custom_fields in value:
                        del value[k_custom_fields]
                    found = True
                    break
            
            if not found:
                raise Exception(f"Equipment named '{equipment_name}' not found on the grid.")

            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_metadata {equipment_name}", action)
