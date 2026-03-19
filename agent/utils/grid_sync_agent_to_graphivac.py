"""
Sync Out: Push agent's internal_grid to GraphyVAC via a single REST PUT.

The sync is triggered from after_model_callback (not after_agent_callback).
Reason: ag_ui_adk can exit runner.run_async() early via early-return paths,
which causes the runner's generator to be abandoned (aclose()). The
after_agent_callback in base_agent.py is only called AFTER the generator
fully completes — so it never fires when ag_ui_adk exits early.

after_model_callback fires inside the LLM flow, before events are yielded,
so it's reliably called regardless of how ag_ui_adk exits. We guard it with
a "no function calls in response" check so the sync only happens on the
final model response of each turn (when the agent has finished all tool calls).
"""

import asyncio
import logging
import os
from typing import Optional, Any

import edn_format
import requests
from edn_format import Keyword
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from utils.edn_to_mutable import edn_to_mutable
from utils.grid_edn_translator import internal_grid_to_edn_comps

# Use the named app logger so messages appear regardless of root logger level
import importlib
try:
    _lc = importlib.import_module("utils.logging_config")
    logger = _lc.configure_logging()
except Exception:
    logger = logging.getLogger(__name__)


def _dbg(msg: str) -> None:
    """Print to stdout AND write to /tmp/sync_out.log — bypasses all log filtering."""
    print(f"[SYNC-OUT] {msg}", flush=True)
    try:
        import time
        with open("/tmp/sync_out.log", "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _put_grid_to_graphivac(raw_edn_grid: dict) -> tuple:
    """
    Synchronous helper: PUTs the full grid EDN to GraphyVAC.
    Returns (status_code, response_text) for logging.
    """
    base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
    org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
    project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"
    print(f"[SYNC-OUT] PUT → {url}", flush=True)
    headers = {"Content-Type": "application/edn"}
    data = edn_format.dumps(raw_edn_grid)
    response = requests.put(url, headers=headers, data=data, timeout=15)
    print(f"[SYNC-OUT] PUT ← {response.status_code} {response.text[:200]}", flush=True)
    response.raise_for_status()
    return response.status_code, response.text


def _response_has_function_calls(llm_response: Any) -> bool:
    """Returns True if the LLM response contains any function call parts."""
    content = getattr(llm_response, "content", None)
    if not content:
        return False
    parts = getattr(content, "parts", None) or []
    return any(getattr(p, "function_call", None) is not None for p in parts)


async def _run_sync_out(callback_context: CallbackContext) -> Optional[types.Content]:
    """Core sync-out logic: rebuild comps from internal_grid and PUT to GraphyVAC."""
    internal_grid = callback_context.state.get("internal_grid", {"components": []})
    raw_edn_str = callback_context.state.get("_raw_edn_grid", "")
    n = len(internal_grid.get("components", []))

    _dbg(f"_run_sync_out called — {n} components, _raw_edn_grid len={len(raw_edn_str) if isinstance(raw_edn_str, str) else type(raw_edn_str)}")

    if not raw_edn_str:
        _dbg("WARNING: _raw_edn_grid is empty — skipping PUT")
        return None

    try:
        raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))
        _dbg(f"EDN parsed OK, top-level keys: {[str(k) for k in raw_edn_grid.keys()]}")
    except Exception as e:
        _dbg(f"ERROR parsing _raw_edn_grid: {e}")
        return None

    try:
        new_comps = internal_grid_to_edn_comps(internal_grid)
        raw_edn_grid[Keyword("comps")] = new_comps
        _dbg(f"EDN comps built: {len(new_comps)} entries")
    except Exception as e:
        _dbg(f"ERROR building EDN comps: {e}")
        return None

    _dbg(f"Attempting PUT with {n} components...")

    last_error = None
    for attempt in range(2):
        try:
            status, _ = await asyncio.to_thread(_put_grid_to_graphivac, raw_edn_grid)
            _dbg(f"PUT successful (HTTP {status}), {n} components written to GraphyVAC")
            return None
        except Exception as e:
            last_error = e
            _dbg(f"PUT attempt {attempt + 1} failed: {e}")

    error_msg = (
        "SYNC ERROR: Failed to write grid to GraphyVAC after retry. "
        "Grid state is diverged. Stop all grid operations. "
        f"Last error: {last_error}"
    )
    _dbg(f"UNRECOVERABLE: {error_msg}")
    return types.Content(parts=[types.Part(text=error_msg)])


async def sync_agent_to_graphivac_model_callback(
    callback_context: CallbackContext,
    llm_response: Any,
) -> Optional[Any]:
    """
    after_model_callback: Syncs internal_grid to GraphyVAC after the FINAL
    model response of each turn (no function calls = agent is done with tools).
    """
    has_calls = _response_has_function_calls(llm_response)
    _dbg(f"model_callback fired — has_function_calls={has_calls}")

    if has_calls:
        return None

    _dbg("Final model response — triggering sync-out")
    error_content = await _run_sync_out(callback_context)
    if error_content:
        _dbg(f"Sync-out failed: {error_content.parts[0].text if error_content.parts else 'unknown'}")
    return None


async def sync_agent_to_graphivac_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    after_agent_callback: fallback path (may not fire if ag_ui_adk exits early).
    Primary sync is in sync_agent_to_graphivac_model_callback.
    """
    _dbg("after_agent_callback fired (fallback path)")
    return await _run_sync_out(callback_context)
