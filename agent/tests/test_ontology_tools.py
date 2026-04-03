"""
Unit tests for agent/tools/ontology_tools.py and agent/tools/exit_tools.py.

Covers:
- Path constants pointing to agent/223p/
- read_python_files: absolute path, project-relative path, missing file, multi-path
- scan_python_folder: keyword filtering, missing dir error, cap at 10 files, force=True bypass
- Two-write pattern for write_ontology (scratch + session archive)
- write_ontology auto-increments ontology_code_iteration_count
- Session ID auto-detection from disk
- Zero-padded archive filename
- Two-write pattern for execute_ontology TTL (session archive only)
- execute_ontology Linux venv path checked before Windows path
- execute_ontology auto-detects session from python_iterations
- exit_with_success: sets EXIT_LEVEL_2, returns success status, no domain-specific keys
- exit_with_failure: sets EXIT_LEVEL_2, returns failure status, no domain-specific keys
- execute_ontology patches python_code_snapshots to Final/validated on success
- extract_lessons function (returns session iteration files + current skill content)
- create_master_agent.py wiring (read_python_files, scan_python_folder, extract_lessons)
- level_3_master_main_llm.py imports exit_with_success/exit_with_failure from exit_tools
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
    read_python_files,
    scan_python_folder,
    write_ontology,
    execute_ontology,
    extract_lessons,
)
from tools.exit_tools import (  # noqa: E402
    exit_with_success,
    exit_with_failure,
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

def test_ontology_file_path_ends_with_uploads_latest():
    """ONTOLOGY_FILE must point to mapper/uploads/python/latest_ontology.py."""
    assert ONTOLOGY_FILE.replace("\\", "/").endswith("uploads/python/latest_ontology.py"), (
        f"Expected ONTOLOGY_FILE to end with 'uploads/python/latest_ontology.py', got: {ONTOLOGY_FILE}"
    )


def test_ttl_output_dir_ends_with_uploads_ttl():
    """TTL_OUTPUT_DIR must point to mapper/uploads/ttl."""
    assert TTL_OUTPUT_DIR.replace("\\", "/").endswith("uploads/ttl"), (
        f"Expected TTL_OUTPUT_DIR to end with 'uploads/ttl', got: {TTL_OUTPUT_DIR}"
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


# ---------------------------------------------------------------------------
# read_python_files
# ---------------------------------------------------------------------------

def test_read_python_files_absolute_path(tmp_path):
    """read_python_files reads a file given an absolute path (full_content=True)."""
    f = tmp_path / "test.py"
    f.write_text("print('hello')", encoding="utf-8")

    results = json.loads(read_python_files([str(f)], keywords=[], full_content=True))
    assert len(results) == 1
    assert results[0]["error"] is None
    assert results[0]["total_lines"] == 1
    assert "print('hello')" in results[0]["sections"][0]["content"]


def test_read_python_files_project_relative_path(tmp_path):
    """read_python_files resolves project-relative paths (e.g. 'agent/223p/ontology.py')."""
    rel = "agent/223p/ontology.py"
    target = tmp_path / "agent" / "223p" / "ontology.py"
    target.parent.mkdir(parents=True)
    target.write_text("# ontology", encoding="utf-8")

    with patch("tools.ontology_tools._PROJECT_ROOT", str(tmp_path)):
        results = json.loads(read_python_files([rel], keywords=[], full_content=True))

    assert len(results) == 1
    assert results[0]["error"] is None
    assert "# ontology" in results[0]["sections"][0]["content"]


def test_read_python_files_missing_file(tmp_path):
    """read_python_files returns an error entry for files that do not exist."""
    missing = str(tmp_path / "does_not_exist.py")
    results = json.loads(read_python_files([missing], keywords=[], full_content=True))
    assert len(results) == 1
    assert results[0]["error"] is not None
    assert results[0]["sections"] == []


def test_read_python_files_multiple_paths(tmp_path):
    """read_python_files reads multiple files in one call."""
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("aaa", encoding="utf-8")
    f2.write_text("bbb", encoding="utf-8")

    results = json.loads(read_python_files([str(f1), str(f2)], keywords=[], full_content=True))
    assert len(results) == 2
    contents = [r["sections"][0]["content"] for r in results]
    assert any("aaa" in c for c in contents)
    assert any("bbb" in c for c in contents)


def test_read_python_files_handles_non_py_files(tmp_path):
    """read_python_files reads non-.py files (e.g. prompt.md) without error."""
    md = tmp_path / "prompt.md"
    md.write_text("# prompt content", encoding="utf-8")

    results = json.loads(read_python_files([str(md)], keywords=[], full_content=True))
    assert len(results) == 1
    assert results[0]["error"] is None
    assert "# prompt content" in results[0]["sections"][0]["content"]


# ---------------------------------------------------------------------------
# scan_python_folder
# ---------------------------------------------------------------------------

def test_scan_python_folder_keyword_filtering(tmp_path):
    """scan_python_folder returns only files whose content contains a keyword."""
    (tmp_path / "fan.py").write_text("class Fan: pass", encoding="utf-8")
    (tmp_path / "coil.py").write_text("class Coil: pass", encoding="utf-8")

    result = json.loads(scan_python_folder(str(tmp_path), ["fan"]))
    file_paths = [f["path"] for f in result["files"]]
    assert "fan.py" in file_paths
    assert "coil.py" not in file_paths


def test_scan_python_folder_missing_dir(tmp_path):
    """scan_python_folder returns an error when the directory does not exist."""
    missing = str(tmp_path / "no_such_dir")
    result = json.loads(scan_python_folder(missing, ["anything"]))
    assert "error" in result
    assert result["files"] == []


def test_scan_python_folder_rejects_file_path(tmp_path):
    """scan_python_folder returns an error when given a file path instead of a dir."""
    f = tmp_path / "not_a_dir.py"
    f.write_text("x = 1")
    result = json.loads(scan_python_folder(str(f), ["x"]))
    assert "error" in result


def test_scan_python_folder_caps_at_10_files(tmp_path):
    """scan_python_folder returns message-only when > 10 files match."""
    # Create 12 matching files
    for i in range(12):
        (tmp_path / f"fan_{i}.py").write_text("class Fan: pass", encoding="utf-8")
    result = json.loads(scan_python_folder(str(tmp_path), ["fan"]))
    assert "message" in result, "Expected message key when > 10 matches"
    assert result["files"] == [], "Expected empty files list when > 10 matches"
    assert "12" in result["message"], "Message should contain match count"


def test_scan_python_folder_force_bypasses_cap(tmp_path):
    """scan_python_folder returns all files when force=True even if > 10."""
    for i in range(12):
        (tmp_path / f"fan_{i}.py").write_text("class Fan: pass", encoding="utf-8")
    result = json.loads(scan_python_folder(str(tmp_path), ["fan"], force=True))
    assert "message" not in result, "force=True should bypass cap"
    assert len(result["files"]) == 12


# ---------------------------------------------------------------------------
# write_ontology two-write pattern
# ---------------------------------------------------------------------------

def test_write_ontology_two_write_pattern(tmp_path):
    """write_ontology writes to latest_ontology.py + session archive (2 locations)."""
    scratch_file = tmp_path / "ontology.py"
    py_iterations = tmp_path / "python_iterations"

    ctx = MockToolContext(state={})

    with (
        patch("tools.ontology_tools.ONTOLOGY_FILE", str(scratch_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
    ):
        result_json = write_ontology("test code", tool_context=ctx)

    result = json.loads(result_json)
    assert result["success"] is True

    # 1. Primary file written
    assert scratch_file.exists(), "Primary latest_ontology.py not written"
    assert scratch_file.read_text() == "test code"

    # 2. Session archive written
    session_dir = py_iterations / "session_1"
    archive = session_dir / "ontology_001.py"
    assert archive.exists(), f"Session archive not written: {archive}"
    assert archive.read_text() == "test code"


def test_write_ontology_auto_increments_iteration_count(tmp_path):
    """write_ontology increments ontology_code_iteration_count on each call."""
    scratch_file = tmp_path / "ontology.py"
    py_iterations = tmp_path / "python_iterations"
    ctx = MockToolContext(state={"ontology_session_id": 1, "ontology_code_iteration_count": 0})
    with (
        patch("tools.ontology_tools.ONTOLOGY_FILE", str(scratch_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
    ):
        write_ontology("code v1", tool_context=ctx)
    assert ctx.state["ontology_code_iteration_count"] == 1
    with (
        patch("tools.ontology_tools.ONTOLOGY_FILE", str(scratch_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
    ):
        write_ontology("code v2", tool_context=ctx)
    assert ctx.state["ontology_code_iteration_count"] == 2


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
    ):
        write_ontology("iteration code", tool_context=ctx)

    archive = py_iterations / "session_1" / "ontology_001.py"
    assert archive.exists(), f"Expected zero-padded archive at {archive}"


# ---------------------------------------------------------------------------
# execute_ontology two-write for TTL
# ---------------------------------------------------------------------------

def test_execute_ontology_two_write_ttl(tmp_path):
    """execute_ontology reads latest_ontology.ttl and writes session archive only."""
    ttl_dir = tmp_path / "uploads" / "ttl"
    ttl_dir.mkdir(parents=True)
    latest = ttl_dir / "latest_ontology.ttl"
    latest.write_text("@prefix s223: <...> .", encoding="utf-8")

    ttl_iterations = tmp_path / "ttl_iterations"
    py_iterations = tmp_path / "py_iterations"

    ctx = MockToolContext(state={
        "ontology_session_id": 1,
        "ontology_code_iteration_count": 1,  # iter_count=1 → archive name = 002
    })

    with (
        patch("tools.ontology_tools.TTL_OUTPUT_DIR", str(ttl_dir)),
        patch("tools.ontology_tools.TTL_ITERATIONS_DIR", str(ttl_iterations)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        execute_ontology(tool_context=ctx)

    # TTL archive uses 1-based numbering matching Python: iter_count=1 → ontology_002.ttl
    ttl_archive = ttl_iterations / "session_1" / "ontology_002.ttl"
    assert ttl_archive.exists(), f"TTL session archive not written at expected path: {ttl_archive}"

    # latest_ontology.ttl still exists — it IS the canonical file, not deleted
    assert latest.exists(), "latest_ontology.ttl should not have been deleted"


def test_execute_ontology_auto_detects_session_from_python_iterations(tmp_path):
    """execute_ontology auto-detects session_id from python_iterations when missing from state."""
    ttl_dir = tmp_path / "uploads" / "ttl"
    ttl_dir.mkdir(parents=True)
    (ttl_dir / "latest_ontology.ttl").write_text("@prefix s223: <...> .", encoding="utf-8")

    ttl_iterations = tmp_path / "ttl_iterations"
    py_iterations = tmp_path / "py_iterations"
    # Pre-create session_1 in python_iterations to simulate an active session
    (py_iterations / "session_1").mkdir(parents=True)

    ctx = MockToolContext(state={})  # No session_id in state

    with (
        patch("tools.ontology_tools.TTL_OUTPUT_DIR", str(ttl_dir)),
        patch("tools.ontology_tools.TTL_ITERATIONS_DIR", str(ttl_iterations)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        execute_ontology(tool_context=ctx)

    assert ctx.state["ontology_session_id"] == 1, (
        f"Expected session_id=1 (auto-detected from 1 python session), got: {ctx.state.get('ontology_session_id')}"
    )
    ttl_archive = ttl_iterations / "session_1" / "ontology_001.ttl"
    assert ttl_archive.exists(), f"TTL archive not created under auto-detected session: {ttl_archive}"


def test_execute_ontology_checks_linux_venv_first(tmp_path):
    """execute_ontology checks Linux venv path before Windows path."""
    src = open(os.path.join(os.path.dirname(__file__), "..", "tools", "ontology_tools.py")).read()
    # Find the venv detection block in execute_ontology
    exec_block = src.split("def execute_ontology")[1].split("def ")[0]
    linux_pos = exec_block.index("bin/python")
    windows_pos = exec_block.index("Scripts/python.exe")
    assert linux_pos < windows_pos, "Linux venv path must be checked before Windows path"


# ---------------------------------------------------------------------------
# exit_with_success / exit_with_failure (generic exit tools)
# ---------------------------------------------------------------------------

def test_exit_with_success_sets_exit_level_2_and_returns_status():
    """exit_with_success sets EXIT_LEVEL_2=True, escalate=True, returns success."""
    ctx = MockToolContext(state={})
    result = exit_with_success(ctx, summary="task done")
    assert result["status"] == "success"
    assert result["summary"] == "task done"
    assert ctx.state["EXIT_LEVEL_2"] is True
    assert ctx.actions.escalate is True
    # Must NOT set any domain-specific keys
    assert "ONTOLOGY_GENERATION_SUCCESS" not in ctx.state
    assert "ONTOLOGY_VALIDATION_SUCCESS" not in ctx.state


def test_exit_with_failure_sets_exit_level_2_and_returns_status():
    """exit_with_failure sets EXIT_LEVEL_2=True, escalate=True, returns failure."""
    ctx = MockToolContext(state={})
    result = exit_with_failure(ctx, reason="could not parse")
    assert result["status"] == "failure"
    assert result["reason"] == "could not parse"
    assert ctx.state["EXIT_LEVEL_2"] is True
    assert ctx.actions.escalate is True
    # Must NOT set any domain-specific keys
    assert "ONTOLOGY_GENERATION_SUCCESS" not in ctx.state
    assert "ONTOLOGY_VALIDATION_SUCCESS" not in ctx.state


# ---------------------------------------------------------------------------
# execute_ontology snapshot patching
# ---------------------------------------------------------------------------

def test_execute_ontology_patches_python_snapshots_to_final(tmp_path):
    """execute_ontology patches last python_code_snapshot to Final/validated on success."""
    ttl_dir = tmp_path / "uploads" / "ttl"
    ttl_dir.mkdir(parents=True)
    latest = ttl_dir / "latest_ontology.ttl"
    latest.write_text("@prefix s223: <urn:test> .", encoding="utf-8")

    ttl_iterations = tmp_path / "ttl_iterations"
    py_iterations = tmp_path / "py_iterations"

    ctx = MockToolContext(state={
        "ontology_session_id": 1,
        "ontology_code_iteration_count": 0,
        "python_code_snapshots": [
            {"label": "Iteration 1", "code": "x=1", "iteration": 0, "status": "generated"}
        ],
    })

    with (
        patch("tools.ontology_tools.TTL_OUTPUT_DIR", str(ttl_dir)),
        patch("tools.ontology_tools.TTL_ITERATIONS_DIR", str(ttl_iterations)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(py_iterations)),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        execute_ontology(tool_context=ctx)

    # Python snapshot patched to Final/validated
    py_snaps = ctx.state["python_code_snapshots"]
    assert py_snaps[-1]["label"] == "Final"
    assert py_snaps[-1]["status"] == "validated"

    # TTL snapshot uses label="TTL" and iteration=0
    ttl_snaps = ctx.state.get("ttl_code_snapshots", [])
    assert len(ttl_snaps) >= 1
    assert ttl_snaps[-1]["label"] == "TTL"
    assert ttl_snaps[-1]["iteration"] == 0
    assert ttl_snaps[-1]["status"] == "validated"
    assert "@prefix s223:" in ttl_snaps[-1]["code"]


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


def test_extract_lessons_includes_current_skill_content(tmp_path):
    """extract_lessons returns current_skill_content from skill-ontology-lessons/SKILL.md."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# existing lessons", encoding="utf-8")

    iterations = tmp_path / "iterations"
    iterations.mkdir()

    with (
        patch("tools.ontology_tools.LESSONS_FILE", str(skill_file)),
        patch("tools.ontology_tools.PYTHON_ITERATIONS_DIR", str(iterations)),
    ):
        result_json = extract_lessons()

    result = json.loads(result_json)
    assert result["current_skill_content"] == "# existing lessons"


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

