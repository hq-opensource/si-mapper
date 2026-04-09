"""
Metadata tools: write BACnet/control metadata to GraphyVAC component custom-fields.

These are ADK-native tools that write metadata directly to Graphivac.
They read the live grid, patch the target component's :custom-fields, and PUT it back — all
in a single transaction.
"""

import asyncio
import json
import os
from collections.abc import Mapping, Sequence
from typing import Any, Dict

import edn_format
import requests
from edn_format import Keyword
from google.adk.tools import ToolContext

from utils.edn_to_mutable import edn_to_mutable
from utils.bacnet_helpers import explode_bacnet_points, enrich_flat_bacnet_points


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _graphivac_url(tool_context=None) -> str:
    base_url   = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id     = os.getenv("GRAPHIVAC_ORG_ID", "")
    # State-first (13-09): prefer IDs injected by the frontend; fall back to env vars
    active_project = tool_context.state.get("active_project") or {} if tool_context else {}
    active_system  = tool_context.state.get("active_system")  or {} if tool_context else {}
    project_id = active_project.get("graphivac_project_id") or os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id    = active_system.get("graphivac_grid_id")     or os.getenv("GRAPHIVAC_GRID_ID", "")
    return f"{base_url}/api/v1/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"


def _get_grid_edn(tool_context=None) -> dict:
    """Fetch the full grid from GraphyVAC and return as a mutable Python dict."""
    response = requests.get(
        _graphivac_url(tool_context),
        headers={"Accept": "application/edn"},
        timeout=10,
    )
    response.raise_for_status()
    return edn_to_mutable(edn_format.loads(response.text))


def _put_grid_edn(mutable_grid: dict, tool_context=None) -> int:
    """PUT the full grid back to GraphyVAC. Returns HTTP status code."""
    response = requests.put(
        _graphivac_url(tool_context),
        headers={"Content-Type": "application/edn"},
        data=edn_format.dumps(mutable_grid),
        timeout=60,
    )
    response.raise_for_status()
    return response.status_code


# ── Name matching ──────────────────────────────────────────────────────────────

def _slug(name: Any) -> str:
    return str(name).lower().replace(" ", "_").replace("-", "_")


def _name_matches(grid_name: Any, target: str) -> bool:
    if not grid_name or not target:
        return False
    g, t = str(grid_name).strip(), str(target).strip()
    return g == t or g.lower() == t.lower() or _slug(g) == _slug(t)


def _extract_grid_name(key: Any, value: Any, k_obj: Keyword, k_name: Keyword) -> Any:
    """Extract the equipment name from a comp key/value pair."""
    if (
        isinstance(key, (tuple, list, Sequence))
        and not isinstance(key, (str, bytes))
        and len(key) > 1
        and key[0] == k_obj
    ):
        return key[1]
    if isinstance(value, (dict, Mapping)):
        return value.get(k_name)
    return None


# ── Metadata merge ─────────────────────────────────────────────────────────────

def _apply_metadata(value: dict, metadata: Dict[str, Any], k_cf: Keyword) -> None:
    """Merge new metadata into a component's :custom-fields in-place."""
    metadata = explode_bacnet_points(metadata)
    component_type = str(value.get(Keyword("type"), ""))
    metadata = enrich_flat_bacnet_points(metadata, component_type)
    current = value.get(k_cf, {})
    if not isinstance(current, dict):
        current = {}
    for raw_key, raw_val in metadata.items():
        clean_key = str(raw_key).strip("'\"")
        if isinstance(raw_val, (dict, list)):
            if isinstance(raw_val, dict):
                raw_val = {str(k).strip("'\""): v for k, v in raw_val.items()}
            raw_val = json.dumps(raw_val)
        current[clean_key] = raw_val
    value[k_cf] = current


# ── ADK Tools ─────────────────────────────────────────────────────────────────

async def write_metadata(
    tool_context: ToolContext,
    equipment_name: str,
    metadata: Dict[str, Any],
) -> str:
    """
    Writes metadata to a single equipment component on the GraphyVAC canvas.
    The metadata is merged into the component's custom-fields.

    Args:
        equipment_name: Unique name of the equipment on the grid (e.g. "AHU-1").
        metadata: Key-value pairs to store (e.g. {"bacnet": {"2500.AI11": {...}}}).
    """
    # Unwrap double-wrapping e.g. {"metadata": {...}}
    if len(metadata) == 1 and "metadata" in metadata and isinstance(metadata["metadata"], dict):
        metadata = metadata["metadata"]

    k_comps = Keyword("comps")
    k_obj   = Keyword("obj")
    k_name  = Keyword("name")
    k_cf    = Keyword("custom-fields")

    def action():
        mutable_grid = _get_grid_edn(tool_context)
        comps = mutable_grid.get(k_comps, {})
        for key, value in comps.items():
            grid_name = _extract_grid_name(key, value, k_obj, k_name)
            if _name_matches(grid_name, equipment_name):
                if not isinstance(value, dict):
                    raise ValueError(f"Component '{grid_name}' value is not a dict.")
                _apply_metadata(value, metadata, k_cf)
                _put_grid_edn(mutable_grid, tool_context)
                return str(grid_name)
        raise ValueError(f"Equipment '{equipment_name}' not found on the grid.")

    try:
        matched_name = await asyncio.to_thread(action)
        print(f"[METADATA] write_metadata: updated '{matched_name}'", flush=True)
        return f":::thought\n[System] Metadata written to '{matched_name}'.\n:::\n"
    except Exception as e:
        print(f"[METADATA] write_metadata ERROR: {e}", flush=True)
        return f":::thought\n[System] write_metadata failed: {e}\n:::\n"


async def write_metadata_batch(
    tool_context: ToolContext,
    updates: Dict[str, Dict[str, Any]],
) -> str:
    """
    Writes metadata to multiple equipment components in a single transaction.
    Reads the grid once, applies all updates, then writes it back once.

    Args:
        updates: Dict where each key is an equipment name and the value is its metadata dict.
                 Example: {
                   "AHU-1": {"bacnet": {"2500.AI11": {"name": "VITESSE RET.", "unit": "A"}}},
                   "VAV-101": {"bacnet": {"2501.BI3": {"name": "STATUT", "unit": ""}}}
                 }
    """
    # Unwrap double-wrapping e.g. {"updates": {...}}
    if len(updates) == 1 and "updates" in updates and isinstance(updates["updates"], dict):
        updates = updates["updates"]

    k_comps = Keyword("comps")
    k_obj   = Keyword("obj")
    k_name  = Keyword("name")
    k_cf    = Keyword("custom-fields")

    def action():
        mutable_grid = _get_grid_edn(tool_context)
        comps = mutable_grid.get(k_comps, {})

        slug_map = {_slug(k): k for k in updates}
        processed = 0

        for key, value in comps.items():
            grid_name = _extract_grid_name(key, value, k_obj, k_name)
            if not grid_name:
                continue
            g_str = str(grid_name)

            # Resolve: exact → case-insensitive → slug
            found_key = None
            if g_str in updates:
                found_key = g_str
            else:
                for k in updates:
                    if k.lower() == g_str.lower():
                        found_key = k
                        break
            if not found_key:
                found_key = slug_map.get(_slug(g_str))

            if found_key:
                if not isinstance(value, dict):
                    continue
                _apply_metadata(value, updates[found_key], k_cf)
                processed += 1

        _put_grid_edn(mutable_grid, tool_context)
        return processed

    try:
        n_total = len(updates)
        processed = await asyncio.to_thread(action)
        print(f"[METADATA] write_metadata_batch: {processed}/{n_total} updated", flush=True)
        return (
            f":::thought\n[System] write_metadata_batch: "
            f"{processed}/{n_total} components updated.\n:::\n"
        )
    except Exception as e:
        print(f"[METADATA] write_metadata_batch ERROR: {e}", flush=True)
        return f":::thought\n[System] write_metadata_batch failed: {e}\n:::\n"
