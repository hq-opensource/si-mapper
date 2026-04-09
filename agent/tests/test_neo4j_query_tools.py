"""Unit tests for neo4j_query_tools — all 4 BaseTool subclasses, mocked Neo4j driver."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tool_context() -> AsyncMock:
    """Return a minimal mock that satisfies ToolContext usage in the tools."""
    return AsyncMock()


def _make_driver_mock() -> MagicMock:
    """Return a MagicMock Neo4j driver that acts as a context manager."""
    mock_driver = MagicMock()
    mock_driver.__enter__ = MagicMock(return_value=mock_driver)
    mock_driver.__exit__ = MagicMock(return_value=False)
    return mock_driver


def _make_record(data: dict) -> MagicMock:
    """Return a fake Neo4j record backed by a dict."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: data[key]
    record.keys.return_value = list(data.keys())
    # dict(record) needs items() — use data directly
    return record


# ---------------------------------------------------------------------------
# TestExecuteCypherTool
# ---------------------------------------------------------------------------


class TestExecuteCypherTool:

    @pytest.mark.asyncio
    async def test_successful_query_returns_result(self):
        """Successful query returns {query, result, error: null, truncated: false}."""
        from tools.neo4j_query_tools import ExecuteCypherTool

        tool = ExecuteCypherTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        fan_record = MagicMock()
        fan_record.__iter__ = MagicMock(return_value=iter([("name", "Fan")]))
        fan_record.keys.return_value = ["name"]
        # Make dict(fan_record) work
        fan_record.data = MagicMock(return_value={"name": "Fan"})

        # execute_query returns (records, summary, keys)
        mock_driver.execute_query.return_value = ([fan_record], None, None)

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(
                args={"query": "MATCH (n) RETURN n.name AS name LIMIT 1"},
                tool_context=ctx,
            )

        assert result["query"] == "MATCH (n) RETURN n.name AS name LIMIT 1"
        assert result["error"] is None
        assert result["truncated"] is False
        assert result["result"] is not None

    @pytest.mark.asyncio
    async def test_cypher_syntax_error_returns_error(self):
        """Cypher syntax error returns {query, result: null, error: str}."""
        from tools.neo4j_query_tools import ExecuteCypherTool

        tool = ExecuteCypherTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        mock_driver.execute_query.side_effect = Exception("SyntaxError: BAD QUERY")

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(
                args={"query": "BAD QUERY"},
                tool_context=ctx,
            )

        assert result["query"] == "BAD QUERY"
        assert result["result"] is None
        assert "SyntaxError" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_query_returns_validation_error(self):
        """Empty query returns {query: '', result: null, error: 'query is required'}."""
        from tools.neo4j_query_tools import ExecuteCypherTool

        tool = ExecuteCypherTool()
        ctx = _make_tool_context()

        result = await tool.run_async(args={"query": ""}, tool_context=ctx)

        assert result["query"] == ""
        assert result["result"] is None
        assert "query is required" in result["error"]

    @pytest.mark.asyncio
    async def test_501_rows_truncated_to_500(self):
        """501 returned rows → first 500 kept, truncated=True."""
        from tools.neo4j_query_tools import ExecuteCypherTool

        tool = ExecuteCypherTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        # Build 501 fake records
        records = []
        for i in range(501):
            r = MagicMock()
            r.__iter__ = MagicMock(return_value=iter([("i", i)]))
            r.keys.return_value = ["i"]
            records.append(r)

        mock_driver.execute_query.return_value = (records, None, None)

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(
                args={"query": "MATCH (n) RETURN n LIMIT 501"},
                tool_context=ctx,
            )

        assert result["truncated"] is True
        assert len(result["result"]) == 500

    def test_declaration_name_and_query_parameter(self):
        """FunctionDeclaration name is 'execute_cypher' with 'query' STRING parameter."""
        from google.genai import types
        from tools.neo4j_query_tools import ExecuteCypherTool

        tool = ExecuteCypherTool()
        decl = tool._get_declaration()

        assert decl is not None
        assert decl.name == "execute_cypher"
        assert "query" in decl.parameters.properties
        assert decl.parameters.properties["query"].type == types.Type.STRING


# ---------------------------------------------------------------------------
# TestExecuteCypherBatchTool
# ---------------------------------------------------------------------------


class TestExecuteCypherBatchTool:

    @pytest.mark.asyncio
    async def test_three_queries_return_ordered_results(self):
        """3 queries → ordered list of 3 result dicts matching input order."""
        from tools.neo4j_query_tools import ExecuteCypherBatchTool

        tool = ExecuteCypherBatchTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        queries = ["MATCH (a) RETURN a", "MATCH (b) RETURN b", "MATCH (c) RETURN c"]

        def fake_execute(query, database_="neo4j"):
            r = MagicMock()
            r.__iter__ = MagicMock(return_value=iter([("q", query)]))
            r.keys.return_value = ["q"]
            return ([r], None, None)

        mock_driver.execute_query.side_effect = fake_execute

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(
                args={"queries": queries},
                tool_context=ctx,
            )

        assert result["status"] == "success"
        assert len(result["results"]) == 3
        # All results should be non-None (success case)
        for r in result["results"]:
            assert r is not None
            assert r["error"] is None

    @pytest.mark.asyncio
    async def test_partial_failure_preserves_order(self):
        """Partial failure (query 2 of 3 fails) → success+error+success in correct positions."""
        from tools.neo4j_query_tools import ExecuteCypherBatchTool

        tool = ExecuteCypherBatchTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        q0 = "MATCH (a) RETURN a"
        q1 = "BAD QUERY"
        q2 = "MATCH (c) RETURN c"

        def fake_execute(query, database_="neo4j"):
            if query == q1:
                raise Exception("SyntaxError on q1")
            r = MagicMock()
            r.__iter__ = MagicMock(return_value=iter([("q", query)]))
            r.keys.return_value = ["q"]
            return ([r], None, None)

        mock_driver.execute_query.side_effect = fake_execute

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(
                args={"queries": [q0, q1, q2]},
                tool_context=ctx,
            )

        assert result["status"] == "success"
        assert len(result["results"]) == 3
        assert result["results"][0]["error"] is None   # q0 succeeded
        assert result["results"][1]["error"] is not None  # q1 failed
        assert result["results"][2]["error"] is None   # q2 succeeded

    @pytest.mark.asyncio
    async def test_empty_queries_returns_empty_results(self):
        """Empty queries list → {status: 'success', results: []}."""
        from tools.neo4j_query_tools import ExecuteCypherBatchTool

        tool = ExecuteCypherBatchTool()
        ctx = _make_tool_context()

        result = await tool.run_async(args={"queries": []}, tool_context=ctx)

        assert result["status"] == "success"
        assert result["results"] == []

    def test_declaration_name_and_queries_array_parameter(self):
        """FunctionDeclaration name is 'execute_cypher_batch' with 'queries' ARRAY parameter."""
        from google.genai import types
        from tools.neo4j_query_tools import ExecuteCypherBatchTool

        tool = ExecuteCypherBatchTool()
        decl = tool._get_declaration()

        assert decl is not None
        assert decl.name == "execute_cypher_batch"
        assert "queries" in decl.parameters.properties
        assert decl.parameters.properties["queries"].type == types.Type.ARRAY


# ---------------------------------------------------------------------------
# TestGetGraphSchemaTool
# ---------------------------------------------------------------------------


class TestGetGraphSchemaTool:

    @pytest.mark.asyncio
    async def test_returns_schema_dict(self):
        """Returns {status: 'success', labels: [...], relationship_types: [...], property_keys: [...]}."""
        from tools.neo4j_query_tools import GetGraphSchemaTool

        tool = GetGraphSchemaTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        labels_record = MagicMock()
        labels_record.__getitem__ = lambda self, key: ["ashrae223__Fan", "ashrae223__Sensor"]

        rel_record = MagicMock()
        rel_record.__getitem__ = lambda self, key: ["hasProperty", "connectsTo"]

        prop_record = MagicMock()
        prop_record.__getitem__ = lambda self, key: ["uri", "name"]

        mock_driver.execute_query.side_effect = [
            ([labels_record], None, None),
            ([rel_record], None, None),
            ([prop_record], None, None),
        ]

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(args={}, tool_context=ctx)

        assert result["status"] == "success"
        assert "labels" in result
        assert "relationship_types" in result
        assert "property_keys" in result
        assert "ashrae223__Fan" in result["labels"]
        assert "hasProperty" in result["relationship_types"]

    @pytest.mark.asyncio
    async def test_connection_error_returns_error(self):
        """Connection error returns {status: 'error', message: str}."""
        from tools.neo4j_query_tools import GetGraphSchemaTool

        tool = GetGraphSchemaTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        mock_driver.execute_query.side_effect = Exception("Connection refused")

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(args={}, tool_context=ctx)

        assert result["status"] == "error"
        assert "message" in result

    def test_declaration_name_no_required_params(self):
        """FunctionDeclaration name is 'get_graph_schema' with no required parameters."""
        from tools.neo4j_query_tools import GetGraphSchemaTool

        tool = GetGraphSchemaTool()
        decl = tool._get_declaration()

        assert decl is not None
        assert decl.name == "get_graph_schema"
        # No required parameters
        required = getattr(decl.parameters, "required", None) or []
        assert len(required) == 0


# ---------------------------------------------------------------------------
# TestSearchGraphEntitiesTool
# ---------------------------------------------------------------------------


class TestSearchGraphEntitiesTool:

    @pytest.mark.asyncio
    async def test_keyword_matches_labels_case_insensitive(self):
        """keyword 'fan' matches 'ashrae223__Fan' and 'ashrae223__FanCoil' case-insensitively."""
        from tools.neo4j_query_tools import SearchGraphEntitiesTool

        tool = SearchGraphEntitiesTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        labels_record = MagicMock()
        labels_record.__getitem__ = lambda self, key: [
            "ashrae223__Fan",
            "ashrae223__FanCoil",
            "ashrae223__Sensor",
            "Resource",
        ]

        rel_record = MagicMock()
        rel_record.__getitem__ = lambda self, key: ["hasProperty", "connectsTo"]

        mock_driver.execute_query.side_effect = [
            ([labels_record], None, None),
            ([rel_record], None, None),
        ]

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(args={"keyword": "fan"}, tool_context=ctx)

        assert result["status"] == "success"
        assert result["keyword"] == "fan"
        assert "ashrae223__Fan" in result["matching_labels"]
        assert "ashrae223__FanCoil" in result["matching_labels"]
        assert "ashrae223__Sensor" not in result["matching_labels"]

    @pytest.mark.asyncio
    async def test_keyword_no_match_returns_empty_lists(self):
        """keyword 'xyz' returns empty matching_labels and matching_relationship_types."""
        from tools.neo4j_query_tools import SearchGraphEntitiesTool

        tool = SearchGraphEntitiesTool()
        ctx = _make_tool_context()
        mock_driver = _make_driver_mock()

        labels_record = MagicMock()
        labels_record.__getitem__ = lambda self, key: [
            "ashrae223__Fan",
            "ashrae223__Sensor",
        ]

        rel_record = MagicMock()
        rel_record.__getitem__ = lambda self, key: ["hasProperty", "connectsTo"]

        mock_driver.execute_query.side_effect = [
            ([labels_record], None, None),
            ([rel_record], None, None),
        ]

        with patch("tools.neo4j_query_tools.GraphDatabase") as mock_gdb:
            mock_gdb.driver.return_value = mock_driver
            result = await tool.run_async(args={"keyword": "xyz"}, tool_context=ctx)

        assert result["status"] == "success"
        assert result["matching_labels"] == []
        assert result["matching_relationship_types"] == []

    def test_declaration_name_and_keyword_parameter(self):
        """FunctionDeclaration name is 'search_graph_entities' with 'keyword' STRING parameter."""
        from google.genai import types
        from tools.neo4j_query_tools import SearchGraphEntitiesTool

        tool = SearchGraphEntitiesTool()
        decl = tool._get_declaration()

        assert decl is not None
        assert decl.name == "search_graph_entities"
        assert "keyword" in decl.parameters.properties
        assert decl.parameters.properties["keyword"].type == types.Type.STRING
