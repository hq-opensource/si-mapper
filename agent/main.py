import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

"""Main entrypoint for the PAR Agent Service."""

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

# Local imports
from master_architecture.create_master_agent import create_master_agent
from utils.logging_config import configure_logging
from utils.callback_utils import GLOBAL_SESSION_STORE
from utils.adk_patch import apply_adk_patches
# Apply patches for Gemini 3.1 compatibility (Runtime Fix)
apply_adk_patches()

# --- Configuration ---
load_dotenv()
logger = configure_logging()

SHARED_ADK_MODEL = os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")
logger.info(f"Using SHARED_ADK_MODEL: {SHARED_ADK_MODEL}")
APP_TITLE = "SI-MAPPER Agent"
AGENT_NAME = "si_mapper_agent"


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
        model_name=SHARED_ADK_MODEL,
    )

    # 3. Wrap with ADK
    adk_agent = ADKAgent(
        adk_agent=master_agent,
        app_name="si_mapper", # Must match what the frontend expects
        user_id="demo_user",
        session_timeout_seconds=3600,
        execution_timeout_seconds=1800, # 30 minutes
        tool_timeout_seconds=900,       # 15 minutes
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

    @app.post("/stop")
    async def stop_agent():
        """Cancel all active agent executions."""
        cancelled = 0
        for execution in list(adk_agent._active_executions.values()):
            await execution.cancel()
            cancelled += 1
        adk_agent._active_executions.clear()
        logger.info(f"Stop requested — cancelled {cancelled} execution(s).")
        return {"status": "stopped", "cancelled": cancelled}

    @app.get("/session_state")
    async def get_session_state(
        request_session_id: str = None,
        app_name: str = "si_mapper",
        user_id: str = "demo_user"
    ):
        """Expose the session state to the frontend."""
        
        sm = adk_agent._session_manager
        tracked_ids = [k.split(":")[-1] for k in sm._session_keys]
        
        target_session_id = request_session_id or session_id
        if target_session_id not in tracked_ids and tracked_ids:
             target_session_id = tracked_ids[0]

        # 1. Get base state from ADK SessionManager
        state = await sm.get_session_state(
            session_id=target_session_id,
            app_name=app_name,
            user_id=user_id
        )
        base_state = state or {}
        
        # 2. Layer on real-time updates from the Global Store
        # We try to match by ID, but also fall back to 'latest' if in a single-session demo mode
        real_time_updates = GLOBAL_SESSION_STORE.get(target_session_id) or GLOBAL_SESSION_STORE.get("latest")
        
        if real_time_updates:
            logger.debug(f"[/session_state] Merging real-time updates from Global Store for {target_session_id}")
            # Correctly handle merged lists (thoughts, tool_calls, tasks)
            # and other metadata (active_agent, current_step, status)
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