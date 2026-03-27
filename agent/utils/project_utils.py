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

import os
import pathlib


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
    projects_root = os.getenv("PROJECTS_FOLDER", "")
    active_project: dict = {}
    active_system: dict = {}

    if tool_context is not None:
        active_project = tool_context.state.get("active_project") or {}
        active_system = tool_context.state.get("active_system") or {}

    proj_folder = active_project.get("folder_path", "")
    sys_folder = active_system.get("folder_path", "")

    if projects_root and proj_folder and sys_folder:
        return str(pathlib.Path(projects_root) / proj_folder / sys_folder / relative)

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
    projects_root = os.getenv("PROJECTS_FOLDER", "")
    active_project: dict = {}

    if tool_context is not None:
        active_project = tool_context.state.get("active_project") or {}

    proj_folder = active_project.get("folder_path", "")

    if projects_root and proj_folder:
        return str(pathlib.Path(projects_root) / proj_folder / relative)

    # Fallback: caller should detect this via os.path.isabs() returning False
    return relative


