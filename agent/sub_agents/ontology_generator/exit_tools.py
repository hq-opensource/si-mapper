"""
Exit tools for the ontology generator sub-agent.

``exit_generator_success``
    Called by the generator agent when it has successfully produced ontology
    code. Appends an Initial snapshot to ``python_code_snapshots`` and
    escalates to terminate the generator loop.

``exit_generator_failure``
    Called by the generator agent when an unrecoverable error occurs.
    Sets ``ONTOLOGY_GENERATION_SUCCESS=False`` and escalates.
"""
from __future__ import annotations

import logging

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def exit_generator_success(
    tool_context: ToolContext,
    code: str,
    summary: str,
) -> dict:
    """Appends Initial snapshot, sets ONTOLOGY_GENERATION_SUCCESS=True, escalates."""
    logger.debug(
        "[exit_generator_success] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    # Read-copy-write pattern — never mutate the state list directly
    snapshots = list(tool_context.state.get("python_code_snapshots", []))
    snapshots.append(
        {"label": "Initial", "code": code, "iteration": 0, "status": "generated"}
    )
    tool_context.state["python_code_snapshots"] = snapshots
    tool_context.state["ontology_code_iteration_count"] = 0
    tool_context.state["ONTOLOGY_GENERATION_SUCCESS"] = True
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "summary": summary}


def exit_generator_failure(
    tool_context: ToolContext,
    reason: str,
) -> dict:
    """Sets ONTOLOGY_GENERATION_SUCCESS=False, escalates."""
    logger.debug(
        "[exit_generator_failure] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    tool_context.state["ONTOLOGY_GENERATION_SUCCESS"] = False
    tool_context.state["ONTOLOGY_GENERATION_FAILURE_REASON"] = reason
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "reason": reason}
