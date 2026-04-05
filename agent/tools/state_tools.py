from typing import Optional
import json
from google.adk.tools import ToolContext
from utils.logging_config import configure_logging

logger = configure_logging()

def save_agent_state(
    tool_context: ToolContext, 
    equipment_id: str, 
    status: str
) -> str:
    """
    Saves the processing status of a specific component to persist state across turns.
    This is used to track which equipment has already been processed by the technical mapping loop.
    
    Args:
        equipment_id: The ID of the equipment being processed (e.g. '0LJ2gpN3pY').
        status: The status of the equipment (e.g. 'treated', 'error', 'pending').
    """
    logger.info(f"Saving state for {equipment_id}: {status}")
    
    # Initialize treated dict if not exists in tool_context.state
    if "treated" not in tool_context.state:
        tool_context.state["treated"] = {}
    
    # Update the dictionary
    tool_context.state["treated"][equipment_id] = status
    
    return f":::thought\n[System] Persistent state updated for {equipment_id}: {status}\n:::\n"

def get_agent_state(
    tool_context: ToolContext, 
    equipment_id: Optional[str] = None
) -> str:
    """
    Retrieves the processing status from the persistent state.
    
    Args:
        equipment_id: (Optional) Specific ID to check. If None, returns the whole 'treated' dictionary.
    """
    treated = tool_context.state.get("treated", {})
    if equipment_id:
        status = treated.get(equipment_id, "unknown")
        return f":::thought\n[System] Status for {equipment_id}: {status}\n:::\n"
    
    return f":::thought\n[System] Persistent state (treated): {json.dumps(treated)}\n:::\n"

def get_active_project(tool_context: ToolContext) -> str:
    """
    Returns the JSON of the active_project from the persistent state.
    If not found, returns an empty JSON object {}.
    """
    active_project = tool_context.state.get("active_project", {})
    return json.dumps(active_project)


def get_active_system(tool_context: ToolContext) -> str:
    """
    Returns the JSON of the active_system from the persistent state.
    If not found, returns an empty JSON object {}.
    """
    active_system = tool_context.state.get("active_system", {})
    return json.dumps(active_system)
