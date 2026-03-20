"""
Bidirectional EDN <-> internal_grid translator.

Converts between the Graphivac EDN comps dict format and the agent's
internal_grid components list format.

Public API:
    edn_comps_to_internal_grid(comps_map: dict) -> dict
    internal_grid_to_edn_comps(internal_grid: dict) -> dict
"""

import logging
from typing import Any, Dict, List

from edn_format import Keyword
from edn_format.immutable_list import ImmutableList

from tools.internal_grid_tools import (
    LINE_TYPES, ROTATION_TYPES, EQUIPMENT_TYPES, SENSOR_TYPES, COORD_TYPES
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bidirectional type mapping tables
# ---------------------------------------------------------------------------

SYMBOL_TO_AGENT: Dict[str, str] = {
    "duct.fan": "fan",
    "duct.damper": "damper",
    "duct.coil.cooling": "cooling_coil",
    "duct.coil.heating": "heating_coil",
    "duct.filter": "filter",
    "duct.thermal-wheel": "thermal_wheel",
    "duct.humidifier": "humidifier",
    "duct.sensor.enthalpy": "duct_sensor_enthalpy",
    "duct.sensor.temperature": "duct_sensor_temperature",
    "duct.sensor.pressure": "duct_sensor_differential_pressure",
    "duct.sensor.humidity": "duct_sensor_humidity",
    "duct.sensor.flow": "duct_sensor_flow",
    "duct.sensor.low-limit": "duct_sensor_low_limit",
    "duct.sensor.static-pressure": "duct_sensor_static_pressure",
    "pipe.boiler": "boiler",
    "pipe.heat-pump": "heat_pump",
    "pipe.pump": "pump",
    "pipe.valve.three-way": "valve_three_way",
    "pipe.valve.two-way": "valve_two_way",
    "pipe.sensor.temperature": "pipe_sensor_temperature",
    "electric.vfd": "variable_frequency_drive",
    "user.room.baseboard": "room_baseboard",
    "user.pipe.chiller": "pipe_chiller",
}

# Reverse mapping: agent type name -> EDN symbol string
AGENT_TO_SYMBOL: Dict[str, str] = {v: k for k, v in SYMBOL_TO_AGENT.items()}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def edn_comps_to_internal_grid(comps_map: dict) -> dict:
    """
    Convert a mutable EDN comps dict (already processed via edn_to_mutable)
    into the agent's internal_grid format.

    Args:
        comps_map: dict keyed by (Keyword, name_str) tuples, values are EDN
                   component dicts (already converted to plain Python dicts).

    Returns:
        {"components": [...]} where each component is a plain Python dict
        with 'type', 'name', and coordinate fields.
    """
    components: List[dict] = []

    for key, value in comps_map.items():
        # Keys must be a 2-element tuple/list: (Keyword, name)
        if not (isinstance(key, (list, tuple, ImmutableList)) and len(key) == 2):
            continue

        obj_type_kw = key[0]
        obj_name = key[1]
        obj_type = obj_type_kw.name if isinstance(obj_type_kw, Keyword) else str(obj_type_kw)

        if obj_type == "duct":
            n1 = value.get(Keyword("n1"), {})
            n2 = value.get(Keyword("n2"), {})
            pos1 = n1.get(Keyword("pos"), [0, 0])
            pos2 = n2.get(Keyword("pos"), [0, 0])
            components.append({
                "type": "duct",
                "name": obj_name,
                "start": list(pos1),
                "end": list(pos2),
            })

        elif obj_type == "pipe":
            n1 = value.get(Keyword("n1"), {})
            n2 = value.get(Keyword("n2"), {})
            pos1 = n1.get(Keyword("pos"), [0, 0])
            pos2 = n2.get(Keyword("pos"), [0, 0])
            components.append({
                "type": "pipe",
                "name": obj_name,
                "start": list(pos1),
                "end": list(pos2),
            })

        elif obj_type == "obj":
            sym = value.get(Keyword("symbol"))
            if sym is None:
                logger.warning(
                    f"EDN obj component '{obj_name}' has no symbol key — dropping"
                )
                continue

            symbol_str = sym.name if isinstance(sym, Keyword) else str(sym)
            agent_type = SYMBOL_TO_AGENT.get(symbol_str)

            if agent_type is None:
                logger.warning(
                    f"Unknown EDN symbol '{symbol_str}' for component '{obj_name}' — dropping"
                )
                continue

            pos = value.get(Keyword("pos"), [0, 0])
            component: dict = {
                "type": agent_type,
                "name": obj_name,
                "coord": list(pos),
            }

            # Rotation: use Keyword("rot") — the correct EDN key (bug fix: old code used wrong key)
            if agent_type in ROTATION_TYPES:
                rot = value.get(Keyword("rot"), 0)
                component["rotation"] = int(rot) if rot else 0

            components.append(component)

        else:
            # Unknown key type — skip silently
            continue

    return {"components": components}


def internal_grid_to_edn_comps(internal_grid: dict) -> dict:
    """
    Convert the agent's internal_grid format back to an EDN comps dict.

    Args:
        internal_grid: {"components": [...]} — the agent's internal grid state.

    Returns:
        A dict keyed by (Keyword, name) tuples, ready to be placed under
        Keyword("comps") in the full EDN grid dict for the REST PUT.
    """
    comps: dict = {}

    for comp in internal_grid.get("components", []):
        comp_type = comp.get("type", "")
        comp_name = comp.get("name", "")

        if comp_type in LINE_TYPES:
            # Line types: key = (Keyword(type), name)
            # Duct uses Keyword("duct"), pipe uses Keyword("pipe")
            key = (Keyword(comp_type), comp_name)
            value = {
                Keyword("n1"): {Keyword("pos"): comp.get("start", [0, 0])},
                Keyword("n2"): {Keyword("pos"): comp.get("end", [0, 0])},
            }
            comps[key] = value

        elif comp_type in COORD_TYPES:
            symbol = AGENT_TO_SYMBOL.get(comp_type)
            if symbol is None:
                logger.warning(
                    f"No EDN symbol mapping for agent type '{comp_type}' "
                    f"(component '{comp_name}') — skipping"
                )
                continue

            key = (Keyword("obj"), comp_name)
            value = {
                Keyword("symbol"): symbol,
                Keyword("name"): comp_name,
                Keyword("pos"): comp.get("coord", [0, 0]),
            }

            # Rotation: write Keyword("rot") only if non-zero
            if comp_type in ROTATION_TYPES and comp.get("rotation", 0) != 0:
                value[Keyword("rot")] = comp["rotation"]

            comps[key] = value

        else:
            logger.warning(
                f"Unknown component type '{comp_type}' for '{comp_name}' — skipping"
            )
            continue

    return comps
