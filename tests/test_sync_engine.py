"""
Unit tests for sync_service/sync_engine.py and sync_service/mcp_client.py

Diff logic tests: pure computation, no MCP calls needed.
MCP client mapping tests: call_tool is mocked to capture arguments.
Persist/load tests: use /tmp/test_sync_state_*.json paths.

Run with:
    cd /home/juan/codes/si-mapper
    python -m pytest tests/test_sync_engine.py -v
"""

import asyncio
import json
import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure project root on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------------------------------------------------------
# Stub heavy external dependencies before importing sync_service modules
# ---------------------------------------------------------------------------

# Stub google.adk hierarchy
def _ensure_stub(module_name, **attrs):
    if module_name not in sys.modules:
        mod = types.ModuleType(module_name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[module_name] = mod
    return sys.modules[module_name]

_ensure_stub("google")
_ensure_stub("google.adk")
_ensure_stub("google.adk.tools")
_ensure_stub("google.adk.tools.mcp_tool")

# streamablehttp_client stub — never actually called in mapping tests
_session_manager_stub = _ensure_stub("google.adk.tools.mcp_tool.mcp_session_manager")
_session_manager_stub.streamablehttp_client = MagicMock()

# mcp stub
_mcp_stub = _ensure_stub("mcp")
_mcp_stub.ClientSession = MagicMock()

# Now import the modules under test
from sync_service.sync_engine import SyncEngine
from sync_service.mcp_client import McpSyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fan(name, coord=None, rotation=0):
    return {"id": "abc123", "type": "fan", "name": name,
            "coord": coord or [1, 1], "rotation": rotation}

def _make_duct(name, start=None, end=None):
    return {"id": "def456", "type": "duct", "name": name,
            "start": start or [0, 0], "end": end or [5, 0]}

def _make_sensor(name, sensor_type="duct_sensor_temperature", coord=None):
    return {"id": "ghi789", "type": sensor_type, "name": name,
            "coord": coord or [3, 3]}


def _tmp_path(suffix=""):
    return f"/tmp/test_sync_state_{os.getpid()}{suffix}.json"


def _run(coro):
    """Run an async coroutine in a new event loop."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Diff tests (pure, no MCP)
# ---------------------------------------------------------------------------

class TestDiff(unittest.TestCase):

    def _make_engine(self, persist_path=None):
        client = McpSyncClient()
        if persist_path is None:
            persist_path = _tmp_path("_diff")
        return SyncEngine(client, persist_path=persist_path)

    def test_diff_empty_to_new(self):
        """Diff from empty state to 2 components = 2 creates, 0 deletes."""
        engine = self._make_engine()
        components = [_make_fan("fan-a"), _make_fan("fan-b", coord=[2, 2])]
        to_create, to_delete = engine.diff(components)
        self.assertEqual(len(to_create), 2)
        self.assertEqual(len(to_delete), 0)

    def test_diff_no_change(self):
        """Same state as last synced = 0 creates, 0 deletes."""
        engine = self._make_engine()
        fan = _make_fan("fan-nc")
        # Seed last_synced manually
        engine._last_synced = {"fan-nc": fan}
        to_create, to_delete = engine.diff([fan])
        self.assertEqual(len(to_create), 0)
        self.assertEqual(len(to_delete), 0)

    def test_diff_additions(self):
        """1 existing + 1 new component = 1 create, 0 deletes."""
        engine = self._make_engine()
        existing = _make_fan("fan-existing")
        new_comp = _make_fan("fan-new", coord=[9, 9])
        engine._last_synced = {"fan-existing": existing}
        to_create, to_delete = engine.diff([existing, new_comp])
        self.assertEqual(len(to_create), 1)
        self.assertEqual(to_create[0]["name"], "fan-new")
        self.assertEqual(len(to_delete), 0)

    def test_diff_deletions(self):
        """1 existing in last_synced, current empty = 0 creates, 1 delete."""
        engine = self._make_engine()
        fan = _make_fan("fan-gone")
        engine._last_synced = {"fan-gone": fan}
        to_create, to_delete = engine.diff([])
        self.assertEqual(len(to_create), 0)
        self.assertEqual(len(to_delete), 1)
        self.assertEqual(to_delete[0]["name"], "fan-gone")

    def test_diff_replacement(self):
        """Remove old + add new in same cycle: 1 create, 1 delete."""
        engine = self._make_engine()
        old_fan = _make_fan("fan-old")
        new_fan = _make_fan("fan-new", coord=[8, 8])
        engine._last_synced = {"fan-old": old_fan}
        to_create, to_delete = engine.diff([new_fan])
        self.assertEqual(len(to_create), 1)
        self.assertEqual(to_create[0]["name"], "fan-new")
        self.assertEqual(len(to_delete), 1)
        self.assertEqual(to_delete[0]["name"], "fan-old")


# ---------------------------------------------------------------------------
# Persist / load tests
# ---------------------------------------------------------------------------

class TestPersistAndLoad(unittest.TestCase):

    def test_persist_and_load(self):
        """Persist state, create new engine, verify state is loaded."""
        persist_path = _tmp_path("_persist")
        try:
            # Create engine and seed it with some synced state
            client = McpSyncClient()
            engine1 = SyncEngine(client, persist_path=persist_path)
            fan = _make_fan("fan-persist")
            engine1._last_synced = {"fan-persist": fan}
            engine1._persist_state()

            # Create a second engine pointing at same file
            engine2 = SyncEngine(client, persist_path=persist_path)
            self.assertIn("fan-persist", engine2._last_synced)
            loaded = engine2._last_synced["fan-persist"]
            self.assertEqual(loaded["name"], "fan-persist")
        finally:
            if os.path.exists(persist_path):
                os.remove(persist_path)


# ---------------------------------------------------------------------------
# MCP client tool mapping tests
# ---------------------------------------------------------------------------

class TestMcpClientToolMapping(unittest.TestCase):
    """Verify that create_component maps component types to correct tool names and args."""

    def _client_with_captured_call(self):
        """Return (client, captured) where captured is a list that records call_tool args."""
        client = McpSyncClient()
        captured = []

        async def fake_call_tool(tool_name, arguments):
            captured.append({"tool_name": tool_name, "arguments": arguments})
            return {"tool_name": tool_name, "status": "ok"}

        client.call_tool = fake_call_tool
        return client, captured

    def test_mcp_client_tool_mapping_duct(self):
        """create_component for duct maps to create_duct with start_coord/end_coord."""
        client, captured = self._client_with_captured_call()
        duct = _make_duct("duct-map", start=[0, 0], end=[10, 0])
        _run(client.create_component(duct))
        self.assertEqual(len(captured), 1)
        call = captured[0]
        self.assertEqual(call["tool_name"], "create_duct")
        self.assertIn("start_coord", call["arguments"])
        self.assertIn("end_coord", call["arguments"])
        self.assertEqual(call["arguments"]["name"], "duct-map")
        self.assertEqual(call["arguments"]["start_coord"], [0, 0])
        self.assertEqual(call["arguments"]["end_coord"], [10, 0])

    def test_mcp_client_tool_mapping_fan(self):
        """create_component for fan maps to create_fan with coord/rotation."""
        client, captured = self._client_with_captured_call()
        fan = _make_fan("fan-map", coord=[5, 5], rotation=180)
        _run(client.create_component(fan))
        self.assertEqual(len(captured), 1)
        call = captured[0]
        self.assertEqual(call["tool_name"], "create_fan")
        self.assertIn("coord", call["arguments"])
        self.assertIn("rotation", call["arguments"])
        self.assertEqual(call["arguments"]["name"], "fan-map")
        self.assertEqual(call["arguments"]["coord"], [5, 5])
        self.assertEqual(call["arguments"]["rotation"], 180)

    def test_mcp_client_tool_mapping_sensor(self):
        """create_component for sensor maps to create_{sensor_type} with coord."""
        client, captured = self._client_with_captured_call()
        sensor = _make_sensor("sensor-map", sensor_type="duct_sensor_temperature", coord=[3, 3])
        _run(client.create_component(sensor))
        self.assertEqual(len(captured), 1)
        call = captured[0]
        self.assertEqual(call["tool_name"], "create_duct_sensor_temperature")
        self.assertIn("coord", call["arguments"])
        self.assertEqual(call["arguments"]["name"], "sensor-map")
        self.assertEqual(call["arguments"]["coord"], [3, 3])
        self.assertNotIn("rotation", call["arguments"])


if __name__ == "__main__":
    unittest.main()
