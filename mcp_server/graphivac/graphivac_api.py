from typing import Any, Dict, List

import edn_format
import requests
from mcp_server.utils.logging_config import configure_logging

logger = configure_logging()


class GraphivacAPI:
    def __init__(self, org_id: str, project_id: str, grid_id: str, grid_title:str, font_configs: Dict[str, Any], base_url: str):
        self.org_id = org_id
        self.project_id = project_id
        self.grid_id = grid_id
        self.grid_title = grid_title
        self.font_configs = font_configs
        self.base_url = base_url

    def get_grid_info_edn(self) -> Dict[str, Any]:
        """
        Retrieves information about a grid.

        Returns:
            dict: The text response from the API if successful, otherwise raises an exception.
        """
        endpoint = f"/api/v1/orgs/{self.org_id}/projects/{self.project_id}/grids/{self.grid_id}"
        url = f"{self.base_url}{endpoint}"
        headers = {"Accept": "application/edn"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return edn_format.loads(response.text)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving grid info: {e}")
            raise

    def update_grid_edn(self, grid: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates a specific grid.

        Args:
            title (str, optional): The new title of the grid. Defaults to None.
            description (str, optional): The new description of the grid. Defaults to None.
            font_configs (dict, optional): New font configuration for the grid. Defaults to None.

        Returns:
            dict: The text response from the API if successful, otherwise raises an exception.
        """
        endpoint = f"/api/v1/orgs/{self.org_id}/projects/{self.project_id}/grids/{self.grid_id}"
        url = f"{self.base_url}{endpoint}"

        headers = {"Content-Type": "application/edn"}
        try:
            data=edn_format.dumps(grid)
            response = requests.put(url, headers=headers, data=data)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating grid: {e}")
            raise

    def get_all_grids(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of grids for the initialized organization and project.

        Returns:
            dict: The JSON response from the API if successful, otherwise raises an exception.
        """
        endpoint = f"/api/v1/orgs/{self.org_id}/projects/{self.project_id}/grids"
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving grids: {e}")
            raise
