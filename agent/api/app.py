"""FastAPI application factory."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import add_adk_fastapi_endpoint

from . import lifecycle
from .lifecycle import bootstrap_session, model_config, rebuild_agent
from .routers import health, model, session

logger = logging.getLogger(__name__)

APP_TITLE = "SI-MAPPER Agent"


def create_app() -> FastAPI:
    """Initialise and return the FastAPI application.

    Bootstraps the initial agent tree (equivalent to the previous inline
    construction in main.py — no behavioural regression).
    """
    # Bootstrap initial session & agent tree
    session_id = bootstrap_session()
    logger.info(f"[create_app] Starting global session: {session_id}, using model: {model_config.current}")
    rebuild_agent(model_config.current, session_id)

    app = FastAPI(title=APP_TITLE)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(model.router)
    app.include_router(session.router)

    # Register the ADK streaming endpoint.
    # NOTE: this captures the ADKAgent instance at startup; the session
    # introspection routes use holder.adk_agent dynamically and always
    # reflect the latest swap.
    add_adk_fastapi_endpoint(app, lifecycle.holder.adk_agent, path="/")

    logger.debug("[create_app] Master Agent Service Ready.")
    return app


