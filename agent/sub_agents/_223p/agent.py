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
Use the unified runner::

    cd agent
    python -m sub_agents._223p.run pipeline

See :mod:`sub_agents._223p.run` for all options (``--model``, ``--github-token``,
custom task, etc.).

Backward compatibility
----------------------
``OntologyLlmAgent`` is re-exported from this module so that existing
``from sub_agents._223p.agent import OntologyLlmAgent`` imports continue to
work unchanged.
"""
from __future__ import annotations

import logging
import os
import sys
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
        Optional list of additional tools forwarded to both sub-agents.
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

