"""
ASHRAE 223P Ontology Generator Agent.

Uses a LoopWrapper (max 50 iterations) around an LlmAgent.

The model is injected by the parent agent at construction time; callers must
supply ``model_name``.

Tools
-----
- All helpers from ``sub_agents/_223p/tool.py`` (library introspection,
  ontology read/write, prompt reader).
- Any common shared tools forwarded via the ``tools`` parameter.
- ``exit_generator_success`` — signals successful generation **and**
  persists the ``ONTOLOGY_GENERATION_SUCCESS`` state flag so the sequential
  agent can conditionally run the validator.
- ``exit_generator_failure`` — signals a generation failure and escalates.
"""
from __future__ import annotations

import os
import sys
from typing import Any

# ── Path bootstrap ────────────────────────────────────────────────────────────
_agent_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

if not __package__:
    if _agent_root not in sys.path:
        sys.path.insert(0, _agent_root)
# ─────────────────────────────────────────────────────────────────────────────

# ── SSL Verification disabled ────────────────────────────────────────────────
os.environ["SSL_CERT_FILE"] = ""
# ─────────────────────────────────────────────────────────────────────────────

from google.adk.agents import LlmAgent
from google.genai import types

from sub_agents._223p.tool import (
    scan_python_files_filtered,
    search_class_mapping,
    write_ontology,
    skills_toolset,
)
from tools.internal_grid_tools import read_internal_grid
from sub_agents.ontology_generator.exit_tools import (
    exit_generator_success,
    exit_generator_failure,
)
from sub_agents.loop_agents.loop_wrapper import LoopWrapper
from utils.callback_utils import shared_model_callback as model_callback, shared_before_model_callback as before_model_callback
from utils.models import get_adk_model
from utils.prompt_utils import load_prompt_instruction

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

#: Default model used when no parent agent injects one.
_STANDALONE_DEFAULT_MODEL = "github_copilot/claude-sonnet-4.5"

_MAX_ITERATIONS = 50

# ──────────────────────────────────────────────────────────────────────────────
# Public interface: LoopWrapper
# ──────────────────────────────────────────────────────────────────────────────


class OntologyGeneratorAgent(LoopWrapper):
    """
    Loop-wrapped 223P Ontology Generator Agent.

    The *model_name* parameter is required and is forwarded to the inner
    :class:`OntologyGeneratorInternal` LlmAgent.  Typically this is set
    (hardcoded) by the parent sequential agent.
    """

    def __init__(
        self,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        internal_agent = OntologyGeneratorInternal(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
        )
        super().__init__(
            name="OntologyGeneratorAgent",
            agent=internal_agent,
            description=(
                "Generates an ASHRAE 223P semantic ontology Python file from the live "
                "HVAC grid using the bob and scratch Python libraries."
            ),
            max_iterations=_MAX_ITERATIONS,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Internal LlmAgent
# ──────────────────────────────────────────────────────────────────────────────


class OntologyGeneratorInternal(LlmAgent):
    """Internal LlmAgent – not instantiated directly by callers."""

    def __init__(
        self,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        instruction = load_prompt_instruction("sub_agents/ontology_generator/prompt.md")

        # Local tools provided by this sub-agent
        local_tools: list[Any] = [
            skills_toolset,
            read_internal_grid,
            scan_python_files_filtered,
            search_class_mapping,
            write_ontology,
            exit_generator_success,
            exit_generator_failure,
        ]

        # Merge with any additional tools forwarded by the caller
        all_tools = local_tools + (tools or [])

        # Deduplicate by name (keeps first occurrence, which is the local tool)
        unique_tools = list(
            {
                (t.__name__ if hasattr(t, "__name__") else str(t)): t
                for t in all_tools
            }.values()
        )

        super().__init__(
            name="OntologyGeneratorInternal",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=unique_tools,
            before_model_callback=before_model_callback,
            after_model_callback=model_callback,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )
