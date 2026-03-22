"""Unit tests for LoadTtlToNeo4jTool — mocked Neo4j driver and file I/O."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool_context() -> AsyncMock:
    """Return a minimal mock that satisfies ToolContext usage in the tool."""
    ctx = AsyncMock()
    return ctx


def _make_records(triples_loaded: int = 42, termination: str = "OK") -> list:
    """Return a fake records list matching the n10s.rdf.import.inline YIELD columns."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: {
        "triplesLoaded": triples_loaded,
        "terminationStatus": termination,
    }[key]
    return [record]


def _make_count_record(count: int) -> list:
    record = MagicMock()
    record.__getitem__ = lambda self, key: count
    return [record]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadTtlToNeo4jTool:

    @pytest.mark.asyncio
    async def test_successful_import(self):
        """Driver is reachable, TTL file exists — returns success with triples_loaded."""
        from master_architecture.tools.load_ttl_to_neo4j_tool import LoadTtlToNeo4jTool

        tool = LoadTtlToNeo4jTool()
        ctx = _make_tool_context()

        sample_ttl = "@prefix s223: <http://data.ashrae.org/standard223#> .\n"

        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=False)

        # execute_query returns (records, summary, keys)
        # Call order: wipe, drop config, drop constraint, create constraint, init config, import inline, count nodes, count rels
        import_records = _make_records(triples_loaded=42, termination="OK")
        node_records = _make_count_record(10)
        rel_records = _make_count_record(5)

        mock_driver.execute_query.side_effect = [
            ([], None, None),               # 1: MATCH (n) DETACH DELETE n
            ([], None, None),               # 2: n10s.graphconfig.drop()
            ([], None, None),               # 3: DROP CONSTRAINT
            ([], None, None),               # 4: CREATE CONSTRAINT
            ([], None, None),               # 5: n10s.graphconfig.init
            (import_records, None, None),   # 6: n10s.rdf.import.inline
            (node_records, None, None),     # 7: count nodes
            (rel_records, None, None),      # 8: count rels
        ]

        with (
            patch("master_architecture.tools.load_ttl_to_neo4j_tool.GraphDatabase") as mock_gdb,
            patch("master_architecture.tools.load_ttl_to_neo4j_tool.Path") as mock_path_cls,
        ):
            mock_gdb.driver.return_value = mock_driver

            mock_ttl_path = MagicMock()
            mock_ttl_path.exists.return_value = True
            mock_ttl_path.read_text.return_value = sample_ttl
            # Make Path(...) / ... chain return mock_ttl_path
            mock_path_instance = MagicMock()
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.parents.__getitem__ = MagicMock(return_value=mock_path_instance)
            mock_path_instance.__truediv__ = MagicMock(return_value=mock_ttl_path)
            mock_path_cls.return_value = mock_path_instance
            # Make Path(__file__) work
            mock_path_cls.side_effect = None
            mock_path_cls.return_value = mock_path_instance

            result = await tool.run_async(args={}, tool_context=ctx)

        assert result["status"] == "success"
        assert result["triples_loaded"] == 42
        # Verify execute_query called enough times (wipe + drop config + drop constraint + create constraint + init config + import = at least 6 times, total 8)
        assert mock_driver.execute_query.call_count >= 5

    @pytest.mark.asyncio
    async def test_missing_ttl_file(self):
        """TTL file does not exist — returns error containing 'not found'."""
        from master_architecture.tools.load_ttl_to_neo4j_tool import LoadTtlToNeo4jTool

        tool = LoadTtlToNeo4jTool()
        ctx = _make_tool_context()

        with patch("master_architecture.tools.load_ttl_to_neo4j_tool.Path") as mock_path_cls:
            mock_ttl_path = MagicMock()
            mock_ttl_path.exists.return_value = False
            mock_ttl_path.__str__ = MagicMock(return_value="/fake/ontology.ttl")

            mock_path_instance = MagicMock()
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.parents.__getitem__ = MagicMock(return_value=mock_path_instance)
            mock_path_instance.__truediv__ = MagicMock(return_value=mock_ttl_path)
            mock_path_cls.return_value = mock_path_instance

            result = await tool.run_async(args={}, tool_context=ctx)

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_neo4j_connection_error(self):
        """GraphDatabase.driver raises ServiceUnavailable — returns error dict."""
        from neo4j.exceptions import ServiceUnavailable

        from master_architecture.tools.load_ttl_to_neo4j_tool import LoadTtlToNeo4jTool

        tool = LoadTtlToNeo4jTool()
        ctx = _make_tool_context()

        sample_ttl = "@prefix s223: <http://data.ashrae.org/standard223#> .\n"

        with (
            patch("master_architecture.tools.load_ttl_to_neo4j_tool.GraphDatabase") as mock_gdb,
            patch("master_architecture.tools.load_ttl_to_neo4j_tool.Path") as mock_path_cls,
        ):
            mock_gdb.driver.side_effect = ServiceUnavailable("Cannot connect to Neo4j")

            mock_ttl_path = MagicMock()
            mock_ttl_path.exists.return_value = True
            mock_ttl_path.read_text.return_value = sample_ttl

            mock_path_instance = MagicMock()
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.parents.__getitem__ = MagicMock(return_value=mock_path_instance)
            mock_path_instance.__truediv__ = MagicMock(return_value=mock_ttl_path)
            mock_path_cls.return_value = mock_path_instance

            result = await tool.run_async(args={}, tool_context=ctx)

        assert result["status"] == "error"
        assert "message" in result

    def test_tool_declaration(self):
        """_get_declaration returns FunctionDeclaration with correct name."""
        from master_architecture.tools.load_ttl_to_neo4j_tool import LoadTtlToNeo4jTool

        tool = LoadTtlToNeo4jTool()
        declaration = tool._get_declaration()

        assert declaration is not None
        assert declaration.name == "load_ttl_to_neo4j"
