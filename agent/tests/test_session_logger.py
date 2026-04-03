"""
Unit tests for agent/utils/session_logger.py.

Covers:
- test_creates_log_dir_on_first_write: Directory and file created on first call
- test_each_event_is_one_json_line: N events = N JSON lines
- test_log_filename_format: File named {session_id}_{YYYYMMDD}.jsonl
- test_agent_event_fields_complete: All AgentEvent fields present in JSON output
- test_append_does_not_truncate: Second call appends, does not overwrite
- test_empty_events_no_file: Empty list produces no file
- test_oserror_does_not_raise: OSError during write is caught silently
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock

import pytest

# Resolve imports: tests run from agent/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import utils.session_logger as session_logger_module
from utils.session_logger import log_events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(**overrides) -> dict:
    """Return a minimal AgentEvent.model_dump() shaped dict."""
    base = {
        "id": "test-uuid-1",
        "timestamp": 1711234567890,
        "agent_name": "master",
        "event_type": "BRAINSTORM",
        "content": "thinking...",
        "metadata": {"latency_s": 0.5},
        "trace_id": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_creates_log_dir_on_first_write(tmp_path, monkeypatch):
    """Calling log_events with at least one event creates the log directory and file."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    event = _make_event()
    log_events("sess-abc", [event])

    assert log_dir.exists(), "log directory should have been created"
    files = list(log_dir.iterdir())
    assert len(files) == 1, "exactly one log file should exist"


def test_each_event_is_one_json_line(tmp_path, monkeypatch):
    """Writing 3 events produces exactly 3 lines, each parseable as JSON."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    events = [
        _make_event(id=f"uuid-{i}", content=f"event {i}")
        for i in range(3)
    ]
    log_events("sess-abc", events)

    log_files = list(log_dir.iterdir())
    assert len(log_files) == 1
    lines = log_files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, f"expected 3 lines, got {len(lines)}"
    for line in lines:
        parsed = json.loads(line)
        assert isinstance(parsed, dict)


def test_log_filename_format(tmp_path, monkeypatch):
    """Log file is named {session_id}_{YYYYMMDD}.jsonl."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    fixed_date = datetime(2026, 4, 3)
    with patch("utils.session_logger.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_date
        log_events("sess-abc", [_make_event()])

    log_files = list(log_dir.iterdir())
    assert len(log_files) == 1
    assert log_files[0].name == "sess-abc_20260403.jsonl", (
        f"unexpected filename: {log_files[0].name}"
    )


def test_agent_event_fields_complete(tmp_path, monkeypatch):
    """Written JSON contains all AgentEvent fields."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    event = _make_event(
        id="complete-uuid",
        timestamp=1711234567890,
        agent_name="master",
        event_type="ACTION_RESULT",
        content="tool output",
        metadata={"latency_s": 1.2},
        trace_id="trace-xyz",
    )
    log_events("sess-abc", [event])

    log_file = next(log_dir.iterdir())
    parsed = json.loads(log_file.read_text(encoding="utf-8").strip())

    assert parsed["id"] == "complete-uuid"
    assert parsed["timestamp"] == 1711234567890
    assert parsed["agent_name"] == "master"
    assert parsed["event_type"] == "ACTION_RESULT"
    assert parsed["content"] == "tool output"
    assert parsed["metadata"] == {"latency_s": 1.2}
    assert parsed["trace_id"] == "trace-xyz"


def test_append_does_not_truncate(tmp_path, monkeypatch):
    """Two separate log_events() calls produce cumulative lines (2 + 1 = 3 total)."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    # First call: 2 events
    log_events("sess-abc", [
        _make_event(id="e1", content="first"),
        _make_event(id="e2", content="second"),
    ])
    # Second call: 1 event
    log_events("sess-abc", [_make_event(id="e3", content="third")])

    log_files = list(log_dir.iterdir())
    assert len(log_files) == 1
    lines = log_files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, f"expected 3 total lines after 2 calls, got {len(lines)}"
    contents = [json.loads(line)["content"] for line in lines]
    assert contents == ["first", "second", "third"]


def test_empty_events_no_file(tmp_path, monkeypatch):
    """Calling log_events with an empty list does NOT create any file."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    log_events("sess-abc", [])

    # Directory may or may not exist — either way no file should be created
    if log_dir.exists():
        assert list(log_dir.iterdir()) == [], "no files should be created for empty events"


def test_oserror_does_not_raise(tmp_path, monkeypatch):
    """When builtins.open raises OSError, log_events catches it silently."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    def _raise_oserror(*args, **kwargs):
        raise OSError("disk full")

    with patch("builtins.open", side_effect=_raise_oserror):
        # Must NOT raise
        log_events("sess-abc", [_make_event()])
