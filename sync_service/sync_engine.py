import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from mcp_client import McpSyncClient

logger = logging.getLogger("sync_service.sync_engine")

LAST_SYNCED_PATH = os.path.join(os.path.dirname(__file__), ".last_synced_state.json")


class SyncEngine:
    """Diffs internal_grid state against last-synced state and calls MCP for changes."""

    def __init__(self, mcp_client: McpSyncClient, persist_path: str = LAST_SYNCED_PATH):
        self.mcp_client = mcp_client
        self.persist_path = persist_path
        self._last_synced: Dict[str, Dict] = {}  # keyed by component name
        self._load_persisted_state()

    def _load_persisted_state(self):
        """Load last-synced state from disk for crash recovery."""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r") as f:
                    data = json.load(f)
                self._last_synced = {c["name"]: c for c in data.get("components", [])}
                logger.info(f"Loaded persisted state: {len(self._last_synced)} components")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load persisted state: {e}. Starting fresh.")
                self._last_synced = {}

    def _persist_state(self):
        """Save current synced state to disk."""
        components = list(self._last_synced.values())
        with open(self.persist_path, "w") as f:
            json.dump({"components": components}, f, indent=2)

    def diff(self, current_components: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """Compare current state against last-synced state.
        Returns: (to_create, to_delete)
        - to_create: components in current but not in last-synced (by name)
        - to_delete: components in last-synced but not in current (by name)
        """
        current_by_name = {c["name"]: c for c in current_components}
        last_names = set(self._last_synced.keys())
        current_names = set(current_by_name.keys())

        new_names = current_names - last_names
        deleted_names = last_names - current_names

        to_create = [current_by_name[n] for n in new_names]
        to_delete = [self._last_synced[n] for n in deleted_names]

        return to_create, to_delete

    async def sync(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run one sync cycle: diff, call MCP for each change, update last-synced.
        Args:
            current_state: The internal_grid dict with key "components" (list of component dicts)
        Returns:
            Summary dict with created/deleted counts and any errors
        """
        components = current_state.get("components", [])
        to_create, to_delete = self.diff(components)

        if not to_create and not to_delete:
            logger.debug(f"[sync] No changes — {len(components)} components already in sync")
            return {"created": 0, "deleted": 0, "errors": []}

        logger.info(f"[sync] Diff: {len(to_create)} to CREATE, {len(to_delete)} to DELETE")
        if to_create:
            logger.info(f"[sync] Creating: {[c['name'] for c in to_create]}")
        if to_delete:
            logger.info(f"[sync] Deleting: {[c['name'] for c in to_delete]}")

        errors = []

        # Process deletes first (avoid name conflicts)
        for comp in to_delete:
            try:
                await self.mcp_client.delete_component(comp)
                del self._last_synced[comp["name"]]
            except Exception as e:
                err = f"Failed to delete {comp['name']}: {e}"
                logger.error(err)
                errors.append(err)

        # Process creates
        for comp in to_create:
            try:
                logger.info(f"[sync] Calling MCP create for {comp['type']} '{comp['name']}'")
                result = await self.mcp_client.create_component(comp)
                logger.info(f"[sync] MCP create result: {result}")
                self._last_synced[comp["name"]] = comp
            except Exception as e:
                err = f"Failed to create {comp['name']}: {e}"
                logger.error(f"[sync] {err}", exc_info=True)
                errors.append(err)

        # Persist state after sync
        self._persist_state()

        summary = {"created": len(to_create) - len([e for e in errors if "create" in e.lower()]),
                    "deleted": len(to_delete) - len([e for e in errors if "delete" in e.lower()]),
                    "errors": errors}
        logger.info(f"Sync complete: {summary}")
        return summary
