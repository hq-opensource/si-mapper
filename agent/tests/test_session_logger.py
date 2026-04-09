"""
Unit tests for agent/utils/session_logger.py.

Covers:
- test_creates_log_dir_on_first_write: Directory and file created on first call
- test_each_event_is_one_json_line: N kept events = N JSON lines (TEXT_RESPONSE dropped)
- test_log_filename_format: File named {session_id}_{YYYYMMDD}.jsonl
- test_compact_fields: Written JSON has only "t" and "c" fields
- test_append_does_not_truncate: Second call appends, does not overwrite
- test_empty_events_no_file: Empty list produces no file
- test_oserror_does_not_raise: OSError during write is caught silently
- test_text_response_skipped: TEXT_RESPONSE events produce no output
- test_brainstorm_deduplication: Consecutive identical BRAINSTORM entries written once
- test_markdown_stripped: Bold, italic, backtick markers removed from content
- test_tool_call_formatted: ACTION_TRIGGER rendered as tool_name(k=v) from metadata
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

# Resolve imports: tests run from agent/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import utils.session_logger as session_logger_module
from utils.session_logger import log_events, _last_brainstorm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(event_type="BRAINSTORM", content="thinking...", **overrides) -> dict:
    """Return a minimal AgentEvent.model_dump() shaped dict."""
    base = {
        "id": "test-uuid-1",
        "timestamp": 1711234567890,
        "agent_name": "master",
        "event_type": event_type,
        "content": content,
        "metadata": {"latency_s": 0.5},
        "trace_id": None,
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def clear_brainstorm_dedup():
    """Clear the in-process dedup state between tests."""
    _last_brainstorm.clear()
    yield
    _last_brainstorm.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_creates_log_dir_on_first_write(tmp_path, monkeypatch):
    """Calling log_events with at least one kept event creates the log directory and file."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    log_events("sess-abc", [_make_event()])

    assert log_dir.exists(), "log directory should have been created"
    files = list(log_dir.iterdir())
    assert len(files) == 1, "exactly one log file should exist"


def test_each_event_is_one_json_line(tmp_path, monkeypatch):
    """3 BRAINSTORM events produce 3 lines; TEXT_RESPONSE events are dropped."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    events = [
        _make_event(event_type="BRAINSTORM", content=f"thought {i}", id=f"uuid-{i}")
        for i in range(3)
    ]
    # Add a TEXT_RESPONSE that should be dropped
    events.append(_make_event(event_type="TEXT_RESPONSE", content="streaming chunk", id="uuid-skip"))
    log_events("sess-abc", events)

    log_files = list(log_dir.iterdir())
    assert len(log_files) == 1
    lines = log_files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, f"expected 3 lines (TEXT_RESPONSE dropped), got {len(lines)}"
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


def test_compact_fields(tmp_path, monkeypatch):
    """Written JSON contains only 't' and 'c' fields — no id, timestamp, metadata, etc."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    log_events("sess-abc", [_make_event(event_type="BRAINSTORM", content="clean thought")])

    log_file = next(log_dir.iterdir())
    parsed = json.loads(log_file.read_text(encoding="utf-8").strip())

    assert set(parsed.keys()) == {"t", "c"}, f"unexpected keys: {set(parsed.keys())}"
    assert parsed["t"] == "BRAINSTORM"
    assert parsed["c"] == "clean thought"


def test_append_does_not_truncate(tmp_path, monkeypatch):
    """Two separate log_events() calls produce cumulative lines (2 + 1 = 3 total)."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    log_events("sess-abc", [
        _make_event(content="first", id="e1"),
        _make_event(content="second", id="e2"),
    ])
    log_events("sess-abc", [_make_event(content="third", id="e3")])

    log_files = list(log_dir.iterdir())
    assert len(log_files) == 1
    lines = log_files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, f"expected 3 total lines after 2 calls, got {len(lines)}"
    contents = [json.loads(line)["c"] for line in lines]
    assert contents == ["first", "second", "third"]


def test_empty_events_no_file(tmp_path, monkeypatch):
    """Calling log_events with an empty list does NOT create any file."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    log_events("sess-abc", [])

    if log_dir.exists():
        assert list(log_dir.iterdir()) == [], "no files should be created for empty events"


def test_oserror_does_not_raise(tmp_path, monkeypatch):
    """When builtins.open raises OSError, log_events catches it silently."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    def _raise_oserror(*args, **kwargs):
        raise OSError("disk full")

    with patch("builtins.open", side_effect=_raise_oserror):
        log_events("sess-abc", [_make_event()])  # must NOT raise


def test_text_response_skipped(tmp_path, monkeypatch):
    """TEXT_RESPONSE events produce no output — not even an empty file."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    events = [
        _make_event(event_type="TEXT_RESPONSE", content=f"chunk {i}", id=f"uuid-{i}")
        for i in range(10)
    ]
    log_events("sess-abc", events)

    if log_dir.exists():
        assert list(log_dir.iterdir()) == [], "TEXT_RESPONSE events must not create a log file"


def test_brainstorm_deduplication(tmp_path, monkeypatch):
    """Consecutive BRAINSTORM entries with identical content are written only once."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    # Same content in two separate calls (simulates re-emission)
    log_events("sess-abc", [_make_event(content="same thought", id="e1")])
    log_events("sess-abc", [_make_event(content="same thought", id="e2")])
    # Different content should go through
    log_events("sess-abc", [_make_event(content="new thought", id="e3")])

    lines = next(log_dir.iterdir()).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2, f"expected 2 lines (dedup removes repeat), got {len(lines)}"
    assert json.loads(lines[0])["c"] == "same thought"
    assert json.loads(lines[1])["c"] == "new thought"


def test_markdown_stripped(tmp_path, monkeypatch):
    """Bold, italic, inline code, and :::markers are removed from content."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    raw = "**Bold title** and *italic* and `code` and :::tool_call\nsome text"
    log_events("sess-abc", [_make_event(content=raw)])

    lines = next(log_dir.iterdir()).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    c = json.loads(lines[0])["c"]
    assert "**" not in c
    assert "*" not in c
    assert "`" not in c
    assert ":::" not in c
    assert "Bold title" in c
    assert "italic" in c
    assert "code" in c


def test_tool_call_formatted(tmp_path, monkeypatch):
    """ACTION_TRIGGER is rendered as tool_name(k=v) using metadata, not raw content."""
    log_dir = tmp_path / "logs" / "sessions"
    monkeypatch.setattr(session_logger_module, "_LOGS_DIR", str(log_dir))

    event = _make_event(
        event_type="ACTION_TRIGGER",
        content="Calling tool: **ingest_category_files**",
        metadata={"tool_name": "ingest_category_files", "arguments": {"category": "hvac"}},
    )
    log_events("sess-abc", [event])

    lines = next(log_dir.iterdir()).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["t"] == "TOOL_CALL"
    assert parsed["c"] == 'ingest_category_files(category="hvac")'
