"""Session management routes (13-11).

GET    /session_info              — current active session info
GET    /session_state             — full agent state for polling
GET    /sessions                  — list sessions (filter by system_id)
POST   /sessions                  — create a new named session
POST   /sessions/{session_id}/restore — restore (make active) a saved session
DELETE /sessions/{session_id}     — delete a session
PATCH  /sessions/{session_id}     — rename a session
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .. import lifecycle
from ..lifecycle import (
    bootstrap_session,
    model_config,
    rebuild_agent,
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

class CreateSessionRequest(BaseModel):
    session_name: str = ""
    system_id: str = ""
    project_id: str = ""


class RenameSessionRequest(BaseModel):
    session_name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_session(session) -> dict:
    """Format an ADK Session object into a flat summary dict."""
    state = dict(session.state) if session.state else {}
    return {
        "session_id": session.id,
        "session_name": state.get("session_name", ""),
        "system_id": state.get("system_id", ""),
        "project_id": state.get("project_id", ""),
        "created_at": state.get("created_at", ""),
        "last_update_time": str(getattr(session, "last_update_time", "")),
    }


def _rebuild_global_store(session_id: str, session_state: dict) -> None:
    """Repopulate GLOBAL_SESSION_STORE from a restored session's state."""
    GLOBAL_SESSION_STORE[session_id] = {
        k: v for k, v in session_state.items()
        if not k.startswith("temp:")
    }
    GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[session_id]


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
# Session management routes (13-11)
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


@router.post("/sessions")
async def create_session(body: CreateSessionRequest):
    """Create a new named session and make it the active session."""
    session_id = await bootstrap_session(
        system_id=body.system_id,
        project_id=body.project_id,
        session_name=body.session_name,
    )
    # Update the module-level pointers so /session_info and /session_state reflect
    # the new session. No agent rebuild needed — the SessionManager singleton will
    # route the next CopilotKit request (threadId=session_id) to this new session.
    lifecycle.current_session_id = session_id
    actual_name = body.session_name or lifecycle.current_session_name
    logger.info(f"[POST /sessions] Created session {session_id!r} name={actual_name!r}")
    return {
        "session_id": session_id,
        "session_name": actual_name,
    }


@router.post("/sessions/{session_id}/restore")
async def restore_session(session_id: str):
    """Restore a saved session — make it the active session.

    Key behaviour:
    - Updates _ag_ui_thread_id in SQLite state to session_id so the singleton
      SessionManager finds this session when CopilotKit sends threadId=session_id.
    - Updates GLOBAL_SESSION_STORE for real-time polling.
    - Does NOT rebuild the ADKAgent — the endpoint captured the original instance
      at startup and the SessionManager is a singleton shared across rebuilds.
    """
    adk_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    if not adk_session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found.")

    state = dict(adk_session.state) if adk_session.state else {}
    session_name = state.get("session_name", "")

    # Ensure _ag_ui_thread_id == session_id so SessionManager._find_session_by_thread_id
    # locates this session when CopilotKit sends threadId=session_id.
    from google.adk.events import Event, EventActions
    try:
        restore_event = Event(
            invocation_id=f"restore-{uuid.uuid4().hex[:8]}",
            author="user",
            actions=EventActions(state_delta={"_ag_ui_thread_id": session_id}),
        )
        await session_service.append_event(session=adk_session, event=restore_event)
        logger.info(f"[restore_session] Set _ag_ui_thread_id={session_id!r} in SQLite")
    except Exception as exc:
        logger.warning(f"[restore_session] Could not update _ag_ui_thread_id: {exc}")

    # Repopulate GLOBAL_SESSION_STORE for real-time polling
    _rebuild_global_store(session_id, state)

    # Update module-level pointers (used by /session_info and /session_state)
    lifecycle.current_session_id = session_id
    lifecycle.current_session_name = session_name

    logger.info(f"[POST /sessions/{session_id}/restore] Restored. name={session_name!r}")
    return {"session_id": session_id, "session_name": session_name}


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
    return None  # 200 with empty body — caller should expect 200 or handle 204


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

    # Update the state dict and persist via append_event with a state_delta.
    from google.adk.events import Event, EventActions
    from google.genai import types as genai_types

    try:
        rename_event = Event(
            invocation_id=f"rename-{uuid.uuid4().hex[:8]}",
            author="user",
            actions=EventActions(state_delta={"session_name": body.session_name}),
        )
        await session_service.append_event(session=adk_session, event=rename_event)
    except Exception as exc:
        logger.warning(f"[PATCH /sessions/{session_id}] append_event error: {exc}")

    # Update GLOBAL_SESSION_STORE if this is the live session
    if session_id in GLOBAL_SESSION_STORE:
        GLOBAL_SESSION_STORE[session_id]["session_name"] = body.session_name
    if session_id == lifecycle.current_session_id:
        lifecycle.current_session_name = body.session_name

    logger.info(f"[PATCH /sessions/{session_id}] Renamed to {body.session_name!r}")
    return {"session_id": session_id, "session_name": body.session_name}
