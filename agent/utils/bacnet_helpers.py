"""
BACnet helper utilities for SI-Mapper.

Provides the explode_bacnet_points helper that converts the nested bacnet
dict format to flat numbered entries for storage in GraphyVAC custom_fields.
"""


def explode_bacnet_points(metadata: dict) -> dict:
    """
    Converts {"bacnet": {"ADDR": {"name": ..., "unit": ...}}}
    into     {"bacnet_1": {"address": "ADDR", "name": ..., "unit": ...}, ...}
    All other keys in metadata pass through unchanged.

    If metadata has no "bacnet" key, returns the original dict unchanged.
    """
    if "bacnet" not in metadata:
        return metadata
    result = {k: v for k, v in metadata.items() if k != "bacnet"}
    for i, (address, point) in enumerate(metadata["bacnet"].items(), start=1):
        result[f"bacnet_{i}"] = {"address": address, **point}
    return result
