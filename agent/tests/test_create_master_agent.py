"""
Unit tests for agent/master_architecture/create_master_agent.py.

Verifies that OntologyGeneratorAgent and OntologyValidatorAgent are correctly
wired into the master agent as flat sub-agents.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch


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


def test_create_master_agent_imports_ontology_generator():
    """create_master_agent.py imports OntologyGeneratorAgent."""
    import importlib
    import master_architecture.create_master_agent as mod
    assert hasattr(mod, "OntologyGeneratorAgent")


def test_create_master_agent_imports_ontology_validator():
    """create_master_agent.py imports OntologyValidatorAgent."""
    import master_architecture.create_master_agent as mod
    assert hasattr(mod, "OntologyValidatorAgent")


def test_ontology_subagents_list_contains_both_agents():
    """The ontology_subagents list inside create_master_agent contains exactly 2 agents."""
    import ast
    import pathlib

    src = pathlib.Path("master_architecture/create_master_agent.py").read_text()
    tree = ast.parse(src)

    # Find the ontology_subagents assignment
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ontology_subagents":
                    # Should be a list with 2 elements
                    assert isinstance(node.value, ast.List)
                    assert len(node.value.elts) == 2
                    found = True
    assert found, "ontology_subagents assignment not found in create_master_agent.py"


def test_main_py_does_not_import_sequential_agent():
    """main.py must not import Ontology223PSequentialAgent (old pipeline removed)."""
    import pathlib
    src = pathlib.Path("main.py").read_text()
    assert "Ontology223PSequentialAgent" not in src
