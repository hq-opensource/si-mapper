"""
Adapted exit tools for ontology generation/validation running directly in the master agent.
These set EXIT_LEVEL_2 so the master loop (MasterMainLoopAgent.is_loop_finished) terminates correctly.
"""
from __future__ import annotations

import logging

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def checkpoint_code(tool_context: ToolContext, code: str) -> dict:
    """Appends a Fix N snapshot to python_code_snapshots. Does NOT escalate — validator loop continues."""
    iteration = tool_context.state.get("ontology_code_iteration_count", 0)
    snapshots = list(tool_context.state.get("python_code_snapshots", []))
    snapshots.append(
        {
            "label": f"Fix {iteration}",
            "code": code,
            "iteration": iteration,
            "status": "fix",
        }
    )
    tool_context.state["python_code_snapshots"] = snapshots
    tool_context.state["ontology_code_iteration_count"] = iteration + 1
    return {"status": "snapshot_saved", "iteration": iteration}
    # CRITICAL: No tool_context.actions.escalate here — loop must continue


def exit_generator_success(
    tool_context: ToolContext,
    code: str,
    summary: str,
) -> dict:
    """Appends Initial snapshot, sets ONTOLOGY_GENERATION_SUCCESS=True, escalates (EXIT_LEVEL_2)."""
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
    tool_context.state["EXIT_LEVEL_2"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "summary": summary}


def exit_generator_failure(
    tool_context: ToolContext,
    reason: str,
) -> dict:
    """Sets ONTOLOGY_GENERATION_SUCCESS=False, escalates (EXIT_LEVEL_2)."""
    logger.debug(
        "[exit_generator_failure] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    tool_context.state["ONTOLOGY_GENERATION_SUCCESS"] = False
    tool_context.state["ONTOLOGY_GENERATION_FAILURE_REASON"] = reason
    tool_context.state["EXIT_LEVEL_2"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "reason": reason}


def exit_validator_success(
    tool_context: ToolContext,
    code: str,
    summary: str,
    ttl_content: str = "",
) -> dict:
    """Saves final Python snapshot, writes TTL snapshot, patches to Final/validated, escalates (EXIT_LEVEL_2)."""
    logger.debug(
        "[exit_validator_success] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    # Inline checkpoint_code logic (read-copy-write) — avoids cross-module import
    iteration = tool_context.state.get("ontology_code_iteration_count", 0)
    snapshots = list(tool_context.state.get("python_code_snapshots", []))
    snapshots.append({"label": f"Fix {iteration}", "code": code, "iteration": iteration, "status": "fix"})
    tool_context.state["python_code_snapshots"] = snapshots
    tool_context.state["ontology_code_iteration_count"] = iteration + 1
    # Patch last Python snapshot to Final/validated
    snapshots = list(tool_context.state.get("python_code_snapshots", []))
    if snapshots:
        snapshots[-1]["label"] = "Final"
        snapshots[-1]["status"] = "validated"
        tool_context.state["python_code_snapshots"] = snapshots
    # Write TTL content to ttl_code_snapshots (separate key for TTL tab)
    if ttl_content:
        ttl_snapshots = list(tool_context.state.get("ttl_code_snapshots", []))
        ttl_snapshots.append(
            {"label": "TTL", "code": ttl_content, "iteration": 0, "status": "validated"}
        )
        tool_context.state["ttl_code_snapshots"] = ttl_snapshots
    tool_context.state["ONTOLOGY_VALIDATION_SUCCESS"] = True
    tool_context.state["EXIT_LEVEL_2"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "summary": summary}


def exit_validator_failure(tool_context: ToolContext, reason: str) -> dict:
    """Signals validation failure, escalates (EXIT_LEVEL_2)."""
    logger.debug(
        "[exit_validator_failure] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    tool_context.state["ONTOLOGY_VALIDATION_SUCCESS"] = False
    tool_context.state["ONTOLOGY_VALIDATION_FAILURE_REASON"] = reason
    tool_context.state["EXIT_LEVEL_2"] = True
    tool_context.actions.escalate = True
    return {"status": "signal_sent", "reason": reason}
