"""Cypher query tools for Neo4j agent exploration.

4 BaseTool subclasses giving the master agent read access to the live Neo4j graph:
  - ExecuteCypherTool       — run a single Cypher query
  - ExecuteCypherBatchTool  — run N queries in parallel via ThreadPoolExecutor
  - GetGraphSchemaTool      — introspect labels, relationship types, property keys
  - SearchGraphEntitiesTool — case-insensitive keyword search across labels/rel types
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from google.adk.tools import BaseTool, ToolContext
from google.genai import types
from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path
from typing_extensions import override

from utils.project_utils import get_neo4j_db_name

logger = logging.getLogger(__name__)

ROW_LIMIT = 500


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _get_neo4j_config() -> tuple[str, str, str]:
    """Return (uri, user, password) from environment variables with defaults."""
    return (
        os.getenv("NEO4J_BOLT_URI", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "neo4j_password"),
    )


def _serialize(value: Any) -> Any:
    """Recursively convert Neo4j graph types to plain Python primitives."""
    if isinstance(value, Node):
        return {"_labels": list(value.labels), **{k: _serialize(v) for k, v in value.items()}}
    if isinstance(value, Relationship):
        return {"_type": value.type, "_start": value.start_node.element_id, "_end": value.end_node.element_id, **{k: _serialize(v) for k, v in value.items()}}
    if isinstance(value, Path):
        return {"_nodes": [_serialize(n) for n in value.nodes], "_relationships": [_serialize(r) for r in value.relationships]}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def _run_query(driver: Any, query: str, database: str = "neo4j") -> dict:
    """Execute a single Cypher query and return a normalised result dict.

    Thread-safe: called from ThreadPoolExecutor workers in batch mode.
    """
    try:
        records, _, _ = driver.execute_query(query, database_=database)
        rows = [_serialize(dict(r)) for r in records]
        truncated = len(rows) > ROW_LIMIT
        return {
            "query": query,
            "result": rows[:ROW_LIMIT],
            "error": None,
            "truncated": truncated,
        }
    except Exception as e:
        return {"query": query, "result": None, "error": str(e)}


# ---------------------------------------------------------------------------
# ExecuteCypherTool
# ---------------------------------------------------------------------------


class ExecuteCypherTool(BaseTool):
    """Run a single Cypher read query against the Neo4j graph."""

    def __init__(self) -> None:
        super().__init__(
            name="execute_cypher",
            description=(
                "Execute a single Cypher query against the Neo4j graph and return the results. "
                "Results are capped at 500 rows. "
                "Returns {query, result, error, truncated}."
            ),
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The Cypher query to execute.",
                    ),
                },
                required=["query"],
            ),
        )

    @override
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        query = args.get("query", "")
        if not query:
            return {"query": query, "result": None, "error": "query is required"}

        uri, user, password = _get_neo4j_config()
        db_name = get_neo4j_db_name(tool_context)
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            return _run_query(driver, query, database=db_name)


# ---------------------------------------------------------------------------
# ExecuteCypherBatchTool
# ---------------------------------------------------------------------------


class ExecuteCypherBatchTool(BaseTool):
    """Run multiple Cypher queries in parallel and return ordered results."""

    def __init__(self) -> None:
        super().__init__(
            name="execute_cypher_batch",
            description=(
                "Execute a list of Cypher queries in parallel using a thread pool. "
                "Results are returned in the same order as the input queries. "
                "Partial failures are reported per-query without aborting the batch. "
                "Returns {status, results: [{query, result, error, truncated}, ...]}."
            ),
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "queries": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="List of Cypher queries to execute in parallel.",
                    ),
                },
                required=["queries"],
            ),
        )

    @override
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        queries: list[str] = args.get("queries", [])
        if not queries:
            return {"status": "success", "results": []}

        uri, user, password = _get_neo4j_config()
        db_name = get_neo4j_db_name(tool_context)
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            ordered: list[dict | None] = [None] * len(queries)
            max_workers = min(len(queries), 8)
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                future_to_index = {
                    pool.submit(_run_query, driver, q, db_name): i
                    for i, q in enumerate(queries)
                }
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        ordered[idx] = future.result()
                    except Exception as e:
                        ordered[idx] = {
                            "query": queries[idx],
                            "result": None,
                            "error": str(e),
                        }

        return {"status": "success", "results": ordered}


# ---------------------------------------------------------------------------
# GetGraphSchemaTool
# ---------------------------------------------------------------------------


class GetGraphSchemaTool(BaseTool):
    """Introspect the Neo4j graph schema: labels, relationship types, property keys."""

    def __init__(self) -> None:
        super().__init__(
            name="get_graph_schema",
            description=(
                "Query the Neo4j graph for its schema: node labels, relationship types, "
                "and property keys. Useful for understanding what is stored in the graph "
                "before writing specific Cypher queries. "
                "Returns {status, labels, relationship_types, property_keys}."
            ),
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        )

    @override
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        uri, user, password = _get_neo4j_config()
        db_name = get_neo4j_db_name(tool_context)
        try:
            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                label_records, _, _ = driver.execute_query(
                    "CALL db.labels() YIELD label RETURN collect(label) AS labels",
                    database_=db_name,
                )
                rel_records, _, _ = driver.execute_query(
                    "CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN collect(relationshipType) AS relationship_types",
                    database_=db_name,
                )
                prop_records, _, _ = driver.execute_query(
                    "CALL db.propertyKeys() YIELD propertyKey "
                    "RETURN collect(propertyKey) AS property_keys",
                    database_=db_name,
                )

            labels = label_records[0]["labels"] if label_records else []
            rel_types = rel_records[0]["relationship_types"] if rel_records else []
            prop_keys = prop_records[0]["property_keys"] if prop_records else []

            return {
                "status": "success",
                "labels": labels,
                "relationship_types": rel_types,
                "property_keys": prop_keys,
            }
        except Exception as e:
            logger.error(f"get_graph_schema failed: {e}")
            return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# SearchGraphEntitiesTool
# ---------------------------------------------------------------------------


class SearchGraphEntitiesTool(BaseTool):
    """Case-insensitive keyword search across Neo4j node labels and relationship types."""

    def __init__(self) -> None:
        super().__init__(
            name="search_graph_entities",
            description=(
                "Search for node labels and relationship types in the Neo4j graph that contain "
                "the given keyword (case-insensitive substring match). "
                "Useful for discovering ASHRAE 223P class names before writing Cypher queries. "
                "Returns {status, keyword, matching_labels, matching_relationship_types}."
            ),
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "keyword": types.Schema(
                        type=types.Type.STRING,
                        description="The keyword to search for (case-insensitive substring match).",
                    ),
                },
                required=["keyword"],
            ),
        )

    @override
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        keyword = args.get("keyword", "")
        if not keyword:
            return {
                "status": "error",
                "message": "keyword is required",
                "matching_labels": [],
                "matching_relationship_types": [],
            }

        uri, user, password = _get_neo4j_config()
        db_name = get_neo4j_db_name(tool_context)
        try:
            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                label_records, _, _ = driver.execute_query(
                    "CALL db.labels() YIELD label RETURN collect(label) AS labels",
                    database_=db_name,
                )
                rel_records, _, _ = driver.execute_query(
                    "CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN collect(relationshipType) AS relationship_types",
                    database_=db_name,
                )

            all_labels: list[str] = label_records[0]["labels"] if label_records else []
            all_rels: list[str] = rel_records[0]["relationship_types"] if rel_records else []

            kw_lower = keyword.lower()
            matching_labels = [lbl for lbl in all_labels if kw_lower in lbl.lower()]
            matching_rels = [rel for rel in all_rels if kw_lower in rel.lower()]

            return {
                "status": "success",
                "keyword": keyword,
                "matching_labels": matching_labels,
                "matching_relationship_types": matching_rels,
            }
        except Exception as e:
            logger.error(f"search_graph_entities failed: {e}")
            return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

execute_cypher_tool = ExecuteCypherTool()
execute_cypher_batch_tool = ExecuteCypherBatchTool()
get_graph_schema_tool = GetGraphSchemaTool()
search_graph_entities_tool = SearchGraphEntitiesTool()
