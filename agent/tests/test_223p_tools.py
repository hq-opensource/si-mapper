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


class TestSearchClassMapping:
    """Tests for search_class_mapping — uses real JSONL files in the repo."""

    def test_finds_matching_entries(self):
        """keywords=["AirHandlingUnit"] returns at least 1 result with that class_name."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["AirHandlingUnit"]))

        assert isinstance(results, list)
        assert len(results) >= 1
        assert any("AirHandlingUnit" in r["class_name"] for r in results)

    def test_case_insensitive(self):
        """keywords=["airhandling"] (lowercase) matches 'AirHandlingUnit'."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["airhandling"]))

        assert len(results) >= 1
        assert all("AirHandlingUnit" in r["class_name"] or "airhandling" in r["class_name"].lower() for r in results)

    def test_adds_library_field(self):
        """Each result dict has a 'library' key with value 'bob' or 'scratch'."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["Boiler"]))

        assert len(results) >= 1
        for r in results:
            assert "library" in r
            assert r["library"] in ("bob", "scratch")

    def test_returns_all_fields(self):
        """Each result dict has 'class_name', 'path', 'types', and 'library' keys."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["Chiller"]))

        assert len(results) >= 1
        for r in results:
            assert "class_name" in r
            assert "path" in r
            assert "types" in r
            assert "library" in r

    def test_no_matches(self):
        """keywords=["zzz_nonexistent_zzz"] returns empty list."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["zzz_nonexistent_zzz"]))

        assert results == []

    def test_multiple_keywords(self):
        """keywords=["Fan", "Boiler"] returns entries matching either keyword."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["Fan", "Boiler"]))

        names = [r["class_name"].lower() for r in results]
        assert any("fan" in n for n in names), "Expected Fan matches"
        assert any("boiler" in n for n in names), "Expected Boiler matches"

    def test_searches_both_libraries(self):
        """A keyword matching entries in both files returns results from both bob and scratch."""
        from sub_agents._223p.tool import search_class_mapping

        results = json.loads(search_class_mapping(keywords=["AirHandlingUnit"]))

        libraries = {r["library"] for r in results}
        assert "bob" in libraries, "Expected bob results"
        assert "scratch" in libraries, "Expected scratch results"
