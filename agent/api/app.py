"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import add_adk_fastapi_endpoint

from . import lifecycle
from .lifecycle import bootstrap_session, model_config, rebuild_agent
from .routers import health, model, session

logger = logging.getLogger(__name__)

APP_TITLE = "SI-MAPPER Agent"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """FastAPI lifespan — runs async startup inside uvicorn's event loop.

    bootstrap_session() is async (SqliteSessionService), so it must run inside
    an already-running event loop.  Using asyncio.run() from create_app() raised
    'asyncio.run() cannot be called from a running event loop' when uvicorn had
    already started the loop before calling the ASGI app factory.
    """
    session_id = await bootstrap_session()
    logger.info(f"[lifespan] Starting global session: {session_id}, model: {model_config.current}")
    rebuild_agent(model_config.current, session_id)

    # Register the ADK streaming endpoint here, after holder.adk_agent is built.
    # FastAPI resolves routes at request time, so adding them during startup works.
    add_adk_fastapi_endpoint(app, lifecycle.holder.adk_agent, path="/")

    logger.info("[lifespan] Master Agent Service ready.")
    yield
    # (cleanup on shutdown can go here if needed)


def create_app() -> FastAPI:
    """Initialise and return the FastAPI application."""
    app = FastAPI(title=APP_TITLE, lifespan=_lifespan)

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

    logger.debug("[create_app] FastAPI app created (startup deferred to lifespan).")
    return app
