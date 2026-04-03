"""
Ontology tools for the master agent.

Available tools
---------------
File reading
  - ``read_python_files``    -- grep-like read of one or more files; returns keyword-matched sections with context lines (use full_content=True for full file)
  - ``scan_python_folder``   -- recursively scan a directory; returns keyword-matched sections per .py file (use full_content=True for full source of matching files)

Class mapping
  - ``search_class_mapping`` -- search classes_bob/scratch JSONL by keyword; returns deduplicated list of absolute file paths

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
from datetime import datetime
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
# Internal helper: _custom_grep
# ---------------------------------------------------------------------------

def _custom_grep(
    abs_path: str,
    original_path: str,
    keywords: list[str],
    context_lines: int,
    full_content: bool,
    _content: Optional[str] = None,
) -> dict:
    """Grep-like search within a single file.

    Returns sections of the file that contain the keywords, each surrounded by
    ``context_lines`` lines of context.  Overlapping windows are merged so no
    line is repeated.

    Args:
        abs_path:      Resolved absolute path to the file.
        original_path: Path as supplied by the caller (used verbatim in output).
        keywords:      Case-insensitive substrings to search for.
        context_lines: Lines to include before and after each match.
        full_content:  If True, return the whole file as one section (keywords
                       are ignored for line selection but the file must still
                       have been pre-screened by the caller for relevance).
        _content:      Pre-read file text — skips the open() call.  Used by
                       scan_python_folder to avoid reading each file twice.

    Returns a plain dict (not a JSON string) with this shape::

        {
          "path":          "<original_path>",
          "abs_path":      "<abs_path>",
          "total_lines":   <int>,
          "matches_found": <int | null>,   # null when full_content=True
          "full_content":  <bool>,
          "sections": [
            {
              "start_line": <int>,          # 1-based, inclusive
              "end_line":   <int>,          # 1-based, inclusive
              "content":    "<text>"        # line-numbered, one line per row
            },
            ...
          ],
          "error": <str | null>
        }
    """
    if _content is None:
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                _content = fh.read()
        except OSError as exc:
            return {
                "path": original_path,
                "abs_path": abs_path,
                "total_lines": 0,
                "matches_found": None,
                "full_content": full_content,
                "sections": [],
                "error": str(exc),
            }

    raw_lines = _content.splitlines(keepends=True)
    total_lines = len(raw_lines)
    pad = len(str(total_lines))  # digit width for aligned line-number prefix

    def _format_section(start_0: int, end_0: int) -> dict:
        """Render a contiguous slice of lines (0-based indices, inclusive)."""
        content = "".join(
            f"{start_0 + i + 1:{pad}d}: {line}"
            for i, line in enumerate(raw_lines[start_0 : end_0 + 1])
        )
        return {
            "start_line": start_0 + 1,
            "end_line": end_0 + 1,
            "content": content,
        }

    if full_content:
        return {
            "path": original_path,
            "abs_path": abs_path,
            "total_lines": total_lines,
            "matches_found": None,
            "full_content": True,
            "sections": [_format_section(0, total_lines - 1)] if total_lines else [],
            "error": None,
        }

    lower_keywords = [kw.lower() for kw in keywords]

    # Collect 0-based indices of every line that contains at least one keyword.
    # Enumeration order is ascending, so match_indices is already sorted.
    match_indices = [
        i
        for i, line in enumerate(raw_lines)
        if any(kw in line.lower() for kw in lower_keywords)
    ]

    if not match_indices:
        return {
            "path": original_path,
            "abs_path": abs_path,
            "total_lines": total_lines,
            "matches_found": 0,
            "full_content": False,
            "sections": [],
            "error": None,
        }

    # Build context windows (0-based, inclusive) and merge overlapping ones.
    # Because match_indices is sorted, a single left-to-right pass suffices.
    windows: list[list[int]] = []
    for idx in match_indices:
        start = max(0, idx - context_lines)
        end = min(total_lines - 1, idx + context_lines)
        if windows and start <= windows[-1][1] + 1:
            # Overlapping or directly adjacent — extend the last window.
            windows[-1][1] = max(windows[-1][1], end)
        else:
            windows.append([start, end])

    return {
        "path": original_path,
        "abs_path": abs_path,
        "total_lines": total_lines,
        "matches_found": len(match_indices),
        "full_content": False,
        "sections": [_format_section(s, e) for s, e in windows],
        "error": None,
    }


# ---------------------------------------------------------------------------
# Tool: read_python_files
# ---------------------------------------------------------------------------

def read_python_files(
    paths: list[str],
    keywords: list[str],
    context_lines: int = 40,
    full_content: bool = False,
) -> str:
    """Read one or more files and return the sections that contain the keywords.

    Accepts absolute paths or paths relative to the project root.
    Handles any text file — not limited to ``.py``.

    Typical uses
    ------------
    Read sections of a library class file (paths from ``search_class_mapping``)::

        read_python_files(["<abs_path>"], keywords=["Damper", "airOutlet"])

    Read a file you need in full (e.g. the lessons skill, ontology.py)::

        read_python_files(["agent/skills/skill-ontology-lessons/SKILL.md"],
                          keywords=[], full_content=True)

    Parameters
    ----------
    paths
        One or more file paths to read.
    keywords
        Case-insensitive substrings to search for.  Every line that contains
        at least one keyword is included in the output, surrounded by
        ``context_lines`` lines of context.  Overlapping windows are merged.
    context_lines
        Lines to include before and after each matching line (default 40).
    full_content
        If True, return the entire file regardless of keywords.  Use when you
        know you need the whole file.

    Either ``keywords`` must be non-empty **or** ``full_content`` must be True.
    If neither holds, the tool returns an error entry.

    Returns a JSON array, one object per path::

        [
          {
            "path":          "<original path>",
            "abs_path":      "<resolved absolute path>",
            "total_lines":   <int>,
            "matches_found": <int | null>,
            "full_content":  <bool>,
            "sections": [
              {
                "start_line": <int>,
                "end_line":   <int>,
                "content":    "<line-numbered text>"
              }
            ],
            "error": <str | null>
          },
          ...
        ]
    """
    if not keywords and not full_content:
        return json.dumps(
            [{"error": "Provide at least one keyword, or set full_content=True to return the entire file."}],
            ensure_ascii=False,
        )

    results: list[dict] = []
    for path in paths:
        expanded = os.path.expanduser(path)
        if os.path.isabs(expanded):
            resolved = os.path.realpath(expanded)
        else:
            resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, expanded))

        if not os.path.exists(resolved):
            results.append({
                "path": path,
                "abs_path": resolved,
                "total_lines": 0,
                "matches_found": None,
                "full_content": full_content,
                "sections": [],
                "error": f"File not found: {resolved}",
            })
        elif not os.path.isfile(resolved):
            results.append({
                "path": path,
                "abs_path": resolved,
                "total_lines": 0,
                "matches_found": None,
                "full_content": full_content,
                "sections": [],
                "error": f"Not a file: {resolved}",
            })
        else:
            results.append(
                _custom_grep(resolved, path, keywords, context_lines, full_content)
            )

    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: scan_python_folder
# ---------------------------------------------------------------------------

def scan_python_folder(
    path: str,
    keywords: list[str],
    context_lines: int = 40,
    full_content: bool = False,
    force: bool = False,
) -> str:
    """Recursively scan a directory and return sections of every ``.py`` file
    that contains at least one keyword (case-insensitive substring match).

    Use for exploratory scans of known directories, e.g.
    ``agent/223p/examples/pritoni`` to find reference implementations.
    For a specific file whose path you already know, prefer
    ``read_python_files`` instead.

    Accepts absolute paths or paths relative to the project root.

    Parameters
    ----------
    path
        Directory to scan recursively.
    keywords
        Case-insensitive substrings used to (a) decide which files are
        returned and (b) locate the matching lines within those files.
    context_lines
        Lines to include before and after each match (default 40).
        Overlapping windows within the same file are merged.
    full_content
        If True, return the full source of each matching file instead of
        just the sections around the keyword hits.  The keyword filter still
        applies — only files that *contain* a keyword are returned.
    force
        If True, bypass the 10-file cap and return all matching files.

    Returns a JSON object::

        {
          "root":          "<resolved absolute path>",
          "context_lines": <int>,
          "full_content":  <bool>,
          "files": [
            {
              "path":          "<relative path from root>",
              "abs_path":      "<absolute path>",
              "total_lines":   <int>,
              "matches_found": <int | null>,
              "full_content":  <bool>,
              "sections": [
                {
                  "start_line": <int>,
                  "end_line":   <int>,
                  "content":    "<line-numbered text>"
                }
              ],
              "error": <str | null>
            },
            ...
          ]
        }

    When the 10-file cap is exceeded and ``force`` is False::

        {
          "root":        "<resolved absolute path>",
          "message":     "There are N matching files. Narrow keywords or set force=True.",
          "match_count": N,
          "files":       []
        }
    """
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        resolved = os.path.realpath(expanded)
    else:
        resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, expanded))

    if not os.path.exists(resolved):
        return json.dumps({"error": f"Path not found: {resolved!r}", "root": resolved, "files": []})
    if not os.path.isdir(resolved):
        return json.dumps({"error": f"Not a directory: {resolved!r}", "root": resolved, "files": []})

    lower_keywords = [kw.lower() for kw in keywords]

    # Single-pass walk: read each .py file once, screen for keywords, and keep
    # the content in memory so _custom_grep does not need to open() it again.
    candidates: list[tuple[str, str, str]] = []  # (abs_path, rel_path, content)
    for dirpath, _dirnames, filenames in os.walk(resolved):
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, resolved).replace("\\", "/")
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except OSError:
                continue  # silently skip unreadable files
            if any(kw in content.lower() for kw in lower_keywords):
                candidates.append((abs_path, rel_path, content))

    MAX_FILES = 10
    if len(candidates) > MAX_FILES and not force:
        return json.dumps({
            "root": resolved,
            "message": (
                f"There are {len(candidates)} files matching these keywords. "
                "Narrow your keywords or set force=True."
            ),
            "match_count": len(candidates),
            "files": [],
        }, ensure_ascii=False, indent=2)

    files = [
        _custom_grep(abs_path, rel_path, keywords, context_lines, full_content, _content=content)
        for abs_path, rel_path, content in candidates
    ]

    return json.dumps({
        "root": resolved,
        "context_lines": context_lines,
        "full_content": full_content,
        "files": files,
    }, ensure_ascii=False, indent=2)


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
    """Search for classes in the bob and scratch libraries by keyword.

    Returns a JSON array of unique absolute file paths for every class whose
    name contains any of the keywords (case-insensitive substring match).
    Multiple classes that live in the same file are deduplicated — each path
    appears at most once.

    Pass the returned list directly to ``read_python_files`` as the ``paths``
    argument::

        paths = search_class_mapping(keywords=["Fan", "Damper"])
        # → ["/abs/.../bob/equipment/hvac/fan.py",
        #    "/abs/.../scratch/hvac/damper.py"]

        read_python_files(paths, keywords=["Fan", "Damper"])

    Returns an empty array ``[]`` if no matches are found or if the library
    installation cannot be located.
    """
    site_packages = _find_site_packages()
    if not site_packages:
        return json.dumps([])

    lower_keywords = [kw.lower() for kw in keywords]
    seen: set[str] = set()
    abs_paths: list[str] = []
    for library in ("bob", "scratch"):
        for entry in _load_mapping(library):
            if any(kw in entry["class_name"].lower() for kw in lower_keywords):
                abs_path = os.path.join(site_packages, entry["path"])
                if abs_path not in seen:
                    seen.add(abs_path)
                    abs_paths.append(abs_path)
    return json.dumps(abs_paths, ensure_ascii=False, indent=2)


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

    # 3. Dated write: mapper/uploads/python/ontology_YYYYMMDD_HHMMSS.py (consumed by frontend)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dated_path = os.path.join(os.path.dirname(ONTOLOGY_FILE), f"ontology_{timestamp}.py")
    try:
        with open(dated_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:
        logger.warning("Failed to write dated archive %s: %s", dated_path, exc)

    # 4. Session archive write
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

                # Dated copy: mapper/uploads/ttl/ontology_YYYYMMDD_HHMMSS.ttl (consumed by frontend)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dated_ttl_path = os.path.join(TTL_OUTPUT_DIR, f"ontology_{timestamp}.ttl")
                try:
                    with open(dated_ttl_path, "w", encoding="utf-8") as fh:
                        fh.write(ttl_content)
                except OSError as exc:
                    logger.warning("Failed to write dated TTL archive %s: %s", dated_ttl_path, exc)

                if tool_context:
                    # Snapshot behavior
                    snapshots = list(tool_context.state.get("ttl_code_snapshots", []))
                    snapshots.append({
                        "label": "TTL",
                        "code": ttl_content,
                        "iteration": 0,
                        "status": "validated"
                    })
                    tool_context.state["ttl_code_snapshots"] = snapshots

                    # Patch last Python snapshot to Final/validated
                    # (moved from exit_validator_success — domain logic belongs here, not in exit tools)
                    try:
                        py_snapshots = list(tool_context.state.get("python_code_snapshots", []))
                        if py_snapshots:
                            py_snapshots[-1]["label"] = "Final"
                            py_snapshots[-1]["status"] = "validated"
                            tool_context.state["python_code_snapshots"] = py_snapshots
                    except OSError as exc:
                        logger.warning("Failed to patch python_code_snapshots: %s", exc)

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
