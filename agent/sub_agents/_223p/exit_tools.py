"""
Exit tools specific to the _223p pipeline.

``exit_loop_generator_success``
    Used by the generator agent to signal successful ontology creation.
    Persists the ``ONTOLOGY_GENERATION_SUCCESS`` flag so the surrounding
    :class:`Ontology223PSequentialAgent` can decide whether to proceed to the
    validator step.
"""
from __future__ import annotations

import logging

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def exit_loop_generator_success(
    tool_context: ToolContext,
    summary: str = "Ontology generated successfully.",
) -> dict:
    """
    Signals that the ontology **generator** completed successfully.

    Sets the ``ONTOLOGY_GENERATION_SUCCESS`` flag in the shared session state
    so the enclosing :class:`Ontology223PSequentialAgent` knows it is safe to
    proceed to the validator step.  Also escalates to terminate the current
    LoopWrapper iteration.

    .. note::
        ADK's ``LoopAgent._run_async_impl`` stops the loop exclusively via
        ``event.actions.escalate`` — it never calls ``LoopWrapper.is_loop_finished``.
        The ``EXIT_LEVEL_4`` flag written here is therefore **not** what stops
        the generator loop; ``actions.escalate = True`` is.  ``EXIT_LEVEL_4`` is
        set here as a state marker for consistency with other exit tools, but
        ``Ontology223PSequentialAgent._run_async_impl`` resets it to ``False``
        before starting the validator so it cannot be mistaken for the
        validator's own completion signal.

    Call this tool (instead of ``exit_loop_level_4``) when:
    - the ontology has been written to ``223p/src/ontology.py`` without errors, AND
    - the code is syntactically valid Python.

    Args:
        summary: A clear description of what was generated — equipment count,
                 connection types modelled, TTL serialisation status, etc.
    """
    logger.debug(
        "[exit_loop_generator_success] called by %s", tool_context.agent_name
    )
    # ONTOLOGY_GENERATION_SUCCESS is the flag actually checked by the sequential
    # agent to decide whether to run the validator.
    tool_context.state["ONTOLOGY_GENERATION_SUCCESS"] = True
    # EXIT_LEVEL_4 is a state marker for consistency; the loop actually stops
    # because of actions.escalate below (ADK never calls is_loop_finished).
    tool_context.state["EXIT_LEVEL_4"] = True
    tool_context.actions.escalate = True
    return {
        "status": "signal_sent",
        "message": "Generator completed – validator will now proceed.",
        "summary": summary,
    }

