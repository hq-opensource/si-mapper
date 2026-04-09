from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any
from typing_extensions import override

from google.adk.tools import BaseTool, ToolContext
from google.genai import types
from neo4j import GraphDatabase

from utils.project_utils import get_system_path

logger = logging.getLogger(__name__)


class LoadTtlToNeo4jTool(BaseTool):
    """Wipes Neo4j and reimports the current ontology.ttl via Neosemantics n10s.rdf.import.inline."""

    def __init__(self):
        super().__init__(
            name="load_ttl_to_neo4j",
            description=(
                "Wipes the Neo4j graph database and reimports the current ontology.ttl file "
                "using Neosemantics. Returns node_count and relationship_count on success."
            ),
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        )

    @override
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        # Preferred: system-scoped TTL written by the ontology validator (13-09)
        ttl_path = Path(get_system_path(tool_context, os.path.join("ttl", "latest_ontology.ttl"))).resolve()
        if not ttl_path.exists():
            return {
                "status": "error",
                "message": (
                    f"ontology.ttl not found at {ttl_path} — "
                    "run the ontology validator first"
                ),
            }

        ttl_content = ttl_path.read_text(encoding="utf-8")
        logger.info(f"Read {len(ttl_content)} chars from {ttl_path}")

        uri = os.getenv("NEO4J_BOLT_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j_password")

        try:
            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                # Step 1: Wipe all existing data
                driver.execute_query("MATCH (n) DETACH DELETE n", database_="neo4j")

                # Step 2: Drop existing n10s config (handles missing gracefully)
                driver.execute_query(
                    "CALL n10s.graphconfig.drop()",
                    database_="neo4j",
                )

                # Step 3: Drop and recreate uniqueness constraint
                driver.execute_query("DROP CONSTRAINT n10s_unique_uri IF EXISTS", database_="neo4j")
                driver.execute_query(
                    "CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE",
                    database_="neo4j",
                )

                # Step 4: Initialize n10s graph config
                driver.execute_query(
                    "CALL n10s.graphconfig.init({handleVocabUris: 'IGNORE'})",
                    database_="neo4j",
                )

                # Step 5: Import TTL inline
                records, _, _ = driver.execute_query(
                    "CALL n10s.rdf.import.inline($ttl_content, 'Turtle') "
                    "YIELD terminationStatus, triplesLoaded, triplesParsed "
                    "RETURN terminationStatus, triplesLoaded, triplesParsed",
                    {"ttl_content": ttl_content},
                    database_="neo4j",
                )
                triples_loaded = records[0]["triplesLoaded"] if records else 0
                termination = records[0]["terminationStatus"] if records else "unknown"

                # Step 6: Count nodes and relationships for the return value
                node_records, _, _ = driver.execute_query(
                    "MATCH (n) RETURN count(n) AS cnt", database_="neo4j"
                )
                rel_records, _, _ = driver.execute_query(
                    "MATCH ()-[r]->() RETURN count(r) AS cnt", database_="neo4j"
                )
                node_count = node_records[0]["cnt"] if node_records else 0
                rel_count = rel_records[0]["cnt"] if rel_records else 0

            logger.info(f"Neo4j import complete: {triples_loaded} triples, {node_count} nodes, {rel_count} relationships")
            return {
                "status": "success",
                "triples_loaded": triples_loaded,
                "termination_status": termination,
                "node_count": node_count,
                "relationship_count": rel_count,
            }
        except Exception as e:
            logger.error(f"Neo4j import failed: {e}")
            return {"status": "error", "message": str(e)}


load_ttl_to_neo4j_tool = LoadTtlToNeo4jTool()
