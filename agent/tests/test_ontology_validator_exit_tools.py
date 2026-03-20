"""
Unit tests for agent/sub_agents/ontology_validator/exit_tools.py.

Uses a minimal MockToolContext (SimpleNamespace with a dict ``state`` and a
mock ``actions`` object) — no ADK runtime required.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from sub_agents.ontology_validator.exit_tools import (
    checkpoint_code,
    exit_validator_failure,
    exit_validator_success,
)


def _make_tool_context(initial_state: dict | None = None) -> SimpleNamespace:
    """Return a minimal stand-in for google.adk.tools.ToolContext."""
    actions = SimpleNamespace(escalate=False)
    state: dict = initial_state if initial_state is not None else {}
    return SimpleNamespace(state=state, actions=actions)


# ---------------------------------------------------------------------------
# checkpoint_code
# ---------------------------------------------------------------------------


def test_checkpoint_code_first_call_appends_fix_0():
    """First call with empty state appends Fix 0 snapshot."""
    tc = _make_tool_context()
    checkpoint_code(tc, code="v1")

    snapshots = tc.state["ontology_code_snapshots"]
    assert len(snapshots) == 1
    assert snapshots[0] == {
        "label": "Fix 0",
        "code": "v1",
        "iteration": 0,
        "status": "fix",
    }


def test_checkpoint_code_first_call_sets_iteration_count_to_1():
    """First call increments ontology_code_iteration_count from 0 to 1."""
    tc = _make_tool_context()
    checkpoint_code(tc, code="v1")
    assert tc.state["ontology_code_iteration_count"] == 1


def test_checkpoint_code_second_call_appends_fix_1():
    """Second call appends Fix 1 snapshot with correct iteration."""
    tc = _make_tool_context()
    checkpoint_code(tc, code="v1")
    checkpoint_code(tc, code="v2")

    snapshots = tc.state["ontology_code_snapshots"]
    assert len(snapshots) == 2
    assert snapshots[1] == {
        "label": "Fix 1",
        "code": "v2",
        "iteration": 1,
        "status": "fix",
    }


def test_checkpoint_code_second_call_sets_iteration_count_to_2():
    """Second call increments ontology_code_iteration_count from 1 to 2."""
    tc = _make_tool_context()
    checkpoint_code(tc, code="v1")
    checkpoint_code(tc, code="v2")
    assert tc.state["ontology_code_iteration_count"] == 2


def test_checkpoint_code_does_not_escalate():
    """checkpoint_code must NOT set actions.escalate — loop must continue."""
    tc = _make_tool_context()
    checkpoint_code(tc, code="v1")
    # escalate must remain False after checkpoint_code
    assert tc.actions.escalate is False


def test_checkpoint_code_returns_snapshot_saved():
    tc = _make_tool_context()
    result = checkpoint_code(tc, code="v1")
    assert result["status"] == "snapshot_saved"


# ---------------------------------------------------------------------------
# exit_validator_success
# ---------------------------------------------------------------------------


def test_exit_validator_success_calls_checkpoint_internally():
    """exit_validator_success calls checkpoint_code, increasing snapshot count."""
    tc = _make_tool_context()
    exit_validator_success(tc, code="final", summary="done")

    snapshots = tc.state["ontology_code_snapshots"]
    # checkpoint_code was called internally → at least one snapshot
    assert len(snapshots) >= 1


def test_exit_validator_success_patches_last_snapshot_to_final():
    """Last snapshot label is patched to 'Final', status to 'validated'."""
    tc = _make_tool_context()
    exit_validator_success(tc, code="final", summary="done")

    snapshots = tc.state["ontology_code_snapshots"]
    last = snapshots[-1]
    assert last["label"] == "Final"
    assert last["status"] == "validated"
    assert last["code"] == "final"


def test_exit_validator_success_sets_validation_success_true():
    tc = _make_tool_context()
    exit_validator_success(tc, code="final", summary="done")
    assert tc.state["ONTOLOGY_VALIDATION_SUCCESS"] is True


def test_exit_validator_success_sets_escalate_true():
    tc = _make_tool_context()
    exit_validator_success(tc, code="final", summary="done")
    assert tc.actions.escalate is True


# ---------------------------------------------------------------------------
# exit_validator_failure
# ---------------------------------------------------------------------------


def test_exit_validator_failure_sets_escalate_true():
    tc = _make_tool_context()
    exit_validator_failure(tc, reason="timeout")
    assert tc.actions.escalate is True


def test_exit_validator_failure_returns_signal_sent_with_reason():
    tc = _make_tool_context()
    result = exit_validator_failure(tc, reason="timeout")
    assert result["status"] == "signal_sent"
    assert result["reason"] == "timeout"
