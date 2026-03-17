"""
ASHRAE 223P Sequential Pipeline Agent.

Orchestrates two sub-agents in strict order:

1. **OntologyLlmAgent** (generator) — generates ``223p/src/ontology.py`` from
   the live HVAC grid using the *bob* and *scratch* libraries.
2. **OntologyValidatorAgent** (validator) — reads, executes, and iteratively
   fixes ``ontology.py`` until it runs cleanly and produces
   ``223p/ttl/ontology.ttl``.

The validator is only started when the generator explicitly calls
``exit_loop_generator_success``, which sets the ``ONTOLOGY_GENERATION_SUCCESS``
flag in the shared session state.  If the generator exhausts its iteration
budget without that call, the validator step is skipped.

Model
-----
The model is **hardcoded** here as ``_PIPELINE_MODEL`` and forwarded to both
sub-agents.  This is the single place to change the model for the entire
pipeline.

Usage (standalone)
------------------
Run the full pipeline::

    cd agent
    python -m sub_agents._223p.agent

or via the bundled :class:`PipelineStandaloneRunner`::

    from sub_agents._223p.agent import PipelineStandaloneRunner
    import asyncio
    asyncio.run(PipelineStandaloneRunner().run())

Backward compatibility
----------------------
``OntologyLlmAgent`` is re-exported from this module so that existing
``from sub_agents._223p.agent import OntologyLlmAgent`` imports continue to
work unchanged.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from contextlib import aclosing
from typing import Any, AsyncGenerator

# ── Path bootstrap ────────────────────────────────────────────────────────────
# agent/ root — used here for the optional bootstrap and later by __main__
# for load_dotenv, so it is always computed.
_agent_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if not __package__:
    if _agent_root not in sys.path:
        sys.path.insert(0, _agent_root)
# ─────────────────────────────────────────────────────────────────────────────

# ── SSL Verification disabled ────────────────────────────────────────────────
os.environ["SSL_CERT_FILE"] = ""
# ─────────────────────────────────────────────────────────────────────────────

from google.adk.agents import SequentialAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from sub_agents._223p.generator.agent import OntologyLlmAgent  # noqa: F401 (re-export)
from sub_agents._223p.validator.agent import OntologyValidatorAgent

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Model — hardcoded here, passed to both sub-agents
# ──────────────────────────────────────────────────────────────────────────────

_PIPELINE_MODEL = "github_copilot/claude-sonnet-4.5"

# ──────────────────────────────────────────────────────────────────────────────
# Sequential pipeline agent
# ──────────────────────────────────────────────────────────────────────────────


class Ontology223PSequentialAgent(SequentialAgent):
    """
    Sequential pipeline: generator → validator.

    Extends :class:`google.adk.agents.SequentialAgent` with a conditional
    check between steps: the validator only runs when the generator set
    ``ONTOLOGY_GENERATION_SUCCESS = True`` in the shared session state.

    Parameters
    ----------
    model_name:
        Model forwarded to both sub-agents. Defaults to ``_PIPELINE_MODEL``
        (hardcoded in this module).
    tools:
        Optional list of additional tools (e.g. an MCP toolset) forwarded to
        both sub-agents.
    session_id:
        Optional session identifier (passed through for logging purposes).
    """

    def __init__(
        self,
        model_name: str = _PIPELINE_MODEL,
        tools: list[Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        generator = OntologyLlmAgent(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
        )
        validator = OntologyValidatorAgent(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
        )
        super().__init__(
            name="Ontology223PPipeline",
            sub_agents=[generator, validator],
            description=(
                "Sequential pipeline: generates an ASHRAE 223P ontology from the "
                "HVAC grid (step 1), then validates and fixes it until execution "
                "succeeds and a TTL file is produced (step 2)."
            ),
        )

    # ------------------------------------------------------------------
    # Conditional execution: skip validator when generator failed
    # ------------------------------------------------------------------

    async def _run_async_impl(self, ctx) -> AsyncGenerator:  # type: ignore[override]
        """
        Run generator then validator, but only if generator succeeded.

        The generator calls ``exit_loop_generator_success`` on success, which
        persists ``ONTOLOGY_GENERATION_SUCCESS = True`` in ``ctx.session.state``
        and sets ``actions.escalate = True`` to stop its own LoopWrapper.

        Notes on EXIT_LEVEL_4 hygiene
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ADK's LoopAgent stops its loop exclusively via ``event.actions.escalate``
        — it never calls ``LoopWrapper.is_loop_finished``.  This means
        ``EXIT_LEVEL_4 = True`` written by ``exit_loop_generator_success`` is
        never reset by the generator's LoopWrapper termination logic.  We
        therefore reset it explicitly here before starting the validator, so a
        stale generator flag cannot be mistaken for the validator's completion
        signal by any outer loop.

        After the full pipeline finishes (success or early-return) we always
        set ``EXIT_LEVEL_4 = True`` so that outer loops receive the same
        completion signal that every other sub-agent provides.
        """
        if not self.sub_agents:
            return

        # ── Step 1: generator ─────────────────────────────────────────
        generator = self.sub_agents[0]
        async with aclosing(generator.run_async(ctx)) as agen:
            async for event in agen:
                yield event

        # ── Reset EXIT_LEVEL_4 left by the generator ──────────────────
        # exit_loop_generator_success sets EXIT_LEVEL_4=True + escalate=True.
        # ADK stops the generator loop via escalate but never calls
        # is_loop_finished, so the flag stays True.  Clear it now so the
        # validator's LoopWrapper (and any outer loop) starts with a clean slate.
        ctx.session.state["EXIT_LEVEL_4"] = False

        # ── Conditional gate ──────────────────────────────────────────
        generation_ok = ctx.session.state.get("ONTOLOGY_GENERATION_SUCCESS", False)
        if not generation_ok:
            failure_reason = ctx.session.state["ONTOLOGY_GENERATION_FAILURE_REASON"]
            logger.warning(
                "[Ontology223PPipeline] Generator did not set ONTOLOGY_GENERATION_SUCCESS. "
                + (failure_reason if failure_reason else "The generator likely exhausted its iteration budget without calling exit_loop_generator_success.")
                + " Skipping validator step."
            )
            # Signal pipeline completion to any outer loop even on early exit.
            ctx.session.state["EXIT_LEVEL_4"] = True
            return

        # ── Step 2: validator ─────────────────────────────────────────
        if len(self.sub_agents) > 1:
            validator = self.sub_agents[1]
            async with aclosing(validator.run_async(ctx)) as agen:
                async for event in agen:
                    yield event

        # ── Signal pipeline completion to any outer loop ───────────────
        # All other sub-agents set EXIT_LEVEL_4=True when they finish.
        # The validator's exit_loop_level_4 call already sets it, but we
        # also set it here explicitly so the convention holds even if the
        # validator hits max_iterations without calling the tool.
        ctx.session.state["EXIT_LEVEL_4"] = True


# ──────────────────────────────────────────────────────────────────────────────
# Standalone runner (full pipeline)
# ──────────────────────────────────────────────────────────────────────────────

_DEFAULT_TASK = (
    "Read the grid, inspect the bob and scratch libraries, "
    "then generate ontology.py that models the entire HVAC system "
    "in ASHRAE 223P and serialises it to ttl/ontology.ttl. "
    "When the ontology is written without errors call exit_loop_generator_success. "
    "The validator will then execute and fix the generated file automatically."
)


class PipelineStandaloneRunner:
    """
    Thin harness that runs the full :class:`Ontology223PSequentialAgent`
    pipeline (generator + validator) independently of the FastAPI service.

    Environment variables (all optional when the matching parameter is supplied)
    ----------------------------------------------------------------------------
    ``MCP_SERVER_URL``   URL of the MCP server.
    ``GOOGLE_API_KEY``   Google ADK / Gemini API key.
    ``GITHUB_TOKEN``     GitHub Copilot token forwarded to LiteLLM.
    """

    def __init__(
        self,
        mcp_server_url: str | None = None,
        google_api_key: str | None = None,
        github_token: str | None = None,
    ) -> None:
        self.mcp_server_url = mcp_server_url or os.getenv(
            "MCP_SERVER_URL", "http://localhost:8080/mcp/"
        )
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

    def _inject_credentials(self) -> None:
        if self.google_api_key:
            os.environ.setdefault("GOOGLE_API_KEY", self.google_api_key)
            os.environ.setdefault("GOOGLE_GENAI_API_KEY", self.google_api_key)
        if self.github_token:
            os.environ.setdefault("GITHUB_TOKEN", self.github_token)
            os.environ.setdefault("LITELLM_API_KEY", self.github_token)

    async def run(self, task: str = _DEFAULT_TASK) -> str:
        """Run the pipeline with *task* as the initial user message."""
        self._inject_credentials()

        from utils.mcp_utils import create_mcp_toolset

        print(f"[PipelineStandaloneRunner] Connecting to MCP server at {self.mcp_server_url} …")
        mcp_toolset = create_mcp_toolset(self.mcp_server_url)

        agent = Ontology223PSequentialAgent(tools=[mcp_toolset])

        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        session_id = f"pipeline-{uuid.uuid4().hex[:8]}"

        await session_service.create_session(
            app_name="ontology_pipeline_standalone",
            user_id="standalone_user",
            session_id=session_id,
        )

        runner = Runner(
            agent=agent,
            app_name="ontology_pipeline_standalone",
            session_service=session_service,
            artifact_service=artifact_service,
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=task)],
        )

        final_response = ""
        print("[PipelineStandaloneRunner] Starting pipeline …\n")

        async for event in runner.run_async(
            user_id="standalone_user",
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                print("\n[PipelineStandaloneRunner] ✓ Pipeline finished.\n")
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
        description="Run the 223P Ontology Generation+Validation Pipeline standalone.",
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
        help="Task description (defaults to the built-in 223P pipeline task).",
    )
    parser.add_argument("--google-api-key", metavar="KEY", default=None)
    parser.add_argument("--github-token", metavar="TOKEN", default=None)
    parser.add_argument("--mcp-server-url", metavar="URL", default=None)

    args = parser.parse_args()
    task_arg = " ".join(args.task) if args.task else _DEFAULT_TASK

    asyncio.run(
        PipelineStandaloneRunner(
            mcp_server_url=args.mcp_server_url,
            google_api_key=args.google_api_key,
            github_token=args.github_token,
        ).run(task=task_arg)
    )

