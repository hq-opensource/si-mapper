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
