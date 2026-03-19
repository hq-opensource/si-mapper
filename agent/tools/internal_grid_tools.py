import uuid
import json
from typing import List, Optional
from google.adk.tools import ToolContext
from utils.logging_config import configure_logging

logger = configure_logging()

# ---------------------------------------------------------------------------
# Component type categories
# ---------------------------------------------------------------------------

LINE_TYPES = {"duct", "pipe"}  # Components with start/end coords

EQUIPMENT_TYPES = {
    "cooling_coil", "heating_coil", "fan", "filter", "damper",
    "thermal_wheel", "humidifier", "boiler", "heat_pump", "pump",
    "valve_three_way", "valve_two_way", "variable_frequency_drive",
    "room_baseboard", "pipe_chiller"
}

SENSOR_TYPES = {
    "duct_sensor_enthalpy", "duct_sensor_temperature",
    "duct_sensor_differential_pressure", "duct_sensor_humidity",
    "duct_sensor_flow", "duct_sensor_low_limit", "duct_sensor_static_pressure",
    "pipe_sensor_temperature"
}

COORD_TYPES = EQUIPMENT_TYPES | SENSOR_TYPES  # All single-coord types
ALL_TYPES = LINE_TYPES | COORD_TYPES
ROTATION_TYPES = {"fan", "damper"}  # Types that support rotation parameter


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ensure_internal_grid(tool_context: ToolContext) -> None:
    """Auto-initialize internal_grid if not present."""
    if "internal_grid" not in tool_context.state:
        tool_context.state["internal_grid"] = {"components": []}


# ---------------------------------------------------------------------------
# Public tools
# ---------------------------------------------------------------------------

def initialize_internal_grid(tool_context: ToolContext) -> str:
    """
    Initializes the internal grid state.

    If the internal grid already exists, returns an early message with the
    current component count. Otherwise creates an empty grid.

    Note: After initialization, the agent should call the read_grid MCP tool
    and then use add_component / add_components_batch to populate the state
    from the existing grid.
    """
    if "internal_grid" in tool_context.state:
        n = len(tool_context.state["internal_grid"].get("components", []))
        return f":::thought\n[System] Internal grid already initialized with {n} components.\n:::"

    tool_context.state["internal_grid"] = {"components": []}
    logger.info("Internal grid initialized (empty).")
    return ":::thought\n[System] Internal grid initialized (empty). Use read_grid MCP tool to load existing state if needed.\n:::"


def add_component(
    tool_context: ToolContext,
    component_type: str,
    name: str,
    coord: List[int] = None,
    start_coord: List[int] = None,
    end_coord: List[int] = None,
    rotation: int = 0,
) -> str:
    """
    Adds a single component to the internal grid state.

    Args:
        component_type: The type of component (e.g. 'duct', 'fan', 'duct_sensor_temperature').
        name: Unique name for the component.
        coord: [x, y] coordinate for equipment/sensor types.
        start_coord: [x, y] start coordinate for line types (duct/pipe).
        end_coord: [x, y] end coordinate for line types (duct/pipe).
        rotation: Rotation angle (only used for fan and damper types, default 0).
    """
    if component_type not in ALL_TYPES:
        return (
            f":::thought\n[System] Error: Unknown component type '{component_type}'. "
            f"Valid types: {sorted(ALL_TYPES)}\n:::"
        )

    # Validate coordinates based on type
    if component_type in LINE_TYPES:
        if start_coord is None or end_coord is None:
            return (
                f":::thought\n[System] Error: '{component_type}' requires both "
                f"start_coord and end_coord.\n:::"
            )
    else:  # COORD_TYPES
        if coord is None:
            return (
                f":::thought\n[System] Error: '{component_type}' requires a coord.\n:::"
            )

    # Auto-initialize if missing
    _ensure_internal_grid(tool_context)

    components = tool_context.state["internal_grid"]["components"]

    # Check for duplicate name
    for existing in components:
        if existing["name"] == name:
            return (
                f":::thought\n[System] Error: Component named '{name}' already exists "
                f"in the internal grid.\n:::"
            )

    # Build component dict
    component_id = str(uuid.uuid4())[:8]
    component: dict = {"id": component_id, "type": component_type, "name": name}

    if component_type in LINE_TYPES:
        component["start"] = start_coord
        component["end"] = end_coord
    else:
        component["coord"] = coord
        if component_type in ROTATION_TYPES:
            component["rotation"] = rotation

    components.append(component)
    tool_context.state["internal_grid"] = tool_context.state["internal_grid"]
    n = len(components)

    print(f"[GRID] ADD {component_type} '{name}' → internal_grid now has {n} component(s)", flush=True)
    logger.info(f"Added {component_type} '{name}' (id={component_id}) to internal grid. Total: {n}")
    return (
        f":::thought\n[System] Added {component_type} '{name}' (id={component_id}) "
        f"to internal grid. Total: {n} components.\n:::"
    )


