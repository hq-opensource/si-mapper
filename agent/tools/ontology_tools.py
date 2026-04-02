"""
Ontology tools for the master agent.

Available tools
---------------
Introspection / mapping
  - ``scan_python_files_filtered`` -- scan .py files matching keywords
  - ``search_class_mapping``       -- grep across classes_bob/scratch JSONL

Ontology (agent/223p/ontology.py)
  - ``read_ontology``    -- read current source of ontology.py
  - ``write_ontology``   -- overwrite ontology.py (three-write: scratch + session archive + uploads)
  - ``execute_ontology`` -- run ontology.py and return stdout/stderr/TTL path (three-write for TTL)
  - ``read_prompt``      -- read the prompt.md generation reference
  - ``extract_lessons``  -- read all session iteration files for LLM lesson extraction (HITL-gated)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from google.adk.tools import ToolContext
from tools.ontology_exit_tools import _persist_python, _persist_ttl

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
ONTOLOGY_FILE = os.path.join(_223P_DIR, "ontology.py")
TTL_OUTPUT_DIR = _223P_DIR  # ontology.ttl written as agent/223p/ontology.ttl
_MAPPINGS_DIR = os.path.join(_223P_DIR, "mappings")
PYTHON_ITERATIONS_DIR = os.path.join(_223P_DIR, "python_iterations")
TTL_ITERATIONS_DIR = os.path.join(_223P_DIR, "ttl_iterations")
LESSONS_FILE = os.path.join(_AGENT_ROOT, "skills", "skill-ontology-lessons", "SKILL.md")
_PROMPT_MD = os.path.join(_223P_DIR, "ref", "code", "prompt.md")

_JSONL_FILES = {
    "bob": "classes_bob.jsonl",
    "scratch": "classes_scratch.jsonl",
}
_mapping_cache: dict[str, list[dict]] = {}

# Reused across schemas that take no parameters.
_EMPTY_PARAMS: dict[str, Any] = {"type": "object", "properties": {}, "required": []}


# ---------------------------------------------------------------------------
# Tool: scan_python_files_filtered
# ---------------------------------------------------------------------------

def scan_python_files_filtered(path: str, keywords: list[str]) -> str:
    """
    Recursively scan a directory and return the full source content of every
    ``.py`` file whose content contains at least one of the given keywords
    (case-insensitive substring match).

    Returns a JSON object::

        {
          "root": "<resolved absolute path>",
          "files": {
            "subdir/module.py": "<source code>",
            ...
          },
          "error": "<message>"   // only present on failure
        }
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
    """Locate the site-packages directory where bob and scratch are installed.

    Uses importlib to find the bob package, then derives site-packages from it.
    Falls back to None if the package is not importable.
    """
    import importlib.util
    spec = importlib.util.find_spec("bob")
    if spec and spec.origin:
        # spec.origin = .../site-packages/bob/__init__.py
        # parent = .../site-packages/bob/
        # parent.parent = .../site-packages/
        return str(os.path.dirname(os.path.dirname(spec.origin)))
    return None


def search_class_mapping(keywords: list[str]) -> str:
    """
    Grep-like search across classes_bob.jsonl and classes_scratch.jsonl.
    Returns entries where class_name contains any keyword (case-insensitive).

    Each result includes:
      - 'library': 'bob' or 'scratch'
      - 'path': relative path within the library (e.g. 'bob/equipment/hvac/fan.py')
      - 'abs_path': absolute path to the file in the venv site-packages
      - 'scan_dir': parent directory of the file — pass this directly to
                    scan_python_files_filtered to read the class source
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
                    result["scan_dir"] = os.path.dirname(abs_path)
                results.append(result)
    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Ontology tools — shared helpers
# ---------------------------------------------------------------------------

def _read_text_file(path: str) -> str:
    if not os.path.exists(path):
        return json.dumps({"path": path, "content": "", "error": f"File not found: {path}"})
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.dumps({"path": path, "content": fh.read()}, ensure_ascii=False)
    except OSError as exc:
        return json.dumps({"path": path, "content": "", "error": str(exc)})


def _backup_file(path: str) -> tuple[str | None, str | None]:
    """Create a numbered backup of *path* (e.g. ``file_1.py``, ``file_2.py``, …).

    Returns ``(backup_path, error_message)``.  Both are ``None`` when the
    source file does not exist yet (nothing to back up).
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
# Tool: read_ontology
# ---------------------------------------------------------------------------

