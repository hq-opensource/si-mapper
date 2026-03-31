"""FastAPI application factory."""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import add_adk_fastapi_endpoint

from . import lifecycle
from .lifecycle import model_config, rebuild_agent, session_service, _default_session_name, agent_proxy
from .routers import health, session, workspace

logger = logging.getLogger(__name__)

APP_TITLE = "SI-MAPPER Agent"
APP_NAME = "si_mapper"
USER_ID = "demo_user"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """FastAPI lifespan — runs async startup inside uvicorn's event loop."""
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    session_name = _default_session_name()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
        state={
            "_ag_ui_thread_id": session_id,
            "session_name": session_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "detailed_equipment_dict": {},
            "completed_sub_agents": [],
            "python_code_snapshots": [],
            "ttl_code_snapshots": [],
        },
    )
    lifecycle.current_session_id = session_id
    lifecycle.current_session_name = session_name

    logger.info(f"[lifespan] Startup session: {session_id}, model: {model_config.current}")
    rebuild_agent(model_config.current, session_id)

    add_adk_fastapi_endpoint(app, agent_proxy, path="/")
    logger.info("[lifespan] Master Agent Service ready.")
    yield


def create_app() -> FastAPI:
    """Initialise and return the FastAPI application."""
    app = FastAPI(title=APP_TITLE, lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(session.router)
    app.include_router(workspace.router)

    logger.debug("[create_app] FastAPI app created (startup deferred to lifespan).")
    return app