def add_components_batch(
    tool_context: ToolContext,
    components_json: str,
) -> str:
    """
    Adds multiple components to the internal grid in a single batch operation.

    Args:
        components_json: JSON-encoded list of component dicts. Each dict must have:
            - 'type': component type string
            - 'name': unique name
            - For line types (duct/pipe): 'start_coord' and 'end_coord'
            - For equipment/sensor types: 'coord'
            - Optionally 'rotation' for fan/damper

    Example: '[{"type":"fan","name":"SF-1","coord":[5,5]},{"type":"duct","name":"D-1","start_coord":[0,0],"end_coord":[10,0]}]'
    """
    try:
        components = json.loads(components_json)
        if not isinstance(components, list):
            return ":::thought\n[System] Error: components_json must be a JSON array.\n:::"
    except json.JSONDecodeError as e:
        return f":::thought\n[System] Error: Invalid JSON in components_json: {e}\n:::"

    _ensure_internal_grid(tool_context)

    existing_components = tool_context.state["internal_grid"]["components"]
    existing_names = {c["name"] for c in existing_components}

    added = 0
    skipped = 0
    errors: List[str] = []

    for item in components:
        component_type = item.get("type", "")
        name = item.get("name", "")

        if component_type not in ALL_TYPES:
            errors.append(f"Unknown type '{component_type}' for '{name}' — skipped.")
            skipped += 1
            continue

        if not name:
            errors.append(f"Missing name for component of type '{component_type}' — skipped.")
            skipped += 1
            continue

        if name in existing_names:
            errors.append(f"Duplicate name '{name}' — skipped.")
            skipped += 1
            continue

        if component_type in LINE_TYPES:
            start_coord = item.get("start_coord")
            end_coord = item.get("end_coord")
            if start_coord is None or end_coord is None:
                errors.append(
                    f"'{name}' ({component_type}) missing start_coord or end_coord — skipped."
                )
                skipped += 1
                continue
            component_id = str(uuid.uuid4())[:8]
            component: dict = {
                "id": component_id,
                "type": component_type,
                "name": name,
                "start": start_coord,
                "end": end_coord,
            }
        else:
            coord = item.get("coord")
            if coord is None:
                errors.append(f"'{name}' ({component_type}) missing coord — skipped.")
                skipped += 1
                continue
            component_id = str(uuid.uuid4())[:8]
            component = {
                "id": component_id,
                "type": component_type,
                "name": name,
                "coord": coord,
            }
            if component_type in ROTATION_TYPES:
                component["rotation"] = item.get("rotation", 0)

        existing_components.append(component)
        existing_names.add(name)
        added += 1

    tool_context.state["internal_grid"] = tool_context.state["internal_grid"]
    n = len(existing_components)
    error_detail = " | ".join(errors) if errors else ""
    detail_part = f" Errors: {error_detail}" if error_detail else ""

    # Log a breakdown of what was actually added, grouped by type
    added_components = existing_components[-added:] if added > 0 else []
    type_counts: dict = {}
    for c in added_components:
        type_counts[c["type"]] = type_counts.get(c["type"], 0) + 1
    breakdown = ", ".join(f"{count}x {t}" for t, count in sorted(type_counts.items()))
    added_names = [c["name"] for c in added_components]
    print(
        f"[GRID] BATCH ADD {added} component(s) [{breakdown}]"
        f"{' | ' + str(skipped) + ' skipped' if skipped else ''}"
        f" → internal_grid now has {n} component(s)"
        f"\n       Names: {added_names}",
        flush=True,
    )
    logger.info(f"Batch add: {added} added [{breakdown}], {skipped} skipped. Total: {n}")
    return (
        f":::thought\n[System] Batch add: {added} added, {skipped} skipped. "
        f"Total: {n} components.{detail_part}\n:::"
    )


