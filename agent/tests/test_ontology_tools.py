"""
Unit tests for agent/tools/ontology_tools.py.

Covers:
- Path constants pointing to agent/223p/
- Three-write pattern for write_ontology (scratch + session archive + uploads)
- Session ID auto-detection from disk
- Zero-padded archive filename
- Three-write pattern for execute_ontology TTL
- extract_lessons function (returns session iteration files as JSON)
- create_master_agent.py imports extract_lessons
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Resolve imports: tests run from agent/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub heavy ADK imports before importing ontology_tools
_STUBS = {
    "google": MagicMock(),
    "google.adk": MagicMock(),
    "google.adk.agents": MagicMock(),
    "google.adk.tools": MagicMock(),
    "google.adk.tools.skill_toolset": MagicMock(),
    "dotenv": MagicMock(),
}
for _name, _mock in _STUBS.items():
    if _name not in sys.modules:
        sys.modules[_name] = _mock

from tools.ontology_tools import (  # noqa: E402
    ONTOLOGY_FILE,
    TTL_OUTPUT_DIR,
    _MAPPINGS_DIR,
    PYTHON_ITERATIONS_DIR,
    TTL_ITERATIONS_DIR,
    LESSONS_FILE,
    _PROMPT_MD,
    write_ontology,
    execute_ontology,
    extract_lessons,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class MockToolContext:
    """Minimal stand-in for google.adk.tools.ToolContext."""

    def __init__(self, state: dict | None = None):
        self.state = state or {}
        self.actions = MagicMock()
        self.agent_name = "test_agent"


# ---------------------------------------------------------------------------
# Path constant tests
# ---------------------------------------------------------------------------

def test_ontology_file_path_ends_with_agent_223p():
    """ONTOLOGY_FILE must point to agent/223p/ontology.py."""
    assert ONTOLOGY_FILE.replace("\\", "/").endswith("agent/223p/ontology.py"), (
        f"Expected ONTOLOGY_FILE to end with 'agent/223p/ontology.py', got: {ONTOLOGY_FILE}"
    )


def test_ttl_output_dir_ends_with_agent_223p():
    """TTL_OUTPUT_DIR must point to agent/223p/."""
    assert TTL_OUTPUT_DIR.replace("\\", "/").endswith("agent/223p"), (
        f"Expected TTL_OUTPUT_DIR to end with 'agent/223p', got: {TTL_OUTPUT_DIR}"
    )


def test_mappings_dir_ends_with_agent_223p_mappings():
    """_MAPPINGS_DIR must point to agent/223p/mappings."""
    assert _MAPPINGS_DIR.replace("\\", "/").endswith("agent/223p/mappings"), (
        f"Expected _MAPPINGS_DIR to end with 'agent/223p/mappings', got: {_MAPPINGS_DIR}"
    )


def test_python_iterations_dir_exists():
    """PYTHON_ITERATIONS_DIR must point to agent/223p/python_iterations."""
    assert PYTHON_ITERATIONS_DIR.replace("\\", "/").endswith("agent/223p/python_iterations"), (
        f"Expected PYTHON_ITERATIONS_DIR to end with 'agent/223p/python_iterations', got: {PYTHON_ITERATIONS_DIR}"
    )


def test_ttl_iterations_dir_exists():
    """TTL_ITERATIONS_DIR must point to agent/223p/ttl_iterations."""
    assert TTL_ITERATIONS_DIR.replace("\\", "/").endswith("agent/223p/ttl_iterations"), (
        f"Expected TTL_ITERATIONS_DIR to end with 'agent/223p/ttl_iterations', got: {TTL_ITERATIONS_DIR}"
    )


def test_lessons_file_ends_with_skill_ontology_lessons():
    """LESSONS_FILE must point to agent/skills/skill-ontology-lessons/SKILL.md."""
    assert LESSONS_FILE.replace("\\", "/").endswith("skill-ontology-lessons/SKILL.md"), (
        f"Expected LESSONS_FILE to end with 'skill-ontology-lessons/SKILL.md', got: {LESSONS_FILE}"
    )


def test_prompt_md_ends_with_ref_code():
    """_PROMPT_MD must point to agent/223p/ref/code/prompt.md."""
    assert _PROMPT_MD.replace("\\", "/").endswith("agent/223p/ref/code/prompt.md"), (
        f"Expected _PROMPT_MD to end with 'agent/223p/ref/code/prompt.md', got: {_PROMPT_MD}"
    )


# ---------------------------------------------------------------------------
# write_ontology three-write pattern
# ---------------------------------------------------------------------------

def test_write_ontology_three_write_pattern(tmp_path):
    """write_ontology writes to scratch + session archive + uploads (3 locations)."""
    scratch_file = tmp_path / "ontology.py"
    py_iterations = tmp_path / "python_iterations"

    ctx = MockToolContext(state={})

    with (
        patch("tools.ontology_tools.ONTOLOGY_FILE", str(scratch_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
        patch("tools.ontology_tools._persist_python") as mock_persist,
    ):
        result_json = write_ontology("test code", tool_context=ctx)

    result = json.loads(result_json)
    assert result["success"] is True

    # 1. Scratch file written
    assert scratch_file.exists(), "Scratch ontology.py not written"
    assert scratch_file.read_text() == "test code"

    # 2. Session archive written
    session_dir = py_iterations / "session_1"
    archive = session_dir / "ontology_001.py"
    assert archive.exists(), f"Session archive not written: {archive}"
    assert archive.read_text() == "test code"

    # 3. Uploads write called
    mock_persist.assert_called_once_with("test code", "write_ontology")


def test_write_ontology_auto_detects_session_id(tmp_path):
    """write_ontology auto-initializes ontology_session_id from disk when absent."""
    scratch_file = tmp_path / "ontology.py"
    py_iterations = tmp_path / "python_iterations"

    # Pre-create session_1 and session_2 directories (simulating prior sessions)
    (py_iterations / "session_1").mkdir(parents=True)
    (py_iterations / "session_2").mkdir(parents=True)

    ctx = MockToolContext(state={})  # No ontology_session_id in state

    with (
        patch("tools.ontology_tools.ONTOLOGY_FILE", str(scratch_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
        patch("tools.ontology_tools._persist_python"),
    ):
        write_ontology("auto detect code", tool_context=ctx)

    assert ctx.state["ontology_session_id"] == 3, (
        f"Expected session_id=3 (auto-detected from 2 existing sessions), "
        f"got: {ctx.state.get('ontology_session_id')}"
    )


def test_write_ontology_zero_pads_iteration_filename(tmp_path):
    """write_ontology names archive files as ontology_001.py (zero-padded 3 digits)."""
    scratch_file = tmp_path / "ontology.py"
    py_iterations = tmp_path / "python_iterations"

    ctx = MockToolContext(state={
        "ontology_session_id": 1,
        "ontology_code_iteration_count": 0,
    })

    with (
        patch("tools.ontology_tools.ONTOLOGY_FILE", str(scratch_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
        patch("tools.ontology_tools._persist_python"),
    ):
        write_ontology("iteration code", tool_context=ctx)

    archive = py_iterations / "session_1" / "ontology_001.py"
    assert archive.exists(), f"Expected zero-padded archive at {archive}"


# ---------------------------------------------------------------------------
# execute_ontology three-write for TTL
# ---------------------------------------------------------------------------

def test_execute_ontology_three_write_ttl(tmp_path):
    """execute_ontology writes TTL to uploads + session archive on success."""
    ttl_dir = tmp_path / "223p"
    ttl_dir.mkdir(parents=True)
    ttl_file = ttl_dir / "ontology.ttl"
    ttl_file.write_text("@prefix s223: <...> .", encoding="utf-8")

    ttl_iterations = tmp_path / "ttl_iterations"

    ctx = MockToolContext(state={
        "ontology_session_id": 1,
        "ontology_code_iteration_count": 1,
    })

    with (
        patch("tools.ontology_tools.TTL_OUTPUT_DIR", str(ttl_dir)),
        patch("tools.ontology_tools.TTL_ITERATIONS_DIR", str(ttl_iterations)),
        patch("tools.ontology_tools._persist_ttl") as mock_persist_ttl,
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        execute_ontology(tool_context=ctx)

    # _persist_ttl called once with the TTL content
    mock_persist_ttl.assert_called_once()
    call_args = mock_persist_ttl.call_args[0]
    assert "@prefix s223:" in call_args[0], "TTL content not passed to _persist_ttl"

    # TTL session archive file written
    ttl_archive = ttl_iterations / "session_1" / "ontology_001.ttl"
    assert ttl_archive.exists(), f"TTL session archive not written: {ttl_archive}"


# ---------------------------------------------------------------------------
# extract_lessons
# ---------------------------------------------------------------------------

def test_extract_lessons_returns_session_files(tmp_path):
    """extract_lessons returns all session iteration files as structured JSON."""
    session_dir = tmp_path / "session_1"
    session_dir.mkdir(parents=True)
    (session_dir / "ontology_001.py").write_text("code1", encoding="utf-8")
    (session_dir / "ontology_002.py").write_text("code2", encoding="utf-8")

    with patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(tmp_path)):
        result_json = extract_lessons()

    result = json.loads(result_json)
    assert result["success"] is True
    assert "session_1" in result["sessions"]
    assert len(result["sessions"]["session_1"]) == 2
    assert result["total_files"] == 2


def test_extract_lessons_empty_dir(tmp_path):
    """extract_lessons returns empty result when no iterations exist."""
    with patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(tmp_path)):
        result_json = extract_lessons()

    result = json.loads(result_json)
    assert result["success"] is True
    assert result["sessions"] == {}
    assert result["total_files"] == 0


def test_extract_lessons_nonexistent_dir(tmp_path):
    """extract_lessons returns empty result when PYTHON_ITERATIONS_DIR does not exist."""
    nonexistent = str(tmp_path / "does_not_exist")
    with patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", nonexistent):
        result_json = extract_lessons()

    result = json.loads(result_json)
    assert result["success"] is True
    assert result["sessions"] == {}
    assert result["total_files"] == 0


# ---------------------------------------------------------------------------
# Master agent wiring
# ---------------------------------------------------------------------------

def test_create_master_agent_imports_extract_lessons():
    """create_master_agent.py must import and wire extract_lessons."""
    src = (
        Path(__file__).parent.parent / "master_architecture" / "create_master_agent.py"
    ).read_text(encoding="utf-8")
    assert "extract_lessons" in src, (
        "extract_lessons not found in create_master_agent.py"
    )
