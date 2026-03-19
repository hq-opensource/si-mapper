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

from mcp_client import McpSyncClient
from sync_engine import SyncEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("sync_service.main")

# Configuration
AGENT_STATE_URL = os.getenv("AGENT_STATE_URL", "http://localhost:8001/session_state")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8080/mcp/")
POLL_INTERVAL = float(os.getenv("SYNC_POLL_INTERVAL", "1.0"))  # seconds


async def fetch_internal_grid(http_client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Fetch the agent's internal_grid state from the /session_state endpoint."""
    try:
        response = await http_client.get(AGENT_STATE_URL)
        response.raise_for_status()
        state = response.json()

        # Diagnostic: log all top-level keys so we can see what's being returned
        keys = list(state.keys())
        logger.info(f"[fetch] /session_state returned {len(keys)} keys: {keys}")

        internal_grid = state.get("internal_grid")
        if internal_grid is None:
            logger.warning("[fetch] 'internal_grid' NOT found in session state — agent may not have written it yet")
            return None

        n = len(internal_grid.get("components", []))
        logger.info(f"[fetch] internal_grid found — {n} components")
        return internal_grid
    except httpx.ConnectError:
        logger.warning(f"[fetch] Cannot connect to agent at {AGENT_STATE_URL} — is the agent running?")
        return None
    except Exception as e:
        logger.error(f"[fetch] Error fetching session state: {e}")
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
    # DEACTIVATED: Sync is now handled by the agent's before/after callbacks.
    # See agent/utils/grid_sync_*.py and level_3_master_main_llm.py
    print("\n[DISABLED] The standalone sync service is no longer required.")
    print("Synchronization is now handled by the Master Agent lifecycle callbacks.")
    print("Refer to agent/utils/grid_sync_graphivac_to_agent.py and grid_sync_agent_to_graphivac.py\n")
    return

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
