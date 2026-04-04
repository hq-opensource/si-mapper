"""
BACnet helper utilities for SI-Mapper.

Provides helpers that convert raw BACnet address formats to flat numbered
entries and fully-formed URIs for storage in GraphyVAC custom_fields.
"""

import re

# ---------------------------------------------------------------------------
# BACnet object-type constants
# ---------------------------------------------------------------------------

BACNET_TYPE_MAP = {
    "AI": "analog-input",
    "AO": "analog-output",
    "AV": "analog-value",
    "BI": "binary-input",
    "BO": "binary-output",
    "BV": "binary-value",
    "SCH": "schedule",
}

# These address type codes are not mappable — skip them.
SKIP_TYPES = {"PG", "CO", "TL"}

# Component types that represent physical sensors (matches SENSOR_TYPES in
# internal_grid_tools.py — keep in sync).
SENSOR_COMPONENT_TYPES = {
    "duct_sensor_enthalpy", "duct_sensor_temperature",
    "duct_sensor_differential_pressure", "duct_sensor_humidity",
    "duct_sensor_flow", "duct_sensor_low_limit", "duct_sensor_static_pressure",
    "pipe_sensor_temperature",
}

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_ADDR_RE = re.compile(r"([A-Za-z]+)(\d+)")


def _parse_bacnet_address(raw: str, component_type: str) -> tuple:
    """
    Parse a raw BACnet address string into a (uri, ref_type) tuple.

    Returns (None, "skip") for addresses that are empty, malformed,
    belong to SKIP_TYPES, or use an unknown type code.

    Parameters
    ----------
    raw:            e.g. "2500.AI13"
    component_type: e.g. "duct_sensor_temperature"

    Returns
    -------
    (uri: str | None, ref_type: str)
    """
    if not raw or "." not in raw:
        return (None, "skip")
    device, obj = raw.split(".", 1)
    match = _ADDR_RE.fullmatch(obj)
    if not match:
        return (None, "skip")
    type_code, instance = match.group(1).upper(), match.group(2)
    if type_code in SKIP_TYPES:
        return (None, "skip")
    obj_type = BACNET_TYPE_MAP.get(type_code)
    if obj_type is None:
        return (None, "skip")
    uri = f"bacnet://{device}/{obj_type},{instance}/present-value"
    ref_type = "sensor" if component_type in SENSOR_COMPONENT_TYPES else "property"
    return (uri, ref_type)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enrich_bacnet_point(point: dict, component_type: str = "") -> dict:
    """
    Enrich a single BACnet point dict with URI, code, and ref_type.

    Does NOT mutate the input dict.

    Parameters
    ----------
    point:          Dict with at least an "address" key (raw address string).
    component_type: Component type string used to classify ref_type.

    Returns
    -------
    New dict with added/replaced keys: code, address (URI), ref_type.
    """
    raw = point.get("address", "")
    enriched = dict(point)
    enriched["code"] = raw
    uri, ref_type = _parse_bacnet_address(raw, component_type)
    enriched["address"] = uri
    enriched["ref_type"] = ref_type
    return enriched


def enrich_flat_bacnet_points(metadata: dict, component_type: str = "") -> dict:
    """
    Enrich all bacnet_N entries in a flat metadata dict in-place-copy.

    Only entries whose key starts with "bacnet_", are dicts, have an
    "address" field, and do NOT already have a "code" field are enriched.
    All other keys pass through unchanged.

    Idempotent: entries with "code" present are never re-processed.

    Parameters
    ----------
    metadata:       Flat dict of component metadata keys.
    component_type: Forwarded to enrich_bacnet_point for sensor classification.

    Returns
    -------
    New dict with enriched bacnet_N entries.
    """
    result = {}
    for key, val in metadata.items():
        if (
            key.startswith("bacnet_")
            and isinstance(val, dict)
            and "address" in val
            and "code" not in val
        ):
            result[key] = enrich_bacnet_point(val, component_type)
        else:
            result[key] = val
    return result


def explode_bacnet_points(metadata: dict, component_type: str = "") -> dict:
    """
    Convert nested bacnet dict format to flat numbered entries.

    Converts::

        {"bacnet": {"ADDR": {"name": ..., "unit": ...}}}

    into::

        {"bacnet_1": {"code": "ADDR", "address": <URI>, "ref_type": ..., "name": ..., "unit": ...}, ...}

    All other keys in metadata pass through unchanged.

    If metadata has no "bacnet" key, returns the original dict unchanged.

    Parameters
    ----------
    metadata:       Component metadata dict.
    component_type: Used for sensor/property classification (default "").
                    Existing callers that pass no argument receive ref_type="property"
                    for non-sensor default — backward compatible.
    """
    if "bacnet" not in metadata:
        return metadata
    result = {k: v for k, v in metadata.items() if k != "bacnet"}
    for i, (address, point) in enumerate(metadata["bacnet"].items(), start=1):
        raw_point = {"address": address, **point}
        result[f"bacnet_{i}"] = enrich_bacnet_point(raw_point, component_type)
    return result
