import warnings
from pathlib import Path
from urllib.parse import quote

warnings.filterwarnings("ignore", category=DeprecationWarning)

"""Main entrypoint for the PAR Agent Service."""

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.sessions import DatabaseSessionService

# Local imports
from master_architecture.create_master_agent import create_master_agent
from utils.logging_config import configure_logging
from utils.callback_utils import GLOBAL_SESSION_STORE
from utils.adk_patch import apply_adk_patches
from utils.session_lookup import get_latest_session_by_thread_id_async
# Apply patches for Gemini 3.1 compatibility (Runtime Fix)
apply_adk_patches()

# --- Configuration ---
load_dotenv()
logger = configure_logging()

SHARED_ADK_MODEL = os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")
SESSIONS_DB_PATH = os.getenv("SESSIONS_DB_PATH", "/app/data/sessions.db")
Path(SESSIONS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Per-system model override (13-09): ACTIVE_AI_MODEL can be set to the value of
# active_system.ai_model_name before the agent process starts (e.g. injected by
# the launcher or Docker entrypoint).  Falls back to SHARED_ADK_MODEL so existing
# deployments without this env var continue to work unchanged.
# Full live session-level switching (without restart) is handled in 13-10.
ACTIVE_AI_MODEL = os.getenv("ACTIVE_AI_MODEL", "") or SHARED_ADK_MODEL
logger.info(f"Using SHARED_ADK_MODEL: {SHARED_ADK_MODEL}")
logger.info(f"Effective model: {ACTIVE_AI_MODEL}")

APP_TITLE = "SI-MAPPER Agent"
AGENT_NAME = "si_mapper_agent"

# --- SQLite Session DB ---
_DB_URL = f"sqlite+aiosqlite:///{quote(SESSIONS_DB_PATH, safe='/:')}"

def create_app() -> FastAPI:
    """Initializes and configures the FastAPI application."""
    
    # 1. Create Session & Agent
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting Global Session: {session_id}")
    
    # Initialize global state to avoid KeyErrors in instruction templates
    if session_id not in GLOBAL_SESSION_STORE:
        GLOBAL_SESSION_STORE[session_id] = {
            "detailed_equipment_dict": {},
            "completed_sub_agents": [],
            "python_code_snapshots": [],
            "ttl_code_snapshots": []
        }
    GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[session_id]
    
    # 2. Create Master Agent
    # OntologyGeneratorAgent and OntologyValidatorAgent are instantiated
    # inside create_master_agent — no external subagents needed here.
    master_agent = create_master_agent(
        session_id=session_id,
        model_name=ACTIVE_AI_MODEL,
    )

    # 3. Wrap with ADK
    session_service = DatabaseSessionService(db_url=_DB_URL)
    logger.info(f"Using DatabaseSessionService → {_DB_URL}")

    adk_agent = ADKAgent(
        adk_agent=master_agent,
        app_name="si_mapper", # Must match what the frontend expects
        user_id="demo_user",
        session_timeout_seconds=3600,
        execution_timeout_seconds=1800, # 30 minutes
        tool_timeout_seconds=900,       # 15 minutes
        session_service=session_service,
        use_in_memory_services=True
    )

    # 4. Create FastAPI App
    app = FastAPI(title=APP_TITLE)
    
    # Add CORS middleware
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # For development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    @app.head("/")
    async def root():
        return {"status": "ok", "agent": "si_mapper_agent"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    add_adk_fastapi_endpoint(app, adk_agent, path="/")

    @app.get("/session_info")
    async def get_session_info():
        """Expose the session info to the frontend."""
        logger.debug(f"[/session_info] Returning session: {session_id}")
        return {
            "session_id": session_id,
            "app_name": "si_mapper",
            "user_id": "demo_user"
        }

    @app.get("/session_state")
    async def get_session_state(
        request_session_id: str = None,
        app_name: str = "si_mapper",
        user_id: str = "demo_user"
    ):
        """Persisted session state merged with real-time in-memory updates."""
        
        target_session_id = request_session_id or session_id
        sm = adk_agent._session_manager
        state = await sm.get_session_state(
            session_id=target_session_id,
            app_name=app_name,
            user_id=user_id
        )
        
        # Session not found by id — retry treating the supplied id as a thread_id.
        if not state and request_session_id:
            if match := await get_latest_session_by_thread_id_async(request_session_id):
                target_session_id = match.id
                state = await sm.get_session_state(
                    session_id=target_session_id,
                    app_name=app_name,
                    user_id=user_id
                )
        
        base_state = state or {}

        logger.debug(f"[/session_state] Resolved {target_session_id} — {len(base_state)} persisted keys.")

        # Overlay real-time updates; fall back to "latest" in single-session mode.
        real_time_updates = GLOBAL_SESSION_STORE.get(target_session_id) or GLOBAL_SESSION_STORE.get("latest")
        
        if real_time_updates:
            logger.debug(f"[/session_state] Merging real-time updates from Global Store for {target_session_id}")
            base_state.update(real_time_updates)
            
        # --- DEBUG LOGGING ---
        logger.debug(f"[/session_state] Returning {len(base_state)} keys for session {target_session_id}")
        logger.debug(f"[/session_state] Available keys: {list(base_state.keys())}")
        
        # Check for specific equipment keys that the user is looking for
        equipment_keys = [k for k in base_state.keys() if k in ["detailed_equipment", "boilers", "fans", "pumps"]]
        if equipment_keys:
             logger.debug(f"[/session_state] Found target equipment keys: {equipment_keys}")

        return base_state
    
    logger.debug("Master Agent Service Ready.")
    return app


# Expose the app object for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY environment variable not set!")
    
    port = int(os.getenv("PORT", 8001))
    logger.info(f"Starting Master Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)