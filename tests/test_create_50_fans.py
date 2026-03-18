"""
test_create_50_fans.py
----------------------
Diagnostic test that replicates the mechanism an ADK agent uses when the LLM
decides to call multiple tools IN PARALLEL (i.e. it returns several tool calls
in a single response turn).

The ADK fires parallel tool calls via asyncio.gather – each call gets its own
independent MCP session so they are truly concurrent.  This test does exactly
the same:

  • 50 coroutines, each opening its own streamablehttp_client session and
    calling create_fan once.
  • All 50 coroutines are launched simultaneously with asyncio.gather().
  • Timing is measured per-call from fire to response.
  • After all creates complete, the grid is read via read_grid and verified
    to contain all 50 fans.

Usage
-----
    cd /home/juan/codes/si-mapper
    source agent/.venv/bin/activate
    python3 -m tests.test_create_50_fans

The MCP server must be running on port 8080 before executing this script.
"""

import asyncio
import json
import os
import sys
import time

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------------------------------------------------------
# ADK MCP client – same imports the agent stack uses internally
# ---------------------------------------------------------------------------
from google.adk.tools.mcp_tool.mcp_session_manager import streamablehttp_client
from mcp import ClientSession

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MCP_URL = "http://localhost:8080/mcp/"
TOTAL_FANS = 50

