"""POST /model — runtime model swap without service restart (13-10)."""

import logging

from fastapi import APIRouter

from ..lifecycle import _rebuild_lock, bootstrap_session, rebuild_agent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["model"])


@router.post("/model")
async def set_model(model_name: str):
    """Swap the active LLM model without restarting the service.

    Rebuilds the full agent tree (MasterLlmAgent, OntologyGeneratorAgent,
    OntologyValidatorAgent) for *model_name*.  Conversation history from the
    previous session is discarded — this is an operator-level action.
    The asyncio.Lock serialises concurrent swap requests.
    """
    async with _rebuild_lock:
        new_session_id = await bootstrap_session()
        rebuild_agent(model_name, new_session_id)

    logger.info(f"[POST /model] Model swapped to {model_name!r}, new session: {new_session_id!r}")
    return {"status": "ok", "model": model_name, "session_id": new_session_id}