def read_ontology() -> str:
    """Read the current content of ``223p/src/ontology.py``.

    Returns a JSON object::

        {"path": "<absolute path>", "content": "<source code>"}
        {"path": "...", "content": "", "error": "<message>"}  // on failure
    """
    return _read_text_file(ONTOLOGY_FILE)


# ---------------------------------------------------------------------------
# Tool: write_ontology
# ---------------------------------------------------------------------------

def write_ontology(content: str, tool_context: Optional[ToolContext] = None) -> str:
    """Overwrite ``agent/223p/ontology.py`` with *content*.

    Implements the three-write pattern:
    1. Scratch write: agent/223p/ontology.py (immediate availability)
    2. Session archive: agent/223p/python_iterations/session_N/ontology_NNN.py
    3. Uploads write: mapper/uploads/python/ (real-time frontend visibility)

    A numbered backup is created before writing the scratch file.

    Returns a JSON object::

        {"path": "...", "success": true, "backup": "<backup path>"}
        {"path": "...", "success": false, "error": "<message>"}  // on failure
    """
    # 1. State snapshots (existing behavior -- keep as-is)
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

    # 2. Scratch write (existing behavior)
    os.makedirs(os.path.dirname(ONTOLOGY_FILE), exist_ok=True)
    backup_path, backup_err = _backup_file(ONTOLOGY_FILE)
    if backup_err:
        return json.dumps({"path": ONTOLOGY_FILE, "success": False, "error": backup_err})
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

    # 4. Uploads write (real-time frontend visibility)
    _persist_python(content, "write_ontology")

    result: dict[str, Any] = {"path": ONTOLOGY_FILE, "success": True}
    if backup_path is not None:
        result["backup"] = backup_path
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: execute_ontology
# ---------------------------------------------------------------------------

def execute_ontology(tool_context: Optional[ToolContext] = None) -> str:
    """
    Execute agent/223p/ontology.py in a subprocess using the agent's virtual
    environment Python interpreter.

    Implements the three-write pattern for TTL on success:
    1. Scratch: agent/223p/ontology.ttl (produced by the script)
    2. Session archive: agent/223p/ttl_iterations/session_N/ontology_NNN.ttl
    3. Uploads write: mapper/uploads/ttl/ (real-time frontend visibility)

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

    run_cwd = _223P_DIR
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
        candidate = os.path.join(TTL_OUTPUT_DIR, "ontology.ttl")
        if os.path.exists(candidate):
            ttl_file = candidate
            ttl_content: str | None = None
            try:
                with open(ttl_file, "r", encoding="utf-8") as f:
                    ttl_content = f.read()
            except Exception as e:
                logger.warning("Failed to read TTL file: %s", e)

            if ttl_content and tool_context:
                # Existing snapshot behavior
                snapshots = list(tool_context.state.get("ttl_code_snapshots", []))
                label = f"Version {len(snapshots) + 1}"
                snapshots.append({
                    "label": label,
                    "code": ttl_content,
                    "iteration": len(snapshots),
                    "status": "validated"
                })
                tool_context.state["ttl_code_snapshots"] = snapshots

                # Session archive write (three-write pattern)
                session_id = tool_context.state.get("ontology_session_id")
                iter_count = tool_context.state.get("ontology_code_iteration_count", 0)
                if session_id is not None:
                    session_dir = Path(TTL_ITERATIONS_DIR) / f"session_{session_id}"
                    session_dir.mkdir(parents=True, exist_ok=True)
                    ttl_archive = session_dir / f"ontology_{iter_count:03d}.ttl"
                    try:
                        ttl_archive.write_text(ttl_content, encoding="utf-8")
                    except OSError as exc:
                        logger.warning("Failed to write TTL archive %s: %s", ttl_archive, exc)

            # Uploads write (real-time frontend visibility)
            if ttl_content:
                _persist_ttl(ttl_content)

    return json.dumps({"success": success, "returncode": proc.returncode,
                       "stdout": proc.stdout, "stderr": proc.stderr,
                       "ttl_file": ttl_file}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: read_prompt
# ---------------------------------------------------------------------------

def read_prompt() -> str:
    """Read the 223P ontology generator ``prompt.md`` reference file.

    Returns a JSON object::

        {"path": "<absolute path>", "content": "<text>"}
        {"path": "...", "content": "", "error": "<message>"}  // on failure
    """
    return _read_text_file(_PROMPT_MD)


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
