"""
Generic exit tools for all skills.

Both tools set EXIT_LEVEL_2 = True and actions.escalate = True
so the master loop (MasterMainLoopAgent.is_loop_finished) terminates.
No domain-specific state keys are written.
"""
from __future__ import annotations

import logging

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def exit_with_success(tool_context: ToolContext, summary: str) -> dict:
    """Signal task success and terminate the master loop.

    Parameters
    ----------
    tool_context : ToolContext
        ADK tool context (injected by framework).
    summary : str
        Human-readable summary of what was accomplished.
    """
    logger.info(
        "[exit_with_success] called by %s — %s",
        getattr(tool_context, "agent_name", "unknown"),
        summary,
    )
    tool_context.state["EXIT_LEVEL_2"] = True
    tool_context.actions.escalate = True
    return {"status": "success", "summary": summary}


def exit_with_failure(tool_context: ToolContext, reason: str) -> dict:
    """Signal task failure and terminate the master loop.

    Parameters
    ----------
    tool_context : ToolContext
        ADK tool context (injected by framework).
    reason : str
        Human-readable reason for the failure.
    """
    logger.warning(
        "[exit_with_failure] called by %s — %s",
        getattr(tool_context, "agent_name", "unknown"),
        reason,
    )
    tool_context.state["EXIT_LEVEL_2"] = True
    tool_context.actions.escalate = True
    return {"status": "failure", "reason": reason}
