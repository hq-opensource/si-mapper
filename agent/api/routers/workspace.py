"""POST /workspace/state — unified workspace state update.

Single entry-point for every workspace context change from the UI.
The caller always sends the FULL state — no partial updates.

Request body:
  {
    "active_project": { id, folder_path, name, graphivac_project_id },
    "active_system":  { id, folder_path, name, graphivac_grid_id, ai_model_name },
    "active_session": { id, name }
  }

The endpoint:
  1. Creates the target session in SQLite if it does not exist yet.
  2. Makes it the active session (_ag_ui_thread_id, lifecycle pointers,
     GLOBAL_SESSION_STORE).
  3. Persists the structured project / system / session objects inside the
     session state — only the fields listed in the models below.
  4. Updates model_config.current from active_system.ai_model_name so
     subsequent /session_state polls reflect the correct model.
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from .. import lifecycle
from ..lifecycle import model_config, rebuild_agent, session_service
from utils.callback_utils import GLOBAL_SESSION_STORE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workspace"])

APP_NAME = "si_mapper"
USER_ID = "demo_user"


# ---------------------------------------------------------------------------
# Request / Response models — only the fields the agent cares about
# ---------------------------------------------------------------------------

class ActiveProjectState(BaseModel):
    id: str
    folder_path: str
    name: str
    graphivac_project_id: str


class ActiveSystemState(BaseModel):
    id: str
    folder_path: str
    name: str
    graphivac_grid_id: str
    ai_model_name: str


class ActiveSessionState(BaseModel):
    id: str = ""   # empty string → agent generates a new session ID
    name: str


class WorkspaceStateRequest(BaseModel):
    """Full workspace context sent by the UI on every relevant state change."""
    active_project: ActiveProjectState
    active_system: ActiveSystemState
    active_session: ActiveSessionState


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/workspace/state")
async def update_workspace_state(body: WorkspaceStateRequest):
    """Update the agent's active context with the complete workspace state.

    - No session ID supplied → agent creates a new session and returns the ID.
    - Session ID supplied    → agent updates that session's state.
    """
    session_id = body.active_session.id.strip()
    active_project = body.active_project.model_dump()
    active_system  = body.active_system.model_dump()
    session_name   = body.active_session.name

    if not session_id:
        # ── Create: caller has no session yet ─────────────────────────────────
        session_id     = f"session-{uuid.uuid4().hex[:8]}"
        active_session = {"id": session_id, "name": session_name}

        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state={
                "_ag_ui_thread_id":       session_id,
                "session_name":            session_name,
                "created_at":              datetime.now(timezone.utc).isoformat(),
                "active_project":          active_project,
                "active_system":           active_system,
                "active_session":          active_session,
                "detailed_equipment_dict": {},
                "completed_sub_agents":    [],
                "python_code_snapshots":   [],
                "ttl_code_snapshots":      [],
            },
        )
        logger.info(
            f"[workspace/state] Created session {session_id!r} — "
            f"project={active_project['id']!r}, system={active_system['id']!r}"
        )

    else:
        # ── Update: session ID was provided ───────────────────────────────────
        # Only ensure the session exists in SQLite (so CopilotKit can route to
        # it).  State is NOT updated here via append_event.  Instead, the
        # before_agent_callback (inject_workspace_state) reads GLOBAL_SESSION_STORE
        # and writes to callback_context.state at the start of each invocation —
        # the ADK-recommended mechanism.  The framework then automatically
        # tracks those writes as state_delta and flushes them to SQLite.
        active_session = {"id": session_id, "name": session_name}

        adk_session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        if not adk_session:
            # Session not found (e.g. DB reset) — recreate with full context.
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id,
                state={
                    "_ag_ui_thread_id":       session_id,
                    "session_name":            session_name,
                    "created_at":              datetime.now(timezone.utc).isoformat(),
                    "active_project":          active_project,
                    "active_system":           active_system,
                    "active_session":          active_session,
                    "detailed_equipment_dict": {},
                    "completed_sub_agents":    [],
                    "python_code_snapshots":   [],
                    "ttl_code_snapshots":      [],
                },
            )
            logger.info(f"[workspace/state] Re-created missing session {session_id!r}")

    # ── Mirror into GLOBAL_SESSION_STORE for real-time polling ────────────────
    if session_id not in GLOBAL_SESSION_STORE:
        GLOBAL_SESSION_STORE[session_id] = {}
    GLOBAL_SESSION_STORE[session_id].update({
        "session_name":   session_name,
        "active_project": active_project,
        "active_system":  active_system,
        "active_session": active_session,
    })
    GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[session_id]

    lifecycle.current_session_id   = session_id
    lifecycle.current_session_name = session_name

    new_model = str(active_system.get("ai_model_name") or "").strip()
    if new_model and new_model != model_config.current:
        logger.info(
            f"[workspace/state] Model changed: {model_config.current!r} → {new_model!r}. "
            f"Restarting agent for session {session_id!r}."
        )
        rebuild_agent(new_model, session_id)

    logger.info(
        f"[workspace/state] session={session_id!r}, "
        f"project={active_project['id']!r}, system={active_system['id']!r}, "
        f"model={model_config.current!r}"
    )

    return {
        "status":       "ok",
        "session_id":   session_id,
        "session_name": session_name,
        "project_id":   active_project["id"],
        "system_id":    active_system["id"],
        "model":        model_config.current,
    }