# fan1 → fan50 at coordinates (1,1) → (1,50)
FANS = [
    {"name": f"fan{i}", "coord": [1, i]}
    for i in range(1, TOTAL_FANS + 1)
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _fmt_result(result) -> str:
    texts = [c.text for c in result.content if hasattr(c, "text")]
    return " | ".join(texts) if texts else repr(result)


# ---------------------------------------------------------------------------
# Single-fan coroutine — opens its OWN session, fires call, returns record
# This is the unit of parallel work, mirroring how ADK dispatches parallel
# tool calls (each tool call gets its own session context).
# ---------------------------------------------------------------------------

async def _create_one_fan(idx: int, name: str, coord: list) -> dict:
    t_start = time.perf_counter()
    try:
        async with streamablehttp_client(url=MCP_URL, timeout=120.0) as (
            read, write, _get_id
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "create_fan",
                    arguments={"name": name, "coord": coord},
                )
        elapsed = time.perf_counter() - t_start
        ok = not result.isError
        status = _fmt_result(result) if ok else f"MCP_ERROR: {_fmt_result(result)}"
    except Exception as exc:
        elapsed = time.perf_counter() - t_start
        ok = False
        status = f"EXCEPTION: {exc}"

    return {
        "index": idx,
        "name": name,
        "coord": coord,
        "elapsed_s": round(elapsed, 4),
        "ok": ok,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Grid verification — reads the grid directly from the Graphivac API
# (bypasses MCP structured_content serialisation which is not forwarded
#  through the wire protocol by all client versions)
# ---------------------------------------------------------------------------

def _verify_grid_direct(expected_names: set) -> dict:
    """
    Read the grid state directly via the Graphivac HTTP API and verify
    that all expected fan names are present.
    """
    import requests
    import edn_format
    from edn_format import Keyword
    from dotenv import load_dotenv

    # Load credentials from mcp.env (same source the server uses)
    env_path = os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server", "mcp.env")
    load_dotenv(env_path)

    org_id    = os.getenv("GRAPHIVAC_ORG_ID")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID")
    grid_id   = os.getenv("GRAPHIVAC_GRID_ID")
    base_url  = os.getenv("GRAPHIVAC_BASE_URL")

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    response = requests.get(url, headers={"Accept": "application/edn"})
    response.raise_for_status()

    grid = edn_format.loads(response.text)
    comps = grid.get(Keyword("comps"), {})

    from edn_format.immutable_list import ImmutableList
    from collections.abc import Mapping as ABCMapping

    fans_on_grid = set()
    total_components = len(comps)

    for key, value in comps.items():
        if not (isinstance(key, (tuple, list, ImmutableList)) and len(key) == 2):
            continue
        obj_type_kw, obj_name = key
        obj_type = obj_type_kw.name if isinstance(obj_type_kw, Keyword) else str(obj_type_kw)
        if obj_type != "obj":
            continue
        symbol = value.get(Keyword("symbol")) if isinstance(value, ABCMapping) else None
        if symbol == "duct.fan":
            fans_on_grid.add(obj_name)

    found   = expected_names & fans_on_grid
    missing = expected_names - fans_on_grid

    return {
        "total_components": total_components,
        "fans_on_grid": len(fans_on_grid),
        "expected": len(expected_names),
        "found": len(found),
        "missing": sorted(missing),
        "ok": len(missing) == 0,
    }


async def _verify_grid(expected_names: set) -> dict:
    """Async wrapper that runs the direct API check in a thread."""
    print("\n  Reading grid directly from Graphivac API to verify persistence...", flush=True)
    try:
        return await asyncio.to_thread(_verify_grid_direct, expected_names)
    except Exception as exc:
        return {
            "total_components": 0,
            "fans_on_grid": 0,
            "expected": len(expected_names),
            "found": 0,
            "missing": sorted(expected_names),
            "ok": False,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Main test — fires all 50 coroutines at once with asyncio.gather
# ---------------------------------------------------------------------------

async def create_50_fans_parallel():
    print("=" * 70)
    print("TEST: create_50_fans  *** PARALLEL ***  via MCP Streamable-HTTP")
    print(f"  Target URL    : {MCP_URL}")
    print(f"  Total fans    : {TOTAL_FANS}")
    print(f"  Concurrency   : ALL {TOTAL_FANS} calls fired simultaneously")
    print("=" * 70)
    print(f"\nFiring {TOTAL_FANS} concurrent create_fan calls … ", flush=True)

    wall_start = time.perf_counter()

    # Build all coroutines
    tasks = [
        _create_one_fan(i, fan["name"], fan["coord"])
        for i, fan in enumerate(FANS, start=1)
    ]

    # Launch in parallel — return_exceptions=True so one failure doesn't
    # cancel the rest (same behaviour as ADK gather over tool calls)
    raw = await asyncio.gather(*tasks, return_exceptions=True)

    wall_elapsed = time.perf_counter() - wall_start

    # Normalise: gather may return Exception objects when return_exceptions=True
    results = []
    for i, item in enumerate(raw):
        if isinstance(item, Exception):
            results.append({
                "index": i + 1,
                "name": FANS[i]["name"],
                "coord": FANS[i]["coord"],
                "elapsed_s": None,
                "ok": False,
                "status": f"GATHER_EXCEPTION: {item}",
            })
        else:
            results.append(item)

    # Sort by index for readable output
    results.sort(key=lambda r: r["index"])

    # -----------------------------------------------------------------------
    # Per-call table
    # -----------------------------------------------------------------------
    print(f"\n{'#':>4}  {'Fan Name':<12}  {'Coord':<10}  {'Time (s)':>8}  Status")
    print("-" * 70)
    for r in results:
        mark = "✓" if r["ok"] else "✗"
        elapsed_str = f"{r['elapsed_s']:>8.4f}" if r["elapsed_s"] is not None else "     N/A"
        print(
            f"{r['index']:>4}  {r['name']:<12}  {str(r['coord']):<10}  "
            f"{elapsed_str}  {mark} {r['status']}"
        )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    total_ok   = sum(1 for r in results if r["ok"])
    total_fail = TOTAL_FANS - total_ok
    times      = [r["elapsed_s"] for r in results if r["elapsed_s"] is not None]
    avg_time   = sum(times) / len(times) if times else 0.0
    min_time   = min(times) if times else 0.0
    max_time   = max(times) if times else 0.0

    print("\n" + "=" * 70)
    print("CREATE SUMMARY")
    print("=" * 70)
    print(f"  Fans attempted    : {TOTAL_FANS}")
    print(f"  Succeeded         : {total_ok}   {'✓ ALL OK' if total_ok == TOTAL_FANS else '⚠ SOME FAILED'}")
    print(f"  Failed            : {total_fail}")
    print(f"")
    print(f"  Wall-clock total  : {wall_elapsed:.3f} s  (all calls in parallel)")
    print(f"  Per-call avg      : {avg_time:.4f} s")
    print(f"  Per-call min      : {min_time:.4f} s")
    print(f"  Per-call max      : {max_time:.4f} s")

    if total_fail > 0:
        print("\n  FAILED CALLS:")
        for r in results:
            if not r["ok"]:
                print(f"    #{r['index']:>2}  {r['name']}  →  {r['status']}")

    # -----------------------------------------------------------------------
    # Grid verification — read the final grid and check all 50 fans exist
    # -----------------------------------------------------------------------
    expected_names = {fan["name"] for fan in FANS}
    verification = await _verify_grid(expected_names)

    print("\n" + "=" * 70)
    print("GRID VERIFICATION")
    print("=" * 70)
    print(f"  Total components on grid : {verification['total_components']}")
    print(f"  Fans found on grid       : {verification['fans_on_grid']}")
    print(f"  Expected fans            : {verification['expected']}")
    print(f"  Matched                  : {verification['found']}")

    if verification["ok"]:
        print(f"\n  ✓ ALL {TOTAL_FANS} FANS VERIFIED ON THE GRID")
        test_passed = True
    else:
        missing = verification["missing"]
        print(f"\n  ✗ MISSING {len(missing)} FANS ON THE GRID:")
        for name in missing:
            print(f"      - {name}")
        if "error" in verification:
            print(f"  Error reading grid: {verification['error']}")
        test_passed = False

    # Write full results for deeper analysis
    out_path = os.path.join(os.path.dirname(__file__), "fan_creation_results_parallel.json")
    with open(out_path, "w") as fh:
        json.dump({"create_results": results, "verification": verification}, fh, indent=2)
    print(f"\n  Full results saved to: {out_path}")
    print("=" * 70)

    return results, verification, test_passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _, _, passed = asyncio.run(create_50_fans_parallel())
    sys.exit(0 if passed else 1)
