"""Session introspection routes: GET /session_info, GET /session_state."""

import logging

from fastapi import APIRouter

from .. import lifecycle
from utils.callback_utils import GLOBAL_SESSION_STORE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["session"])


@router.get("/session_info")
async def get_session_info():
    """Expose the current session info to the frontend."""
    logger.debug(f"[/session_info] Returning session: {lifecycle.current_session_id}")
    return {
        "session_id": lifecycle.current_session_id,
        "app_name": "si_mapper",
        "user_id": "demo_user",
    }


@router.get("/session_state")
async def get_session_state(
    request_session_id: str = None,
    app_name: str = "si_mapper",
    user_id: str = "demo_user",
):
    """Expose the full session state to the frontend."""
    sm = lifecycle.holder.adk_agent._session_manager
    tracked_ids = [k.split(":")[-1] for k in sm._session_keys]

    target_session_id = request_session_id or lifecycle.current_session_id
    if target_session_id not in tracked_ids and tracked_ids:
        target_session_id = tracked_ids[0]

    # 1. Base state from ADK SessionManager
    state = await sm.get_session_state(
        session_id=target_session_id,
        app_name=app_name,
        user_id=user_id,
    )
    base_state = state or {}

    # 2. Layer on real-time updates from GLOBAL_SESSION_STORE
    # Fall back to "latest" in single-session demo mode
    real_time_updates = (
        GLOBAL_SESSION_STORE.get(target_session_id) or GLOBAL_SESSION_STORE.get("latest")
    )
    if real_time_updates:
        logger.debug(
            f"[/session_state] Merging real-time updates from Global Store for {target_session_id}"
        )
        base_state.update(real_time_updates)

    logger.debug(
        f"[/session_state] Returning {len(base_state)} keys for session {target_session_id}"
    )
    logger.debug(f"[/session_state] Available keys: {list(base_state.keys())}")

    equipment_keys = [
        k for k in base_state if k in ["detailed_equipment", "boilers", "fans", "pumps"]
    ]
    if equipment_keys:
        logger.debug(f"[/session_state] Found target equipment keys: {equipment_keys}")

    return base_state


