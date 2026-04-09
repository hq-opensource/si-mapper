"""
project_utils.py — Path helpers for multi-project / multi-system support.

Resolves file-system paths relative to the active project and system folders
stored in ToolContext.state (injected by the frontend via CopilotKit).

State shape expected (set by the frontend via 13-07):
    {
      "active_project": {
          "id": "proj-abc123",
          "name": "Building A",
          "folder_path": "proj-abc123",
          "graphivac_project_id": "P-j8QIvTGH7p",
      },
      "active_system": {
          "id": "sys-aaa111",
          "name": "Chilled Water Plant",
          "folder_path": "sys-aaa111",
          "graphivac_grid_id": "G-LAiRS3mgp6",
          "neo4j_db_name": "sys-aaa111",
          "ai_model_name": "gemini-3.1-pro",
      }
    }

Path hierarchy:
    {PROJECTS_FOLDER}/{active_project.folder_path}/{active_system.folder_path}/{relative}

Fallback behaviour:
    When PROJECTS_FOLDER is unset, or either folder_path is missing from state,
    the helper returns the bare *relative* string so callers can detect that no
    resolved path is available and fall back to their legacy hardcoded path.
"""

from __future__ import annotations

import logging
import os
import pathlib

logger = logging.getLogger(__name__)


# ── Field-level state accessors ───────────────────────────────────────────────


def get_graphivac_project_id(tool_context) -> str:
    """
    Returns the Graphivac project ID for the active project.
    Falls back to the GRAPHIVAC_PROJECT_ID environment variable.
    """
    if tool_context is not None:
        active_project = tool_context.state.get("active_project") or {}
        project_id = active_project.get("graphivac_project_id", "")
        if project_id:
            return project_id
    return os.getenv("GRAPHIVAC_PROJECT_ID", "")


def get_graphivac_grid_id(tool_context) -> str:
    """
    Returns the Graphivac grid ID for the active system.
    Falls back to the GRAPHIVAC_GRID_ID environment variable.
    """
    if tool_context is not None:
        active_system = tool_context.state.get("active_system") or {}
        grid_id = active_system.get("graphivac_grid_id", "")
        if grid_id:
            return grid_id
    return os.getenv("GRAPHIVAC_GRID_ID", "")


VALID_GRAPH_BACKENDS = {"neo4j_single", "neo4j_prefix", "neo4j_enterprise", "graphdb"}


def get_graph_backend() -> str:
    """
    Returns the active graph backend mode from the GRAPH_BACKEND environment
    variable.  Defaults to 'neo4j_single' when the variable is unset or empty.

    Valid values: neo4j_single | neo4j_prefix | neo4j_enterprise | graphdb
    """
    backend = os.getenv("GRAPH_BACKEND", "neo4j_single").strip().lower()
    if backend not in VALID_GRAPH_BACKENDS:
        logger.warning(
            "Unknown GRAPH_BACKEND value '%s'; falling back to 'neo4j_single'", backend
        )
        return "neo4j_single"
    return backend


def get_neo4j_db_name(tool_context) -> str:
    """
    Returns the Neo4j database name for the active system.

    - neo4j_single mode: always returns 'neo4j' (Community Edition compatible).
    - neo4j_prefix mode: always returns 'neo4j' (single shared DB, ns-filtered).
    - neo4j_enterprise mode: reads neo4j_db_name from active_system state.
                             Each system gets its own named database.
                             CREATE DATABASE is managed automatically.
    """
    backend = get_graph_backend()
    if backend in ("neo4j_single", "neo4j_prefix"):
        return "neo4j"
    # neo4j_enterprise / legacy: read from state
    if tool_context is not None:
        active_system = tool_context.state.get("active_system") or {}
        db_name = active_system.get("neo4j_db_name", "")
        if db_name:
            return db_name
    raise ValueError(
        "Neo4j database name not found. "
        "Ensure 'neo4j_db_name' is set on the active system in the tool context, "
        "or set GRAPH_BACKEND=neo4j_single."
    )


# ── Path helpers ──────────────────────────────────────────────────────────────


def get_system_path(tool_context, relative: str) -> str:
    """
    Resolve *relative* against the active system's folder.

    Returns an **absolute** path string when PROJECTS_FOLDER and both
    folder_path values are present in state.  Returns the bare *relative*
    string otherwise — callers should check ``os.path.isabs(result)`` to
    detect the fallback case.

    Args:
        tool_context: ADK ToolContext or None (None always triggers fallback).
        relative: Path relative to the system folder, e.g. "src/ontology.py".

    Returns:
        Absolute path string, or *relative* when context is unavailable.
    """
    if tool_context is not None:
        active_system = tool_context.state.get("active_system") or None
        if active_system is not None:
            sys_folder = active_system.get("folder_path", "")
            if sys_folder:
                return get_project_path(tool_context, str(pathlib.Path(sys_folder) / relative))

    # Fallback: caller should detect this via os.path.isabs() returning False
    return relative


def get_project_path(tool_context, relative: str) -> str:
    """
    Resolve *relative* against the active project's folder (one level up from
    the system folder).  Use this for resources that are per-project rather
    than per-system (e.g. uploaded reference documents in ``uploads/``).

    Returns an **absolute** path string when PROJECTS_FOLDER and the project's
    folder_path are present in state.  Returns the bare *relative* string
    otherwise.

    Args:
        tool_context: ADK ToolContext or None (None always triggers fallback).
        relative: Path relative to the project folder, e.g. "uploads/bacnet".

    Returns:
        Absolute path string, or *relative* when context is unavailable.
    """
    if tool_context is not None:
        active_project = tool_context.state.get("active_project") or None
        if active_project is not None:
            projects_root = os.getenv("PROJECTS_FOLDER", "")
            proj_folder = active_project.get("folder_path", "")
            if projects_root and proj_folder:
                return str(pathlib.Path(projects_root) / proj_folder / relative)

    # Fallback: caller should detect this via os.path.isabs() returning False
    return relative

