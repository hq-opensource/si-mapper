"""Unit tests for OntologyGeneratorAgent instantiation."""
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


def test_ontology_generator_agent_is_loop_wrapper():
    from sub_agents.ontology_generator.agent import OntologyGeneratorAgent

    agent = OntologyGeneratorAgent(model_name="test-model")
    assert isinstance(agent, LoopWrapper)


def test_ontology_generator_agent_name():
    from sub_agents.ontology_generator.agent import OntologyGeneratorAgent

    agent = OntologyGeneratorAgent(model_name="test-model")
    assert agent.name == "OntologyGeneratorAgent"


def test_ontology_generator_agent_max_iterations():
    from sub_agents.ontology_generator.agent import OntologyGeneratorAgent

    agent = OntologyGeneratorAgent(model_name="test-model")
    assert agent.max_iterations == 50


def test_ontology_generator_internal_name():
    from sub_agents.ontology_generator.agent import OntologyGeneratorAgent

    agent = OntologyGeneratorAgent(model_name="test-model")
    internal = agent.sub_agents[0]
    assert internal.name == "OntologyGeneratorInternal"
