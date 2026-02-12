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
from mcp_server.graphivac.utils.grid_status import read_grid

logger = configure_logging()

class DuctManager:
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

    # --- DUCT ---

    def create_duct(self, name: str, start_coord: List[int], end_coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE DUCT: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_duct_key = (Keyword("duct"), name) 
            new_duct_value = {
                Keyword("n1"): {Keyword("pos"): start_coord},
                Keyword("n2"): {Keyword("pos"): end_coord}
            }

            mutable_grid[k_comps][new_duct_key] = new_duct_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_duct {name}", action)

    def create_ducts_batch(self, ducts: Dict[str, Any]) -> Dict[str, Any]:
        def action():
            logger.debug("--- STARTING CREATE DUCTS BATCH ---")
            
            # Extract the actual ducts dictionary if nested
            if "horizontal_ducts" in ducts:
                actual_ducts = ducts["horizontal_ducts"]
            elif "vertical_ducts" in ducts:
                actual_ducts = ducts["vertical_ducts"]
            else:
                actual_ducts = ducts
                
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            for name, data in actual_ducts.items():
                if not isinstance(data, dict):
                    continue
                start_coord = data.get("start")
                end_coord = data.get("end")
                if start_coord and end_coord:
                    new_duct_key = (Keyword("duct"), name) 
                    new_duct_value = {
                        Keyword("n1"): {Keyword("pos"): start_coord},
                        Keyword("n2"): {Keyword("pos"): end_coord}
                    }
                    mutable_grid[k_comps][new_duct_key] = new_duct_value
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution("create_ducts_batch", action)

    def delete_duct(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE DUCT: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            k_duct = Keyword("duct")
            k_name = Keyword("name")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)
            comps = mutable_grid[k_comps]
            keys_to_remove = []

            for key, value in comps.items():
                if isinstance(key, (tuple, list)) and len(key) > 0 and key[0] == k_duct:
                    is_match = False
                    if len(key) > 1 and key[1] == name:
                        is_match = True
                    elif isinstance(value, dict) and value.get(k_name) == name:
                        is_match = True
                    if is_match:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete duct named {name}. Duct not found.")
                # We could potentially raise an exception here to signal failure in status,
                # but valid execution with no-op is also "success" technically? 
                # User asked for "sucess/fail". If item not found, it wasn't deleted.
                # I'll raise an exception to indicate specific failure?
                # Or just let it return. If I return, tool_status is success.
                # The user said "sucess, fail". "Duct not found" sounds like a fail case for a delete operation?
                # For now I will NOT raise, so it shows success but grid remains same.
                # Actually, raising makes "fail: Duct not found" explicit in the status.
                raise Exception(f"Duct named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_duct {name}", action)

    # --- COOLING COIL ---

    def create_cooling_coil(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE COOLING COIL: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_coil_key = (Keyword("obj"), name)
            new_coil_value = {
                Keyword("symbol"): "duct.coil.cooling",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_coil_key] = new_coil_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_cooling_coil {name}", action)

    def delete_cooling_coil(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE COOLING COIL: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.coil.cooling"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete cooling coil named {name}. Coil not found.")
                raise Exception(f"Cooling coil named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_cooling_coil {name}", action)

    # --- HEATING COIL ---

    def create_heating_coil(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE HEATING COIL: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.coil.heating",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_heating_coil {name}", action)

    def delete_heating_coil(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE HEATING COIL: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.coil.heating"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete heating coil named {name}. Item not found.")
                raise Exception(f"Heating coil named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_heating_coil {name}", action)

    # --- FAN ---

    def create_fan(self, name: str, coord: List[int], rotation: int = 0) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE FAN: {name} rot={rotation} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.fan",
                Keyword("name"): name,
                Keyword("pos"): coord
            }
            if rotation != 0:
                new_value[Keyword("rot")] = rotation

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_fan {name}", action)

    def delete_fan(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE FAN: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.fan"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete fan named {name}. Item not found.")
                raise Exception(f"Fan named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_fan {name}", action)

    # --- FILTER ---

    def create_filter(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE FILTER: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.filter",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_filter {name}", action)

    def delete_filter(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE FILTER: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.filter"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete filter named {name}. Item not found.")
                raise Exception(f"Filter named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_filter {name}", action)

    # --- DAMPER ---

    def create_damper(self, name: str, coord: List[int], rotation: int = 0) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE DAMPER: {name} rot={rotation} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.damper",
                Keyword("name"): name,
                Keyword("pos"): coord
            }
            if rotation != 0:
                new_value[Keyword("rot")] = rotation

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_damper {name}", action)

    def delete_damper(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE DAMPER: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.damper"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete damper named {name}. Item not found.")
                raise Exception(f"Damper named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_damper {name}", action)

    # --- THERMAL WHEEL ---

    def create_thermal_wheel(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE THERMAL WHEEL: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.thermal-wheel",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_thermal_wheel {name}", action)

    def delete_thermal_wheel(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE THERMAL WHEEL: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.thermal-wheel"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete thermal wheel named {name}. Item not found.")
                raise Exception(f"Thermal wheel named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_thermal_wheel {name}", action)

    # --- HUMIDIFIER ---

    def create_humidifier(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE HUMIDIFIER: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.humidifier",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_humidifier {name}", action)

    def delete_humidifier(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE HUMIDIFIER: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.humidifier"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete humidifier named {name}. Item not found.")
                raise Exception(f"Humidifier named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_humidifier {name}", action)

    # --- SENSORS ---

    def create_sensor_enthalpy(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE ENTHALPY SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.enthalpy",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_enthalpy {name}", action)

    def delete_sensor_enthalpy(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE ENTHALPY SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.enthalpy"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete enthalpy sensor named {name}. Item not found.")
                raise Exception(f"Enthalpy sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_enthalpy {name}", action)

    def create_sensor_temperature(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE TEMPERATURE SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.temperature",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_temperature {name}", action)

    def delete_sensor_temperature(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE TEMPERATURE SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.temperature"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete temperature sensor named {name}. Item not found.")
                raise Exception(f"Temperature sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_temperature {name}", action)

    def create_sensor_differential_pressure(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE DIFFERENTIAL PRESSURE SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.pressure",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_differential_pressure {name}", action)

    def delete_sensor_differential_pressure(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE DIFFERENTIAL PRESSURE SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.pressure"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete differential pressure sensor named {name}. Item not found.")
                raise Exception(f"Differential pressure sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_differential_pressure {name}", action)

    def create_sensor_humidity(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE HUMIDITY SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.humidity",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_humidity {name}", action)

    def create_sensor_low_limit(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE LOW LIMIT SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.low-limit",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_low_limit {name}", action)

    def delete_sensor_low_limit(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE LOW LIMIT SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.low-limit"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete low limit sensor named {name}. Item not found.")
                raise Exception(f"Low limit sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_low_limit {name}", action)

    def delete_sensor_humidity(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE HUMIDITY SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.humidity"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete humidity sensor named {name}. Item not found.")
                raise Exception(f"Humidity sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_humidity {name}", action)

    def create_sensor_flow(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE FLOW SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.flow",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_flow {name}", action)

    def delete_sensor_flow(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE FLOW SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.flow"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete flow sensor named {name}. Item not found.")
                raise Exception(f"Flow sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_flow {name}", action)

    def create_sensor_static_pressure(self, name: str, coord: List[int]) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING CREATE STATIC PRESSURE SENSOR: {name} ---")
            immutable_grid = self.api.get_grid_info_edn()
            mutable_grid = edn_to_mutable(immutable_grid)
            k_comps = Keyword("comps")
            mutable_grid = self._ensure_comps_exists(mutable_grid, k_comps)

            new_key = (Keyword("obj"), name)
            new_value = {
                Keyword("symbol"): "duct.sensor.static-pressure",
                Keyword("name"): name,
                Keyword("pos"): coord
            }

            mutable_grid[k_comps][new_key] = new_value
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"create_sensor_static_pressure {name}", action)

    def delete_sensor_static_pressure(self, name: str) -> Dict[str, Any]:
        def action():
            logger.debug(f"--- STARTING DELETE STATIC PRESSURE SENSOR: {name} ---")
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
                    
                    is_correct_type = isinstance(value, dict) and value.get(Keyword("symbol")) == "duct.sensor.static-pressure"

                    if is_match and is_correct_type:
                        keys_to_remove.append(key)

            if not keys_to_remove:
                logger.warning(f"Impossible to delete static pressure sensor named {name}. Item not found.")
                raise Exception(f"Static pressure sensor named {name} not found.")

            for k in keys_to_remove:
                del comps[k]
            
            self.api.update_grid_edn(mutable_grid)

        return self._wrap_tool_execution(f"delete_sensor_static_pressure {name}", action)

