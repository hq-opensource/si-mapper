"""Main entrypoint for the PAR Agent Service."""
from __future__ import annotations

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

# Local imports
from master_architecture.create_master_agent import create_master_agent
from sub_agents import HorizontalDuctLlmAgent, VerticalDuctLlmAgent, EquipmentLlmAgent, BacnetLlmAgent, ControlLlmAgent, ElectricityLlmAgent
from utils.logging_config import configure_logging
from utils.mcp_utils import create_mcp_toolset
from utils.callback_utils import GLOBAL_SESSION_STORE
from utils.adk_patch import apply_adk_patches

# Apply patches for Gemini 3.0 compatibility (Runtime Fix)
apply_adk_patches()

# --- Configuration ---
load_dotenv()
logger = configure_logging()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp/")
SHARED_ADK_MODEL = os.getenv("SHARED_ADK_MODEL", "gemini-3.1-pro")
logger.info(f"Using SHARED_ADK_MODEL: {SHARED_ADK_MODEL}")
APP_TITLE = "SI-MAPPER Agent"
AGENT_NAME = "si_mapper_agent"


def create_app() -> FastAPI:
    """Initializes and configures the FastAPI application."""
    
    # 1. Initialize Tools
    # Note: Toolsets are loaded once at startup in this pattern
    logger.info("Initializing MCP Toolsets...")
    try:
        si_mapper_toolset = create_mcp_toolset(MCP_SERVER_URL)
    except Exception as e:
        logger.error(f"Failed to create toolsets: {e}")
        # We might want to re-raise or handle gracefully, for now letting it fail is visible.
        raise e

    # 2. Create Session & Agent
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting Global Session: {session_id}")
    
    # Initialize global state to avoid KeyErrors in instruction templates
    if session_id not in GLOBAL_SESSION_STORE:
        GLOBAL_SESSION_STORE[session_id] = {
            "detailed_equipment_dict": {},
            "completed_sub_agents": []
        }
    GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[session_id]
    
    # Create subagents
    horizontal_agent = HorizontalDuctLlmAgent(model_name=SHARED_ADK_MODEL, session_id=session_id, tools=[si_mapper_toolset])
    vertical_agent = VerticalDuctLlmAgent(model_name=SHARED_ADK_MODEL, session_id=session_id, tools=[si_mapper_toolset])
    equipment_agent = EquipmentLlmAgent(model_name=SHARED_ADK_MODEL, session_id=session_id, tools=[si_mapper_toolset])
    bacnet_agent = BacnetLlmAgent(model_name=SHARED_ADK_MODEL, session_id=session_id, tools=[si_mapper_toolset])
    control_agent = ControlLlmAgent(model_name=SHARED_ADK_MODEL, session_id=session_id, tools=[si_mapper_toolset])
    electricity_agent = ElectricityLlmAgent(model_name=SHARED_ADK_MODEL, session_id=session_id, tools=[si_mapper_toolset])
    
    subagents = [horizontal_agent, vertical_agent, equipment_agent, bacnet_agent, control_agent, electricity_agent]
    
    # Create Master Agent
    master_agent = create_master_agent(session_id=session_id, subagents=subagents, model_name=SHARED_ADK_MODEL, si_mapper_toolset=si_mapper_toolset)

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