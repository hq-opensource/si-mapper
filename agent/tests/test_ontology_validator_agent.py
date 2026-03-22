"""Unit tests for OntologyValidatorAgent instantiation."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from sub_agents.loop_agents.loop_wrapper import LoopWrapper


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock external dependencies that require real model/file access."""
    with (
        patch("utils.models.get_adk_model", return_value="mocked-model"),
        patch(
            "utils.prompt_utils.load_prompt_instruction",
            return_value="mocked prompt instruction",
        ),
    ):
        yield


def test_ontology_validator_agent_is_loop_wrapper():
    from sub_agents.ontology_validator.agent import OntologyValidatorAgent

    agent = OntologyValidatorAgent(model_name="test-model")
    assert isinstance(agent, LoopWrapper)


def test_ontology_validator_agent_name():
    from sub_agents.ontology_validator.agent import OntologyValidatorAgent

    agent = OntologyValidatorAgent(model_name="test-model")
    assert agent.name == "OntologyValidatorAgent"


def test_ontology_validator_agent_max_iterations():
    from sub_agents.ontology_validator.agent import OntologyValidatorAgent

    agent = OntologyValidatorAgent(model_name="test-model")
    assert agent.max_iterations == 100


def test_ontology_validator_internal_name():
    from sub_agents.ontology_validator.agent import OntologyValidatorAgent

    agent = OntologyValidatorAgent(model_name="test-model")
    internal = agent.sub_agents[0]
    assert internal.name == "OntologyValidatorInternal"


def test_validator_has_new_tools():
    from sub_agents.ontology_validator.agent import OntologyValidatorAgent
    agent = OntologyValidatorAgent(model_name="test-model")
    internal = agent.sub_agents[0]
    tool_names = [t.__name__ if hasattr(t, "__name__") else str(t) for t in internal.tools]
    assert "scan_python_files_filtered" in tool_names
    assert "search_class_mapping" in tool_names

def test_validator_no_old_tools():
    from sub_agents.ontology_validator.agent import OntologyValidatorAgent
    agent = OntologyValidatorAgent(model_name="test-model")
    internal = agent.sub_agents[0]
    tool_names = [t.__name__ if hasattr(t, "__name__") else str(t) for t in internal.tools]
    assert "list_library_classes" not in tool_names
    assert "get_class_details" not in tool_names
    assert "scan_python_files" not in tool_names
