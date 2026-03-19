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

logger = logging.getLogger(__name__)


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
    headers = {"Content-Type": "application/edn"}
    data = edn_format.dumps(raw_edn_grid)
    response = requests.put(url, headers=headers, data=data, timeout=15)
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
    """
    Core sync-out logic: rebuild comps from internal_grid and PUT to GraphyVAC.
    Shared by both sync_agent_to_graphivac_callback (after_agent_callback, kept
    for backwards compat) and sync_agent_to_graphivac_model_callback.
    """
    internal_grid = callback_context.state.get("internal_grid", {"components": []})
    raw_edn_str = callback_context.state.get("_raw_edn_grid", "")

    if not raw_edn_str:
        logger.warning("grid_sync_agent_to_graphivac: No _raw_edn_grid in state — skipping PUT")
        return None

    try:
        raw_edn_grid = edn_to_mutable(edn_format.loads(raw_edn_str))
    except Exception as e:
        logger.error(f"grid_sync_agent_to_graphivac: Failed to parse _raw_edn_grid: {e}")
        return None

    try:
        new_comps = internal_grid_to_edn_comps(internal_grid)
        raw_edn_grid[Keyword("comps")] = new_comps
    except Exception as e:
        logger.error(f"grid_sync_agent_to_graphivac: Failed to build EDN comps: {e}")
        return None

    n = len(internal_grid.get("components", []))
    logger.info(f"grid_sync_agent_to_graphivac: Rebuilding {n} components into EDN and PUTting to GraphyVAC")

    last_error = None
    for attempt in range(2):
        try:
            status, _ = await asyncio.to_thread(_put_grid_to_graphivac, raw_edn_grid)
            logger.info(f"grid_sync_agent_to_graphivac: PUT successful (HTTP {status}), {n} components")
            return None
        except Exception as e:
            last_error = e
            if attempt == 0:
                logger.warning(f"grid_sync_agent_to_graphivac: PUT failed (attempt 1), retrying: {e}")

    error_msg = (
        "SYNC ERROR: Failed to write grid to GraphyVAC after retry. "
        "Grid state is diverged. Stop all grid operations. "
        f"Last error: {last_error}"
    )
    logger.warning(f"grid_sync_agent_to_graphivac: {error_msg}")
    return types.Content(parts=[types.Part(text=error_msg)])


async def sync_agent_to_graphivac_model_callback(
    callback_context: CallbackContext,
    llm_response: Any,
) -> Optional[Any]:
    """
    after_model_callback: Syncs internal_grid to GraphyVAC after the FINAL
    model response of each turn (the response with no function calls).

    This fires reliably inside the LLM flow regardless of how ag_ui_adk
    exits the runner.run_async() generator, unlike after_agent_callback
    which requires the generator to be fully consumed.

    Returns None to let the response pass through unchanged.
    """
    # Only sync on the final response — when the model is done calling tools.
    if _response_has_function_calls(llm_response):
        return None

    logger.debug("grid_sync_agent_to_graphivac: Final model response detected — triggering sync-out")
    error_content = await _run_sync_out(callback_context)

    # after_model_callback must return Optional[LlmResponse], not types.Content.
    # If sync failed, log the error but don't surface it as a model response —
    # returning None lets the agent's own response pass through.
    if error_content:
        logger.error(
            "grid_sync_agent_to_graphivac: Sync-out failed after final model response. "
            f"Error: {error_content.parts[0].text if error_content.parts else 'unknown'}"
        )
    return None


async def sync_agent_to_graphivac_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    after_agent_callback: kept for completeness but NOT the primary sync trigger.

    ag_ui_adk may exit runner.run_async() early, preventing this from firing.
    The primary sync is done in sync_agent_to_graphivac_model_callback.
    This is a fallback — if the generator IS fully consumed, it provides a
    second sync opportunity at the very end of the agent turn.
    """
    return await _run_sync_out(callback_context)
