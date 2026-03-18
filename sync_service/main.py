"""
Sync Service — Standalone process that polls the agent's internal_grid state
and replicates changes to GraphyVAC via the MCP server.

Usage:
    cd /home/juan/codes/si-mapper
    source agent/.venv/bin/activate
    python -m sync_service.main

Requires:
    - Agent service running on port 8001 (for /session_state endpoint)
    - MCP server running on port 8080
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional

import httpx

from sync_service.mcp_client import McpSyncClient
from sync_service.sync_engine import SyncEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("sync_service.main")

# Configuration
AGENT_STATE_URL = os.getenv("AGENT_STATE_URL", "http://localhost:8001/session_state")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8080/mcp/")
POLL_INTERVAL = float(os.getenv("SYNC_POLL_INTERVAL", "2.0"))  # seconds


async def fetch_internal_grid(http_client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Fetch the agent's internal_grid state from the /session_state endpoint."""
    try:
        response = await http_client.get(AGENT_STATE_URL)
        response.raise_for_status()
        state = response.json()
        internal_grid = state.get("internal_grid")
        if internal_grid is None:
            logger.debug("No 'internal_grid' key in session state yet")
            return None
        return internal_grid
    except httpx.ConnectError:
        logger.warning(f"Cannot connect to agent at {AGENT_STATE_URL} — is the agent running?")
        return None
    except Exception as e:
        logger.error(f"Error fetching session state: {e}")
        return None


async def poll_loop(engine: SyncEngine):
    """Main polling loop: fetch state -> diff -> sync -> wait."""
    logger.info(f"Starting sync polling loop (interval={POLL_INTERVAL}s)")
    logger.info(f"Agent state URL: {AGENT_STATE_URL}")
    logger.info(f"MCP URL: {MCP_URL}")

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        while True:
            internal_grid = await fetch_internal_grid(http_client)

            if internal_grid is not None:
                try:
                    summary = await engine.sync(internal_grid)
                    if summary["created"] > 0 or summary["deleted"] > 0:
                        logger.info(f"Sync result: created={summary['created']}, deleted={summary['deleted']}")
                    if summary["errors"]:
                        for err in summary["errors"]:
                            logger.error(f"Sync error: {err}")
                except Exception as e:
                    logger.error(f"Sync cycle failed: {e}", exc_info=True)

            await asyncio.sleep(POLL_INTERVAL)


async def main():
    """Entry point for the sync service."""
    mcp_client = McpSyncClient(mcp_url=MCP_URL)
    engine = SyncEngine(mcp_client)

    logger.info("Sync service starting...")
    try:
        await poll_loop(engine)
    except KeyboardInterrupt:
        logger.info("Sync service stopped by user")
    except Exception as e:
        logger.error(f"Sync service crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
