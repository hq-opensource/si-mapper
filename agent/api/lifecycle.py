"""Agent lifecycle: mutable holders, model config, and rebuild_agent factory.

Centralises all state that is shared across FastAPI routes so that a runtime
model swap (POST /model, 13-10) touches exactly one place.
"""

import asyncio
import os
import pathlib
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv  # idempotent — safe to call here as a guard

# Load .env before reading any env vars (guard for direct module imports / tests)
load_dotenv()

from ag_ui_adk import ADKAgent  # noqa: E402  (after patch is applied in main.py)
from google.adk.sessions.sqlite_session_service import SqliteSessionService

from master_architecture.create_master_agent import create_master_agent
from utils.callback_utils import GLOBAL_SESSION_STORE
from utils.logging_config import configure_logging

logger = configure_logging()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SHARED_ADK_MODEL: str = os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")
ACTIVE_AI_MODEL: str = os.getenv("ACTIVE_AI_MODEL", "") or SHARED_ADK_MODEL
SESSIONS_DB_PATH: str = os.getenv("SESSIONS_DB_PATH", "./data/sessions.db")

logger.info(f"[lifecycle] SHARED_ADK_MODEL: {SHARED_ADK_MODEL}")
logger.info(f"[lifecycle] Effective model:  {ACTIVE_AI_MODEL}")
logger.info(f"[lifecycle] Sessions DB:      {SESSIONS_DB_PATH}")

# Ensure the data directory exists before creating the session service
pathlib.Path(SESSIONS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# SQLite session service (singleton — shared across all builds)
# ---------------------------------------------------------------------------
session_service = SqliteSessionService(db_path=SESSIONS_DB_PATH)

# ---------------------------------------------------------------------------
# Mutable holders (13-10)
# ---------------------------------------------------------------------------

class ModelConfig:
    """Mutable holder for the currently active model name."""

    current: str = ACTIVE_AI_MODEL


class AgentHolder:
    """Indirection wrapper so FastAPI routes always delegate to the live ADKAgent.

    Every reference to ``holder.adk_agent`` picks up the latest instance even
    after a POST /model swap — Python keeps the old object alive until all
    in-flight requests finish.
    """

    adk_agent: ADKAgent | None = None


model_config = ModelConfig()
holder = AgentHolder()
_rebuild_lock = asyncio.Lock()

# Session ID that belongs to the current holder.adk_agent instance.
# Updated by rebuild_agent() on every build (startup + POST /model).
current_session_id: str = ""
current_session_name: str = ""


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def _default_session_name() -> str:
    """Return a human-readable default session name based on the current time."""
    return f"Session {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"


async def bootstrap_session(
    system_id: str = "",
    project_id: str = "",
    session_name: str = "",
    session_id: str | None = None,
) -> str:
    """Create a new ADK session in SqliteSessionService and GLOBAL_SESSION_STORE.

    Returns the new session_id.
    """
    global current_session_name
    if not session_id:
        session_id = f"session-{uuid.uuid4().hex[:8]}"
    if not session_name:
        session_name = _default_session_name()

    # Persist initial state in SQLite.
    # _ag_ui_thread_id must equal session_id so that when CopilotKit sends
    # threadId=session_id, SessionManager._find_session_by_thread_id locates
    # this session and uses its event history instead of creating a fresh one.
    initial_state = {
        "_ag_ui_thread_id": session_id,
        "session_name": session_name,
        "system_id": system_id,
        "project_id": project_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "detailed_equipment_dict": {},
        "completed_sub_agents": [],
        "python_code_snapshots": [],
        "ttl_code_snapshots": [],
    }
    session = await session_service.create_session(
        app_name="si_mapper",
        user_id="demo_user",
        state=initial_state,
        session_id=session_id,
    )
    actual_id = session.id

    # Mirror in GLOBAL_SESSION_STORE for real-time polling
    GLOBAL_SESSION_STORE[actual_id] = {
        "detailed_equipment_dict": {},
        "completed_sub_agents": [],
        "python_code_snapshots": [],
        "ttl_code_snapshots": [],
        "session_name": session_name,
        "system_id": system_id,
        "project_id": project_id,
    }
    GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[actual_id]
    current_session_name = session_name
    return actual_id


def rebuild_agent(model_name: str, session_id: str) -> None:
    """(Re-)construct the full agent tree for *model_name* and update the holder.

    Safe to call at startup or at runtime from POST /model.  In-flight
    requests against the previous ``holder.adk_agent`` complete normally —
    Python keeps the old object alive until all references are released.

    NOTE: ``add_adk_fastapi_endpoint`` is registered once at startup with the
    initial ADKAgent.  After a swap the SSE/WebSocket endpoint at ``/`` still
    uses the original instance.  The session introspection endpoints
    (``/session_info``, ``/session_state``) and all downstream tool calls DO
    use the new instance via ``holder.adk_agent``.  A full hot-swap of the
    ADK endpoint is tracked as a future improvement.
    """
    global current_session_id

    logger.info(
        f"[rebuild_agent] Building agent tree: model={model_name!r}, session={session_id!r}"
    )

    master = create_master_agent(session_id=session_id, model_name=model_name)
    holder.adk_agent = ADKAgent(
        adk_agent=master,
        app_name="si_mapper",       # Must match what the frontend expects
        user_id="demo_user",
        session_service=session_service,  # SQLite persistence (13-11)
        session_timeout_seconds=3600,
        execution_timeout_seconds=1800,   # 30 minutes
        tool_timeout_seconds=900,         # 15 minutes
        use_in_memory_services=True,      # kept for artifact/memory/credential
    )
    current_session_id = session_id
    model_config.current = model_name

    logger.info(f"[rebuild_agent] Agent ready. session_id={session_id!r}")

