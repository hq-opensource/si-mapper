
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

def exit_loop_level_2(tool_context: ToolContext) -> dict:
    """
    Signals the Level 2 Main Loop (MasterMainLoop) to terminate.
    This Ends the ENTIRE Agent Session.
    """
    logger.debug(f"[Tool Call] exit_loop_level_2 triggered by {tool_context.agent_name}")
    
    # Set the state flag for the top-level loop
    tool_context.state["EXIT_LEVEL_2"] = True
    
    tool_context.actions.escalate = True
    
    return {"status": "signal_sent", "message": "Exiting Level 2 Main Loop. Session Complete."}
