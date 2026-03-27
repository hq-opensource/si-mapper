"""
Exit tools for the ontology validator sub-agent.

``checkpoint_code``
    Appends a Fix N snapshot to ``python_code_snapshots`` and increments the
    iteration counter.  Does NOT escalate — the validator loop continues.

``exit_validator_success``
    Saves the final Python code via ``checkpoint_code``, patches the last
    snapshot to label="Final"/status="validated", writes the TTL output to
    ``ttl_code_snapshots``, sets ``ONTOLOGY_VALIDATION_SUCCESS=True``, then
    escalates to terminate the validator loop.

``exit_validator_failure``
    Signals validation failure and escalates.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from google.adk.tools import ToolContext

from utils.project_utils import get_system_path

logger = logging.getLogger(__name__)

# Legacy fallback paths (used when no active system is in state)
_LEGACY_UPLOADS_PYTHON = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "python"
_LEGACY_UPLOADS_TTL    = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "ttl"


def _resolve_uploads_python(tool_context: ToolContext) -> Path:
    """Return the python dir scoped to the active system; fall back to legacy path."""
    resolved = get_system_path(tool_context, "python")
    if os.path.isabs(resolved):
        return Path(resolved)
    return _LEGACY_UPLOADS_PYTHON


def _resolve_uploads_ttl(tool_context: ToolContext) -> Path:
    """Return the ttl dir scoped to the active system; fall back to legacy path."""
    resolved = get_system_path(tool_context, "ttl")
    if os.path.isabs(resolved):
        return Path(resolved)
    return _LEGACY_UPLOADS_TTL


def _persist_python(code: str, tool_context: ToolContext) -> None:
    """Write versioned + latest Python file to the active system's uploads/python/."""
    try:
        dest = _resolve_uploads_python(tool_context)
        dest.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned = dest / f"ontology_{ts}.py"
        latest    = dest / "latest_ontology.py"
        versioned.write_text(code, encoding="utf-8")
        latest.write_text(code, encoding="utf-8")
        logger.info("[exit_validator_success] Python written → %s + latest_ontology.py", versioned.name)
    except Exception as exc:  # pragma: no cover
        logger.warning("[exit_validator_success] Failed to persist Python: %s", exc)


def _persist_ttl(ttl_content: str, tool_context: ToolContext) -> None:
    """Write versioned + latest TTL file to the active system's uploads/ttl/."""
    try:
        dest = _resolve_uploads_ttl(tool_context)
        dest.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned = dest / f"ontology_{ts}.ttl"
        latest    = dest / "latest_ontology.ttl"
        versioned.write_text(ttl_content, encoding="utf-8")
        latest.write_text(ttl_content, encoding="utf-8")
        logger.info("[exit_validator_success] TTL written → %s + latest_ontology.ttl", versioned.name)
    except Exception as exc:  # pragma: no cover
        logger.warning("[exit_validator_success] Failed to persist TTL: %s", exc)


def checkpoint_code(tool_context: ToolContext, code: str) -> dict:
    """Appends a Fix N snapshot. Does NOT escalate — validator loop continues."""
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


def exit_validator_success(
    tool_context: ToolContext,
    code: str,
    summary: str,
    ttl_content: str = "",
) -> dict:
    """Saves final Python snapshot, writes TTL snapshot, patches to Final/validated, escalates."""
    logger.debug(
        "[exit_validator_success] called by %s",
        getattr(tool_context, "agent_name", "unknown"),
    )
    checkpoint_code(tool_context, code)
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
        _persist_ttl(ttl_content, tool_context)
    _persist_python(code, tool_context)
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
