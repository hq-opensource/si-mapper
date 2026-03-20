"""
Exit tools for the ontology validator sub-agent.

``checkpoint_code``
    Appends a Fix N snapshot to ``ontology_code_snapshots`` and increments the
    iteration counter.  Does NOT escalate — the validator loop continues.

``exit_validator_success``
    Saves the final code via ``checkpoint_code``, patches the last snapshot to
    label="Final"/status="validated", sets ``ONTOLOGY_VALIDATION_SUCCESS=True``,
    then escalates to terminate the validator loop.

``exit_validator_failure``
    Signals validation failure and escalates.
"""
from __future__ import annotations

import logging

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def checkpoint_code(tool_context: ToolContext, code: str) -> dict:
    """Appends a Fix N snapshot. Does NOT escalate — validator loop continues."""
    iteration = tool_context.state.get("ontology_code_iteration_count", 0)
    # Read-copy-write pattern — never mutate the state list directly
    snapshots = list(tool_context.state.get("ontology_code_snapshots", []))
    snapshots.append(
        {
            "label": f"Fix {iteration}",
            "code": code,
            "iteration": iteration,
            "status": "fix",
        }
    )
    tool_context.state["ontology_code_snapshots"] = snapshots
    tool_context.state["ontology_code_iteration_count"] = iteration + 1
    return {"status": "snapshot_saved", "iteration": iteration}
    # CRITICAL: No tool_context.actions.escalate here — loop must continue


def exit_validator_success(
    tool_context: ToolContext, code: str, summary: str
) -> dict:
    """Saves final snapshot, patches to Final/validated, escalates."""
    logger.debug(
        "[exit_validator_success] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    # Save the final code version via checkpoint_code
    checkpoint_code(tool_context, code)
    # Patch last snapshot to Final/validated
    snapshots = list(tool_context.state.get("ontology_code_snapshots", []))
    if snapshots:
        snapshots[-1]["label"] = "Final"
        snapshots[-1]["status"] = "validated"
        tool_context.state["ontology_code_snapshots"] = snapshots
    tool_context.state["ONTOLOGY_VALIDATION_SUCCESS"] = True
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "summary": summary}


def exit_validator_failure(tool_context: ToolContext, reason: str) -> dict:
    """Signals validation failure, escalates."""
    logger.debug(
        "[exit_validator_failure] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    tool_context.state["ONTOLOGY_VALIDATION_SUCCESS"] = False
    tool_context.state["ONTOLOGY_VALIDATION_FAILURE_REASON"] = reason
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "reason": reason}
