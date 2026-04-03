"""
Adapted exit tools for ontology generation/validation running directly in the master agent.
These set EXIT_LEVEL_2 so the master loop (MasterMainLoopAgent.is_loop_finished) terminates correctly.
"""
from __future__ import annotations

import logging
from pathlib import Path

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path anchors
# ---------------------------------------------------------------------------
# This file: agent/tools/ontology_exit_tools.py
# _PROJECT_ROOT = project root (two levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_TTL_LATEST = _PROJECT_ROOT / "mapper" / "uploads" / "ttl" / "latest_ontology.ttl"


def exit_generator_success(
    tool_context: ToolContext,
    summary: str,
) -> dict:
    """Signal generation success. Sets ONTOLOGY_GENERATION_SUCCESS=True, escalates (EXIT_LEVEL_2)."""
    logger.debug(
        "[exit_generator_success] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
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
    summary: str,
) -> dict:
    """Signal validation success. Reads TTL from disk, patches last snapshot to Final, escalates (EXIT_LEVEL_2)."""
    logger.debug(
        "[exit_validator_success] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    # Internal TTL read — file is written by execute_ontology before this exit is called
    ttl_content = ""
    try:
        with open(_TTL_LATEST, "r", encoding="utf-8") as f:
            ttl_content = f.read()
    except OSError as exc:
        logger.warning("[exit_validator_success] Failed to read TTL from disk: %s", exc)

    # Patch last Python snapshot to Final/validated (read from state, not from parameter)
    snapshots = list(tool_context.state.get("python_code_snapshots", []))
    if snapshots:
        snapshots[-1]["label"] = "Final"
        snapshots[-1]["status"] = "validated"
        tool_context.state["python_code_snapshots"] = snapshots

    # Write TTL content to ttl_code_snapshots (separate key for TTL tab)
    if ttl_content:
        ttl_snapshots = list(tool_context.state.get("ttl_code_snapshots", []))
        ttl_snapshots.append({"label": "TTL", "code": ttl_content, "iteration": 0, "status": "validated"})
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
