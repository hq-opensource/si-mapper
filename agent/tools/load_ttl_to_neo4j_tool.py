from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any
from typing_extensions import override

from google.adk.tools import BaseTool, ToolContext
from google.genai import types
from neo4j import GraphDatabase

from utils.project_utils import get_system_path, get_neo4j_db_name, get_graph_backend, get_graph_namespace

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
        db_name = get_neo4j_db_name(tool_context)
        ns = get_graph_namespace(tool_context)  # None unless neo4j_prefix mode
        logger.info(f"Using Neo4j database: {db_name}" + (f" (namespace: {ns})" if ns else ""))

        try:
            backend = get_graph_backend()

            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                if backend not in ("neo4j_single", "neo4j_prefix"):
                    # --- Enterprise mode: create DB if missing ---
                    existing, _, _ = driver.execute_query(
                        "SHOW DATABASES YIELD name WHERE name = $name RETURN name",
                        {"name": db_name},
                        database_="system",
                    )
                    db_exists = len(existing) > 0
                    if not db_exists:
                        logger.info("Database '%s' not found — creating it", db_name)
                        driver.execute_query(
                            f"CREATE DATABASE `{db_name}`",
                            database_="system",
                        )
                        logger.info("Database '%s' created", db_name)
                    else:
                        # Wipe all existing data
                        driver.execute_query("MATCH (n) DETACH DELETE n", database_=db_name)
                        driver.execute_query("CALL n10s.graphconfig.drop()", database_=db_name)
                        driver.execute_query("DROP CONSTRAINT n10s_unique_uri IF EXISTS", database_=db_name)
                else:
                    # --- Community Edition modes ---
                    if ns:
                        # neo4j_prefix: only delete this system's nodes
                        driver.execute_query(
                            "MATCH (n {_graph_ns: $ns}) DETACH DELETE n",
                            {"ns": ns}, database_=db_name,
                        )
                    else:
                        # neo4j_single: wipe entire database
                        driver.execute_query("MATCH (n) DETACH DELETE n", database_=db_name)

                    # n10s config drop — only touch when no namespace isolation is active
                    if not ns:
                        try:
                            driver.execute_query("CALL n10s.graphconfig.drop()", database_=db_name)
                        except Exception:
                            pass  # config may not exist yet on first run
                        driver.execute_query(
                            "DROP CONSTRAINT n10s_unique_uri IF EXISTS", database_=db_name
                        )

                # Step 5: n10s constraint + init
                if not ns:
                    # neo4j_single / enterprise: safe to reinit every time
                    driver.execute_query(
                        "CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS "
                        "FOR (r:Resource) REQUIRE r.uri IS UNIQUE",
                        database_=db_name,
                    )
                    driver.execute_query(
                        "CALL n10s.graphconfig.init({handleVocabUris: 'IGNORE'})",
                        database_=db_name,
                    )
                else:
                    # neo4j_prefix: ensure constraint + config exist; skip if already set
                    try:
                        driver.execute_query(
                            "CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS "
                            "FOR (r:Resource) REQUIRE r.uri IS UNIQUE",
                            database_=db_name,
                        )
                        driver.execute_query(
                            "CALL n10s.graphconfig.init({handleVocabUris: 'IGNORE'})",
                            database_=db_name,
                        )
                    except Exception:
                        pass  # already initialised

                # Step 6: Import TTL inline
                records, _, _ = driver.execute_query(
                    "CALL n10s.rdf.import.inline($ttl_content, 'Turtle') "
                    "YIELD terminationStatus, triplesLoaded, triplesParsed "
                    "RETURN terminationStatus, triplesLoaded, triplesParsed",
                    {"ttl_content": ttl_content},
                    database_=db_name,
                )
                triples_loaded = records[0]["triplesLoaded"] if records else 0
                termination = records[0]["terminationStatus"] if records else "unknown"

                # Step 6b (prefix mode only): stamp newly-imported nodes with the namespace
                if ns:
                    driver.execute_query(
                        "MATCH (n) WHERE n._graph_ns IS NULL SET n._graph_ns = $ns",
                        {"ns": ns}, database_=db_name,
                    )
                    logger.info("Stamped imported nodes with _graph_ns='%s'", ns)

                # Step 7: Count nodes and relationships for the return value
                node_records, _, _ = driver.execute_query(
                    "MATCH (n) RETURN count(n) AS cnt", database_=db_name
                )
                rel_records, _, _ = driver.execute_query(
                    "MATCH ()-[r]->() RETURN count(r) AS cnt", database_=db_name
                )
                node_count = node_records[0]["cnt"] if node_records else 0
                rel_count = rel_records[0]["cnt"] if rel_records else 0

            ns_suffix = f" (namespace: {ns})" if ns else ""
            logger.info(f"Neo4j import complete: {triples_loaded} triples, {node_count} nodes, {rel_count} relationships{ns_suffix}")
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
