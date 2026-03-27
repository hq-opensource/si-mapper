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
import os
from datetime import datetime
from pathlib import Path

from google.adk.tools import ToolContext

from utils.project_utils import get_system_path

logger = logging.getLogger(__name__)

# Legacy fallback path (used when no active system is in state)
_LEGACY_UPLOADS_PYTHON = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "python"


def _resolve_uploads_python(tool_context: ToolContext) -> Path:
    """Return the python dir scoped to the active system; fall back to legacy path."""
    resolved = get_system_path(tool_context, "python")
    if os.path.isabs(resolved):
        return Path(resolved)
    return _LEGACY_UPLOADS_PYTHON


def _persist_python(code: str, label: str, tool_context: ToolContext) -> None:
    """Write versioned + latest Python file to the active system's uploads/python/."""
    try:
        dest = _resolve_uploads_python(tool_context)
        dest.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned = dest / f"ontology_{ts}.py"
        latest = dest / "latest_ontology.py"
        versioned.write_text(code, encoding="utf-8")
        latest.write_text(code, encoding="utf-8")
        logger.info("[%s] Python written → %s + latest_ontology.py", label, versioned.name)
    except Exception as exc:  # pragma: no cover
        logger.warning("[%s] Failed to persist Python to uploads: %s", label, exc)


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
    _persist_python(code, "exit_generator_success", tool_context)
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
