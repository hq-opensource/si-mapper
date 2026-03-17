from __future__ import annotations

from typing import Optional, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from utils.logging_config import configure_logging
from utils.callback_utils import shared_model_callback, shared_before_model_callback

# --- Configuration ---
logger = configure_logging()
AGENT_NAMES = [
    "ImageRecognitionAgent",
    "PlanAgent",
    "ActAgent",
    "ReviewAgent",
    "MasterAgent",
]

def model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Callback function to process the model's response.
    Uses the shared implementation to ensure persistence and consistent UI markers.
    """
    return shared_model_callback(callback_context, llm_response)


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: Any,
) -> Optional[LlmResponse]:
    """Records LLM-call start time for the per-iteration report."""
    return shared_before_model_callback(callback_context, llm_request)


