"""
Ontology tools for the ASHRAE 223P agents.

Exposes file-scanning utilities and ontology read/write/execute tools
as callable functions compatible with the Google ADK ``tools=`` parameter.

Available tools
---------------
File scanning / mapping
  - ``scan_python_files_filtered``  – read .py files matching keywords
  - ``search_class_mapping``        – grep the bob/scratch class mapping JSONL files

Ontology ([project]/[system]/python/)
  - ``read_ontology``   – read current source of ontology.py
  - ``write_ontology``  – overwrite ontology.py (auto-backup)
  - ``execute_ontology`` – run ontology.py and return stdout/stderr/TTL path

Prompt file reader
  - ``read_prompt``     – read the prompt.md generation reference

Skills
  - ``skills_toolset``  – pre-loaded ADK SkillToolset for the read-code skill
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from typing import Any, Optional

from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset, ToolContext

from utils.project_utils import get_system_path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))          # agent/sub_agents/tools/
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_223P_DIR = os.path.abspath(os.path.join(_HERE, "..", "_223p"))

ONTOLOGY_FILE = os.path.join(_PROJECT_ROOT, "223p", "src", "ontology.py")
TTL_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "223p", "ttl")

# ---------------------------------------------------------------------------
# search_class_mapping helpers
# ---------------------------------------------------------------------------

_MAPPINGS_DIR = os.path.join(
    _PROJECT_ROOT, "agent", "skills", "skill-read-code", "assets", "mappings"
)
_JSONL_FILES = {
    "bob": "classes_bob.jsonl",
    "scratch": "classes_scratch.jsonl",
}
_mapping_cache: dict[str, list[dict]] = {}


def _load_mapping(library: str) -> list[dict]:
    if library not in _mapping_cache:
        path = os.path.join(_MAPPINGS_DIR, _JSONL_FILES[library])
        entries = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        _mapping_cache[library] = entries
    return _mapping_cache[library]


# Reused across schemas that take no parameters.
_EMPTY_PARAMS: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

# ---------------------------------------------------------------------------
# Per-call path resolvers (multi-project support)
# ---------------------------------------------------------------------------


def _resolve_ontology_file(tool_context) -> str:
    """Return the absolute path to ontology.py for the active system."""
    if tool_context is not None:
        resolved = get_system_path(tool_context, os.path.join("python", "ontology.py"))
        if os.path.isabs(resolved):
            logger.info(f"Resolved ontology file path: {resolved}")
            return resolved
    logger.info(f"Resolved ontology file path: {ONTOLOGY_FILE}")
    return ONTOLOGY_FILE


def _resolve_ttl_dir(tool_context) -> str:
    """Return the absolute path to the TTL output directory for the active system."""
    if tool_context is not None:
        resolved = get_system_path(tool_context, "ttl")
        if os.path.isabs(resolved):
            logger.info(f"Resolved TTL output directory: {resolved}")
            return resolved
    logger.info(f"Resolved TTL output directory: {TTL_OUTPUT_DIR}")
    return TTL_OUTPUT_DIR


def _read_text_file(path: str) -> str:
    """Read *path* and return a ``{"path", "content"}`` JSON response."""
    if not os.path.exists(path):
        return json.dumps({"path": path, "content": "", "error": f"File not found: {path}"})
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.dumps({"path": path, "content": fh.read()}, ensure_ascii=False)
    except OSError as exc:
        return json.dumps({"path": path, "content": "", "error": str(exc)})


def _backup_file(path: str) -> tuple[str | None, str | None]:
    """Create a numbered backup of *path* (e.g. ``file_1.py``, ``file_2.py``, …).

    Returns ``(backup_path, error_message)``.
    """
    if not os.path.exists(path):
        return None, None
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    candidate = f"{base}_{counter}{ext}"
    try:
        shutil.copy2(path, candidate)
        return candidate, None
    except OSError as exc:
        return None, f"Backup failed: {exc}"


# ---------------------------------------------------------------------------
# Tool: scan_python_files_filtered
# ---------------------------------------------------------------------------


def scan_python_files_filtered(path: str, keywords: list[str]) -> str:
    """
    Recursively scan a directory and return the full source content of every
    ``.py`` file whose content contains at least one of the given keywords
    (case-insensitive substring match).

    Returns a JSON object with the same shape as ``scan_python_files``::

        {
          "root": "<resolved absolute path>",
          "files": {
            "subdir/module.py": "<source code>",
            ...
          },
          "error": "<message>"   // only present on failure
        }

    Use this instead of ``scan_python_files`` when you know which class names
    or terms you need — it reduces context window consumption by only returning
    files that are relevant.
    """
    resolved = os.path.realpath(os.path.expanduser(path))

    if not os.path.exists(resolved):
        return json.dumps({"error": f"Path not found: {resolved!r}", "root": resolved, "files": {}})
    if not os.path.isdir(resolved):
        return json.dumps({"error": f"Path is not a directory: {resolved!r}", "root": resolved, "files": {}})

    lower_keywords = [kw.lower() for kw in keywords]

    files: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(resolved):
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, resolved).replace("\\", "/")
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except OSError as exc:
                files[rel_path] = f"<ERROR reading file: {exc}>"
                continue
            content_lower = content.lower()
            if any(kw in content_lower for kw in lower_keywords):
                files[rel_path] = content

    return json.dumps({"root": resolved, "files": files}, ensure_ascii=False, indent=2)


SCAN_PYTHON_FILES_FILTERED_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "scan_python_files_filtered",
        "description": (
            "Recursively scan a directory and return the full source code of .py files "
            "whose content contains at least one of the given keywords (case-insensitive "
            "substring match). Use this instead of scan_python_files when you know "
            "which class names or terms you need."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the directory to scan.",
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of keywords to filter by. A file is included if its content contains at least one keyword (case-insensitive).",
                },
            },
            "required": ["path", "keywords"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool: search_class_mapping
# ---------------------------------------------------------------------------


def search_class_mapping(keywords: list[str]) -> str:
    """
    Grep-like search across classes_bob.jsonl and classes_scratch.jsonl.
    Returns entries where class_name contains any keyword (case-insensitive).
    Each result includes a 'library' field ('bob' or 'scratch').
    """
    lower_keywords = [kw.lower() for kw in keywords]
    results = []
    for library in ("bob", "scratch"):
        for entry in _load_mapping(library):
            name_lower = entry["class_name"].lower()
            if any(kw in name_lower for kw in lower_keywords):
                results.append({**entry, "library": library})
    return json.dumps(results, ensure_ascii=False, indent=2)


SEARCH_CLASS_MAPPING_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_class_mapping",
        "description": (
            "Search the ASHRAE 223P class mappings (bob and scratch libraries) "
            "for classes matching any of the given keywords. Returns a list of "
            "{class_name, path, types, library} dicts. Use the 'path' field to "
            "then read the actual Python source with scan_python_files_filtered."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to match against class_name (case-insensitive substring).",
                },
            },
            "required": ["keywords"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool: read_ontology
# ---------------------------------------------------------------------------


def read_ontology(tool_context: Optional[ToolContext] = None) -> str:
    """Read the current content of ``[project]/[system]/python/ontology.py`` (or the active system's
    equivalent when multi-project state is available).

    Returns a JSON object::

        {"path": "<absolute path>", "content": "<source code>"}
        {"path": "...", "content": "", "error": "<message>"}  // on failure
    """
    return _read_text_file(_resolve_ontology_file(tool_context))


READ_ONTOLOGY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_ontology",
        "description": (
            "Read the current source code of the ontology.py file located at "
            "[project]/[system]/python/ontology.py. Returns the full Python source as a string. "
            "Use this to inspect the current state of the file before making corrections."
        ),
        "parameters": _EMPTY_PARAMS,
    },
}


# ---------------------------------------------------------------------------
# Tool: write_ontology
# ---------------------------------------------------------------------------


def write_ontology(content: str, tool_context: Optional[ToolContext] = None) -> str:
    """Overwrite ``[project]/[system]/python/ontology.py`` (or the active system's equivalent) with *content*.

    A numbered backup is created before writing
    (e.g. ``ontology_1.py``, ``ontology_2.py``, …).

    Returns a JSON object::

        {"path": "...", "success": true, "backup": "<backup path>"}
        {"path": "...", "success": false, "error": "<message>"}  // on failure
    """
    ontology_file = _resolve_ontology_file(tool_context)

    if tool_context:
        # Update session state for the frontend (Python snapshots)
        snapshots = list(tool_context.state.get("python_code_snapshots", []))
        label = f"Iteration {len(snapshots) + 1}"
        snapshots.append({
            "label": label,
            "code": content,
            "iteration": len(snapshots),
            "status": "generated"
        })
        tool_context.state["python_code_snapshots"] = snapshots

    os.makedirs(os.path.dirname(ontology_file), exist_ok=True)

    backup_path, backup_err = _backup_file(ontology_file)
    if backup_err:
        return json.dumps({"path": ontology_file, "success": False, "error": backup_err})

    try:
        with open(ontology_file, "w", encoding="utf-8") as fh:
            fh.write(content)
        result: dict[str, Any] = {"path": ontology_file, "success": True}
        if backup_path is not None:
            result["backup"] = backup_path
        return json.dumps(result)
    except OSError as exc:
        return json.dumps({"path": ontology_file, "success": False, "error": str(exc)})


WRITE_ONTOLOGY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "write_ontology",
        "description": (
            "Overwrite the content of [project]/[system]/python/ontology.py with new Python source code. "
            "Before writing, a numbered backup is automatically created "
            "(e.g. ontology_1.py, ontology_2.py, …). "
            "The entire file content must be provided — partial updates are not supported."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": (
                        "The complete Python source code to write to ontology.py. "
                        "Must be valid Python. Do not include markdown fences."
                    ),
                }
            },
            "required": ["content"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool: execute_ontology
# ---------------------------------------------------------------------------


def execute_ontology(tool_context: Optional[ToolContext] = None) -> str:
    """
    Execute [project]/[system]/python/ontology.py in a subprocess using the agent's virtual
    environment Python interpreter.

    Returns a JSON object::

        {
          "success": true | false,
          "returncode": <int>,
          "stdout": "<text>",
          "stderr": "<text>",
          "ttl_file": "<path>"   // only present when success == true
        }
    """
    venv_python = os.path.join(_PROJECT_ROOT, "agent", ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    ontology_file = _resolve_ontology_file(tool_context)
    ttl_output_dir = _resolve_ttl_dir(tool_context)

    # run_cwd: the parent of the "python/" folder (i.e. the system root or legacy "223p/")
    if os.path.isabs(ontology_file):
        run_cwd = str(os.path.dirname(os.path.dirname(ontology_file)))
    else:
        run_cwd = os.path.join(_PROJECT_ROOT, "223p")

    os.makedirs(ttl_output_dir, exist_ok=True)

    try:
        proc = subprocess.run(
            [venv_python, ontology_file],
            capture_output=True,
            text=True,
            cwd=run_cwd,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "returncode": -1, "stdout": "",
                           "stderr": "Execution timed out after 120 seconds.", "ttl_file": None})
    except Exception as exc:
        return json.dumps({"success": False, "returncode": -1, "stdout": "",
                           "stderr": str(exc), "ttl_file": None})

    success = proc.returncode == 0
    ttl_file: str | None = None
    if success:
        candidate = os.path.join(ttl_output_dir, "ontology.ttl")
        if os.path.exists(candidate):
            ttl_file = candidate

            # Update session state for the frontend (TTL snapshots)
            if tool_context:
                try:
                    with open(ttl_file, "r", encoding="utf-8") as f:
                        ttl_content = f.read()

                    snapshots = list(tool_context.state.get("ttl_code_snapshots", []))
                    label = f"Version {len(snapshots) + 1}"
                    snapshots.append({
                        "label": label,
                        "code": ttl_content,
                        "iteration": len(snapshots),
                        "status": "validated"
                    })
                    tool_context.state["ttl_code_snapshots"] = snapshots
                except Exception as e:
                    logger.warning(f"Failed to read TTL file for snapshot: {e}")

    return json.dumps({"success": success, "returncode": proc.returncode,
                       "stdout": proc.stdout, "stderr": proc.stderr,
                       "ttl_file": ttl_file}, ensure_ascii=False)


EXECUTE_ONTOLOGY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "execute_ontology",
        "description": (
            "Execute [project]/[system]/python/ontology.py using the agent's Python interpreter. "
            "Returns stdout, stderr, return code, and the generated TTL file path "
            "if execution was successful."
        ),
        "parameters": _EMPTY_PARAMS,
    },
}


# ---------------------------------------------------------------------------
# Tool: read_prompt
# ---------------------------------------------------------------------------


def read_prompt() -> str:
    """Read the 223P ontology generator ``prompt.md`` reference file.

    Returns a JSON object::

        {"path": "<absolute path>", "content": "<text>"}
        {"path": "...", "content": "", "error": "<message>"}  // on failure
    """
    return _read_text_file(os.path.join(_223P_DIR, "generator", "prompt.md"))


READ_PROMPT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_prompt",
        "description": (
            "Read the prompt.md file used as reference when generating ontology.py. "
            "Documents the 223P ontology generation conventions, library usage "
            "guidelines, and modeling requirements."
        ),
        "parameters": _EMPTY_PARAMS,
    },
}


# ---------------------------------------------------------------------------
# Skills toolset
# ---------------------------------------------------------------------------

skills_toolset = skill_toolset.SkillToolset(
    skills=[
        load_skill_from_dir(os.path.join(_PROJECT_ROOT, "agent", "skills", "skill-read-code"))
    ]
)

__all__ = [
    # Constants
    "ONTOLOGY_FILE",
    "TTL_OUTPUT_DIR",
    # Tools
    "scan_python_files_filtered",
    "search_class_mapping",
    "read_ontology",
    "write_ontology",
    "execute_ontology",
    "read_prompt",
    "skills_toolset",
    # Schemas
    "SCAN_PYTHON_FILES_FILTERED_SCHEMA",
    "SEARCH_CLASS_MAPPING_SCHEMA",
    "READ_ONTOLOGY_SCHEMA",
    "WRITE_ONTOLOGY_SCHEMA",
    "EXECUTE_ONTOLOGY_SCHEMA",
    "READ_PROMPT_SCHEMA",
]

