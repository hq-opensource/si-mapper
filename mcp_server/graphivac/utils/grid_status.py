from collections.abc import Mapping
from typing import Any, Dict, List
import logging

from edn_format import Keyword
from edn_format.immutable_list import ImmutableList

# Configure logging for this module
logger = logging.getLogger(__name__)

def _to_json_friendly(data: Any) -> Any:
    """
    Recursively converts EDN types to standard Python types for JSON serialization.
    Keywords are converted to strings without the leading colon.
    Dictionary keys are ensured to be strings.
    """
    if isinstance(data, Keyword):
        return data.name
    elif isinstance(data, Mapping):
        new_dict = {}
        for k, v in data.items():
            # Process key: first convert it recursively
            friendly_k = _to_json_friendly(k)
            # JSON keys must be strings. If we got a list/dict back, convert to str.
            if not isinstance(friendly_k, str):
                friendly_k = str(friendly_k)
            new_dict[friendly_k] = _to_json_friendly(v)
        return new_dict
    elif isinstance(data, (list, tuple)) and not isinstance(data, (str, bytes)):
        return [_to_json_friendly(i) for i in data]
    elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes, Mapping)):
        # Handle other iterables like ImmutableList
        return [_to_json_friendly(i) for i in data]
    else:
        return data

def read_grid(api_instance) -> List[Dict[str, Any]]:
    """
    Retrieves the current state of the grid via the provided API instance 
    and returns a simplified list of components.
    """
    logger.debug(f"--- STARTING READ GRID (Utility) ---")
    try:
        immutable_grid = api_instance.get_grid_info_edn()
        
        # Extract 'comps'
        comps = immutable_grid.get(Keyword("comps"), {})
        parsed_comps = []
        
        for key, value in comps.items():
            # Expected key format: (Keyword("type"), "Name")
            if not (isinstance(key, (list, tuple, ImmutableList)) and len(key) == 2):
                continue
                
            obj_type_kw, obj_name = key
            obj_type = obj_type_kw.name if isinstance(obj_type_kw, Keyword) else str(obj_type_kw)
            
            comp_data = {
                "name": obj_name
            }
            
            # Parse value based on type
            if obj_type == "duct":
                comp_data["type"] = "duct"
                # Extract 'n1' -> 'pos' and 'n2' -> 'pos'
                n1 = value.get(Keyword("n1"), {})
                n2 = value.get(Keyword("n2"), {})
                
                pos1 = n1.get(Keyword("pos"))
                pos2 = n2.get(Keyword("pos"))
                
                if pos1:
                    comp_data["start"] = _to_json_friendly(pos1)
                if pos2:
                    comp_data["end"] = _to_json_friendly(pos2)

            elif obj_type == "obj":
                # Extract 'pos' -> 'position'
                symbol = value.get(Keyword("symbol"))
                pos = value.get(Keyword("pos"))
                if pos:
                    comp_data["type"] = _to_json_friendly(symbol)
                    comp_data["position"] = _to_json_friendly(pos)
            
            # If neither (or default fallback), we could add more generic parsing here
            # For now, adhering to user request for 'duct' and 'obj' specific fields.
            
            parsed_comps.append(comp_data)
            
        return parsed_comps

    except Exception as e:
        logger.error(f"Error reading grid in utility: {e}")
        raise
