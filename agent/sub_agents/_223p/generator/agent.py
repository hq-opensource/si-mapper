"""
ASHRAE 223P Ontology Generator Agent.

Uses a LoopWrapper (max 50 iterations) around an LlmAgent.

The model is injected by the parent :class:`Ontology223PSequentialAgent` at
construction time; callers must supply ``model_name``.

Tools
-----
- All helpers from ``sub_agents/_223p/tool.py`` (library introspection,
  ontology read/write, prompt reader).
- Any common MCP/shared tools forwarded via the ``tools`` parameter.
- ``exit_loop_generator_success`` — signals successful generation **and**
  persists the ``ONTOLOGY_GENERATION_SUCCESS`` state flag so the sequential
  agent can conditionally run the validator.

Usage (standalone)
------------------
Run directly with:

    cd agent
    python -m sub_agents._223p.generator.agent

or via the bundled :class:`StandaloneRunner`::

    from sub_agents._223p.generator.agent import StandaloneRunner
    import asyncio
    asyncio.run(StandaloneRunner().run())
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
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
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from sub_agents._223p.tool import (
    list_library_classes,
    get_class_details,
    scan_python_files,
    write_ontology,
)
from sub_agents._223p.exit_tools import (
    exit_loop_generator_success,
    exit_loop_generator_failure
)
from sub_agents.loop_agents.loop_wrapper import LoopWrapper
from utils.callback_utils import shared_model_callback as model_callback, shared_before_model_callback as before_model_callback
from utils.models import get_adk_model
from utils.prompt_utils import load_composed_prompt

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

#: Fallback model used when running standalone (no parent to inject the model).
_STANDALONE_DEFAULT_MODEL = "github_copilot/claude-sonnet-4.5"

#: Default task description used when no message is supplied to the standalone runner.
_DEFAULT_TASK = (
    "Read the grid, inspect the bob and scratch libraries, "
    "then generate ontology.py that models the entire HVAC system "
    "in ASHRAE 223P and serialises it to ttl/ontology.ttl. "
    "When the ontology is written without errors call exit_loop_generator_success."
)

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
        instruction = load_composed_prompt(
            "sub_agents/_223p/generator/prompt.md",
            ["skills/read-code-iterations/SKILL.md"]
        )

        # Local tools provided by this sub-agent
        local_tools: list[Any] = [
            list_library_classes,
            get_class_details,
            scan_python_files,
            write_ontology,
            exit_loop_generator_success,
            exit_loop_generator_failure,
        ]

        # Merge with any common/MCP tools forwarded by the caller
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


# ──────────────────────────────────────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────────────────────────────────────


class StandaloneRunner:
    """
    Thin harness that runs :class:`OntologyLlmAgent` independently of the
    main FastAPI service or the sequential pipeline.

    Environment variables (all optional when the matching parameter is supplied)
    ----------------------------------------------------------------------------
    ``MCP_SERVER_URL``
        URL of the MCP server.
    ``GOOGLE_API_KEY``
        Google ADK / Gemini API key.
    ``GITHUB_TOKEN``
        GitHub Copilot token forwarded to LiteLLM.
    """

    iteration = 0

    def __init__(
        self,
        mcp_server_url: str | None = None,
        google_api_key: str | None = None,
        github_token: str | None = None,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
    ) -> None:
        self.mcp_server_url = mcp_server_url or os.getenv(
            "MCP_SERVER_URL", "http://localhost:8080/mcp/"
        )
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.model_name = model_name

    def _inject_credentials(self) -> None:
        if self.google_api_key:
            os.environ.setdefault("GOOGLE_API_KEY", self.google_api_key)
            os.environ.setdefault("GOOGLE_GENAI_API_KEY", self.google_api_key)
        if self.github_token:
            os.environ.setdefault("GITHUB_TOKEN", self.github_token)
            os.environ.setdefault("LITELLM_API_KEY", self.github_token)

    async def run(self, task: str = _DEFAULT_TASK) -> str:
        """Run the generator agent with *task* as the initial user message."""
        self._inject_credentials()

        from utils.mcp_utils import create_mcp_toolset

        print(f"[StandaloneRunner] Connecting to MCP server at {self.mcp_server_url} …")
        mcp_toolset = create_mcp_toolset(self.mcp_server_url)

        agent = OntologyLlmAgent(model_name=self.model_name, tools=[mcp_toolset])

        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        session_id = f"standalone-{uuid.uuid4().hex[:8]}"

        await session_service.create_session(
            app_name="ontology_standalone",
            user_id="standalone_user",
            session_id=session_id,
        )

        runner = Runner(
            agent=agent,
            app_name="ontology_standalone",
            session_service=session_service,
            artifact_service=artifact_service,
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=task)],
        )

        final_response = ""
        print(f"[StandaloneRunner] Starting agent (max {_MAX_ITERATIONS} iterations) …\n")

        async for event in runner.run_async(
            user_id="standalone_user",
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                self.iteration += 1
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                print(f"\n[StandaloneRunner {self.iteration}/{_MAX_ITERATIONS}] ✓ Agent finished.\n")
                print(final_response)

        return final_response


# ──────────────────────────────────────────────────────────────────────────────
# Entry-point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    from dotenv import load_dotenv
    import argparse

    load_dotenv(os.path.join(_agent_root, ".env"))

    parser = argparse.ArgumentParser(
        description="Run the 223P Ontology Generator Agent standalone.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Credentials can also be supplied via environment variables:\n"
            "  GOOGLE_API_KEY  – Google ADK / Gemini API key\n"
            "  GITHUB_TOKEN    – GitHub Copilot token (used by LiteLLM)\n"
            "  MCP_SERVER_URL  – MCP server URL\n"
        ),
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="Task description for the agent (defaults to the built-in 223P task).",
    )
    parser.add_argument("--google-api-key", metavar="KEY", default=None)
    parser.add_argument("--github-token", metavar="TOKEN", default=None)
    parser.add_argument("--mcp-server-url", metavar="URL", default=None)
    parser.add_argument(
        "--model",
        metavar="MODEL",
        default=_STANDALONE_DEFAULT_MODEL,
        help="Model name to use (default: %(default)s).",
    )

    args = parser.parse_args()
    task_arg = " ".join(args.task) if args.task else _DEFAULT_TASK

    asyncio.run(
        StandaloneRunner(
            mcp_server_url=args.mcp_server_url,
            google_api_key=args.google_api_key,
            github_token=args.github_token,
            model_name=args.model,
        ).run(task=task_arg)
    )

