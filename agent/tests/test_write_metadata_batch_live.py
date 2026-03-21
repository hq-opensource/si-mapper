"""
Live integration test for write_metadata_batch.

Reads the real GraphyVAC grid, writes BACnet point metadata to the first
available equipment, then verifies the data was persisted correctly.

Usage (from the agent/ directory):
    uv run python tests/test_write_metadata_batch_live.py

What it tests:
  [1] GET grid — can reach GraphyVAC and parse EDN
  [2] write_metadata_batch — writes BACnet points to real equipment
  [3] GET grid again — verifies the metadata was actually persisted
  [4] Timing breakdown for each step
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Allow imports from agent/
sys.path.insert(0, str(Path(__file__).parent.parent))

# Sample BACnet points — mimics what the skill would extract from the CSV
SAMPLE_BACNET_POINTS = {
    "2500.AI11": {"name": "VITESSE RET. No.1A", "unit": "Amperes"},
    "2500.AI13": {"name": "TEMP. ALIM. No.1A", "unit": "Celsius"},
    "2500.BI3":  {"name": "STATUT DIG. 1A", "unit": ""},
    "2500.BO1":  {"name": "A/D VENT. 1A", "unit": ""},
    "2500.AO5":  {"name": "MOD. VFD 1A", "unit": "%"},
}


def _fmt(seconds: float) -> str:
    return f"{seconds:.3f}s"


def _get_grid_names(comps: dict) -> list[str]:
    """Extract all equipment names from the comps dict."""
    from edn_format import Keyword
    k_obj  = Keyword("obj")
    k_name = Keyword("name")
    names = []
    for key, value in comps.items():
        if (
            isinstance(key, (tuple, list))
            and len(key) > 1
            and key[0] == k_obj
        ):
            names.append(str(key[1]))
        elif isinstance(value, dict) and k_name in value:
            names.append(str(value[k_name]))
    return names


def _read_custom_fields(comps: dict, target_name: str) -> dict | None:
    """Return the :custom-fields dict for the named equipment, or None."""
    from edn_format import Keyword
    k_obj = Keyword("obj")
    k_cf  = Keyword("custom-fields")
    for key, value in comps.items():
        grid_name = None
        if isinstance(key, (tuple, list)) and len(key) > 1 and key[0] == k_obj:
            grid_name = str(key[1])
        if grid_name == target_name and isinstance(value, dict):
            return value.get(k_cf)
    return None


async def run():
    from tools.metadata_tools import _get_grid_edn, write_metadata_batch
    from edn_format import Keyword

    k_comps = Keyword("comps")

    print("\n── Live test: write_metadata_batch ─────────────────────────────────\n")

    # ── Step 1: GET grid ─────────────────────────────────────────────────────
    print("[1/3] Fetching grid from GraphyVAC...")
    t0 = time.perf_counter()
    try:
        grid = _get_grid_edn()
    except Exception as e:
        print(f"  ✗ Failed to fetch grid: {e}")
        return
    t1 = time.perf_counter()
    comps = grid.get(k_comps, {})
    names = _get_grid_names(comps)
    print(f"  ✓ Grid fetched in {_fmt(t1 - t0)} — {len(names)} components found")
    if not names:
        print("  ✗ No equipment on the grid — cannot run test")
        return
    print(f"  Equipment: {names}")

    # Pick the first equipment for the test
    target = names[0]
    print(f"\n  → Testing against: '{target}'")

    # ── Step 2: write_metadata_batch ─────────────────────────────────────────
    print("\n[2/3] Calling write_metadata_batch with sample BACnet points...")
    updates = {target: {"bacnet": SAMPLE_BACNET_POINTS}}
    t2 = time.perf_counter()
    mock_ctx = type("TC", (), {})()  # write_metadata_batch only uses tool_context for logging
    result = await write_metadata_batch(tool_context=mock_ctx, updates=updates)
    t3 = time.perf_counter()
    print(f"  Tool returned in {_fmt(t3 - t2)}")
    print(f"  Result: {result.strip()}")

    if "failed" in result.lower():
        print("  ✗ write_metadata_batch reported a failure — check output above")
        return

    # ── Step 3: verify persistence ───────────────────────────────────────────
    print("\n[3/3] Re-fetching grid to verify metadata was persisted...")
    t4 = time.perf_counter()
    try:
        grid2 = _get_grid_edn()
    except Exception as e:
        print(f"  ✗ Failed to re-fetch grid: {e}")
        return
    t5 = time.perf_counter()
    print(f"  ✓ Grid re-fetched in {_fmt(t5 - t4)}")

    comps2 = grid2.get(k_comps, {})
    cf = _read_custom_fields(comps2, target)

    if cf is None:
        print(f"  ✗ Could not find :custom-fields for '{target}'")
        return

    bacnet_raw = cf.get("bacnet")
    if bacnet_raw is None:
        print(f"  ✗ 'bacnet' key missing from :custom-fields of '{target}'")
        print(f"  Custom-fields content: {cf}")
        return

    # The value is stored as a JSON string
    if isinstance(bacnet_raw, str):
        bacnet_data = json.loads(bacnet_raw)
    else:
        bacnet_data = bacnet_raw

    errors = []
    for point_id, expected in SAMPLE_BACNET_POINTS.items():
        if point_id not in bacnet_data:
            errors.append(f"  ✗ Missing point: {point_id}")
        else:
            stored = bacnet_data[point_id]
            if stored.get("name") != expected["name"]:
                errors.append(f"  ✗ {point_id} name mismatch: got '{stored.get('name')}', expected '{expected['name']}'")
            if stored.get("unit") != expected["unit"]:
                errors.append(f"  ✗ {point_id} unit mismatch: got '{stored.get('unit')}', expected '{expected['unit']}'")

    total = time.perf_counter() - t0

    print(f"""
┌──────────────────────────────────────────────────────────────────┐
│  RESULTS                                                         │
├──────────────────────────────────────────────────────────────────┤
│  Equipment tested : {target:<44} │
│  Points written   : {len(SAMPLE_BACNET_POINTS):<44} │
│  Points verified  : {len(SAMPLE_BACNET_POINTS) - len(errors):<44} │
│  Total time       : {_fmt(total):<44} │
└──────────────────────────────────────────────────────────────────┘""")

    if errors:
        print("\n  FAILURES:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("\n  ✓ All BACnet points written and verified successfully.")
        print(f"  ✓ write_metadata_batch is working correctly.")


if __name__ == "__main__":
    asyncio.run(run())
