"""
Tool helpers for the _223p agent.

Exposes Python library introspection tools and a file-scanning utility as
OpenAI-compatible function schemas that LiteLLM can pass directly in the
``tools=`` parameter.

Ontology-specific tools (read/write/execute ontology, scan_python_files_filtered,
search_class_mapping, read_prompt, skills_toolset) have been moved to
``sub_agents.tools.ontology_tools`` and are re-exported here for backward
compatibility.

Available tools
---------------
Library introspection
  - ``list_library_classes``  – list all public classes in an inspectable library
  - ``get_class_details``     – full details for one or more classes
  - ``scan_python_files``     – read every .py file in a directory tree

Ontology (223p/src/ontology.py)  [re-exported from sub_agents.tools.ontology_tools]
  - ``read_ontology``         – read current source of ontology.py
  - ``write_ontology``        – overwrite ontology.py (auto-backup)
  - ``execute_ontology``      – run ontology.py and return stdout/stderr/TTL path
  - ``read_prompt``           – read the prompt.md generation reference
  - ``scan_python_files_filtered`` – read .py files matching keywords
  - ``search_class_mapping``  – grep the bob/scratch class mapping JSONL files
  - ``skills_toolset``        – pre-loaded ADK SkillToolset
"""

from __future__ import annotations

import importlib
import inspect
import logging
import json
import os
import pkgutil
import textwrap
from typing import Any

logger = logging.getLogger(__name__)

# Re-export ontology tools from their new canonical location
from sub_agents.tools.ontology_tools import (  # noqa: E402
    scan_python_files_filtered,
    SCAN_PYTHON_FILES_FILTERED_SCHEMA,
    search_class_mapping,
    SEARCH_CLASS_MAPPING_SCHEMA,
    read_ontology,
    READ_ONTOLOGY_SCHEMA,
    write_ontology,
    WRITE_ONTOLOGY_SCHEMA,
    execute_ontology,
    EXECUTE_ONTOLOGY_SCHEMA,
    read_prompt,
    READ_PROMPT_SCHEMA,
    skills_toolset,
    ONTOLOGY_FILE,
    TTL_OUTPUT_DIR,
)

__all__ = [
    # Library introspection
    "INSPECTABLE_LIBRARIES",
    "list_library_classes",
    "LIST_LIBRARY_CLASSES_SCHEMA",
    "get_class_details",
    "GET_CLASS_DETAILS_SCHEMA",
    "scan_python_files",
    "SCAN_PYTHON_FILES_SCHEMA",
    # Re-exported from sub_agents.tools.ontology_tools
    "scan_python_files_filtered",
    "SCAN_PYTHON_FILES_FILTERED_SCHEMA",
    "search_class_mapping",
    "SEARCH_CLASS_MAPPING_SCHEMA",
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
    "skills_toolset",
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
