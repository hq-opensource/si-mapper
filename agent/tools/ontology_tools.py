"""
Ontology tools for the master agent.

Available tools
---------------
File reading
  - ``read_python_files``    -- read one or more files by path (absolute or project-relative)
  - ``scan_python_folder``   -- recursively scan a directory, return .py files matching keywords

Class mapping
  - ``search_class_mapping`` -- grep across classes_bob/scratch JSONL; returns abs_path per class

Ontology (agent/223p/ontology.py)
  - ``write_ontology``   -- overwrite ontology.py (two-write: primary + session archive); auto-increments iteration counter
  - ``execute_ontology`` -- run ontology.py and return stdout/stderr/TTL path; Linux venv path checked first
  - ``extract_lessons``  -- read all session iteration files for LLM lesson extraction (HITL-gated)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path anchors
# ---------------------------------------------------------------------------
# This file: agent/tools/ontology_tools.py
# _HERE = agent/tools/
# _AGENT_ROOT = agent/
# _PROJECT_ROOT = project_root/
_HERE = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))    # agent/
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))  # project root

_223P_DIR = os.path.join(_AGENT_ROOT, "223p")
ONTOLOGY_FILE = os.path.join(_PROJECT_ROOT, "mapper", "uploads", "python", "latest_ontology.py")
TTL_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "mapper", "uploads", "ttl")
_MAPPINGS_DIR = os.path.join(_223P_DIR, "mappings")
PYTHON_ITERATIONS_DIR = os.path.join(_223P_DIR, "python_iterations")
TTL_ITERATIONS_DIR = os.path.join(_223P_DIR, "ttl_iterations")
LESSONS_FILE = os.path.join(_AGENT_ROOT, "skills", "skill-ontology-lessons", "SKILL.md")

_JSONL_FILES = {
    "bob": "classes_bob.jsonl",
    "scratch": "classes_scratch.jsonl",
}
_mapping_cache: dict[str, list[dict]] = {}

# Reused across schemas that take no parameters.
_EMPTY_PARAMS: dict[str, Any] = {"type": "object", "properties": {}, "required": []}


# ---------------------------------------------------------------------------
# Tool: read_python_files
# ---------------------------------------------------------------------------

def read_python_files(paths: list[str]) -> str:
    """Read one or more files by path and return their contents.

    Accepts absolute paths or paths relative to the project root
    (e.g. ``"agent/223p/ontology.py"``, ``"agent/223p/ref/code/prompt.md"``).
    Handles any text file — not limited to ``.py``.

    Typical uses:
    - Read a specific library class file: pass ``abs_path`` from
      ``search_class_mapping`` directly.
    - Read ``ontology.py``: pass ``"agent/223p/ontology.py"``.
    - Read the prompt reference: pass ``"agent/223p/ref/code/prompt.md"``.

    Returns a JSON object::

        {
          "<original path>": {"content": "<text>"},
          "<original path>": {"content": "", "error": "<message>"},
          ...
        }
    """
    results: dict[str, Any] = {}
    for path in paths:
        expanded = os.path.expanduser(path)
        # Resolve: try as-is first (works for absolute paths), then relative to project root.
        if os.path.isabs(expanded):
            resolved = os.path.realpath(expanded)
        else:
            resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, expanded))

        if not os.path.exists(resolved):
            results[path] = {"content": "", "error": f"File not found: {resolved}"}
        elif not os.path.isfile(resolved):
            results[path] = {"content": "", "error": f"Not a file: {resolved}"}
        else:
            try:
                with open(resolved, "r", encoding="utf-8", errors="replace") as fh:
                    results[path] = {"content": fh.read()}
            except OSError as exc:
                results[path] = {"content": "", "error": str(exc)}

    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: scan_python_folder
# ---------------------------------------------------------------------------

def scan_python_folder(path: str, keywords: list[str], force: bool = False) -> str:
    """Recursively scan a directory and return the full source of every
    ``.py`` file whose content contains at least one keyword
    (case-insensitive substring match).

    Use this for exploratory scans of known directories, e.g.
    ``agent/223p/ref/code`` to find reference implementations.
    For reading a specific file whose path you already know, use
    ``read_python_files`` instead.

    Accepts absolute paths or paths relative to the project root.

    If more than 10 files match and ``force`` is False, returns a message
    asking the agent to narrow keywords instead of returning file contents.
    Pass ``force=True`` to override the cap and return all matching files.

    Returns a JSON object::

        {
          "root": "<resolved absolute path>",
          "files": {
            "subdir/module.py": "<source code>",
            ...
          },
          "error": "<message>"   // only present on failure
        }

    Or when cap is exceeded::

        {
          "root": "<resolved absolute path>",
          "message": "There are N files matching these keywords. Narrow your keywords and try again.",
          "match_count": N,
          "files": {}
        }
    """
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        resolved = os.path.realpath(expanded)
    else:
        resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, expanded))

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
            if any(kw in content.lower() for kw in lower_keywords):
                files[rel_path] = content

    MAX_FILES = 10
    if len(files) > MAX_FILES and not force:
        return json.dumps({
            "root": resolved,
            "message": f"There are {len(files)} files matching these keywords. Narrow your keywords and try again.",
            "match_count": len(files),
            "files": {},
        }, ensure_ascii=False, indent=2)

    return json.dumps({"root": resolved, "files": files}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: search_class_mapping
# ---------------------------------------------------------------------------

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


def _find_site_packages() -> str | None:
    """Locate the site-packages directory where bob and scratch are installed."""
    import importlib.util
    spec = importlib.util.find_spec("bob")
    if spec and spec.origin:
        return str(os.path.dirname(os.path.dirname(spec.origin)))
    return None


def search_class_mapping(keywords: list[str]) -> str:
    """Grep-like search across classes_bob.jsonl and classes_scratch.jsonl.
    Returns entries where class_name contains any keyword (case-insensitive).

    Each result includes:
      - 'library': 'bob' or 'scratch'
      - 'path': relative path within the library (e.g. 'bob/equipment/hvac/fan.py')
      - 'abs_path': absolute path to the file — pass directly to ``read_python_files``
                    to read exactly that class file (one file, no scanning overhead)
    """
    site_packages = _find_site_packages()

    lower_keywords = [kw.lower() for kw in keywords]
    results = []
    for library in ("bob", "scratch"):
        for entry in _load_mapping(library):
            name_lower = entry["class_name"].lower()
            if any(kw in name_lower for kw in lower_keywords):
                result = {**entry, "library": library}
                if site_packages:
                    abs_path = os.path.join(site_packages, entry["path"])
                    result["abs_path"] = abs_path
                results.append(result)
    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Ontology tools — internal helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tool: write_ontology
# ---------------------------------------------------------------------------

def write_ontology(content: str, tool_context: Optional[ToolContext] = None) -> str:
    """Write *content* to ``mapper/uploads/python/latest_ontology.py``.

    Implements the two-write pattern:
    1. Primary write: mapper/uploads/python/latest_ontology.py
    2. Session archive: agent/223p/python_iterations/session_N/ontology_NNN.py

    Also auto-increments ``ontology_code_iteration_count`` and appends a snapshot
    to ``python_code_snapshots`` in tool_context.state (replaces the former
    standalone ``checkpoint_code`` tool).

    Returns a JSON object::

        {"path": "...", "success": true}
        {"path": "...", "success": false, "error": "<message>"}  // on failure
    """
    # 1. State snapshots
    if tool_context:
        snapshots = list(tool_context.state.get("python_code_snapshots", []))
        label = f"Iteration {len(snapshots) + 1}"
        snapshots.append({
            "label": label,
            "code": content,
            "iteration": len(snapshots),
            "status": "generated"
        })
        tool_context.state["python_code_snapshots"] = snapshots

    # 2. Primary write: mapper/uploads/python/latest_ontology.py
    os.makedirs(os.path.dirname(ONTOLOGY_FILE), exist_ok=True)
    try:
        with open(ONTOLOGY_FILE, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:
        return json.dumps({"path": ONTOLOGY_FILE, "success": False, "error": str(exc)})

    # 3. Session archive write
    if tool_context:
        session_id = tool_context.state.get("ontology_session_id")
        iter_count = tool_context.state.get("ontology_code_iteration_count", 0)
        if session_id is None:
            # Auto-detect from disk to avoid session ID drift after state reset
            existing = sorted(Path(PYTHON_ITERATIONS_DIR).glob("session_*"))
            session_id = len(existing) + 1 if existing else 1
            tool_context.state["ontology_session_id"] = session_id
        session_dir = Path(PYTHON_ITERATIONS_DIR) / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        archive_name = f"ontology_{iter_count + 1:03d}.py"
        archive = session_dir / archive_name
        try:
            archive.write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to write session archive %s: %s", archive, exc)

        # Auto-checkpoint: increment iteration counter (replaces standalone checkpoint_code tool)
        iter_count = tool_context.state.get("ontology_code_iteration_count", 0)
        tool_context.state["ontology_code_iteration_count"] = iter_count + 1

    return json.dumps({"path": ONTOLOGY_FILE, "success": True})


# ---------------------------------------------------------------------------
# Tool: execute_ontology
# ---------------------------------------------------------------------------

def execute_ontology(tool_context: Optional[ToolContext] = None) -> str:
    """Execute ``mapper/uploads/python/latest_ontology.py`` in a subprocess.

    Uses the agent's virtual environment Python interpreter (Linux path first,
    then Windows, then sys.executable fallback).

    The script writes ``latest_ontology.ttl`` directly to ``mapper/uploads/ttl/``
    (its working directory). On success, a versioned copy is also written to
    ``agent/223p/ttl_iterations/session_N/ontology_NNN.ttl``.

    Returns a JSON object::

        {
          "success": true | false,
          "returncode": <int>,
          "stdout": "<text>",
          "stderr": "<text>",
          "ttl_file": "<path>"   // only present when success == true
        }
    """
    _venv_base = os.path.join(_PROJECT_ROOT, "agent", ".venv")
    venv_python = os.path.join(_venv_base, "bin", "python")   # Linux: bin/python
    if not os.path.exists(venv_python):
        venv_python = os.path.join(_venv_base, "Scripts", "python.exe")  # Windows: Scripts/python.exe
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    run_cwd = TTL_OUTPUT_DIR
    os.makedirs(TTL_OUTPUT_DIR, exist_ok=True)

    try:
        proc = subprocess.run(
            [venv_python, ONTOLOGY_FILE],
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
        # The script writes latest_ontology.ttl directly to TTL_OUTPUT_DIR (mapper/uploads/ttl/).
        # No intermediate file — just read for state snapshots + write the versioned copy.
        latest = os.path.join(TTL_OUTPUT_DIR, "latest_ontology.ttl")
        if os.path.exists(latest):
            ttl_content: str | None = None
            try:
                with open(latest, "r", encoding="utf-8") as f:
                    ttl_content = f.read()
            except Exception as e:
                logger.warning("Failed to read TTL file: %s", e)

            if ttl_content:
                ttl_file = latest

                if tool_context:
                    # Snapshot behavior
                    snapshots = list(tool_context.state.get("ttl_code_snapshots", []))
                    label = f"Version {len(snapshots) + 1}"
                    snapshots.append({
                        "label": label,
                        "code": ttl_content,
                        "iteration": len(snapshots),
                        "status": "validated"
                    })
                    tool_context.state["ttl_code_snapshots"] = snapshots

                    # Session archive write — mirrors write_ontology session logic
                    session_id = tool_context.state.get("ontology_session_id")
                    iter_count = tool_context.state.get("ontology_code_iteration_count", 0)
                    if session_id is None:
                        # Auto-detect from python_iterations to stay in sync with Python session numbering
                        existing = sorted(Path(PYTHON_ITERATIONS_DIR).glob("session_*"))
                        session_id = len(existing) if existing else 1
                        tool_context.state["ontology_session_id"] = session_id
                    session_dir = Path(TTL_ITERATIONS_DIR) / f"session_{session_id}"
                    session_dir.mkdir(parents=True, exist_ok=True)
                    ttl_archive = session_dir / f"ontology_{iter_count + 1:03d}.ttl"
                    try:
                        ttl_archive.write_text(ttl_content, encoding="utf-8")
                    except OSError as exc:
                        logger.warning("Failed to write TTL archive %s: %s", ttl_archive, exc)

    return json.dumps({"success": success, "returncode": proc.returncode,
                       "stdout": proc.stdout, "stderr": proc.stderr,
                       "ttl_file": ttl_file}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: extract_lessons
# ---------------------------------------------------------------------------

EXTRACT_LESSONS_SCHEMA = {
    "name": "extract_lessons",
    "description": (
        "Read all Python iteration files from agent/223p/python_iterations/ "
        "across all sessions, plus the current content of skill-ontology-lessons/SKILL.md. "
        "Returns structured JSON for LLM analysis to MERGE new lessons into the existing skill — "
        "not replace it. HITL-gated: only call when user explicitly asks."
    ),
    "parameters": _EMPTY_PARAMS,
}


def extract_lessons(tool_context: Optional[ToolContext] = None) -> str:
    """Read all python iteration files across sessions for LLM-powered lesson extraction.

    Also reads the current content of skill-ontology-lessons/SKILL.md so the LLM
    can merge new findings into the existing skill rather than replacing it.

    Returns JSON::

        {
          "success": true,
          "sessions": {
            "session_1": [{"file": "ontology_001.py", "content": "<code>"}, ...]
          },
          "current_skill_content": "<current text of skill-ontology-lessons/SKILL.md>",
          "lessons_file": "<path to skill-ontology-lessons/SKILL.md>",
          "total_files": <int>
        }
    """
    # Read current skill content for merge context
    current_skill_content = ""
    try:
        skill_path = Path(LESSONS_FILE)
        if skill_path.exists():
            current_skill_content = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Failed to read skill-ontology-lessons/SKILL.md: %s", exc)

    iterations_dir = Path(PYTHON_ITERATIONS_DIR)
    if not iterations_dir.exists():
        return json.dumps({
            "success": True,
            "sessions": {},
            "current_skill_content": current_skill_content,
            "lessons_file": LESSONS_FILE,
            "total_files": 0,
        })

    sessions: dict[str, list[dict]] = {}
    total = 0
    for session_dir in sorted(iterations_dir.iterdir()):
        if not session_dir.is_dir() or not session_dir.name.startswith("session_"):
            continue
        files = []
        for py_file in sorted(session_dir.glob("*.py")):
            try:
                content = py_file.read_text(encoding="utf-8")
                files.append({"file": py_file.name, "content": content})
                total += 1
            except OSError as exc:
                logger.warning("Failed to read %s: %s", py_file, exc)
        if files:
            sessions[session_dir.name] = files

    return json.dumps({
        "success": True,
        "sessions": sessions,
        "current_skill_content": current_skill_content,
        "lessons_file": LESSONS_FILE,
        "total_files": total,
    }, ensure_ascii=False)
