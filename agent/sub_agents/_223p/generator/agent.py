"""
ASHRAE 223P Ontology Generator Agent.

Uses a LoopWrapper (max 50 iterations) around an LlmAgent.

The model is injected by the parent :class:`Ontology223PSequentialAgent` at
construction time; callers must supply ``model_name``.

Tools
-----
- All helpers from ``sub_agents/_223p/tool.py`` (library introspection,
  ontology read/write, prompt reader).
- Any common shared tools forwarded via the ``tools`` parameter.
- ``exit_loop_generator_success`` — signals successful generation **and**
  persists the ``ONTOLOGY_GENERATION_SUCCESS`` state flag so the sequential
  agent can conditionally run the validator.

Usage (standalone)
------------------
Use the unified runner::

    cd agent
    python -m sub_agents._223p.run generator

See :mod:`sub_agents._223p.run` for all options (``--model``, ``--github-token``,
custom task, etc.).
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
    list_library_classes,
    get_class_details,
    scan_python_files,
    write_ontology,
    skills_toolset,
)
from sub_agents._223p.exit_tools import (
    exit_loop_generator_success,
    exit_loop_generator_failure
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


class OntologyLlmAgent(LoopWrapper):
    """
    Loop-wrapped 223P Ontology Generator Agent.

    The *model_name* parameter is required and is forwarded to the inner
    :class:`OntologyLlmAgentInternal` LlmAgent.  Typically this is set
    (hardcoded) by the parent :class:`Ontology223PSequentialAgent`.
    """

    def __init__(
        self,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        internal_agent = OntologyLlmAgentInternal(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
        )
        super().__init__(
            name="OntologyAgent",
            agent=internal_agent,
            description=(
                "Generates an ASHRAE 223P semantic ontology from the live HVAC grid "
                "using the bob and scratch Python libraries."
            ),
            max_iterations=_MAX_ITERATIONS,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Internal LlmAgent
# ──────────────────────────────────────────────────────────────────────────────


class OntologyLlmAgentInternal(LlmAgent):
    """Internal LlmAgent – not instantiated directly by callers."""

    def __init__(
        self,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        instruction = load_prompt_instruction("sub_agents/_223p/generator/prompt.md")

        # Local tools provided by this sub-agent
        local_tools: list[Any] = [
            skills_toolset,
            list_library_classes,
            get_class_details,
            scan_python_files,
            write_ontology,
            exit_loop_generator_success,
            exit_loop_generator_failure,
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
            name="OntologyAgentInternal",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=unique_tools,
            before_model_callback=before_model_callback,
            after_model_callback=model_callback,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )


