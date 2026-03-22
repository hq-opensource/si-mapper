"""
Tool helpers for the _223p agent.

Exposes Python library introspection tools, a file-scanning utility, and
ontology read/write/execute tools as OpenAI-compatible function schemas that
LiteLLM can pass directly in the ``tools=`` parameter.

Available tools
---------------
Library introspection
  - ``list_library_classes``  – list all public classes in an inspectable library
  - ``get_class_details``     – full details for one or more classes
  - ``scan_python_files``     – read every .py file in a directory tree

Ontology (223p/src/ontology.py)
  - ``read_ontology``         – read current source of ontology.py
  - ``write_ontology``        – overwrite ontology.py (auto-backup)
  - ``execute_ontology``      – run ontology.py and return stdout/stderr/TTL path
  - ``read_prompt``           – read the prompt.md generation reference
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import pkgutil
import shutil
import subprocess
import sys
import textwrap
from typing import Any, Optional
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset, ToolContext

__all__ = [
    # Library introspection
    "INSPECTABLE_LIBRARIES",
    "list_library_classes",
    "LIST_LIBRARY_CLASSES_SCHEMA",
    "get_class_details",
    "GET_CLASS_DETAILS_SCHEMA",
    "scan_python_files",
    "SCAN_PYTHON_FILES_SCHEMA",
    "scan_python_files_filtered",
    "SCAN_PYTHON_FILES_FILTERED_SCHEMA",
    # Ontology tools
    "ONTOLOGY_FILE",
    "TTL_OUTPUT_DIR",
    "read_ontology",
    "READ_ONTOLOGY_SCHEMA",
    "write_ontology",
    "WRITE_ONTOLOGY_SCHEMA",
    "execute_ontology",
    "EXECUTE_ONTOLOGY_SCHEMA",
    "read_prompt",
    "READ_PROMPT_SCHEMA",
]


# ---------------------------------------------------------------------------
# Library introspection tools
# ---------------------------------------------------------------------------
# To make an additional library discoverable by the agent, simply add its
# top-level import name to INSPECTABLE_LIBRARIES.  No other changes needed.

INSPECTABLE_LIBRARIES: list[str] = ["bob", "scratch"]


def _inspect_package(package_name: str) -> dict[str, Any]:
    """
    Walk every module inside *package_name* and collect all classes defined
    within it (excluding imported third-party classes).

    Returns a dict keyed by fully-qualified class name, each value being a
    summary dict with keys: module, bases, docstring, attributes, methods.
    """
    try:
        root = importlib.import_module(package_name)
    except ImportError as exc:
        return {"error": f"Cannot import {package_name!r}: {exc}"}

    classes: dict[str, Any] = {}

    for _, modname, _ in pkgutil.walk_packages(
        root.__path__, prefix=package_name + "."
    ):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue

        for name, obj in inspect.getmembers(mod, inspect.isclass):
            # Only include classes that are actually defined in this package.
            if not obj.__module__.startswith(package_name):
                continue
            fqn = f"{obj.__module__}.{obj.__qualname__}"
            if fqn in classes:
                continue

            bases = [
                f"{b.__module__}.{b.__qualname__}"
                for b in obj.__bases__
                if b is not object
            ]

            # Public instance attributes from __init__ annotations + __annotations__
            attrs: list[str] = []
            for klass in inspect.getmro(obj):
                for attr, hint in getattr(klass, "__annotations__", {}).items():
                    if not attr.startswith("_"):
                        hint_str = (
                            hint.__name__
                            if isinstance(hint, type)
                            else str(hint)
                        )
                        entry = f"{attr}: {hint_str}"
                        if entry not in attrs:
                            attrs.append(entry)

            # Public methods (exclude dunder)
            methods: list[str] = []
            for mname, mobj in inspect.getmembers(obj, predicate=inspect.isfunction):
                if mname.startswith("_"):
                    continue
                try:
                    sig = str(inspect.signature(mobj))
                except (ValueError, TypeError):
                    sig = "(...)"
                methods.append(f"{mname}{sig}")

            classes[fqn] = {
                "name": obj.__qualname__,
                "module": obj.__module__,
                "bases": bases,
                "docstring": textwrap.dedent(inspect.getdoc(obj) or "").strip(),
                "attributes": attrs,
                "methods": methods,
            }

    return classes


# Module-level cache so repeated calls are instant.
_library_cache: dict[str, dict[str, Any]] = {}


def _get_library_classes(library: str) -> dict[str, Any]:
    if library not in _library_cache:
        _library_cache[library] = _inspect_package(library)
    return _library_cache[library]


# ------------------------------------------------------------------
# Tool: list_library_classes
# ------------------------------------------------------------------

def list_library_classes(library: str) -> str:
    """
    Return a JSON list of all public classes in *library* together with their
    module path, base classes, and a one-line summary of their docstring.

    Use this first to discover what is available; then call
    ``get_class_details`` for the full signature of a specific class.
    """
    if library not in INSPECTABLE_LIBRARIES:
        return json.dumps(
            {
                "error": f"Library {library!r} is not in the inspectable list.",
                "available": INSPECTABLE_LIBRARIES,
            }
        )

    classes = _get_library_classes(library)
    if "error" in classes:
        return json.dumps(classes)

    summary = []
    for fqn, info in sorted(classes.items()):
        first_line = info["docstring"].split("\n")[0] if info["docstring"] else ""
        summary.append(
            {
                "fqn": fqn,
                "name": info["name"],
                "module": info["module"],
                "bases": info["bases"],
                "summary": first_line,
            }
        )
    return json.dumps(summary, ensure_ascii=False, indent=2)


LIST_LIBRARY_CLASSES_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "list_library_classes",
        "description": (
            "List all public classes in a Python library installed in the agent's "
            "virtual environment. Returns each class's fully-qualified name, module, "
            "base classes, and a one-line docstring summary. "
            f"Available libraries: {INSPECTABLE_LIBRARIES}."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "library": {
                    "type": "string",
                    "description": (
                        "Top-level package name to inspect. "
                        f"Must be one of: {INSPECTABLE_LIBRARIES}."
                    ),
                    "enum": INSPECTABLE_LIBRARIES,
                }
            },
            "required": ["library"],
        },
    },
}


# ------------------------------------------------------------------
# Tool: get_class_details
# ------------------------------------------------------------------

def get_class_details(library: str, class_names: list[str]) -> str:
    """
    Return full details for multiple classes: their module, base classes, full
    docstring, public attributes (with type hints), and public method
    signatures.

    *class_names* may contain short names (e.g. "Fan") or fully-qualified
    names (e.g. "bob.equipment.hvac.fan.Fan"). If multiple classes share
    the same short name the first match is returned together with a note.
    Returns a dict mapping each class name to its details or an error.
    """
    if library not in INSPECTABLE_LIBRARIES:
        return json.dumps(
            {
                "error": f"Library {library!r} is not in the inspectable list.",
                "available": INSPECTABLE_LIBRARIES,
            }
        )

    classes = _get_library_classes(library)
    if "error" in classes:
        return json.dumps(classes)

    results = {}
    for class_name in class_names:
        match = classes.get(class_name)
        if match is None:
            candidates = [
                (fqn, info)
                for fqn, info in classes.items()
                if info["name"] == class_name or fqn.endswith(f".{class_name}")
            ]
            if not candidates:
                results[class_name] = {
                    "error": f"Class {class_name!r} not found in library {library!r}.",
                    "hint": "Call list_library_classes first to see available class names.",
                }
                continue
            fqn, match = candidates[0]
            if len(candidates) > 1:
                match = dict(match)
                match["note"] = (
                    f"Multiple classes named {class_name!r} found; "
                    f"returning first match ({fqn}). "
                    f"Other matches: {[c[0] for c in candidates[1:]]}."
                )
        results[class_name] = match

    return json.dumps(results, ensure_ascii=False, indent=2)


GET_CLASS_DETAILS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_class_details",
        "description": (
            "Return the full details of multiple Python classes from an inspectable "
            "library: module path, base classes, complete docstring, public "
            "attributes with type hints, and public method signatures. "
            "Call list_library_classes first to discover available class names."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "library": {
                    "type": "string",
                    "description": f"Library the class belongs to. Must be one of: {INSPECTABLE_LIBRARIES}.",
                    "enum": INSPECTABLE_LIBRARIES,
                },
                "class_names": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": (
                            "Short class name (e.g. 'Fan') or fully-qualified name "
                            "(e.g. 'bob.equipment.hvac.fan.Fan')."
                        ),
                    },
                    "description": "List of class names to retrieve details for.",
                },
            },
            "required": ["library", "class_names"],
        },
    },
}


# ------------------------------------------------------------------
# Tool: scan_python_files
# ------------------------------------------------------------------

def scan_python_files(path: str) -> str:
    """
    Recursively scan a directory (relative or absolute) and return the full
    source content of every ``.py`` file found, indexed by their path
    relative to *path*.

    Returns a JSON object::

        {
          "root": "<resolved absolute path>",
          "files": {
            "subdir/module.py": "<source code>",
            ...
          },
          "error": "<message>"   // only present on failure
        }

    *path* may be absolute (e.g. ``"C:/Projects/foo"``) or relative to the
    current working directory (e.g. ``"223p/src"``).
    """

    resolved = os.path.realpath(os.path.expanduser(path))

    if not os.path.exists(resolved):
        return json.dumps({"error": f"Path not found: {resolved!r}", "root": resolved, "files": {}})
    if not os.path.isdir(resolved):
        return json.dumps({"error": f"Path is not a directory: {resolved!r}", "root": resolved, "files": {}})

    files: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(resolved):
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, resolved).replace("\\", "/")
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    files[rel_path] = fh.read()
            except OSError as exc:
                files[rel_path] = f"<ERROR reading file: {exc}>"

    return json.dumps({"root": resolved, "files": files}, ensure_ascii=False, indent=2)


SCAN_PYTHON_FILES_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "scan_python_files",
        "description": (
            "Recursively scan a directory and return the full source code of every "
            "Python (.py) file it contains, indexed by their relative path. "
            "Accepts both absolute paths (e.g. 'C:/Projects/foo') and paths relative "
            "to the current working directory (e.g. '223p/src'). "
            "Use this to read library source, generated output, or any other Python "
            "code on disk that the agent needs to understand."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Absolute or relative path to the directory to scan. "
                        "All subdirectories are traversed recursively."
                    ),
                }
            },
            "required": ["path"],
        },
    },
}


# ------------------------------------------------------------------
# Tool: scan_python_files_filtered
# ------------------------------------------------------------------

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
# Ontology tools
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

ONTOLOGY_FILE = os.path.join(_PROJECT_ROOT, "223p", "src", "ontology.py")
TTL_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "223p", "ttl")

# Reused across schemas that take no parameters.
_EMPTY_PARAMS: dict[str, Any] = {"type": "object", "properties": {}, "required": []}


def _read_text_file(path: str) -> str:
    """Read *path* and return a ``{"path", "content"}`` JSON response.

    On failure the response includes an ``"error"`` key instead of content.
    """
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


def read_ontology() -> str:
    """Read the current content of ``223p/src/ontology.py``.

    Returns a JSON object::

        {"path": "<absolute path>", "content": "<source code>"}
        {"path": "...", "content": "", "error": "<message>"}  // on failure
    """
    return _read_text_file(ONTOLOGY_FILE)


def write_ontology(content: str, tool_context: Optional[ToolContext] = None) -> str:
    """Overwrite ``223p/src/ontology.py`` with *content*.

    A numbered backup is created before writing
    (e.g. ``ontology_1.py``, ``ontology_2.py``, …).

    Returns a JSON object::

        {"path": "...", "success": true, "backup": "<backup path>"}
        {"path": "...", "success": false, "error": "<message>"}  // on failure
    """
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


def read_prompt() -> str:
    """Read the 223P ontology generator ``prompt.md`` reference file.

    Returns a JSON object::

        {"path": "<absolute path>", "content": "<text>"}
        {"path": "...", "content": "", "error": "<message>"}  // on failure
    """
    return _read_text_file(os.path.join(_HERE, "generator", "prompt.md"))


READ_ONTOLOGY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_ontology",
        "description": (
            "Read the current source code of the ontology.py file located at "
            "223p/src/ontology.py. Returns the full Python source as a string. "
            "Use this to inspect the current state of the file before making corrections."
        ),
        "parameters": _EMPTY_PARAMS,
    },
}

WRITE_ONTOLOGY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "write_ontology",
        "description": (
            "Overwrite the content of 223p/src/ontology.py with new Python source code. "
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

EXECUTE_ONTOLOGY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "execute_ontology",
        "description": (
            "Execute 223p/src/ontology.py using the agent's Python interpreter. "
            "Returns stdout, stderr, return code, and the generated TTL file path "
            "if execution was successful."
        ),
        "parameters": _EMPTY_PARAMS,
    },
}

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

skills_toolset = skill_toolset.SkillToolset(
    skills = [
        load_skill_from_dir(os.path.join(_PROJECT_ROOT, "agent", "skills", "skill-read-code"))
    ]
)

# ---------------------------------------------------------------------------
# CLI entry-point for quick inspection
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import pprint

    _TOOLS = {
        "list_library_classes": (list_library_classes, LIST_LIBRARY_CLASSES_SCHEMA),
        "get_class_details":    (get_class_details,    GET_CLASS_DETAILS_SCHEMA),
        "scan_python_files":    (scan_python_files,    SCAN_PYTHON_FILES_SCHEMA),
        "read_ontology":        (read_ontology,        READ_ONTOLOGY_SCHEMA),
        "write_ontology":       (write_ontology,       WRITE_ONTOLOGY_SCHEMA),
        "execute_ontology":     (execute_ontology,     EXECUTE_ONTOLOGY_SCHEMA),
        "read_prompt":          (read_prompt,          READ_PROMPT_SCHEMA),
    }

    parser = argparse.ArgumentParser(
        description=(
            "Tool CLI.\n\n"
            "With no arguments: print all tool schemas.\n"
            "With --tool TOOL_NAME: invoke that tool and print the result."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tool", metavar="TOOL_NAME", help="Name of the tool to invoke.")
    parser.add_argument(
        "--args", metavar="JSON", default="{}",
        help='Tool arguments as a JSON object string (default: "{}").',
    )
    parser.add_argument("--path", metavar="PATH", default=None,
                        help='Shortcut for {"path": "..."}. Useful for scan_python_files.')
    parser.add_argument("--library", metavar="LIB", default=None,
                        help='Shortcut for the "library" argument.')
    parser.add_argument("--class-name", metavar="CLASS", default=None, dest="class_name",
                        help='Shortcut for the "class_name" argument.')
    cli_args = parser.parse_args()

    shortcut: dict[str, Any] = {}
    if cli_args.path is not None:
        shortcut["path"] = cli_args.path
    if cli_args.library is not None:
        shortcut["library"] = cli_args.library
    if cli_args.class_name is not None:
        shortcut["class_name"] = cli_args.class_name

    if shortcut:
        arguments: dict[str, Any] = shortcut
    else:
        try:
            arguments = json.loads(cli_args.args)
        except json.JSONDecodeError as exc:
            print(f"ERROR: --args is not valid JSON: {exc}")
            raise SystemExit(1)

    if cli_args.tool is None:
        pprint.pprint([schema for _, schema in _TOOLS.values()])
    elif cli_args.tool not in _TOOLS:
        print(f"ERROR: tool {cli_args.tool!r} not found.\nAvailable: {', '.join(_TOOLS)}")
        raise SystemExit(1)
    else:
        fn, _ = _TOOLS[cli_args.tool]
        print(f"{'─' * 60}")
        print(fn(**arguments) or "(empty response)")