def delete_component(tool_context: ToolContext, name: str) -> str:
    """
    Deletes a single component from the internal grid by name.

    Args:
        name: The name of the component to delete.
    """
    if "internal_grid" not in tool_context.state:
        return ":::thought\n[System] Internal grid not initialized.\n:::"

    components = tool_context.state["internal_grid"]["components"]
    original_count = len(components)
    updated = [c for c in components if c["name"] != name]

    if len(updated) == original_count:
        return f":::thought\n[System] Error: Component '{name}' not found in internal grid.\n:::"

    tool_context.state["internal_grid"]["components"] = updated
    tool_context.state["internal_grid"] = tool_context.state["internal_grid"]
    n = len(updated)

    print(f"[GRID] DELETE '{name}' → internal_grid now has {n} component(s)", flush=True)
    logger.info(f"Deleted '{name}' from internal grid. Remaining: {n}")
    return f":::thought\n[System] Deleted '{name}' from internal grid. Remaining: {n} components.\n:::"


def delete_components_batch(tool_context: ToolContext, names: List[str]) -> str:
    """
    Deletes multiple components from the internal grid by name.

    Args:
        names: List of component names to delete.
    """
    if "internal_grid" not in tool_context.state:
        return ":::thought\n[System] Internal grid not initialized.\n:::"

    components = tool_context.state["internal_grid"]["components"]
    names_set = set(names)
    existing_names = {c["name"] for c in components}

    found = names_set & existing_names
    not_found = names_set - existing_names

    updated = [c for c in components if c["name"] not in found]
    tool_context.state["internal_grid"]["components"] = updated
    tool_context.state["internal_grid"] = tool_context.state["internal_grid"]

    n = len(updated)
    deleted = len(found)
    missing = len(not_found)

    detail = f" Not found: {sorted(not_found)}." if not_found else ""
    print(
        f"[GRID] BATCH DELETE {deleted} component(s) {sorted(found)}"
        f"{' | ' + str(missing) + ' not found' if missing else ''}"
        f" → internal_grid now has {n} component(s)",
        flush=True,
    )
    logger.info(f"Batch delete: {deleted} deleted, {missing} not found. Remaining: {n}")
    return (
        f":::thought\n[System] Batch delete: {deleted} deleted, {missing} not found. "
        f"Remaining: {n} components.{detail}\n:::"
    )


def read_internal_grid(
    tool_context: ToolContext,
    component_type: Optional[str] = None,
) -> str:
    """
    Returns the current internal grid state as a JSON string.

    Args:
        component_type: (Optional) If provided, filters components by this type.
    """
    if "internal_grid" not in tool_context.state:
        return ":::thought\n[System] Internal grid not initialized. Call initialize_internal_grid first.\n:::"

    components = tool_context.state["internal_grid"]["components"]

    if component_type:
        components = [c for c in components if c["type"] == component_type]

    n = len(components)
    data = json.dumps(components, indent=2)

    return f":::thought\n[System] Internal grid ({n} components): {data}\n:::"
