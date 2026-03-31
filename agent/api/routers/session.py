"""Session management routes.

GET    /session_info              — current active session info
GET    /session_state             — full agent state for polling
GET    /sessions                  — list sessions (filter by system_id)
DELETE /sessions/{session_id}     — delete a session
PATCH  /sessions/{session_id}     — rename a session

Session creation is handled by POST /workspace/state — which creates the
SQLite session with full context in a single operation.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .. import lifecycle
from ..lifecycle import (
    model_config,
    session_service,
)
from utils.callback_utils import GLOBAL_SESSION_STORE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["session"])

APP_NAME = "si_mapper"
USER_ID = "demo_user"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RenameSessionRequest(BaseModel):
    session_name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_session(session) -> dict:
    """Format an ADK Session object into a flat summary dict."""
    state = dict(session.state) if session.state else {}
    active_project = state.get("active_project") or {}
    active_system = state.get("active_system") or {}
    active_session_obj = state.get("active_session") or {}
    return {
        "session_id": session.id,
        "session_name": (
            active_session_obj.get("name")
            or state.get("session_name", "")
        ),
        "system_id": active_system.get("id", ""),
        "project_id": active_project.get("id", ""),
        "created_at": state.get("created_at", ""),
        "last_update_time": str(getattr(session, "last_update_time", "")),
    }


# ---------------------------------------------------------------------------
# Original polling routes
# ---------------------------------------------------------------------------

@router.get("/session_info")
async def get_session_info():
    """Expose the current session info to the frontend."""
    logger.debug(f"[/session_info] Returning session: {lifecycle.current_session_id}")
    return {
        "session_id": lifecycle.current_session_id,
        "session_name": lifecycle.current_session_name,
        "app_name": APP_NAME,
        "user_id": USER_ID,
    }


@router.get("/session_state")
async def get_session_state(
    request_session_id: str = None,
    app_name: str = APP_NAME,
    user_id: str = USER_ID,
):
    """Expose the full session state to the frontend."""
    target_session_id = request_session_id or lifecycle.current_session_id

    # 1. Try to load from SQLite via the shared session_service
    try:
        adk_session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=target_session_id,
        )
        base_state = dict(adk_session.state) if (adk_session and adk_session.state) else {}
    except Exception as exc:
        logger.warning(f"[/session_state] SQLite get_session failed: {exc}")
        base_state = {}

    # 2. Layer on real-time updates from GLOBAL_SESSION_STORE
    real_time_updates = (
        GLOBAL_SESSION_STORE.get(target_session_id) or GLOBAL_SESSION_STORE.get("latest")
    )
    if real_time_updates:
        base_state.update(real_time_updates)

    # 3. Inject runtime model name
    try:
        master_llm = lifecycle.holder.adk_agent.adk_agent.sub_agents[0]
        raw_model = master_llm.model
        active_model = raw_model.model if hasattr(raw_model, "model") else str(raw_model)
    except Exception:
        active_model = model_config.current

    base_state["active_model"] = active_model
    base_state["active_session_id"] = lifecycle.current_session_id
    # Inject session name — prefer real-time store, fall back to SQLite state
    base_state["active_session_name"] = (
        GLOBAL_SESSION_STORE.get(lifecycle.current_session_id, {}).get("session_name")
        or base_state.get("session_name", "")
        or lifecycle.current_session_name
    )

    logger.debug(
        f"[/session_state] Returning {len(base_state)} keys for session {target_session_id}"
    )
    return base_state


# ---------------------------------------------------------------------------
# Session management routes
# ---------------------------------------------------------------------------

@router.get("/sessions")
async def list_sessions(system_id: Optional[str] = None):
    """List all sessions, optionally filtered by system_id."""
    try:
        response = await session_service.list_sessions(
            app_name=APP_NAME,
            user_id=USER_ID,
        )
        sessions = response.sessions if response else []
    except Exception as exc:
        logger.error(f"[GET /sessions] list_sessions failed: {exc}")
        return []

    summaries = [_format_session(s) for s in sessions]
    if system_id:
        summaries = [s for s in summaries if s.get("system_id") == system_id]
    return summaries


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session from SQLite."""
    try:
        await session_service.delete_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
    except Exception as exc:
        logger.warning(f"[DELETE /sessions/{session_id}] delete_session error: {exc}")

    # Remove from GLOBAL_SESSION_STORE if present
    GLOBAL_SESSION_STORE.pop(session_id, None)
    if GLOBAL_SESSION_STORE.get("latest") is GLOBAL_SESSION_STORE.get(session_id):
        GLOBAL_SESSION_STORE.pop("latest", None)

    logger.info(f"[DELETE /sessions/{session_id}] Deleted.")
    return None  # 200 with empty body


@router.patch("/sessions/{session_id}")
async def rename_session(session_id: str, body: RenameSessionRequest):
    """Rename a session (update session_name in SQLite state)."""
    adk_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    if not adk_session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found.")

    from google.adk.events import Event, EventActions

    try:
        rename_event = Event(
            invocation_id=f"rename-{uuid.uuid4().hex[:8]}",
            author="user",
            actions=EventActions(state_delta={
                "session_name": body.session_name,
                "active_session": {"id": session_id, "name": body.session_name},
            }),
        )
        await session_service.append_event(session=adk_session, event=rename_event)
    except Exception as exc:
        logger.warning(f"[PATCH /sessions/{session_id}] append_event error: {exc}")

    # Update GLOBAL_SESSION_STORE if this is the live session
    if session_id in GLOBAL_SESSION_STORE:
        GLOBAL_SESSION_STORE[session_id]["session_name"] = body.session_name
        sess_obj = GLOBAL_SESSION_STORE[session_id].get("active_session") or {}
        GLOBAL_SESSION_STORE[session_id]["active_session"] = {**sess_obj, "name": body.session_name}
    if session_id == lifecycle.current_session_id:
        lifecycle.current_session_name = body.session_name

    logger.info(f"[PATCH /sessions/{session_id}] Renamed to {body.session_name!r}")
    return {"session_id": session_id, "session_name": body.session_name}
