from typing import Dict, Any
from google.adk.tools import ToolContext
from utils.logging_config import configure_logging

logger = configure_logging()

def update_step(
    tool_context: ToolContext,
    step: str
) -> str:
    """
    Updates the current activity/step being executed.
    """
    logger.info(f"Step Update: {step}")
    observed_steps = tool_context.state.get("observed_steps", [])
    if step not in observed_steps:
        observed_steps.append(step)

    tool_context.state.update({
        "observed_steps": observed_steps,
        "current_step": step
    })
    return f":::thought\n[System] Current step updated to: {step}\n:::\n"

def update_status(
    tool_context: ToolContext,
    status: str
) -> str:
    """
    Updates the overall status of the agent (e.g., 'processing', 'working', 'completed').
    """
    logger.info(f"Status Update: {status}")
    tool_context.state["status"] = status
    return f":::thought\n[System] Agent status changed to: {status}\n:::\n"

def update_state(
    tool_context: ToolContext,
    data: Dict[str, Any]
) -> str:
    """
    Saves arbitrary variables to the agent's shared state.
    Use this to persist structured information like counters, dictionaries, or extracted data.
    """
    logger.info(f"State Update: {data.keys()}")
    tool_context.state.update(data)
    keys_str = ", ".join(data.keys())
    return f":::thought\n[System] Saved state variables: {keys_str}\n:::\n"
