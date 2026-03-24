"""
Ontology tools for the master agent.

Provides Python library introspection, file-scanning utilities, and
ontology read/write/execute tools that the master agent calls directly
(no sub-agent delegation).

Available tools
---------------
Introspection / mapping
  - ``scan_python_files_filtered`` – scan .py files matching keywords
  - ``search_class_mapping``       – grep across classes_bob/scratch JSONL

Ontology (223p/src/ontology.py)
  - ``read_ontology``    – read current source of ontology.py
  - ``write_ontology``   – overwrite ontology.py (auto-backup)
  - ``execute_ontology`` – run ontology.py and return stdout/stderr/TTL path
  - ``read_prompt``      – read the prompt.md generation reference
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from typing import Any, Optional

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path anchors
# ---------------------------------------------------------------------------
# This file: agent/tools/ontology_tools.py
# parents[0] = tools/, parents[1] = agent/, parents[2] = project_root/
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

ONTOLOGY_FILE = os.path.join(_PROJECT_ROOT, "223p", "src", "ontology.py")
TTL_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "223p", "ttl")

_MAPPINGS_DIR = os.path.join(
    _PROJECT_ROOT, "agent", "skills", "skill-read-code", "assets", "mappings"
)
_JSONL_FILES = {
    "bob": "classes_bob.jsonl",
    "scratch": "classes_scratch.jsonl",
}
_mapping_cache: dict[str, list[dict]] = {}

# Prompt.md lives in the original sub-agent generator folder.
_PROMPT_MD = os.path.join(
    _PROJECT_ROOT, "agent", "sub_agents", "_223p", "generator", "prompt.md"
)

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
    """Overwrite ``223p/src/ontology.py`` with *content*.

    A numbered backup is created before writing
    (e.g. ``ontology_1.py``, ``ontology_2.py``, …).

    Returns a JSON object::

        {"path": "...", "success": true, "backup": "<backup path>"}
        {"path": "...", "success": false, "error": "<message>"}  // on failure
    """
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

    os.makedirs(os.path.dirname(ONTOLOGY_FILE), exist_ok=True)

    backup_path, backup_err = _backup_file(ONTOLOGY_FILE)
    if backup_err:
        return json.dumps({"path": ONTOLOGY_FILE, "success": False, "error": backup_err})

    try:
        with open(ONTOLOGY_FILE, "w", encoding="utf-8") as fh:
            fh.write(content)
        result: dict[str, Any] = {"path": ONTOLOGY_FILE, "success": True}
        if backup_path is not None:
            result["backup"] = backup_path
        return json.dumps(result)
    except OSError as exc:
        return json.dumps({"path": ONTOLOGY_FILE, "success": False, "error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: execute_ontology
# ---------------------------------------------------------------------------

def execute_ontology(tool_context: Optional[ToolContext] = None) -> str:
    """
    Execute 223p/src/ontology.py in a subprocess using the agent's virtual
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

    run_cwd = os.path.join(_PROJECT_ROOT, "223p")
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
                    logger.warning("Failed to read TTL file for snapshot: %s", e)

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
