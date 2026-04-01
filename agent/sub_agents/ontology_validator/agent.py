"""
ASHRAE 223P Ontology Validator & Fixer Agent.

Uses a LoopWrapper (max 100 iterations) around an LlmAgent.

Role
----
This agent does **not** generate the ontology from scratch. It reads the
already-generated ``[project]/[system]/python/ontology.py``, executes it, analyzes errors,
and iteratively applies targeted fixes until the file runs without errors
and produces a valid ``[project]/[system]/ttl/ontology.ttl`` output.

The model is injected by the parent agent at construction time; callers must
supply ``model_name``.

Tools
-----
- All helpers from ``tools/ontology_tools.py`` (library introspection,
  ontology read/write/execute, prompt reader).
- Any shared/additional tools forwarded via the ``tools`` parameter.
- ``checkpoint_code`` — saves a version snapshot after each fix iteration
  (does NOT terminate the loop).
- ``exit_validator_success`` — signals clean validation and terminates the loop.
- ``exit_validator_failure`` — signals validation failure and terminates the loop.
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

from sub_agents.tools.ontology_tools import (
    execute_ontology,
    read_ontology,
    read_prompt,
    scan_python_files_filtered,
    search_class_mapping,
    write_ontology,
    skills_toolset,
)
from sub_agents.ontology_validator.exit_tools import (
    checkpoint_code,
    exit_validator_success,
    exit_validator_failure,
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

_MAX_ITERATIONS = 100

# ──────────────────────────────────────────────────────────────────────────────
# Public interface: LoopWrapper
# ──────────────────────────────────────────────────────────────────────────────


class OntologyValidatorAgent(LoopWrapper):
    """
    Loop-wrapped 223P Ontology Validator & Fixer Agent.

    Unlike the generator, this agent does **not** create the ontology from
    scratch.  It reads the already-generated ``[project]/[system]/python/ontology.py``,
    executes it, and applies targeted fixes until execution succeeds.

    The *model_name* parameter is required and is forwarded to the inner
    :class:`OntologyValidatorInternal` LlmAgent.  Typically this is set
    (hardcoded) by the parent sequential agent.
    """

    def __init__(
        self,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        internal_agent = OntologyValidatorInternal(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
        )
        super().__init__(
            name="OntologyValidatorAgent",
            agent=internal_agent,
            description=(
                "Validates and fixes the ASHRAE 223P ontology.py. Executes the file, "
                "analyses errors, and applies targeted repairs until the ontology runs "
                "cleanly and serialises to TTL."
            ),
            max_iterations=_MAX_ITERATIONS,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Internal LlmAgent
# ──────────────────────────────────────────────────────────────────────────────


class OntologyValidatorInternal(LlmAgent):
    """Internal LlmAgent – not instantiated directly by callers."""

    def __init__(
        self,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        instruction = load_prompt_instruction("sub_agents/ontology_validator/prompt.md")

        # Local tools provided by this sub-agent.
        # execute_ontology is included because validation requires actually running the file.
        local_tools: list[Any] = [
            skills_toolset,
            execute_ontology,
            read_ontology,
            write_ontology,
            scan_python_files_filtered,
            search_class_mapping,
            read_prompt,
            checkpoint_code,
            exit_validator_success,
            exit_validator_failure,
        ]

        # Merge with any shared/additional tools forwarded by the caller
        all_tools = local_tools + (tools or [])

        # Deduplicate by name (keeps first occurrence, which is the local tool)
        unique_tools = list(
            {
                (t.__name__ if hasattr(t, "__name__") else str(t)): t
                for t in all_tools
            }.values()
        )

        super().__init__(
            name="OntologyValidatorInternal",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=unique_tools,
            before_model_callback=before_model_callback,
            after_model_callback=model_callback,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )
