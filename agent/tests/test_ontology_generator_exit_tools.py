"""
Unit tests for agent/sub_agents/ontology_generator/exit_tools.py.

Uses a minimal MockToolContext (SimpleNamespace with a dict ``state`` and a
mock ``actions`` object) — no ADK runtime required.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from sub_agents.ontology_generator.exit_tools import (
    exit_generator_failure,
    exit_generator_success,
)


def _make_tool_context(initial_state: dict | None = None) -> SimpleNamespace:
    """Return a minimal stand-in for google.adk.tools.ToolContext."""
    actions = SimpleNamespace(escalate=False)
    state: dict = initial_state if initial_state is not None else {}
    return SimpleNamespace(state=state, actions=actions)


# ---------------------------------------------------------------------------
# exit_generator_success
# ---------------------------------------------------------------------------


def test_exit_generator_success_appends_initial_snapshot():
    """exit_generator_success appends exactly one Initial snapshot."""
    tc = _make_tool_context()
    exit_generator_success(tc, code="print('hello')", summary="test")

    snapshots = tc.state["ontology_code_snapshots"]
    assert len(snapshots) == 1
    assert snapshots[0] == {
        "label": "Initial",
        "code": "print('hello')",
        "iteration": 0,
        "status": "generated",
    }


def test_exit_generator_success_sets_generation_success_true():
    tc = _make_tool_context()
    exit_generator_success(tc, code="x = 1", summary="ok")
    assert tc.state["ONTOLOGY_GENERATION_SUCCESS"] is True


def test_exit_generator_success_sets_exit_level_4_true():
    tc = _make_tool_context()
    exit_generator_success(tc, code="x = 1", summary="ok")
    assert tc.state["EXIT_LEVEL_4"] is True


def test_exit_generator_success_sets_escalate_true():
    tc = _make_tool_context()
    exit_generator_success(tc, code="x = 1", summary="ok")
    assert tc.actions.escalate is True


def test_exit_generator_success_sets_iteration_count_to_zero():
    tc = _make_tool_context()
    exit_generator_success(tc, code="x = 1", summary="ok")
    assert tc.state["ontology_code_iteration_count"] == 0


def test_exit_generator_success_returns_signal_sent():
    tc = _make_tool_context()
    result = exit_generator_success(tc, code="x = 1", summary="ok")
    assert result["status"] == "signal_sent"


# ---------------------------------------------------------------------------
# exit_generator_failure
# ---------------------------------------------------------------------------


def test_exit_generator_failure_sets_generation_success_false():
    tc = _make_tool_context()
    exit_generator_failure(tc, reason="broken")
    assert tc.state["ONTOLOGY_GENERATION_SUCCESS"] is False


def test_exit_generator_failure_sets_failure_reason():
    tc = _make_tool_context()
    exit_generator_failure(tc, reason="broken")
    assert tc.state["ONTOLOGY_GENERATION_FAILURE_REASON"] == "broken"


def test_exit_generator_failure_sets_escalate_true():
    tc = _make_tool_context()
    exit_generator_failure(tc, reason="broken")
    assert tc.actions.escalate is True


def test_exit_generator_failure_returns_signal_sent():
    tc = _make_tool_context()
    result = exit_generator_failure(tc, reason="broken")
    assert result["status"] == "signal_sent"
