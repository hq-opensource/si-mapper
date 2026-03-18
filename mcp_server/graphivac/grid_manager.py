import os
import sys
import asyncio
from typing import Any, Dict, List
from collections.abc import Mapping

import edn_format
from edn_format import Keyword

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.graphivac_api import GraphivacAPI
from mcp_server.graphivac.utils.edn_to_mutable import edn_to_mutable
from mcp_server.graphivac.utils.logging_config import configure_logging
from mcp_server.graphivac.utils.grid_status import read_grid as read_grid_util

logger = configure_logging()

class GridManager:
    def __init__(self, org_id: str, project_id: str, grid_id: str, grid_title: str, font_configs: Dict[str, Any], base_url: str):
        self.api = GraphivacAPI(org_id, project_id, grid_id, grid_title, font_configs, base_url)
        self.lock = asyncio.Lock()

    async def read_grid(self) -> List[Dict[str, Any]]:
        """
        Retrieves the current state of the grid and returns a simplified list of components.
        """
        comps = await asyncio.to_thread(read_grid_util, self.api)
        logger.info(f"GridManager: read_grid retrieved {len(comps)} components")
        return comps

    async def delete_grid(self) -> Dict[str, Any]:
        """
        Deletes the current grid content by removing 'comps'.
        """
        def action():
            logger.debug(f"--- STARTING DELETE GRID ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)

            # Remove "comps" object
            mutable_grid.pop(Keyword("comps"), None)

            # Send updated grid
            return self.api.update_grid_edn(mutable_grid)

        async with self.lock:
            result = await asyncio.to_thread(action)
        return result
