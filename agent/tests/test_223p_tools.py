"""
Unit tests for scan_python_files_filtered in agent/sub_agents/_223p/tool.py.

Tests verify keyword-filtered scanning: only .py files whose content matches
at least one keyword (case-insensitive substring) are returned.
"""
from __future__ import annotations

import json

import pytest

from sub_agents._223p.tool import scan_python_files_filtered


class TestScanPythonFilesFiltered:

    def test_returns_only_matching_files(self, tmp_path):
        """Only files whose content contains the keyword are returned."""
        (tmp_path / "fan_coil.py").write_text("class FanCoilUnit: pass")
        (tmp_path / "pump.py").write_text("class Fan: pass")
        (tmp_path / "chiller.py").write_text("class Chiller: pass")

        result = json.loads(scan_python_files_filtered(str(tmp_path), ["Fan"]))

        assert "files" in result
        assert len(result["files"]) == 2
        assert "fan_coil.py" in result["files"]
        assert "pump.py" in result["files"]
        assert "chiller.py" not in result["files"]

    def test_case_insensitive(self, tmp_path):
        """Keyword 'fan' (lowercase) matches file containing 'Fan' (uppercase)."""
        (tmp_path / "equipment.py").write_text("class Fan: pass")
        (tmp_path / "other.py").write_text("class Pump: pass")

        result = json.loads(scan_python_files_filtered(str(tmp_path), ["fan"]))

        assert "equipment.py" in result["files"]
        assert "other.py" not in result["files"]

    def test_no_matches(self, tmp_path):
        """Keywords that match nothing return an empty files dict."""
        (tmp_path / "boiler.py").write_text("class Boiler: pass")
        (tmp_path / "chiller.py").write_text("class Chiller: pass")

        result = json.loads(scan_python_files_filtered(str(tmp_path), ["nonexistent"]))

        assert result["files"] == {}

    def test_path_not_found(self):
        """Non-existent path returns an error key."""
        result = json.loads(
            scan_python_files_filtered("/nonexistent/path/that/does/not/exist", ["Fan"])
        )

        assert "error" in result

    def test_path_not_dir(self, tmp_path):
        """Path pointing to a file (not a directory) returns an error key."""
        target = tmp_path / "single_file.py"
        target.write_text("class Pump: pass")

        result = json.loads(scan_python_files_filtered(str(target), ["Pump"]))

        assert "error" in result

    def test_multiple_keywords(self, tmp_path):
        """Files matching ANY of the keywords are returned (OR logic)."""
        (tmp_path / "fan.py").write_text("class Fan: pass")
        (tmp_path / "coil.py").write_text("class Coil: pass")
        (tmp_path / "pump.py").write_text("class Pump: pass")

        result = json.loads(scan_python_files_filtered(str(tmp_path), ["Fan", "Coil"]))

        assert len(result["files"]) == 2
        assert "fan.py" in result["files"]
        assert "coil.py" in result["files"]
        assert "pump.py" not in result["files"]

    def test_json_shape(self, tmp_path):
        """Result has same JSON shape as scan_python_files: root + files keys."""
        (tmp_path / "module.py").write_text("# nothing")

        result = json.loads(scan_python_files_filtered(str(tmp_path), ["nothing"]))

        assert "root" in result
        assert "files" in result
        assert isinstance(result["root"], str)
        assert isinstance(result["files"], dict)
