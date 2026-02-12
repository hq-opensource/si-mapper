
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

def exit_loop_level_4(tool_context: ToolContext, summary: str = "Task completed.") -> dict:
    """
    Signals the current Level 4 Loop to terminate.
    This creates a "Phase Handover" to the Level 3 Master Agent.
    
    Args:
        summary: A detailed description of what was accomplished (e.g., "Identified 5 ducts", "Registered 3 fans").
                 This summary is returned to the Master Agent so it knows what happened.
    """
    logger.debug(f"[Tool Call] exit_loop_level_4 triggered by {tool_context.agent_name}")
    
    # Set the state flag that GenericLoopAgent (and subclasses) will check
    tool_context.state["EXIT_LEVEL_4"] = True
    
    # Signal ADK to escalate/interrupt the current thought process if needed
    tool_context.actions.escalate = True
    
    # The return value here is what the Master Agent usually sees as the final "result" of the tool call
    return {
        "status": "signal_sent", 
        "message": "Exiting Loop.", 
        "summary": summary
    }

def exit_loop_level_2(tool_context: ToolContext) -> dict:
    """
    Signals the Level 2 Main Loop to terminate.
    This Ends the ENTIRE Agent Session.
    
    Use this when all tasks across all phases are successfully verified and the job is 100% done.
    """
    logger.debug(f"[Tool Call] exit_loop_level_2 triggered by {tool_context.agent_name}")
    
    # Set the state flag for the top-level loop
    tool_context.state["EXIT_LEVEL_2"] = True
    
    tool_context.actions.escalate = True
    
    return {"status": "signal_sent", "message": "Exiting Level 2 Main Loop. Session Complete."}
