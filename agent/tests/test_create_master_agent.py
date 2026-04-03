"""
Unit tests for agent/master_architecture/create_master_agent.py.

Verifies that ontology tools are wired directly into the master agent
(no sub-agent wrappers) after Phase 13 migration.
"""
from __future__ import annotations

import ast
import pathlib
import sys
from unittest.mock import MagicMock


def _build_stubs() -> None:
    """Stub heavy ADK/dotenv imports so the module can be imported without a runtime."""
    stubs = {
        "google": MagicMock(),
        "google.adk": MagicMock(),
        "google.adk.agents": MagicMock(),
        "google.adk.skills": MagicMock(),
        "google.adk.tools": MagicMock(),
        "google.adk.tools.skill_toolset": MagicMock(),
        "dotenv": MagicMock(),
    }
    for name, mock in stubs.items():
        if name not in sys.modules:
            sys.modules[name] = mock


_build_stubs()


def test_no_ontology_generator_agent_import():
    """create_master_agent.py must NOT import OntologyGeneratorAgent."""
    src = pathlib.Path("master_architecture/create_master_agent.py").read_text()
    assert "OntologyGeneratorAgent" not in src


def test_no_ontology_validator_agent_import():
    """create_master_agent.py must NOT import OntologyValidatorAgent."""
    src = pathlib.Path("master_architecture/create_master_agent.py").read_text()
    assert "OntologyValidatorAgent" not in src


def test_no_ontology_subagents_list():
    """create_master_agent.py must NOT contain ontology_subagents list."""
    src = pathlib.Path("master_architecture/create_master_agent.py").read_text()
    assert "ontology_subagents" not in src


def test_imports_adapted_exit_tools():
    """create_master_agent.py must NOT import old ontology_exit_tools (deleted in Phase 19)."""
    src = pathlib.Path("master_architecture/create_master_agent.py").read_text()
    assert "from tools.ontology_exit_tools import" not in src
    for old_tool in ["exit_generator_success", "exit_generator_failure",
                     "exit_validator_success", "exit_validator_failure"]:
        assert old_tool not in src, f"{old_tool} still referenced in create_master_agent.py"


def test_max_iterations_is_100():
    """MasterMainLoopAgent default max_iterations must be 100."""
    src = pathlib.Path("master_architecture/level_2_master_main_loop.py").read_text()
    assert "100" in src
    # Verify via AST that the default is 100
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            for arg, default in zip(reversed(node.args.args), reversed(node.args.defaults)):
                if arg.arg == "max_iterations":
                    assert isinstance(default, ast.Constant) and default.value == 100


def test_main_py_does_not_import_sequential_agent():
    """main.py must not import Ontology223PSequentialAgent (old pipeline removed)."""
    src = pathlib.Path("main.py").read_text()
    assert "Ontology223PSequentialAgent" not in src