def test_create_master_agent_wires_new_tools():
    """create_master_agent.py must import read_python_files, scan_python_folder, extract_lessons."""
    src = (
        Path(__file__).parent.parent / "master_architecture" / "create_master_agent.py"
    ).read_text(encoding="utf-8")
    assert "read_python_files" in src, "read_python_files not found in create_master_agent.py"
    assert "scan_python_folder" in src, "scan_python_folder not found in create_master_agent.py"
    assert "extract_lessons" in src, "extract_lessons not found in create_master_agent.py"


def test_create_master_agent_does_not_import_removed_tools():
    """create_master_agent.py must not import the removed read_ontology, read_prompt, scan_python_files_filtered."""
    src = (
        Path(__file__).parent.parent / "master_architecture" / "create_master_agent.py"
    ).read_text(encoding="utf-8")
    assert "read_ontology" not in src, "Removed tool read_ontology still in create_master_agent.py"
    assert "read_prompt" not in src, "Removed tool read_prompt still in create_master_agent.py"
    assert "scan_python_files_filtered" not in src, (
        "Removed tool scan_python_files_filtered still in create_master_agent.py"
    )
    assert "exit_generator_success" not in src, "Removed exit_generator_success still in create_master_agent.py"
    assert "exit_generator_failure" not in src, "Removed exit_generator_failure still in create_master_agent.py"
    assert "exit_validator_success" not in src, "Removed exit_validator_success still in create_master_agent.py"
    assert "exit_validator_failure" not in src, "Removed exit_validator_failure still in create_master_agent.py"
    assert "ontology_exit_tools" not in src, "Removed ontology_exit_tools import still in create_master_agent.py"
    assert "loop_exit_tools" not in src, "Removed loop_exit_tools import still in create_master_agent.py"


def test_master_llm_imports_new_exit_tools():
    """level_3_master_main_llm.py must import exit_with_success and exit_with_failure from exit_tools."""
    src = (
        Path(__file__).parent.parent / "master_architecture" / "level_3_master_main_llm.py"
    ).read_text(encoding="utf-8")
    assert "from tools.exit_tools import" in src, "exit_tools import not found in level_3_master_main_llm.py"
    assert "exit_with_success" in src, "exit_with_success not found in level_3_master_main_llm.py"
    assert "exit_with_failure" in src, "exit_with_failure not found in level_3_master_main_llm.py"
    assert "exit_loop_level_2" not in src, "Old exit_loop_level_2 still in level_3_master_main_llm.py"
